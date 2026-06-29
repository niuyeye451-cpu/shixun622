"""
统一 AI 推理管线:
  用户输入 → 关键词提取 → 知识图谱查询 → 组装 Context → DeepSeek API → 返回结果

若未配置 DEEPSEEK_API_KEY，则降级为基于知识图谱的模板回答。
"""

import re
import json
import os
from typing import Optional, List, Dict, Any

from app.graph_db import get_graph_db


# ====================== Step 1: 关键词提取 ======================

def extract_keywords(text: str) -> List[str]:
    """从中文文本中提取关键医学术语（n-gram + 知识图谱实体匹配）"""
    graph_db = get_graph_db()
    # 提取中文连续片段
    cjk_chars = re.findall(r'[一-鿿]+', text)

    # 策略1: 对每个长片段，生成2-6字n-gram，测试是否在KG中存在
    candidates = []
    for segment in cjk_chars:
        seg_len = len(segment)
        # 2-4字 n-grams，优先匹配更长的词
        for n in range(min(6, seg_len), 1, -1):
            for i in range(seg_len - n + 1):
                ngram = segment[i:i + n]
                if ngram not in candidates:
                    candidates.append(ngram)

    # 在KG中验证候选词
    keywords = []
    for c in candidates[:30]:  # 最多测试30个
        entities = graph_db.search_nodes(c, limit=1)
        if entities:
            keywords.append(c)

    # 策略2: 如果没有匹配到，使用所有2-4字候选词
    if not keywords:
        keywords = [c for c in candidates if 2 <= len(c) <= 4][:10]

    return list(dict.fromkeys(keywords))[:10]


# ====================== Step 2: 知识图谱查询 ======================

def query_knowledge_graph(keywords: List[str], max_per_keyword: int = 5) -> List[Dict]:
    """
    对每个关键词在知识图谱中搜索相关实体，并附带一跳关系。
    返回结构化的知识上下文列表。
    """
    graph_db = get_graph_db()
    knowledge = []
    seen_ids = set()

    for kw in keywords:
        entities = graph_db.search_nodes(kw, limit=max_per_keyword)
        for entity in entities:
            eid = entity.get('id', '')
            if eid in seen_ids:
                continue
            seen_ids.add(eid)

            props = entity.get('properties', {})
            item = {
                'entity_id': eid,
                'name': entity.get('name', ''),
                'type': entity.get('label', ''),
                'description': props.get('desc', '')[:300] if props.get('desc') else '',
                'cause': props.get('cause', '')[:200] if props.get('cause') else '',
                'prevent': props.get('prevent', '')[:200] if props.get('prevent') else '',
                'aliases': props.get('alias', [])[:5] if isinstance(props.get('alias'), list) else [],
                'related': []
            }

            # 获取一跳关系
            relations = graph_db.get_relations_by_node(eid)
            for rel in relations[:8]:
                target = graph_db.get_node_by_id(rel.get('target_id', ''))
                if target:
                    item['related'].append({
                        'relation': rel.get('relation_type', ''),
                        'relation_name': rel.get('relation_name', ''),
                        'target_name': target.get('name', ''),
                        'target_type': target.get('label', '')
                    })

            knowledge.append(item)

    return knowledge


# ====================== Step 3: 组装上下文 Prompt ======================

def build_context_prompt(user_query: str, knowledge: List[Dict], role: str = "patient") -> str:
    """将知识图谱查询结果组装为给 AI 的上下文提示"""
    if not knowledge:
        return f"用户问题: {user_query}\n\n知识库中未找到相关信息。请根据你的通用医学知识回答，并注明信息来源于通用知识。"

    context_parts = []
    for item in knowledge[:15]:  # 最多15条
        parts = [f"【{item['type']}】{item['name']}"]
        if item.get('description'):
            parts.append(f"  描述: {item['description'][:200]}")
        if item.get('cause'):
            parts.append(f"  病因: {item['cause'][:150]}")
        if item.get('prevent'):
            parts.append(f"  预防: {item['prevent'][:150]}")
        if item.get('aliases'):
            parts.append(f"  别名: {', '.join(item['aliases'][:3])}")
        if item.get('related'):
            rel_strs = [f"{r['target_name']}({r['relation_name'] or r['relation']})" for r in item['related'][:5]]
            parts.append(f"  关联: {', '.join(rel_strs)}")
        context_parts.append('\n'.join(parts))

    context_text = '\n\n---\n\n'.join(context_parts)

    if role == "doctor":
        system = (
            "你是一个临床决策辅助AI，为医师提供专业的诊疗参考。"
            "请基于以下知识图谱数据，给出严谨的临床分析，包括可能的诊断、建议检查、治疗原则和用药注意事项。"
            "每一条结论必须注明来自知识库还是通用医学知识。\n\n"
        )
    else:
        system = (
            "你是一个医疗健康咨询AI，为患者提供通俗易懂的健康指导。"
            "请基于以下知识图谱数据，用平实的语言回答用户问题，给出就医建议。"
            "禁止给出明确的诊断结论，必须建议咨询专业医生。\n\n"
        )

    return system + f"知识库数据:\n{context_text}\n\n用户问题: {user_query}"


