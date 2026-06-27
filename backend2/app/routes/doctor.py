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
    
    assistant_message = Message(
        message_id=generate_id("msg_"),
        conversation_id=conversation_id,
        sender_role="assistant",
        content=f"收到您的输入：{content}。正在进行专业分析...",
        reasoning_path='["信息解析", "知识图谱检索", "专业分析"]',
        answer_source="rag"
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
            "reasoning_path": ["信息解析", "知识图谱检索", "专业分析"],
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
    analysis_results = []
    for disease in request.diseases:
        entity = db.query(MedicalEntity).filter(MedicalEntity.name == disease, MedicalEntity.type == "disease").first()
        if entity:
            relations = db.query(MedicalRelation).filter(
                (MedicalRelation.source_entity_id == entity.entity_id) |
                (MedicalRelation.target_entity_id == entity.entity_id)
            ).limit(10).all()
            disease_info = {
                "disease_id": entity.entity_id,
                "disease_name": entity.name,
                "description": entity.description,
                "related_symptoms": [],
                "related_treatments": [],
                "related_drugs": []
            }
            for rel in relations:
                target = db.query(MedicalEntity).filter(MedicalEntity.entity_id == rel.target_entity_id).first()
                if target:
                    if rel.relation_type == "has_symptom":
                        disease_info["related_symptoms"].append({"name": target.name, "entity_id": target.entity_id})
                    elif rel.relation_type == "has_treatment":
                        disease_info["related_treatments"].append({"name": target.name, "entity_id": target.entity_id})
                    elif rel.relation_type == "treats_with":
                        disease_info["related_drugs"].append({"name": target.name, "entity_id": target.entity_id})
            analysis_results.append(disease_info)
    
    return ResponseModel(data={
        "analysis_depth": request.analysis_depth,
        "results": analysis_results,
        "correlation_analysis": "多症状关联分析结果：各疾病之间存在一定的关联，建议综合考虑"
    })


@router.post("/consultation/differential-diagnosis", response_model=ResponseModel)
def differential_diagnosis(request: DifferentialDiagnosisRequest, current_user: dict = Depends(get_doctor_user)):
    return ResponseModel(data={
        "differential_list": [
            {
                "disease_id": "ent_001",
                "disease_name": "偏头痛",
                "probability": 0.78,
                "supporting_symptoms": ["头痛", "恶心", "对光敏感"],
                "conflicting_symptoms": [],
                "typical_onset": "青春期",
                "key_examination": "头颅MRI排除器质性病变",
                "treatment_principle": "药物治疗+生活方式调整"
            },
            {
                "disease_id": "ent_002",
                "disease_name": "紧张性头痛",
                "probability": 0.55,
                "supporting_symptoms": ["头痛", "颈部肌肉紧张"],
                "conflicting_symptoms": ["恶心"],
                "typical_onset": "成年期",
                "key_examination": "排除其他头痛类型",
                "treatment_principle": "放松训练+药物治疗"
            },
            {
                "disease_id": "ent_003",
                "disease_name": "脑血管疾病",
                "probability": 0.15,
                "supporting_symptoms": ["头痛"],
                "conflicting_symptoms": ["无神经系统定位体征"],
                "typical_onset": "中老年",
                "key_examination": "头颅CT/MRI",
                "treatment_principle": "急性期溶栓/取栓"
            }
        ],
        "recommended_next_step": "建议完善头颅MRI检查，神经内科门诊就诊",
        "high_risk_diseases": [],
        "emergency_flag": False
    })


@router.post("/knowledge/query", response_model=ResponseModel)
def query_knowledge(request: KnowledgeQueryRequest, current_user: dict = Depends(get_doctor_user), db: Session = Depends(get_db)):
    entities = db.query(MedicalEntity).filter(MedicalEntity.name.like(f"%{request.query}%")).limit(5).all()
    results = []
    
    for entity in entities:
        relations = db.query(MedicalRelation).filter(
            (MedicalRelation.source_entity_id == entity.entity_id) |
            (MedicalRelation.target_entity_id == entity.entity_id)
        ).limit(10).all()
        
        result_item = {
            "entity_id": entity.entity_id,
            "name": entity.name,
            "type": entity.type,
            "description": entity.description,
            "attributes": json_str_to_dict(entity.attributes),
            "related_entities": []
        }
        
        for rel in relations:
            target = db.query(MedicalEntity).filter(MedicalEntity.entity_id == rel.target_entity_id).first()
            if target:
                result_item["related_entities"].append({
                    "entity_id": target.entity_id,
                    "name": target.name,
                    "relation_type": rel.relation_type,
                    "relation_name": rel.relation_name
                })
        
        results.append(result_item)
    
    if not results:
        results.append({
            "entity_id": None,
            "name": request.query,
            "type": "unknown",
            "description": f"未在知识库中找到'{request.query}'相关信息",
            "attributes": {},
            "related_entities": []
        })
    
    return ResponseModel(data={
        "results": results,
        "query_type": request.query_type,
        "context": request.context
    })


@router.post("/knowledge/drug-interaction", response_model=ResponseModel)
def check_drug_interaction(request: DrugInteractionRequest, current_user: dict = Depends(get_doctor_user)):
    return ResponseModel(data={
        "interactions": [
            {
                "level": "warning",
                "drug_a": "阿司匹林",
                "drug_b": "华法林",
                "description": "合用可能增加出血风险",
                "severity": "中",
                "recommendation": "监测凝血功能，必要时调整剂量"
            },
            {
                "level": "info",
                "drug_a": "布洛芬",
                "drug_b": "奥美拉唑",
                "description": "奥美拉唑可减轻布洛芬的胃肠道刺激",
                "severity": "低",
                "recommendation": "可正常合用"
            }
        ],
        "summary": "存在1项需要关注的药物相互作用，建议临床密切监测"
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