from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import json

from app.graph_db import get_graph_db
from app.schemas import ResponseModel
from app.services.ai_service import inference, extract_keywords, query_knowledge_graph


router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


class LlmQueryRequest(BaseModel):
    question: str
    user_type: str = "patient"
    context: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7


class LlmGraphQueryRequest(BaseModel):
    question: str
    use_rag: bool = True
    include_graph_data: bool = True


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    include_context: bool = True


@router.post("/query", response_model=ResponseModel)
def llm_query(request: LlmQueryRequest):
    """通用AI问答: 关键词提取 → KG查询 → AI生成"""
    result = inference(request.question, role=request.user_type, max_tokens=request.max_tokens)

    return ResponseModel(data={
        'answer': result['answer'],
        'related_entities': [{
            'id': k['entity_id'],
            'name': k['name'],
            'type': k['type'],
            'properties': {
                'desc': k.get('description', ''),
                'cause': k.get('cause', ''),
                'prevent': k.get('prevent', '')
            }
        } for k in result.get('knowledge', [])[:10]],
        'keywords': result['keywords'],
        'is_rag_used': True,
        'is_ai_generated': result['is_ai_generated'],
        'sources': [f"{k['name']} ({k['type']})" for k in result.get('knowledge', [])[:5]]
    })


@router.post("/graph-analysis", response_model=ResponseModel)
def llm_graph_analysis(request: LlmGraphQueryRequest):
    """知识图谱分析: 从KG提取疾病、症状、药物等关联"""
    graph_db = get_graph_db()

    keywords = extract_keywords(request.question)

    analysis_result = {
        'question': request.question,
        'analysis': {},
        'recommendations': [],
        'graph_data': None
    }

    for keyword in keywords:
        disease = graph_db.get_node_by_name(keyword, 'Disease')
        if disease:
            result = graph_db.get_graph_by_disease(keyword, max_depth=2)

            nodes_by_type = {}
            for node in result['nodes']:
                if node['label'] not in nodes_by_type:
                    nodes_by_type[node['label']] = []
                nodes_by_type[node['label']].append(node['name'])

            analysis_result['analysis'][keyword] = {
                'disease_id': disease['id'],
                'symptoms': nodes_by_type.get('Symptom', []),
                'drugs': nodes_by_type.get('Drug', []),
                'checks': nodes_by_type.get('Check', []),
                'departments': nodes_by_type.get('Department', []),
                'cure_ways': nodes_by_type.get('CureWay', []),
                'food_do': nodes_by_type.get('Food', []),
                'properties': disease.get('properties', {})
            }

            props = disease.get('properties', {})
            analysis_result['recommendations'].append({
                'disease': keyword,
                'suggestion': f"建议及时就医，前往{', '.join(nodes_by_type.get('Department', ['相关科室']))}就诊。",
                'precautions': props.get('prevent', '请遵循医嘱进行治疗。')[:200],
                'common_drugs': nodes_by_type.get('Drug', [])[:5]
            })

            if request.include_graph_data:
                analysis_result['graph_data'] = result

    # 如果找到疾病，用 AI 生成分析总结
    if analysis_result['analysis'] and request.use_rag:
        disease_names = list(analysis_result['analysis'].keys())
        summary_query = f"请对以下疾病进行综合分析：{'、'.join(disease_names)}"
        ai_result = inference(summary_query, role="doctor")
        analysis_result['answer'] = ai_result['answer']
    elif analysis_result['analysis']:
        analysis_result['answer'] = _generate_graph_analysis(analysis_result)
    else:
        analysis_result['answer'] = f"未在知识图谱中找到与「{request.question}」相关的疾病信息。"

    return ResponseModel(data=analysis_result)


@router.post("/rag/search", response_model=ResponseModel)
def rag_search(request: RAGQueryRequest):
    """RAG检索: 关键词提取 → KG查询 → 返回结构化上下文"""
    keywords = extract_keywords(request.query)
    knowledge = query_knowledge_graph(keywords, max_per_keyword=request.top_k)

    results = []
    for item in knowledge:
        context_parts = [f"【{item['type']}】{item['name']}"]
        if item.get('description'): context_parts.append(f"描述: {item['description']}")
        if item.get('cause'): context_parts.append(f"病因: {item['cause']}")
        if item.get('prevent'): context_parts.append(f"预防: {item['prevent']}")

        results.append({
            'entity_id': item['entity_id'],
            'name': item['name'],
            'type': item['type'],
            'context': '\n'.join(context_parts),
            'score': len(item.get('related', [])) / 10  # 关联越多分越高
        })

    results.sort(key=lambda x: -x['score'])

    return ResponseModel(data={
        'query': request.query,
        'keywords': keywords,
        'results': results[:request.top_k],
        'total_found': len(results)
    })


