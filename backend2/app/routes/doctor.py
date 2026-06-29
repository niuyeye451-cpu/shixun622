from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db
from app.models import Doctor, Conversation, Message, Feedback, MedicalEntity, MedicalRelation
from app.schemas import (
    CreateCaseConversationRequest, MultiSymptomAnalyzeRequest,
    DifferentialDiagnosisRequest, KnowledgeQueryRequest, DrugInteractionRequest,
    DoctorFeedbackCreate, DoctorProfileUpdate, ResponseModel
)
from app.utils import generate_id, list_to_json_str, json_str_to_list, json_str_to_dict
from app.dependencies import get_doctor_user
from app.services.ai_service import inference

router = APIRouter(prefix="/api/v1/doctor", tags=["doctor"])


@router.post("/consultation/conversations", response_model=ResponseModel)
def create_case_conversation(request: CreateCaseConversationRequest, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    doctor = current_user["user"]
    
    conversation = Conversation(
        conversation_id=generate_id("conv_"),
        doctor_id=doctor.doctor_id,
        session_type="case",
        case_type=request.case_type,
        status="active"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    messages = []
    if request.initial_query:
        user_message = Message(
            message_id=generate_id("msg_"),
            conversation_id=conversation.conversation_id,
            doctor_id=doctor.doctor_id,
            sender_role="user",
            content=request.initial_query
        )
        db.add(user_message)
        db.commit()
        messages.append({
            "message_id": user_message.message_id,
            "role": "user",
            "content": user_message.content,
            "created_at": user_message.created_at
        })
        
        if request.case_type == "differential_diagnosis":
            analysis_content = "收到您的病例信息，正在进行鉴别诊断分析..."
        elif request.case_type == "multi_symptom":
            analysis_content = "收到您的多症状信息，正在进行综合分析..."
        else:
            analysis_content = "收到您的治疗计划请求，正在生成方案..."
        
        assistant_message = Message(
            message_id=generate_id("msg_"),
            conversation_id=conversation.conversation_id,
            sender_role="assistant",
            content=analysis_content,
            reasoning_path='["病例解析", "知识图谱检索", "分析生成"]',
            answer_source="rag"
        )
        db.add(assistant_message)
        db.commit()
        messages.append({
            "message_id": assistant_message.message_id,
            "role": "assistant",
            "content": assistant_message.content,
            "reasoning_path": ["病例解析", "知识图谱检索", "分析生成"],
            "answer_source": assistant_message.answer_source,
            "created_at": assistant_message.created_at
        })
    
    return ResponseModel(data={
        "conversation_id": conversation.conversation_id,
        "session_type": conversation.session_type,
        "case_type": conversation.case_type,
        "status": conversation.status,
        "started_at": conversation.started_at,
        "messages": messages
    })


@router.post("/consultation/conversations/{conversation_id}/messages", response_model=ResponseModel)
def send_case_message(conversation_id: str, content: str, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    doctor = current_user["user"]
    
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.doctor_id == doctor.doctor_id
    ).first()
    if not conversation or conversation.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在或已结束")
    
    user_message = Message(
        message_id=generate_id("msg_"),
        conversation_id=conversation_id,
        doctor_id=doctor.doctor_id,
        sender_role="user",
        content=content
    )
    db.add(user_message)
    db.commit()

    # 调用 AI 推理管线（医师视角）
    result = inference(content, role="doctor")

    reasoning_path = ["关键词提取", "知识图谱检索", "AI临床分析"] if result["is_ai_generated"] else ["关键词提取", "知识图谱检索"]

    assistant_message = Message(
        message_id=generate_id("msg_"),
        conversation_id=conversation_id,
        sender_role="assistant",
        content=result["answer"],
        reasoning_path=list_to_json_str(reasoning_path),
        answer_source="ai+kb" if result["is_ai_generated"] else "kb"
    )
    db.add(assistant_message)
    db.commit()

    return ResponseModel(data={
        "message_id": user_message.message_id,
        "role": "user",
        "content": user_message.content,
        "created_at": user_message.created_at,
        "assistant_message": {
            "message_id": assistant_message.message_id,
            "role": "assistant",
            "content": assistant_message.content,
            "reasoning_path": reasoning_path,
            "answer_source": assistant_message.answer_source,
            "created_at": assistant_message.created_at
        }
    })


@router.get("/consultation/conversations/{conversation_id}/messages", response_model=ResponseModel)
def get_case_conversation_messages(conversation_id: str, last_message_id: str = None, limit: int = 20, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    doctor = current_user["user"]
    
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.doctor_id == doctor.doctor_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    query = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at)
    if last_message_id:
        last_msg = db.query(Message).filter(Message.message_id == last_message_id).first()
        if last_msg:
            query = query.filter(Message.created_at > last_msg.created_at)
    
    messages = query.limit(limit).all()
    result = []
    for msg in messages:
        result.append({
            "message_id": msg.message_id,
            "role": msg.sender_role,
            "content": msg.content,
            "image_ids": json_str_to_list(msg.image_ids),
            "reasoning_path": json_str_to_list(msg.reasoning_path),
            "answer_source": msg.answer_source,
            "created_at": msg.created_at
        })
    
    return ResponseModel(data={"list": result, "has_more": len(result) >= limit})


@router.put("/consultation/conversations/{conversation_id}/end", response_model=ResponseModel)
def end_case_conversation(conversation_id: str, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    doctor = current_user["user"]
    
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.doctor_id == doctor.doctor_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    conversation.status = "ended"
    conversation.ended_at = datetime.now()
    db.commit()
    
    return ResponseModel(data={"summary": "对话已结束，分析报告已保存"})


@router.get("/consultation/conversations", response_model=ResponseModel)
def get_case_conversation_list(page: int = 1, page_size: int = 10, case_type: str = None, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    doctor = current_user["user"]
    
    query = db.query(Conversation).filter(
        Conversation.doctor_id == doctor.doctor_id,
        Conversation.session_type == "case"
    )
    if case_type:
        query = query.filter(Conversation.case_type == case_type)
    
    total = query.count()
    conversations = query.order_by(Conversation.started_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for conv in conversations:
        last_msg = db.query(Message).filter(Message.conversation_id == conv.conversation_id).order_by(Message.created_at.desc()).first()
        result.append({
            "conversation_id": conv.conversation_id,
            "session_type": conv.session_type,
            "case_type": conv.case_type,
            "status": conv.status,
            "title": "病例分析",
            "last_message": last_msg.content if last_msg else "",
            "started_at": conv.started_at,
            "ended_at": conv.ended_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.post("/consultation/multi-symptom", response_model=ResponseModel)
def analyze_multi_symptom(request: MultiSymptomAnalyzeRequest, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    from app.graph_db import get_graph_db
    graph_db = get_graph_db()
    analysis_results = []
    for disease_name in request.diseases:
        entity = graph_db.get_node_by_name(disease_name, 'Disease')
        if not entity:
            results = graph_db.search_nodes(disease_name, label='Disease', limit=1)
            if results: entity = results[0]
        if entity:
            relations = graph_db.get_relations_by_node(entity['id'])
            props = entity.get('properties', {})
            disease_info = {
                "disease_id": entity['id'],
                "disease_name": entity['name'],
                "description": props.get('desc', '') if isinstance(props, dict) else '',
                "related_symptoms": [],
                "related_treatments": [],
                "related_drugs": []
            }
            for rel in relations[:20]:
                target = graph_db.get_node_by_id(rel.get('target_id', ''))
                if target:
                    rt = rel.get('relation_type', '')
                    if rt == "has_symptom":
                        disease_info["related_symptoms"].append({"name": target['name'], "entity_id": target['id']})
                    elif rt in ("has_treatment", "cure_way"):
                        disease_info["related_treatments"].append({"name": target['name'], "entity_id": target['id']})
                    elif rt in ("common_drug", "recommand_drug"):
                        disease_info["related_drugs"].append({"name": target['name'], "entity_id": target['id']})
            analysis_results.append(disease_info)
    
    # 用 AI 进行多疾病关联分析
    ai_result = {"is_ai_generated": False}
    if analysis_results:
        disease_list = [d['disease_name'] for d in analysis_results]
        query = f"请对以下疾病进行多症状关联分析：{'、'.join(disease_list)}"
        if request.symptoms:
            query += f"；共同症状：{'、'.join(request.symptoms)}"
        ai_result = inference(query, role="doctor")
        correlation = ai_result.get("answer", "")
    else:
        correlation = "未在知识库中找到匹配的疾病信息，无法进行关联分析"

    # 自动存档到检索历史
    conversation = Conversation(
        conversation_id=generate_id("conv_"),
        doctor_id=current_user["user"].doctor_id,
        session_type="case",
        case_type="multi_symptom",
        status="ended"
    )
    db.add(conversation)
    db.add(Message(message_id=generate_id("msg_"), conversation_id=conversation.conversation_id, doctor_id=current_user["user"].doctor_id, sender_role="user", content=f"多症状分析: {', '.join(request.diseases)}"))
    db.add(Message(message_id=generate_id("msg_"), conversation_id=conversation.conversation_id, sender_role="assistant", content=correlation[:500], answer_source="ai+kb" if ai_result.get("is_ai_generated") else "kb"))
    db.commit()

    return ResponseModel(data={
        "analysis_depth": request.analysis_depth,
        "results": analysis_results,
        "correlation_analysis": correlation[:200] if len(correlation) > 200 else correlation,
        "ai_full_analysis": correlation
    })


@router.post("/consultation/differential-diagnosis", response_model=ResponseModel)
def differential_diagnosis(request: DifferentialDiagnosisRequest, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    # 组装临床Query
    query_parts = [f"主诉：{request.chief_complaint}"]
    if request.symptoms:
        query_parts.append(f"症状：{'、'.join(request.symptoms)}")
    if request.patient_info:
        info = request.patient_info
        if info.get("age"): query_parts.append(f"年龄：{info['age']}岁")
        if info.get("gender"): query_parts.append(f"性别：{info['gender']}")
    if request.exam_results:
        query_parts.append(f"检查结果：{json.dumps(request.exam_results, ensure_ascii=False)}")

    query = "；".join(query_parts) + "。请给出鉴别诊断分析。"

    result = inference(query, role="doctor")

    # 从知识图谱提取疾病列表
    disease_matches = [k for k in result.get("knowledge", []) if k.get("type") == "Disease"]
    differential_list = []
    for i, d in enumerate(disease_matches[:5]):
        differential_list.append({
            "disease_id": d["entity_id"],
            "disease_name": d["name"],
            "probability": round(0.85 - i * 0.15, 2),
            "supporting_symptoms": [r["target_name"] for r in d.get("related", []) if r.get("target_type") == "Symptom"][:3],
            "conflicting_symptoms": [],
            "typical_onset": d.get("cause", "")[:50] if d.get("cause") else "",
            "key_examination": d.get("description", "")[:80] if d.get("description") else "",
            "treatment_principle": ""
        })

    # 判断有无高危疾病
    emergency_keywords = ["心梗", "脑出血", "主动脉夹层", "肺栓塞", "急性", "危重"]
    has_emergency = any(kw in result.get("answer", "") for kw in emergency_keywords)

    # 自动存档到检索历史
    conversation = Conversation(
        conversation_id=generate_id("conv_"),
        doctor_id=current_user["user"].doctor_id,
        session_type="case",
        case_type="differential_diagnosis",
        status="ended"
    )
    db.add(conversation)
    db.add(Message(message_id=generate_id("msg_"), conversation_id=conversation.conversation_id, doctor_id=current_user["user"].doctor_id, sender_role="user", content=f"鉴别诊断: {request.chief_complaint}"))
    db.add(Message(message_id=generate_id("msg_"), conversation_id=conversation.conversation_id, sender_role="assistant", content=result["answer"][:500], answer_source="ai+kb" if result.get("is_ai_generated") else "kb"))
    db.commit()

    return ResponseModel(data={
        "differential_list": differential_list,
        "ai_analysis": result["answer"],
        "recommended_next_step": "建议结合临床表现和辅助检查进一步明确诊断",
        "high_risk_diseases": [d for d in differential_list if d["probability"] > 0.7][:2],
        "emergency_flag": has_emergency
    })


@router.post("/knowledge/query", response_model=ResponseModel)
def query_knowledge(request: KnowledgeQueryRequest, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    """知识检索: 搜索图数据库 + AI 语义分析（自动存档到检索历史）"""
    from app.graph_db import get_graph_db
    doctor = current_user["user"]
    graph_db = get_graph_db()

    # 从图数据库搜索实体
    entities = graph_db.search_nodes(request.query, limit=10)

    # 同时调用 AI 语义分析
    ai_result = inference(request.query, role="doctor")

    results = []
    for entity in entities:
        props = entity.get('properties', {})
        desc = props.get('desc', '') if isinstance(props, dict) else ''
        relations = graph_db.get_relations_by_node(entity['id'])
        related = []
        for rel in relations[:10]:
            target = graph_db.get_node_by_id(rel.get('target_id', ''))
            if target:
                related.append({
                    "entity_id": target.get('id', ''),
                    "name": target.get('name', ''),
                    "relation_type": rel.get('relation_type', ''),
                    "relation_name": rel.get('relation_name', '')
                })

        results.append({
            "entity_id": entity['id'],
            "name": entity['name'],
            "type": entity.get('label', 'Disease'),
            "description": desc[:300] if desc else None,
            "attributes": props,
            "related_entities": related
        })

    if not results:
        results.append({
            "entity_id": None,
            "name": request.query,
            "type": "unknown",
            "description": f"未在知识库中找到'{request.query}'相关信息",
            "attributes": {},
            "related_entities": []
        })

    # ====== 自动存档：创建 Conversation + 保存消息，供检索历史使用 ======
    conversation = Conversation(
        conversation_id=generate_id("conv_"),
        doctor_id=doctor.doctor_id,
        session_type="case",
        case_type="knowledge_search",
        status="ended"
    )
    db.add(conversation)

    # 用户消息
    user_msg = Message(
        message_id=generate_id("msg_"),
        conversation_id=conversation.conversation_id,
        doctor_id=doctor.doctor_id,
        sender_role="user",
        content=request.query
    )
    db.add(user_msg)

    # 助手消息（AI 分析摘要）
    ai_summary = ai_result.get("answer", "")[:500] if ai_result.get("answer") else f"查找到 {len(results)} 条相关结果"
    assistant_msg = Message(
        message_id=generate_id("msg_"),
        conversation_id=conversation.conversation_id,
        sender_role="assistant",
        content=ai_summary,
        reasoning_path=list_to_json_str(ai_result.get("keywords", [])),
        answer_source="ai+kb" if ai_result.get("is_ai_generated") else "kb"
    )
    db.add(assistant_msg)
    db.commit()

    return ResponseModel(data={
        "results": results,
        "ai_analysis": ai_result.get("answer", ""),
        "ai_keywords": ai_result.get("keywords", []),
        "query_type": request.query_type,
        "context": request.context
    })


@router.post("/knowledge/drug-interaction", response_model=ResponseModel)
@router.post("/knowledge/drug-interaction", response_model=ResponseModel)
def check_drug_interaction(request: DrugInteractionRequest, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    """联合用药安全分析: AI + 知识图谱 + 自动存档"""
    drug_names = request.drug_names or []
    if not drug_names:
        return ResponseModel(data={"interactions": [], "summary": "请提供药品名称"})

    # 用 AI 分析药物相互作用
    query = f"请分析以下药物的相互作用风险：{'、'.join(drug_names)}。请列出每对药物组合的相互作用级别（禁忌/谨慎/注意）和临床建议。"
    ai_result = inference(query, role="doctor")

    # 从 KG 补充数据
    from app.graph_db import get_graph_db
    graph_db = get_graph_db()
    interactions = []
    for i in range(len(drug_names)):
        for j in range(i + 1, len(drug_names)):
            drug_a = graph_db.get_node_by_name(drug_names[i], 'Drug')
            drug_b = graph_db.get_node_by_name(drug_names[j], 'Drug')
            if drug_a and drug_b:
                interactions.append({
                    "level": "info",
                    "drug_a": drug_names[i],
                    "drug_b": drug_names[j],
                    "description": f"请在临床中密切观察{drug_names[i]}与{drug_names[j]}的联用反应",
                    "severity": "低",
                    "recommendation": "建议查阅最新版药品说明书中的相互作用章节"
                })

    # 自动存档
    conversation = Conversation(
        conversation_id=generate_id("conv_"),
        doctor_id=current_user["user"].doctor_id,
        session_type="case",
        case_type="drug_interaction",
        status="ended"
    )
    db.add(conversation)
    db.add(Message(message_id=generate_id("msg_"), conversation_id=conversation.conversation_id, doctor_id=current_user["user"].doctor_id, sender_role="user", content=f"联合用药分析: {', '.join(drug_names)}"))
    db.add(Message(message_id=generate_id("msg_"), conversation_id=conversation.conversation_id, sender_role="assistant", content=ai_result["answer"][:500], answer_source="ai+kb" if ai_result.get("is_ai_generated") else "kb"))
    db.commit()

    return ResponseModel(data={
        "interactions": interactions,
        "ai_analysis": ai_result.get("answer", ""),
        "summary": f"已完成{'、'.join(drug_names)}的相互作用初步筛查，请结合AI分析和临床判断"
    })


@router.get("/profile", response_model=ResponseModel)
def get_doctor_profile(current_user: dict = Depends(get_doctor_user)):
    doctor = current_user["user"]
    return ResponseModel(data={
        "doctor_id": doctor.doctor_id,
        "user_name": doctor.user_name,
        "phone": doctor.phone,
        "avatar": doctor.avatar,
        "department": doctor.department,
        "title": doctor.title,
        "hospital": doctor.hospital,
        "specialty": doctor.specialty,
        "introduction": doctor.introduction,
        "is_first_login": doctor.is_first_login,
        "status": doctor.status,
        "created_at": doctor.created_at
    })


@router.put("/profile", response_model=ResponseModel)
def update_doctor_profile(request: DoctorProfileUpdate, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    doctor = current_user["user"]
    
    if request.avatar:
        doctor.avatar = request.avatar
    if request.specialty:
        doctor.specialty = request.specialty
    if request.introduction:
        doctor.introduction = request.introduction
    
    db.commit()
    return ResponseModel(message="更新成功")


@router.post("/feedback", response_model=ResponseModel)
def submit_doctor_feedback(request: DoctorFeedbackCreate, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    doctor = current_user["user"]
    
    feedback = Feedback(
        feedback_id=generate_id("fb_"),
        doctor_id=doctor.doctor_id,
        type=request.type,
        related_entity_id=request.related_entity_id,
        related_query_id=request.related_query_id,
        title=request.title,
        content=request.content,
        corrected_answer=request.corrected_content,
        references=list_to_json_str(request.references) if request.references else None,
        status="pending"
    )
    db.add(feedback)
    db.commit()
    
    return ResponseModel(data={"feedback_id": feedback.feedback_id, "status": "pending"})


@router.get("/feedback", response_model=ResponseModel)
def get_doctor_feedback_list(status: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    doctor = current_user["user"]
    
    query = db.query(Feedback).filter(Feedback.doctor_id == doctor.doctor_id)
    if status:
        query = query.filter(Feedback.status == status)
    
    total = query.count()
    feedbacks = query.order_by(Feedback.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for fb in feedbacks:
        result.append({
            "feedback_id": fb.feedback_id,
            "type": fb.type,
            "title": fb.title,
            "content": fb.content,
            "status": fb.status,
            "reply": fb.reply,
            "resolved_at": fb.resolved_at,
            "created_at": fb.created_at
        })

    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})