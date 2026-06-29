#!/usr/bin/env python3
# coding: utf-8
"""
同义词词典扩充脚本
================================================================
需求来源（项目文档）：
  "同义词与别名扩展：维护疾病、症状、药品的同义词词典，
   提高'感冒/上呼吸道感染''头疼/头痛'等表达的召回率。"

数据来源：
  疾病别名 —— 从 medical.json 的 desc 字段自动挖掘
              （又称/简称/俗称/又名/也叫/又称为/又称之）
  症状俗语 —— 人工维护的口语→规范词映射
  药品别名 —— 从 drug_detail 拆分 + 通用名/商品名

输出（写入 ./output/）：
  - synonym_full.json   完整同义词词典 {标准名: [别名...]}
  - synonym_alias.json  反向索引 {别名: 标准名}（问答召回直接用）
  - synonym_report.md   挖掘统计报告

用法：python build_synonym.py
================================================================
"""

import json
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, "QASystemOnMedicalKG", "data", "medical.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ============================================================
# 一、疾病别名挖掘（从 desc）
# ============================================================
# 触发词：又称、简称、俗称、又名、也叫、又称为、又称之、又称作
ALIAS_TRIGGERS = [
    "又称之为", "又称为", "又称作", "又称叫",
    "又称", "简称", "俗称", "又名", "也叫", "又称曰",
]

# 提取触发词后的别名片段（到句号/逗号/分号为止，最长 60 字符）
# 注意：长触发词优先匹配，避免"又称"吃掉"又称之为"
ALIAS_TRIGGERS_SORTED = sorted(ALIAS_TRIGGERS, key=len, reverse=True)

# 匹配别名片段：触发词 + 内容 + 终止标点
PATTERN_TEMPLATE = r"{trigger}([\u4e00-\u9fa5A-Za-z0-9（）\(\)\-·、，,\s]{{1,80}})[。，；,;。)]"


def extract_aliases_from_desc(desc):
    """从一条 desc 中抽取所有别名，返回别名列表（可能含多个，需进一步切分）"""
    if not desc:
        return []
    raw_fragments = []
    for trigger in ALIAS_TRIGGERS_SORTED:
        pat = PATTERN_TEMPLATE.format(trigger=re.escape(trigger))
        for m in re.finditer(pat, desc):
            frag = m.group(1).strip().rstrip("。，；,;等")
            if frag:
                raw_fragments.append(frag)
    # 去重（同一条 desc 可能被多个触发词命中同一片段）
    seen, result = set(), []
    for frag in raw_fragments:
        if frag not in seen:
            seen.add(frag)
            result.append(frag)
    return result


def split_fragment(fragment):
    """
    将一个别名片段切分为多个独立别名：
      '休克肺、创伤肺' → ['休克肺', '创伤肺']
      '打鼾、打呼噜、睡眠呼吸暂停综合症' → ['打鼾','打呼噜','睡眠呼吸暂停综合症']
      '小叶肺炎' → ['小叶肺炎']
    并分离出括号内的英文缩写作为独立别名：
      '抗基膜性肾小球肾炎' → ['抗基膜性肾小球肾炎']
      '军团病(legionelladisease)' → ['军团病', 'legionelladisease']（英文过长可截断/跳过）
    """
    aliases = []
    # 先按 顿号/逗号/或 切分
    parts = re.split(r"[、，,]|或者|或", fragment)
    for part in parts:
        part = part.strip()
        if not part or len(part) > 20:      # 过滤过长（多半是句子误匹配）
            continue
        # 处理中英文混排：提取中文部分 + 英文括号缩写
        cn = re.sub(r"[（(].*?[)）]", "", part).strip()  # 去掉括号内容
        if cn and 2 <= len(cn) <= 20 and re.search(r"[\u4e00-\u9fa5]", cn):
            aliases.append(cn)
        # 英文缩写：纯字母、长度 2-10、大写为主（如 PAP / ARDS / EFE）
        for m in re.finditer(r"[（(]([A-Za-z][A-Za-z\-]{1,9})[)）]", part):
            abbr = m.group(1)
            if 2 <= len(abbr) <= 10:
                aliases.append(abbr)
    return aliases


# 句子片段噪声前缀/包含词（这些一旦出现，几乎可断定不是别名）
NOISE_PREFIX = (
    "主要", "临床", "病原", "病程", "病变", "常呈", "常诊断", "常与",
    "多见", "多为", "多发生", "易", "好发", "通过", "由于", "因为",
    "为", "由", "在", "其", "该", "本", "可", "若", "如",
    "俗称", "又称", "简称", "又名", "也叫", "亦称", "即",
    "皮肤", "脊髓", "神经", "先天性", "继发", "原发",
    "数个", "几个", "一种", "一组", "一类",
    "导致", "造成", "形成", "作用", "缓慢", "最后", "现多", "同时",
    "成人", "抗体", "这种", "局麻", "炎症",
)
NOISE_CONTAIN = (
    "的症状", "的病理", "的特点", "的改变", "的因素", "的病因", "的命名",
    "首先描述", "代谢障碍", "功能低下", "无明显", "无器质",
    "表现为", "而导致", "从而", "所致", "所引起",
    "分为", "分成", "叫做",
    "导致", "造成", "而致", "作用在", "增加", "肿胀", "播散",
    "进入血液", "也有发病", "代谢紊乱", "冲动形成",
    "高反应性", "反应性增加",
)