@router.get("/symptom-diagnosis", response_model=ResponseModel)
def symptom_diagnosis(
    symptoms: List[str] = Query(...),
    age: Optional[int] = None,
    gender: Optional[str] = None,
    duration: Optional[str] = None
):
    """症状诊断: 从KG中反向匹配症状→疾病"""
    graph_db = get_graph_db()

    disease_scores = {}

    for symptom in symptoms:
        symptom_nodes = graph_db.search_nodes(symptom, 'Symptom', limit=5)

        for symptom_node in symptom_nodes:
            relations = graph_db.execute(
                'SELECT source_id FROM relationships WHERE target_id = ? AND relation_type = ?',
                (symptom_node['id'], 'has_symptom')
            )

            for rel in relations:
                disease_id = rel['source_id']
                if disease_id not in disease_scores:
                    disease_scores[disease_id] = 0
                disease_scores[disease_id] += 1

    sorted_diseases = sorted(disease_scores.items(), key=lambda x: -x[1])[:5]

    diagnosis_results = []
    for disease_id, score in sorted_diseases:
        disease = graph_db.get_node_by_id(disease_id)
        if disease:
            props = disease.get('properties', {})

            departments = []
            dept_rels = graph_db.execute(
                'SELECT target_id FROM relationships WHERE source_id = ? AND relation_type = ?',
                (disease_id, 'belongs_to_dept')
            )
            for dept_rel in dept_rels:
                dept = graph_db.get_node_by_id(dept_rel['target_id'])
                if dept:
                    departments.append(dept['name'])

            diagnosis_results.append({
                'disease_id': disease['id'],
                'disease_name': disease['name'],
                'match_score': score,
                'match_rate': round(score / len(symptoms) * 100, 2),
                'description': props.get('desc', '')[:200],
                'recommended_department': departments[:3],
                'severity': '中等' if score >= len(symptoms) * 0.6 else '轻微',
                'suggestion': f"建议前往{', '.join(departments[:2])}就诊，进一步检查确诊。"
            })

    # 用 AI 生成综合摘要
    if diagnosis_results:
        summary_query = f"症状：{'、'.join(symptoms)}；可能的疾病：{'、'.join(d['disease_name'] for d in diagnosis_results[:3])}。请给出就医建议。"
        ai_result = inference(summary_query, role="patient")
        llm_summary = ai_result['answer']
    else:
        llm_summary = f"根据症状{'、'.join(symptoms)}，未在知识图谱中找到匹配的疾病。建议您前往医院就诊，由专业医生进行诊断。"

    return ResponseModel(data={
        'symptoms': symptoms,
        'patient_info': {
            'age': age,
            'gender': gender,
            'duration': duration
        },
        'possible_diseases': diagnosis_results,
        'summary': llm_summary,
        'total_diseases': len(diagnosis_results)
    })


@router.get("/drug-recommendation", response_model=ResponseModel)
def drug_recommendation(disease_name: str, include_alternatives: bool = True):
    """药品推荐: 从KG查询某疾病的推荐/常用药"""
    graph_db = get_graph_db()

    disease = graph_db.get_node_by_name(disease_name, 'Disease')
    if not disease:
        raise HTTPException(status_code=404, detail=f"未找到疾病: {disease_name}")

    drug_relations = graph_db.execute(
        'SELECT target_id, relation_type FROM relationships WHERE source_id = ? AND (relation_type = ? OR relation_type = ?)',
        (disease['id'], 'common_drug', 'recommand_drug')
    )

    drugs = []
    for rel in drug_relations:
        drug = graph_db.get_node_by_id(rel['target_id'])
        if drug:
            producer_rels = graph_db.execute(
                'SELECT target_id FROM relationships WHERE source_id = ? AND relation_type = ?',
                (drug['id'], 'produced_by')
            )
            producers = []
            for pr in producer_rels:
                producer = graph_db.get_node_by_id(pr['target_id'])
                if producer:
                    producers.append(producer['name'])

            drugs.append({
                'drug_id': drug['id'],
                'drug_name': drug['name'],
                'relation_type': rel['relation_type'],
                'producers': producers[:3],
                'recommended': rel['relation_type'] == 'recommand_drug'
            })

    # 用 AI 生成用药建议
    drug_names = [d['drug_name'] for d in drugs[:5]]
    ai_result = inference(f"请为{disease_name}推荐合理用药方案。常用药物：{'、'.join(drug_names)}", role="doctor")
    llm_recommendation = ai_result['answer']

    return ResponseModel(data={
        'disease_name': disease_name,
        'disease_id': disease['id'],
        'recommended_drugs': drugs,
        'total_drugs': len(drugs),
        'llm_recommendation': llm_recommendation
    })


# ---- 内部辅助函数 ----

def _generate_graph_analysis(data: Dict) -> str:
    result = "知识图谱分析结果：\n\n"

    for disease_name, analysis in data.get('analysis', {}).items():
        result += f"【{disease_name}】\n"

        if analysis.get('symptoms'):
            result += f"• 主要症状：{', '.join(analysis['symptoms'][:5])}\n"

        if analysis.get('drugs'):
            result += f"• 常用药物：{', '.join(analysis['drugs'][:5])}\n"

        if analysis.get('departments'):
            result += f"• 所属科室：{', '.join(analysis['departments'][:3])}\n"

        result += "\n"

    for rec in data.get('recommendations', []):
        result += f"💡 建议：{rec['suggestion']}\n"

    return result


@router.get("/health", response_model=ResponseModel)
def llm_health_check():
    from app.services.ai_service import is_ai_available
    return ResponseModel(data={
        'status': 'ok',
        'services': {
            'graph_db': 'connected',
            'rag': 'available',
            'llm': 'deepseek' if is_ai_available() else 'fallback_kb_only'
        },
        'message': 'AI推理服务运行正常' if is_ai_available() else '未配置DeepSeek API Key，使用知识图谱降级模式'
    })