# ====================== Step 4: 调用外部 AI API ======================

_client = None

def _get_client():
    """延迟初始化 OpenAI 兼容客户端（指向 DeepSeek）"""
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").strip()

    if api_key and api_key != "your-deepseek-api-key-here":
        from openai import OpenAI
        _client = OpenAI(api_key=api_key, base_url=base_url)
        return _client
    return None


def is_ai_available() -> bool:
    """检查外部 AI API 是否可用"""
    return _get_client() is not None


def call_ai(prompt: str, max_tokens: int = 1500, temperature: float = 0.3) -> str:
    """调用外部 AI API 生成回答"""
    client = _get_client()
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

    if client is None:
        return _fallback_response(prompt)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的医疗AI助手。请严格基于提供的知识库数据回答问题。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"[AI Service] API call failed: {e}")
        return _fallback_response(prompt)


def _fallback_response(prompt: str) -> str:
    """外部 AI 不可用时的降级方案：基于知识图谱数据生成模板回答"""
    # 从 prompt 中提取用户问题
    user_q = ""
    for line in prompt.split('\n'):
        if line.startswith('用户问题:'):
            user_q = line.replace('用户问题:', '').strip()

    # 从 prompt 中提取知识条目
    entities_found = []
    for part in prompt.split('---'):
        name_match = re.search(r'【(\w+)】(.+)', part)
        desc_match = re.search(r'描述:\s*(.+?)(?:\n|$)', part)
        if name_match:
            entities_found.append({
                'type': name_match.group(1),
                'name': name_match.group(2).strip(),
                'desc': desc_match.group(1)[:150] if desc_match else ''
            })

    if not entities_found:
        return (
            f"关于「{user_q}」，知识库中暂未找到直接相关的信息。\n\n"
            "建议您：\n"
            "1. 尝试用更具体的症状或疾病名称搜索\n"
            "2. 前往正规医院就诊，由专业医生进行诊断\n"
            "3. 不要自行用药，请遵医嘱"
        )

    lines = [f"基于知识库检索，关于「{user_q}」的参考信息如下：\n"]
    for e in entities_found[:8]:
        lines.append(f"• {e['name']}（{e['type']}）")
        if e['desc']:
            lines.append(f"  {e['desc'][:200]}")

    lines.append(f"\n⚠️ 以上信息来自知识图谱数据库，仅供参考。请咨询专业医生获取准确的诊疗建议。")
    lines.append(f"[当前为离线模式，未接入外部AI。如需AI分析，请配置 DEEPSEEK_API_KEY]")

    return '\n'.join(lines)


# ====================== 统一推理入口 ======================

def inference(user_query: str, role: str = "patient",
              include_graph: bool = True, max_tokens: int = 1500) -> Dict[str, Any]:
    """
    统一 AI 推理管线入口。

    Args:
        user_query: 用户输入的问题
        role: 角色 (patient / doctor)
        include_graph: 是否附带知识图谱数据
        max_tokens: AI 最大输出 token 数

    Returns:
        {
            "answer": str,
            "keywords": list,
            "knowledge": list,
            "is_ai_generated": bool
        }
    """
    # Step 1: 关键词提取
    keywords = extract_keywords(user_query)

    # Step 2: 知识图谱查询
    knowledge = query_knowledge_graph(keywords) if include_graph else []

    # Step 3: 组装 Prompt
    prompt = build_context_prompt(user_query, knowledge, role)

    # Step 4: 调用外部 AI（或降级）
    ai_available = is_ai_available()
    answer = call_ai(prompt, max_tokens=max_tokens)

    return {
        "answer": answer,
        "keywords": keywords,
        "knowledge": knowledge,
        "is_ai_generated": ai_available,
        "entities_matched": len(knowledge)
    }