def clean_alias(alias):
    """清洗单个别名，过滤句子片段噪声"""
    alias = alias.strip().strip("（）()，,。；;·、 ").strip()
    if len(alias) < 2 or len(alias) > 18:
        return None
    if alias.isdigit():
        return None
    # 残留触发词前缀
    for t in ("俗称", "又称", "简称", "又名", "也叫", "称为", "叫做", "即"):
        if alias.startswith(t):
            alias = alias[len(t):].strip()
            if len(alias) < 2:
                return None
    # 噪声前缀（描述性句子开头）
    for p in NOISE_PREFIX:
        if alias.startswith(p):
            return None
    # 噪声包含词
    for c in NOISE_CONTAIN:
        if c in alias:
            return None
    # 含"的/是/和/与/或/等/可/能"等连接词且较长 → 多半是短语
    if len(alias) > 5 and re.search(r"[的是和与或等可能为由因]", alias):
        return None
    # 必须含中文或为合法英文缩写
    has_cn = bool(re.search(r"[\u4e00-\u9fa5]", alias))
    is_abbr = bool(re.fullmatch(r"[A-Za-z][A-Za-z\-.]{1,19}", alias))
    if not has_cn and not is_abbr:
        return None
    # 中文别名应含医学词根，否则疑似片段（针对长中文串）
    if has_cn and len(alias) >= 6:
        med_root = re.search(r"(综合征|综合症|病|症|炎|痛|瘫|瘤|癌|肿|衰|竭|"
                             r"感染|中毒|缺陷|障碍|异常|增生|硬化|衰竭|"
                             r"肺炎|肝炎|肾炎|骨折|脱位|糜烂|溃疡|出血|栓塞)",
                             alias)
        if not med_root:
            return None
    return alias


def mine_disease_synonyms(records):
    """挖掘疾病别名，返回 {标准疾病名: set(别名)}"""
    syn = defaultdict(set)
    stats = {"hit": 0, "total_alias": 0, "multi": 0}
    for r in records:
        name = r.get("name", "").strip()
        desc = r.get("desc", "") or ""
        if not name or not desc:
            continue
        fragments = extract_aliases_from_desc(desc)
        all_aliases = []
        for frag in fragments:
            all_aliases.extend(split_fragment(frag))
        # 清洗 + 去重 + 排除与标准名相同
        cleaned = set()
        for a in all_aliases:
            c = clean_alias(a)
            if c and c != name:
                cleaned.add(c)
        if cleaned:
            syn[name] = cleaned
            stats["hit"] += 1
            stats["total_alias"] += len(cleaned)
            if len(cleaned) > 1:
                stats["multi"] += 1
    print(f"[疾病别名] 命中 {stats['hit']} 个疾病，"
          f"共挖出 {stats['total_alias']} 个别名（其中多别名疾病 {stats['multi']} 个）")
    return dict(syn), stats


# ============================================================
# 二、症状/药品口语同义词（人工 + 规则）
# ============================================================
# 症状：口语 → 规范词（问答系统用户常用口语）
SYMPTOM_COLLOQUIAL = {
    "头疼": "头痛",
    "肚子疼": "腹痛",
    "拉肚子": "腹泻",
    "发烧": "发热",
    "流鼻涕": "鼻塞",
    "咳嗽咳痰": "咳嗽",
    "干咳无痰": "干咳",
    "恶心呕吐": "恶心",
    "上感": "上呼吸道感染",
    "嗓子疼": "咽痛",
    "嗓子发炎": "咽炎",
    "眼花": "视力模糊",
    "心慌": "心悸",
    "喘不上气": "呼吸困难",
    "起不来床": "乏力",
    "没力气": "乏力",
    "睡不着": "失眠",
    "头晕目眩": "眩晕",
}

# 药品通用名 ↔ 常见商品名（高频药，可扩展）
DRUG_COLLOQUIAL = {
    # 通用名（标准）: [商品名/俗称]
    "布洛芬": ["芬必得", "美林"],
    "对乙酰氨基酚": ["扑热息痛", "泰诺林", "散列通"],
    "阿莫西林": ["阿莫仙"],
    "头孢氨苄": ["先锋4号", "头孢4号"],
    "复方氨酚烷胺": ["感康", "快克"],
    "蒙脱石散": ["思密达"],
    "双氯芬酸钠": ["扶他林"],
    "硝苯地平": ["拜新同", "心痛定"],
    "二甲双胍": ["格华止"],
    "阿托伐他汀": ["立普妥"],
    "奥美拉唑": ["洛赛克"],
    "藿香正气水": ["藿香正气液"],
    "复方丹参滴丸": ["丹参滴丸"],
}


