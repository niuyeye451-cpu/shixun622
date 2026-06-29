from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Patient, Conversation, Message, Consultation, Registration
from app.schemas import (
    CreateConversationRequest, SendMessageRequest, QuickSymptomRequest,
    DepartmentRecommendationRequest, RegistrationRequest, PatientProfileUpdate,
    ResponseModel
)
from app.utils import generate_id, list_to_json_str, json_str_to_list
from app.dependencies import get_patient_user
from app.services.ai_service import inference

router = APIRouter(prefix="/api/v1/patient", tags=["patient"])


@router.post("/consultation/conversations", response_model=ResponseModel)
def create_conversation(request: CreateConversationRequest, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    conversation = Conversation(
        conversation_id=generate_id("conv_"),
        patient_id=patient.patient_id,
        session_type=request.session_type,
        status="active"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    messages = []
    if request.initial_message:
        user_message = Message(
            message_id=generate_id("msg_"),
            conversation_id=conversation.conversation_id,
            patient_id=patient.patient_id,
            sender_role="user",
            content=request.initial_message
        )
        db.add(user_message)
        db.commit()
        messages.append({
            "message_id": user_message.message_id,
            "role": "user",
            "content": user_message.content,
            "created_at": user_message.created_at
        })
        
        assistant_message = Message(
            message_id=generate_id("msg_"),
            conversation_id=conversation.conversation_id,
            sender_role="assistant",
            content=f"根据您描述的症状，可能的原因有很多。为了更好地帮助您，请提供更多信息。",
            reasoning_path='["症状提取", "疾病匹配", "答案生成"]',
            answer_source="rag"
        )
        db.add(assistant_message)
        db.commit()
        messages.append({
            "message_id": assistant_message.message_id,
            "role": "assistant",
            "content": assistant_message.content,
            "reasoning_path": ["症状提取", "疾病匹配", "答案生成"],
            "answer_source": assistant_message.answer_source,
            "created_at": assistant_message.created_at
        })
    
    return ResponseModel(data={
        "conversation_id": conversation.conversation_id,
        "session_type": conversation.session_type,
        "status": conversation.status,
        "started_at": conversation.started_at,
        "messages": messages
    })


@router.post("/consultation/conversations/{conversation_id}/messages", response_model=ResponseModel)
def send_message(conversation_id: str, request: SendMessageRequest, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.patient_id == patient.patient_id
    ).first()
    if not conversation or conversation.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在或已结束")
    
    user_message = Message(
        message_id=generate_id("msg_"),
        conversation_id=conversation_id,
        patient_id=patient.patient_id,
        sender_role="user",
        content=request.content,
        image_ids=list_to_json_str(request.image_ids) if request.image_ids else None
    )
    db.add(user_message)
    db.commit()

    # 调用 AI 推理管线
    result = inference(request.content, role="patient")

    reasoning_path = ["关键词提取", "知识图谱检索", "AI生成回答"] if result["is_ai_generated"] else ["关键词提取", "知识图谱检索"]

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

    # 提取匹配的疾病和科室（若有关联数据）
    disease_matches = [k for k in result.get("knowledge", []) if k.get("type") == "Disease"]
    matched_disease = disease_matches[0]["name"] if disease_matches else None
    related_diseases = [
        {"entity_id": d["entity_id"], "name": d["name"], "probability": 0.5}
        for d in disease_matches[:3]
    ]

    dept_matches = [k for k in result.get("knowledge", [])
                    for r in k.get("related", [])
                    if r.get("target_type") == "Department"]
    matched_department = dept_matches[0]["target_name"] if dept_matches else None

    return ResponseModel(data={
        "message_id": user_message.message_id,
        "role": "user",
        "content": user_message.content,
        "image_ids": json_str_to_list(user_message.image_ids),
        "created_at": user_message.created_at,
        "assistant_message": {
            "message_id": assistant_message.message_id,
            "role": "assistant",
            "content": assistant_message.content,
            "reasoning_path": reasoning_path,
            "answer_source": assistant_message.answer_source,
            "matched_disease": matched_disease,
            "matched_department": matched_department,
            "recommendation_detail": f"建议您到{matched_department}就诊" if matched_department else "详情请咨询专业医生",
            "related_diseases": related_diseases,
            "created_at": assistant_message.created_at
        }
    })


@router.get("/consultation/conversations/{conversation_id}/messages", response_model=ResponseModel)
def get_conversation_messages(conversation_id: str, last_message_id: str = None, limit: int = 20, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.patient_id == patient.patient_id
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
def end_conversation(conversation_id: str, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.patient_id == patient.patient_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    conversation.status = "ended"
    conversation.ended_at = datetime.now()
    db.commit()
    
    consultation = Consultation(
        consultation_id=generate_id("cons_"),
        patient_id=patient.patient_id,
        symptom_text="本次咨询对话",
        matched_disease="待诊断",
        recommendation_detail="对话已结束"
    )
    db.add(consultation)
    db.commit()
    
    return ResponseModel(data={"consultation_id": consultation.consultation_id, "summary": "对话已结束"})


@router.get("/consultation/conversations", response_model=ResponseModel)
def get_conversation_list(page: int = 1, page_size: int = 10, session_type: str = None, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    query = db.query(Conversation).filter(Conversation.patient_id == patient.patient_id)
    if session_type:
        query = query.filter(Conversation.session_type == session_type)
    
    total = query.count()
    conversations = query.order_by(Conversation.started_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for conv in conversations:
        last_msg = db.query(Message).filter(Message.conversation_id == conv.conversation_id).order_by(Message.created_at.desc()).first()
        result.append({
            "conversation_id": conv.conversation_id,
            "session_type": conv.session_type,
            "status": conv.status,
            "title": "症状咨询" if conv.session_type == "symptom" else "咨询",
            "last_message": last_msg.content if last_msg else "",
            "matched_disease": "待诊断",
            "matched_department": "",
            "started_at": conv.started_at,
            "ended_at": conv.ended_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.post("/consultation/symptom/quick", response_model=ResponseModel)
def quick_symptom_query(request: QuickSymptomRequest, current_user: dict = Depends(get_patient_user)):
    query = request.symptom_text
    if request.age:
        query += f"，年龄{request.age}岁"
    if request.gender:
        query += f"，{request.gender}性"

    result = inference(query, role="patient")

    disease_matches = [k for k in result.get("knowledge", []) if k.get("type") == "Disease"]
    matched_diseases = []
    for d in disease_matches[:5]:
        matched_diseases.append({
            "disease_id": d["entity_id"],
            "disease_name": d["name"],
            "probability": 0.5,
            "department": next((r["target_name"] for r in d.get("related", [])
                               if r.get("target_type") == "Department"), None)
        })

    return ResponseModel(data={
        "answer": result["answer"],
        "matched_diseases": matched_diseases,
        "recommended_department": matched_diseases[0]["department"] if matched_diseases and matched_diseases[0].get("department") else None
    })


@router.get("/consultation/disease/{disease_name}/graph", response_model=ResponseModel)
def get_disease_graph(disease_name: str, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    from app.routes.common import get_disease_graph as common_graph
    return common_graph(disease_name=disease_name, db=db)


@router.post("/recommendation/department", response_model=ResponseModel)
def recommend_department(request: DepartmentRecommendationRequest, current_user: dict = Depends(get_patient_user)):
    departments = [
        {"department_id": "dept_005", "department_name": "神经内科", "confidence": 0.85, "reason": "头痛伴恶心呕吐是神经内科常见症状"},
        {"department_id": "dept_007", "department_name": "消化内科", "confidence": 0.62, "reason": "恶心呕吐也可能是消化系统问题"},
    ]
    return ResponseModel(data={"recommended_departments": departments, "urgency_level": "normal", "suggestion": "建议优先到神经内科就诊"})


@router.get("/recommendation/hospitals", response_model=ResponseModel)
def recommend_hospitals(department_id: str, city: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_patient_user)):
    hospitals = [
        {"hospital_id": "hosp_001", "hospital_name": "XX人民医院", "hospital_level": "三级甲等", "department_strength": 5, "wait_time": "2-3天", "address": "北京市XX区XX路1号", "distance": 2.5, "has_online_registration": True},
        {"hospital_id": "hosp_002", "hospital_name": "XX协和医院", "hospital_level": "三级甲等", "department_strength": 5, "wait_time": "3-5天", "address": "北京市XX区XX路2号", "distance": 3.2, "has_online_registration": True},
    ]
    return ResponseModel(data={"list": hospitals, "page": page, "page_size": page_size, "total": len(hospitals)})


@router.get("/recommendation/doctors", response_model=ResponseModel)
def recommend_doctors(department_id: str, hospital_id: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_patient_user)):
    doctors = [
        {"doctor_id": "doc_001", "doctor_name": "张医生", "title": "主任医师", "hospital": "XX人民医院", "department": "神经内科", "specialty": "头痛、癫痫、帕金森病", "rating": 4.9, "consultation_count": 5000, "next_available_date": "2024-01-15"},
        {"doctor_id": "doc_002", "doctor_name": "李医生", "title": "副主任医师", "hospital": "XX协和医院", "department": "神经内科", "specialty": "脑血管疾病", "rating": 4.8, "consultation_count": 3000, "next_available_date": "2024-01-16"},
    ]
    return ResponseModel(data={"list": doctors, "page": page, "page_size": page_size, "total": len(doctors)})


@router.get("/registration/slots", response_model=ResponseModel)
def get_registration_slots(doctor_id: str, date: str = None, current_user: dict = Depends(get_patient_user)):
    slots = [
        {"slot_id": "slot_001", "date": "2024-01-15", "time_period": "上午", "start_time": "08:00", "end_time": "09:00", "remaining": 3, "total": 10},
        {"slot_id": "slot_002", "date": "2024-01-15", "time_period": "上午", "start_time": "09:00", "end_time": "10:00", "remaining": 5, "total": 10},
    ]
    return ResponseModel(data={"doctor_id": doctor_id, "hospital_id": "hosp_001", "department_id": "dept_005", "registration_fee": 50.00, "available_slots": slots})


@router.post("/registration", response_model=ResponseModel)
def create_registration(request: RegistrationRequest, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    registration = Registration(
        registration_id=generate_id("reg_"),
        consultation_id=request.consultation_id,
        patient_id=patient.patient_id,
        doctor_id=request.doctor_id,
        department=request.department_id,
        hospital_id=request.hospital_id,
        date="2024-01-15",
        time_period="上午",
        start_time="08:00",
        registration_fee=50.00,
        patient_name=request.patient_name,
        id_card=request.id_card,
        phone=request.phone,
        symptom_description=request.symptom_description,
        status="confirmed"
    )
    db.add(registration)
    db.commit()
    
    return ResponseModel(data={
        "registration_id": registration.registration_id,
        "hospital_system_id": None,
        "status": registration.status,
        "doctor_name": "张医生",
        "department": "神经内科",
        "hospital": "XX人民医院",
        "date": registration.date,
        "time_period": registration.time_period,
        "start_time": registration.start_time,
        "consultation_room": "门诊楼3楼301室",
        "registration_fee": registration.registration_fee,
        "qr_code": None,
        "created_at": registration.registration_time
    })


@router.get("/registration", response_model=ResponseModel)
def get_registration_list(status: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    query = db.query(Registration).filter(Registration.patient_id == patient.patient_id)
    if status:
        query = query.filter(Registration.status == status)
    
    total = query.count()
    registrations = query.order_by(Registration.registration_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for reg in registrations:
        result.append({
            "registration_id": reg.registration_id,
            "doctor_name": "张医生",
            "department": reg.department,
            "hospital": "XX人民医院",
            "date": reg.date,
            "time_period": reg.time_period,
            "status": reg.status,
            "created_at": reg.registration_time
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.put("/registration/{registration_id}/cancel", response_model=ResponseModel)
def cancel_registration(registration_id: str, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    registration = db.query(Registration).filter(
        Registration.registration_id == registration_id,
        Registration.patient_id == patient.patient_id
    ).first()
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="挂号记录不存在")
    
    registration.status = "cancelled"
    db.commit()
    
    return ResponseModel(data={"refund_amount": registration.registration_fee})


@router.get("/profile", response_model=ResponseModel)
def get_patient_profile(current_user: dict = Depends(get_patient_user)):
    patient = current_user["user"]
    return ResponseModel(data={
        "patient_id": patient.patient_id,
        "user_name": patient.user_name,
        "phone": patient.phone,
        "avatar": patient.avatar,
        "gender": patient.gender,
        "age": patient.age,
        "address": patient.address,
        "blood_type": patient.blood_type,
        "allergy_history": json_str_to_list(patient.allergy_history),
        "medical_history": json_str_to_list(patient.medical_history),
        "status": patient.status,
        "created_at": patient.created_at
    })


@router.put("/profile", response_model=ResponseModel)
def update_patient_profile(request: PatientProfileUpdate, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    if request.user_name:
        patient.user_name = request.user_name
    if request.avatar:
        patient.avatar = request.avatar
    if request.gender:
        patient.gender = request.gender
    if request.age is not None:
        patient.age = request.age
    if request.address:
        patient.address = request.address
    if request.blood_type:
        patient.blood_type = request.blood_type
    if request.allergy_history is not None:
        patient.allergy_history = list_to_json_str(request.allergy_history)
    if request.medical_history is not None:
        patient.medical_history = list_to_json_str(request.medical_history)
    
    db.commit()
    return ResponseModel(message="更新成功")


@router.get("/history/consultations", response_model=ResponseModel)
def get_consultation_history(keyword: str = None, start_date: str = None, end_date: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    query = db.query(Consultation).filter(Consultation.patient_id == patient.patient_id)
    if keyword:
        query = query.filter(Consultation.symptom_text.like(f"%{keyword}%"))
    
    total = query.count()
    consultations = query.order_by(Consultation.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for cons in consultations:
        result.append({
            "consultation_id": cons.consultation_id,
            "conversation_id": None,
            "title": "症状咨询",
            "symptom_text": cons.symptom_text,
            "matched_disease": cons.matched_disease,
            "matched_department": cons.matched_department,
            "created_at": cons.created_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.get("/history/consultations/{consultation_id}", response_model=ResponseModel)
def get_consultation_detail(consultation_id: str, current_user: dict = Depends(get_patient_user), db: Session = Depends(get_db)):
    patient = current_user["user"]
    
    consultation = db.query(Consultation).filter(
        Consultation.consultation_id == consultation_id,
        Consultation.patient_id == patient.patient_id
    ).first()
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="咨询记录不存在")
    
    return ResponseModel(data={
        "consultation_id": consultation.consultation_id,
        "conversation_id": None,
        "symptom_text": consultation.symptom_text,
        "matched_disease": consultation.matched_disease,
        "matched_department": consultation.matched_department,
        "recommendation_detail": consultation.recommendation_detail,
        "messages": [],
        "created_at": consultation.created_at
    })


@router.get("/reminders", response_model=ResponseModel)
def get_reminders(is_read: bool = None, type: str = None, page: int = 1, page_size: int = 20, current_user: dict = Depends(get_patient_user)):
    reminders = [
        {"reminder_id": "rem_001", "type": "registration", "title": "就诊提醒", "content": "您明天上午8点有神经内科张医生的门诊预约", "related_id": "reg_001", "is_read": False, "remind_time": datetime.now(), "created_at": datetime.now()},
    ]
    return ResponseModel(data={"list": reminders, "page": page, "page_size": page_size, "total": len(reminders), "unread_count": 1})


@router.put("/reminders/{reminder_id}/read", response_model=ResponseModel)
def mark_reminder_read(reminder_id: str, current_user: dict = Depends(get_patient_user)):
    return ResponseModel(message="标记成功")


@router.put("/reminders/read-all", response_model=ResponseModel)
def mark_all_reminders_read(current_user: dict = Depends(get_patient_user)):
    return ResponseModel(data={"marked_count": 1})
