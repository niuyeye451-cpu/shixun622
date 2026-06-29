from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.graph_db import get_graph_db
from app.schemas import ResponseModel, GraphNode, GraphEdge, GraphResponse


class CypherQueryRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None


router = APIRouter(prefix="/api/v1/common/knowledge-graph", tags=["knowledge-graph"])


@router.get("/disease-graph", response_model=ResponseModel)
def get_disease_graph(disease_name: str, max_depth: int = Query(2, ge=1, le=5)):
    graph_db = get_graph_db()
    result = graph_db.get_graph_by_disease(disease_name, max_depth)
    
    nodes = []
    for node in result['nodes']:
        props = node.get('properties', {})
        description = props.get('desc', '')
        nodes.append(GraphNode(
            id=node['id'],
            name=node['name'],
            type=node['label'],
            description=description[:200] if description else None
        ))
    
    edges = []
    for edge in result['edges']:
        edges.append(GraphEdge(
            id=edge['id'],
            source=edge['source_id'],
            target=edge['target_id'],
            relation=edge['relation_type'],
            relation_name=edge['relation_name']
        ))
    
    return ResponseModel(data=GraphResponse(
        nodes=nodes,
        edges=edges,
        center_node=result['center_node']
    ))


@router.get("/entities/search", response_model=ResponseModel)
def search_entities(
    keyword: str,
    entity_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    graph_db = get_graph_db()
    
    label_map = {
        'disease': 'Disease',
        'symptom': 'Symptom',
        'drug': 'Drug',
        'check': 'Check',
        'department': 'Department',
        'cure_way': 'CureWay',
        'food': 'Food',
        'producer': 'Producer'
    }
    
    label = label_map.get(entity_type.lower()) if entity_type else None
    
    entities = graph_db.search_nodes(keyword, label, limit + offset)
    
    if offset > 0 and len(entities) > offset:
        entities = entities[offset:]
    
    entities = entities[:limit]
    
    results = []
    for entity in entities:
        props = entity.get('properties', {})
        aliases = props.get('alias', [])
        description = props.get('desc', '')
        
        results.append({
            'entity_id': entity['id'],
            'name': entity['name'],
            'type': entity['label'],
            'aliases': aliases,
            'description': description[:300] if description else None,
            'frequency': props.get('freq', 0)
        })
    
    return ResponseModel(data={
        'total': len(results),
        'entities': results
    })


@router.get("/entities/{entity_id}", response_model=ResponseModel)
def get_entity_detail(entity_id: str):
    graph_db = get_graph_db()
    entity = graph_db.get_node_by_id(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    
    props = entity.get('properties', {})
    
    relations = graph_db.get_node_relations(entity_id)
    
    relation_groups = {}
    for rel in relations:
        rel_type = rel['relation_type']
        rel_name = rel['relation_name']
        target_node = graph_db.get_node_by_id(rel['target_id'])
        
        if target_node:
            if rel_type not in relation_groups:
                relation_groups[rel_type] = {
                    'name': rel_name,
                    'items': []
                }
            relation_groups[rel_type]['items'].append({
                'entity_id': target_node['id'],
                'name': target_node['name'],
                'type': target_node['label']
            })
    
    return ResponseModel(data={
        'entity_id': entity['id'],
        'name': entity['name'],
        'type': entity['label'],
        'description': props.get('desc', ''),
        'properties': {
            'cause': props.get('cause', ''),
            'prevent': props.get('prevent', ''),
            'cured_prob': props.get('cured_prob', ''),
            'cost_money': props.get('cost_money', []),
            'cure_lasttime': props.get('cure_lasttime', ''),
            'yibao_status': props.get('yibao_status', ''),
            'get_way': props.get('get_way', ''),
            'easy_get': props.get('easy_get', '')
        },
        'relations': relation_groups,
        'aliases': props.get('alias', []),
        'frequency': props.get('freq', 0)
    })


@router.get("/entities/{entity_id}/relations", response_model=ResponseModel)
def get_entity_relations(entity_id: str, relation_type: Optional[str] = None):
    graph_db = get_graph_db()
    
    entity = graph_db.get_node_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    
    relations = graph_db.get_relations_by_node(entity_id, relation_type)
    
    results = []
    for rel in relations:
        target_node = graph_db.get_node_by_id(rel['target_id'])
        if target_node:
            results.append({
                'relation_id': rel['id'],
                'relation_type': rel['relation_type'],
                'relation_name': rel['relation_name'],
                'target_entity': {
                    'entity_id': target_node['id'],
                    'name': target_node['name'],
                    'type': target_node['label']
                }
            })
    
    return ResponseModel(data=results)


@router.get("/statistics", response_model=ResponseModel)
def get_graph_statistics():
    graph_db = get_graph_db()
    stats = graph_db.get_statistics()
    
    # Convert list-of-{label,count} to Record<string, number> for frontend compatibility
    entity_type_counts = {}
    for item in stats.get('label_distribution', []):
        if isinstance(item, dict):
            entity_type_counts[item.get('label', 'unknown')] = item.get('count', 0)

    relation_type_counts = {}
    for item in stats.get('relation_distribution', []):
        if isinstance(item, dict):
            relation_type_counts[item.get('relation_type', 'unknown')] = item.get('count', 0)

    return ResponseModel(data={
        'total_entities': stats['total_nodes'],
        'total_relations': stats['total_relationships'],
        'entity_type_counts': entity_type_counts,
        'relation_type_counts': relation_type_counts
    })


@router.get("/labels", response_model=ResponseModel)
def get_all_labels():
    graph_db = get_graph_db()
    labels = graph_db.get_all_labels()
    
    label_info = []
    for label in labels:
        nodes = graph_db.get_nodes_by_label(label, 1)
        count_result = graph_db.execute('SELECT COUNT(*) as count FROM nodes WHERE label = ?', (label,))
        count = count_result[0]['count'] if count_result else 0
        label_info.append({
            'label': label,
            'count': count,
            'sample': nodes[0]['name'] if nodes else ''
        })
    
    return ResponseModel(data=label_info)


@router.get("/relation-types", response_model=ResponseModel)
def get_all_relation_types():
    graph_db = get_graph_db()
    rel_types = graph_db.get_all_relation_types()
    
    rel_info = []
    for rel_type in rel_types:
        count_result = graph_db.execute('SELECT COUNT(*) as count FROM relationships WHERE relation_type = ?', (rel_type,))
        count = count_result[0]['count'] if count_result else 0
        rel_info.append({
            'relation_type': rel_type,
            'count': count
        })
    
    return ResponseModel(data=rel_info)


@router.get("/path", response_model=ResponseModel)
def get_path_between_entities(
    source_name: str,
    target_name: str,
    source_type: str = 'Disease',
    target_type: str = 'Disease',
    max_depth: int = Query(3, ge=1, le=5)
):
    graph_db = get_graph_db()
    
    source = graph_db.get_node_by_name(source_name, source_type)
    target = graph_db.get_node_by_name(target_name, target_type)
    
    if not source:
        raise HTTPException(status_code=404, detail=f"源实体 '{source_name}' 不存在")
    
    if not target:
        raise HTTPException(status_code=404, detail=f"目标实体 '{target_name}' 不存在")
    
    paths = graph_db.get_path_between_nodes(source['id'], target['id'], max_depth)
    
    path_results = []
    for path in paths:
        path_nodes = []
        for node_id in path:
            node = graph_db.get_node_by_id(node_id)
            if node:
                path_nodes.append({
                    'entity_id': node['id'],
                    'name': node['name'],
                    'type': node['label']
                })
        
        path_results.append({
            'path': path_nodes,
            'length': len(path) - 1
        })
    
    return ResponseModel(data={
        'source': {'entity_id': source['id'], 'name': source['name']},
        'target': {'entity_id': target['id'], 'name': target['name']},
        'paths': path_results,
        'total_paths': len(path_results)
    })


@router.get("/symptom-analysis", response_model=ResponseModel)
def analyze_symptoms(symptoms: List[str] = Query(...)):
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
    
    sorted_diseases = sorted(disease_scores.items(), key=lambda x: -x[1])[:10]
    
    results = []
    for disease_id, score in sorted_diseases:
        disease = graph_db.get_node_by_id(disease_id)
        if disease:
            props = disease.get('properties', {})
            results.append({
                'disease_id': disease['id'],
                'name': disease['name'],
                'match_score': score,
                'match_rate': round(score / len(symptoms) * 100, 2),
                'description': props.get('desc', '')[:200],
                'common_drugs': [],
                'recommended_department': []
            })
    
    return ResponseModel(data={
        'symptoms': symptoms,
        'matched_diseases': results,
        'total_matched': len(results)
    })


@router.get("/drug-interaction", response_model=ResponseModel)
def get_drug_interaction(drug_name: str):
    graph_db = get_graph_db()
    
    drug = graph_db.get_node_by_name(drug_name, 'Drug')
    if not drug:
        raise HTTPException(status_code=404, detail=f"药品 '{drug_name}' 不存在")
    
    relations = graph_db.get_node_relations(drug['id'])
    
    drug_info = {
        'drug_id': drug['id'],
        'name': drug['name'],
        'producer': [],
        'related_diseases': [],
        'usage': []
    }
    
    for rel in relations:
        target_node = graph_db.get_node_by_id(rel['target_id'])
        if target_node:
            if rel['relation_type'] == 'produced_by':
                drug_info['producer'].append(target_node['name'])
            elif rel['relation_type'] == 'common_drug' or rel['relation_type'] == 'recommand_drug':
                drug_info['related_diseases'].append(target_node['name'])
    
    return ResponseModel(data=drug_info)


@router.get("/db-status", response_model=ResponseModel)
def get_db_status():
    import os
    graph_backend = os.getenv("GRAPH_BACKEND", "sqlite")
    graph_db = get_graph_db()
    
    status = {
        'backend': graph_backend,
        'connected': False,
        'error': None
    }
    
    try:
        stats = graph_db.get_statistics()
        status['connected'] = True
        status['statistics'] = stats
        status['supports_cypher'] = graph_backend == 'neo4j'
    except Exception as e:
        status['error'] = str(e)
    
    return ResponseModel(data=status)


@router.post("/cypher-query", response_model=ResponseModel)
def execute_cypher_query(request: CypherQueryRequest):
    import os
    graph_backend = os.getenv("GRAPH_BACKEND", "sqlite")
    
    if graph_backend != 'neo4j':
        raise HTTPException(status_code=400, detail="Cypher查询仅支持Neo4j后端，请切换GRAPH_BACKEND=neo4j")
    
    graph_db = get_graph_db()
    
    try:
        results = graph_db.execute(request.query, request.params or {})
        return ResponseModel(data={
            'query': request.query,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cypher查询执行失败: {str(e)}")