def build_symptom_drug_synonyms():
    """构建症状、药品的同义词 {标准名: set(别名)}"""
    sym = defaultdict(set)
    for alias, std in SYMPTOM_COLLOQUIAL.items():
        sym[std].add(alias)
    drug = defaultdict(set)
    for std, aliases in DRUG_COLLOQUIAL.items():
        drug[std] = set(aliases)
    print(f"[症状口语] {len(sym)} 组；[药品别名] {len(drug)} 组")
    return dict(sym), dict(drug)


# ============================================================
# 三、汇总输出
# ============================================================
def write_outputs(disease_syn, symptom_syn, drug_syn, disease_stats):
    """
    输出三份文件：
      synonym_full.json  : {category: {标准名: [别名...]}}
      synonym_alias.json : {别名: 标准名}  （扁平，问答召回直接查）
      synonym_report.md  : 统计报告
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- synonym_full.json ---
    full = {
        "disease":  {k: sorted(v) for k, v in disease_syn.items()},
        "symptom":  {k: sorted(v) for k, v in symptom_syn.items()},
        "drug":     {k: sorted(v) for k, v in drug_syn.items()},
        "_meta": {
            "disease_count": len(disease_syn),
            "disease_alias_total": sum(len(v) for v in disease_syn.values()),
            "symptom_count": len(symptom_syn),
            "drug_count": len(drug_syn),
        },
    }
    p1 = os.path.join(OUTPUT_DIR, "synonym_full.json")
    with open(p1, "w", encoding="utf-8") as f:
        json.dump(full, f, ensure_ascii=False, indent=2)
    print(f"[产物] synonym_full.json → {p1}")

    # --- synonym_alias.json （反向索引：别名 → 标准名）---
    alias_map = {}
    for std, aliases in disease_syn.items():
        for a in aliases:
            alias_map[a] = std
    for std, aliases in symptom_syn.items():
        for a in aliases:
            alias_map[a] = std
    for std, aliases in drug_syn.items():
        for a in aliases:
            alias_map[a] = std
    p2 = os.path.join(OUTPUT_DIR, "synonym_alias.json")
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(alias_map, f, ensure_ascii=False, indent=2)
    print(f"[产物] synonym_alias.json（{len(alias_map)} 条 别名→标准名）→ {p2}")

    # --- synonym_report.md ---
    report = []
    report.append("# 同义词词典挖掘报告\n")
    report.append("## 1. 数据来源\n")
    report.append("- **疾病别名**：从 `medical.json` 的 `desc` 字段自动挖掘")
    report.append("  （触发词：又称/简称/俗称/又名/也叫/又称为/又称之）")
    report.append("- **症状口语**：人工维护的高频口语→规范词映射")
    report.append("- **药品别名**：通用名↔商品名映射（高频药）\n")
    report.append("## 2. 挖掘统计\n")
    report.append("| 类别 | 标准词数 | 别名总数 |")
    report.append("|------|---------|---------|")
    report.append(f"| 疾病 | {disease_stats['hit']} | {disease_stats['total_alias']} |")
    report.append(f"| 症状 | {len(symptom_syn)} | {sum(len(v) for v in symptom_syn.values())} |")
    report.append(f"| 药品 | {len(drug_syn)} | {sum(len(v) for v in drug_syn.values())} |")
    all_aliases = (disease_stats['total_alias']
                   + sum(len(v) for v in symptom_syn.values())
                   + sum(len(v) for v in drug_syn.values()))
    report.append(f"| **合计** | — | **{all_aliases}** |\n")

    report.append("## 3. 疾病别名示例\n")
    report.append("| 标准名 | 别名 |")
    report.append("|--------|------|")
    shown = 0
    for std, aliases in disease_syn.items():
        if shown >= 15:
            break
        report.append(f"| {std} | {'、'.join(sorted(aliases)[:4])} |")
        shown += 1
    report.append("")

    report.append("## 4. 使用方式\n")
    report.append("- **问答召回**：加载 `synonym_alias.json`，用户输入'头疼'→映射为'头痛'再查图谱")
    report.append("- **NER 词典扩充**：把别名加入对应实体词典，提升实体识别召回")
    report.append("- **图谱节点**：可将别名作为节点的 `alias` 属性存储\n")

    p3 = os.path.join(OUTPUT_DIR, "synonym_report.md")
    with open(p3, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"[产物] synonym_report.md → {p3}")


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("同义词词典扩充")
    print("=" * 60)

    # 读原始数据（同义词挖掘用原始 desc，清洗前的更全）
    records = []
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    print(f"[读取] {len(records)} 条疾病记录")

    # 挖掘疾病别名
    disease_syn, disease_stats = mine_disease_synonyms(records)
    # 构建 症状/药品 同义词
    symptom_syn, drug_syn = build_symptom_drug_synonyms()

    # 输出
    write_outputs(disease_syn, symptom_syn, drug_syn, disease_stats)

    print("=" * 60)
    print("完成！输出目录：", OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
