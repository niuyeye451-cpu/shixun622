from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db
from app.models import (
    Patient, Doctor, Admin, Feedback, UnknownQuestion, MedicalEntity,
    MedicalRelation, Synonym, KnowledgeVersion, OperationLog
)
from app.schemas import (
    CreateDoctorRequest, UpdateUserStatusRequest, MedicalEntityCreate,
    MedicalEntityUpdate, MedicalRelationCreate, SynonymCreate,
    KnowledgeVersionCreate, ResolveUnknownQuestionRequest,
    BatchResolveRequest, ResponseModel
)
from app.utils import generate_id, list_to_json_str, json_str_to_list, json_str_to_dict, dict_to_json_str, get_password_hash
from app.dependencies import get_admin_user
from app.graph_db import get_graph_db

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def log_operation(current_user: dict, action: str, target: str, target_id: str = None, detail: str = None, db: Session = None):
    if db:
        log = OperationLog(
            log_id=generate_id("log_"),
            operator_id=current_user["user"].admin_id,
            operator_type="admin",
            operator_name=current_user["user"].user_name,
            action=action,
            target=target,
            target_id=target_id,
            detail=detail
        )
        db.add(log)
        db.commit()


@router.get("/users/patients", response_model=ResponseModel)
def get_patient_list(keyword: str = None, status: int = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    query = db.query(Patient)
    if keyword:
        query = query.filter(
            (Patient.user_name.like(f"%{keyword}%")) |
            (Patient.phone.like(f"%{keyword}%"))
        )
    if status is not None:
        query = query.filter(Patient.status == status)
    
    total = query.count()
    patients = query.order_by(Patient.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for patient in patients:
        result.append({
            "patient_id": patient.patient_id,
            "user_name": patient.user_name,
            "phone": patient.phone,
            "avatar": patient.avatar,
            "gender": patient.gender,
            "age": patient.age,
            "status": patient.status,
            "created_at": patient.created_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.get("/users/patients/{patient_id}", response_model=ResponseModel)
def get_patient_detail(patient_id: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    
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


@router.put("/users/patients/{patient_id}/status", response_model=ResponseModel)
def update_patient_status(patient_id: str, request: UpdateUserStatusRequest, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    
    patient.status = request.status
    db.commit()
    
    log_operation(current_user, "update_status", "patient", patient_id, f"状态变更为{request.status}")
    
    return ResponseModel(message="更新成功")


@router.get("/users/doctors", response_model=ResponseModel)
def get_doctor_list(keyword: str = None, department: str = None, status: int = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    query = db.query(Doctor)
    if keyword:
        query = query.filter(
            (Doctor.user_name.like(f"%{keyword}%")) |
            (Doctor.phone.like(f"%{keyword}%"))
        )
    if department:
        query = query.filter(Doctor.department == department)
    if status is not None:
        query = query.filter(Doctor.status == status)
    
    total = query.count()
    doctors = query.order_by(Doctor.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for doctor in doctors:
        result.append({
            "doctor_id": doctor.doctor_id,
            "user_name": doctor.user_name,
            "phone": doctor.phone,
            "department": doctor.department,
            "title": doctor.title,
            "hospital": doctor.hospital,
            "specialty": doctor.specialty,
            "is_first_login": doctor.is_first_login,
            "status": doctor.status,
            "created_at": doctor.created_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.post("/users/doctors", response_model=ResponseModel)
def create_doctor(request: CreateDoctorRequest, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    existing = db.query(Doctor).filter(Doctor.phone == request.phone).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该手机号已注册")
    
    doctor = Doctor(
        doctor_id=generate_id("doc_"),
        user_name=request.user_name,
        phone=request.phone,
        password_hash=get_password_hash(request.password_hash),
        department=request.department,
        title=request.title,
        hospital=request.hospital,
        is_first_login=True,
        status=1
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    
    log_operation(current_user, "create", "doctor", doctor.doctor_id)
    
    return ResponseModel(data={
        "doctor_id": doctor.doctor_id,
        "user_name": doctor.user_name,
        "phone": doctor.phone,
        "department": doctor.department,
        "title": doctor.title,
        "hospital": doctor.hospital,
        "created_at": doctor.created_at
    })


@router.get("/users/doctors/{doctor_id}", response_model=ResponseModel)
def get_doctor_detail(doctor_id: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="医师不存在")
    
    return ResponseModel(data={
        "doctor_id": doctor.doctor_id,
        "user_name": doctor.user_name,
        "phone": doctor.phone,
        "department": doctor.department,
        "title": doctor.title,
        "hospital": doctor.hospital,
        "specialty": doctor.specialty,
        "introduction": doctor.introduction,
        "avatar": doctor.avatar,
        "is_first_login": doctor.is_first_login,
        "status": doctor.status,
        "created_at": doctor.created_at
    })


@router.put("/users/doctors/{doctor_id}/status", response_model=ResponseModel)
def update_doctor_status(doctor_id: str, request: UpdateUserStatusRequest, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="医师不存在")
    
    doctor.status = request.status
    db.commit()
    
    log_operation(current_user, "update_status", "doctor", doctor_id, f"状态变更为{request.status}")
    
    return ResponseModel(message="更新成功")


@router.get("/users/admins", response_model=ResponseModel)
def get_admin_list(keyword: str = None, role_level: int = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    query = db.query(Admin)
    if keyword:
        query = query.filter(
            (Admin.user_name.like(f"%{keyword}%")) |
            (Admin.phone.like(f"%{keyword}%"))
        )
    if role_level is not None:
        query = query.filter(Admin.role_level == role_level)
    
    total = query.count()
    admins = query.order_by(Admin.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for admin in admins:
        result.append({
            "admin_id": admin.admin_id,
            "user_name": admin.user_name,
            "phone": admin.phone,
            "role_level": admin.role_level,
            "status": admin.status,
            "created_at": admin.created_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.post("/knowledge/entities", response_model=ResponseModel)
def create_medical_entity(request: MedicalEntityCreate, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    existing = db.query(MedicalEntity).filter(MedicalEntity.name == request.name, MedicalEntity.type == request.type).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该实体已存在")
    
    entity = MedicalEntity(
        entity_id=generate_id("ent_"),
        name=request.name,
        type=request.type,
        aliases=list_to_json_str(request.aliases) if request.aliases else None,
        description=request.description,
        attributes=dict_to_json_str(request.attributes) if request.attributes else None,
        version_number=request.version_number,
        status="draft"
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    
    log_operation(current_user, "create", "entity", entity.entity_id)
    
    return ResponseModel(data={
        "entity_id": entity.entity_id,
        "name": entity.name,
        "type": entity.type,
        "status": entity.status,
        "created_at": entity.created_at
    })


@router.get("/knowledge/entities", response_model=ResponseModel)
def get_entity_list(entity_type: str = None, keyword: str = None, status: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    # 从图数据库查询实体（数据在 graph.db 中，不在空 SQLite 表中）
    graph_db = get_graph_db()

    # Type mapping: frontend sends lowercase, graph uses Capitalized
    type_map = {
        "disease": "Disease", "symptom": "Symptom", "drug": "Drug",
        "check": "Check", "department": "Department", "cure_way": "CureWay",
        "food": "Food", "producer": "Producer"
    }
    graph_label = type_map.get(entity_type.lower()) if entity_type else None

    if keyword:
        all_entities = graph_db.search_nodes(keyword, graph_label, limit=500)
    elif graph_label:
        all_entities = graph_db.get_nodes_by_label(graph_label, limit=500)
    else:
        # 获取所有类型的实体
        all_entities = []
        for label in type_map.values():
            all_entities.extend(graph_db.get_nodes_by_label(label, limit=100))

    total = len(all_entities)
    # 简单分页
    start = (page - 1) * page_size
    paged = all_entities[start:start + page_size]

    result = []
    for entity in paged:
        props = entity.get('properties', {})
        aliases = props.get('alias', []) if isinstance(props, dict) else []
        result.append({
            "entity_id": entity['id'],
            "name": entity['name'],
            "type": entity.get('label', ''),
            "aliases": aliases if isinstance(aliases, list) else [],
            "description": (props.get('desc', '') if isinstance(props, dict) else '')[:200],
            "status": "published",
            "version_number": "v1",
            "created_at": ""
        })

    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.get("/knowledge/entities/{entity_id}", response_model=ResponseModel)
def get_entity_detail(entity_id: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    graph_db = get_graph_db()
    entity = graph_db.get_node_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="实体不存在")

    props = entity.get('properties', {})
    aliases = props.get('alias', []) if isinstance(props, dict) else []
    return ResponseModel(data={
        "entity_id": entity['id'],
        "name": entity['name'],
        "type": entity.get('label', ''),
        "aliases": aliases if isinstance(aliases, list) else [],
        "description": (props.get('desc', '') if isinstance(props, dict) else '')[:500],
        "attributes": props if isinstance(props, dict) else {},
        "source_version": "v1",
        "version_number": "v1",
        "status": "published",
        "created_at": "",
        "updated_at": ""
    })


@router.put("/knowledge/entities/{entity_id}", response_model=ResponseModel)
def update_entity(entity_id: str, request: MedicalEntityUpdate, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    entity = db.query(MedicalEntity).filter(MedicalEntity.entity_id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="实体不存在")
    
    if request.name:
        entity.name = request.name
    if request.aliases is not None:
        entity.aliases = list_to_json_str(request.aliases)
    if request.description:
        entity.description = request.description
    if request.attributes is not None:
        entity.attributes = dict_to_json_str(request.attributes)
    if request.status:
        entity.status = request.status
    entity.updated_at = datetime.now()
    
    db.commit()
    
    log_operation(current_user, "update", "entity", entity_id)
    
    return ResponseModel(message="更新成功")


@router.delete("/knowledge/entities/{entity_id}", response_model=ResponseModel)
def delete_entity(entity_id: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    entity = db.query(MedicalEntity).filter(MedicalEntity.entity_id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="实体不存在")
    
    db.delete(entity)
    db.commit()
    
    log_operation(current_user, "delete", "entity", entity_id)
    
    return ResponseModel(message="删除成功")


@router.post("/knowledge/relations", response_model=ResponseModel)
def create_medical_relation(request: MedicalRelationCreate, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    source = db.query(MedicalEntity).filter(MedicalEntity.entity_id == request.source_entity_id).first()
    target = db.query(MedicalEntity).filter(MedicalEntity.entity_id == request.target_entity_id).first()
    
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="源实体不存在")
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目标实体不存在")
    
    relation = MedicalRelation(
        relation_id=generate_id("rel_"),
        source_entity_id=request.source_entity_id,
        target_entity_id=request.target_entity_id,
        relation_type=request.relation_type,
        text=request.text,
        version_number=request.version_number
    )
    db.add(relation)
    db.commit()
    db.refresh(relation)
    
    log_operation(current_user, "create", "relation", relation.relation_id)
    
    return ResponseModel(data={
        "relation_id": relation.relation_id,
        "source_entity_id": relation.source_entity_id,
        "target_entity_id": relation.target_entity_id,
        "relation_type": relation.relation_type,
        "created_at": relation.created_at
    })


@router.get("/knowledge/relations", response_model=ResponseModel)
def get_relation_list(source_entity_id: str = None, target_entity_id: str = None, relation_type: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    query = db.query(MedicalRelation)
    if source_entity_id:
        query = query.filter(MedicalRelation.source_entity_id == source_entity_id)
    if target_entity_id:
        query = query.filter(MedicalRelation.target_entity_id == target_entity_id)
    if relation_type:
        query = query.filter(MedicalRelation.relation_type == relation_type)
    
    total = query.count()
    relations = query.order_by(MedicalRelation.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for rel in relations:
        source = db.query(MedicalEntity).filter(MedicalEntity.entity_id == rel.source_entity_id).first()
        target = db.query(MedicalEntity).filter(MedicalEntity.entity_id == rel.target_entity_id).first()
        result.append({
            "relation_id": rel.relation_id,
            "source_entity_id": rel.source_entity_id,
            "source_entity_name": source.name if source else "",
            "target_entity_id": rel.target_entity_id,
            "target_entity_name": target.name if target else "",
            "relation_type": rel.relation_type,
            "relation_name": rel.relation_name,
            "text": rel.text,
            "created_at": rel.created_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.delete("/knowledge/relations/{relation_id}", response_model=ResponseModel)
def delete_relation(relation_id: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    relation = db.query(MedicalRelation).filter(MedicalRelation.relation_id == relation_id).first()
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关系不存在")
    
    db.delete(relation)
    db.commit()
    
    log_operation(current_user, "delete", "relation", relation_id)
    
    return ResponseModel(message="删除成功")


@router.post("/knowledge/synonyms", response_model=ResponseModel)
def create_synonym(request: SynonymCreate, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    entity = db.query(MedicalEntity).filter(MedicalEntity.entity_id == request.standard_entity_id).first()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标准实体不存在")
    
    existing = db.query(Synonym).filter(Synonym.alias_term == request.alias_term).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该别名已存在")
    
    synonym = Synonym(
        synonym_id=generate_id("syn_"),
        alias_term=request.alias_term,
        standard_entity_id=request.standard_entity_id,
        source=request.source
    )
    db.add(synonym)
    db.commit()
    db.refresh(synonym)
    
    log_operation(current_user, "create", "synonym", synonym.synonym_id)
    
    return ResponseModel(data={"synonym_id": synonym.synonym_id, "alias_term": synonym.alias_term})


@router.get("/knowledge/synonyms", response_model=ResponseModel)
def get_synonym_list(standard_entity_id: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    query = db.query(Synonym)
    if standard_entity_id:
        query = query.filter(Synonym.standard_entity_id == standard_entity_id)
    
    total = query.count()
    synonyms = query.order_by(Synonym.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for syn in synonyms:
        entity = db.query(MedicalEntity).filter(MedicalEntity.entity_id == syn.standard_entity_id).first()
        result.append({
            "synonym_id": syn.synonym_id,
            "alias_term": syn.alias_term,
            "standard_entity_id": syn.standard_entity_id,
            "standard_entity_name": entity.name if entity else "",
            "source": syn.source,
            "created_at": syn.created_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.delete("/knowledge/synonyms/{synonym_id}", response_model=ResponseModel)
def delete_synonym(synonym_id: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    synonym = db.query(Synonym).filter(Synonym.synonym_id == synonym_id).first()
    if not synonym:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="同义词不存在")
    
    db.delete(synonym)
    db.commit()
    
    log_operation(current_user, "delete", "synonym", synonym_id)
    
    return ResponseModel(message="删除成功")


@router.post("/knowledge/versions", response_model=ResponseModel)
def create_knowledge_version(request: KnowledgeVersionCreate, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    existing = db.query(KnowledgeVersion).filter(KnowledgeVersion.version_number == request.version_number).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该版本号已存在")
    
    entity_count = db.query(MedicalEntity).count()
    relation_count = db.query(MedicalRelation).count()
    
    version = KnowledgeVersion(
        version_id=generate_id("ver_"),
        version_number=request.version_number,
        entity_count=entity_count,
        relation_count=relation_count,
        operator_id=current_user["user"].admin_id,
        update_content=request.update_content,
        status="draft"
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    
    log_operation(current_user, "create", "version", version.version_id)
    
    return ResponseModel(data={
        "version_id": version.version_id,
        "version_number": version.version_number,
        "entity_count": version.entity_count,
        "relation_count": version.relation_count,
        "status": version.status,
        "created_at": version.created_at
    })


@router.get("/knowledge/versions", response_model=ResponseModel)
def get_version_list(status: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    query = db.query(KnowledgeVersion)
    if status:
        query = query.filter(KnowledgeVersion.status == status)
    
    total = query.count()
    versions = query.order_by(KnowledgeVersion.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for version in versions:
        result.append({
            "version_id": version.version_id,
            "version_number": version.version_number,
            "entity_count": version.entity_count,
            "relation_count": version.relation_count,
            "status": version.status,
            "update_content": version.update_content,
            "change_log": version.change_log,
            "published_at": version.published_at,
            "created_at": version.created_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.put("/knowledge/versions/{version_id}/publish", response_model=ResponseModel)
def publish_version(version_id: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    version = db.query(KnowledgeVersion).filter(KnowledgeVersion.version_id == version_id).first()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")
    
    version.status = "published"
    version.published_at = datetime.now()
    version.approved_by = current_user["user"].admin_id
    
    db.query(MedicalEntity).filter(MedicalEntity.status == "draft").update({"status": "published", "version_number": version.version_number})
    db.query(MedicalRelation).filter(MedicalRelation.status == "draft").update({"version_number": version.version_number})
    
    db.commit()
    
    log_operation(current_user, "publish", "version", version_id)
    
    return ResponseModel(data={"version_id": version.version_id, "status": "published", "published_at": version.published_at})


@router.get("/feedbacks", response_model=ResponseModel)
def get_feedback_list(type: str = None, status: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    query = db.query(Feedback)
    if type:
        query = query.filter(Feedback.type == type)
    if status:
        query = query.filter(Feedback.status == status)
    
    total = query.count()
    feedbacks = query.order_by(Feedback.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for fb in feedbacks:
        patient = db.query(Patient).filter(Patient.patient_id == fb.patient_id).first() if fb.patient_id else None
        doctor = db.query(Doctor).filter(Doctor.doctor_id == fb.doctor_id).first() if fb.doctor_id else None
        result.append({
            "feedback_id": fb.feedback_id,
            "consultation_id": fb.consultation_id,
            "patient_id": fb.patient_id,
            "patient_name": patient.user_name if patient else "",
            "doctor_id": fb.doctor_id,
            "doctor_name": doctor.user_name if doctor else "",
            "rating": fb.rating,
            "is_accurate": fb.is_accurate,
            "corrected_answer": fb.corrected_answer,
            "content": fb.content,
            "type": fb.type,
            "title": fb.title,
            "status": fb.status,
            "reply": fb.reply,
            "resolved_at": fb.resolved_at,
            "created_at": fb.created_at
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.get("/feedbacks/{feedback_id}", response_model=ResponseModel)
def get_feedback_detail(feedback_id: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="反馈不存在")
    
    return ResponseModel(data={
        "feedback_id": feedback.feedback_id,
        "consultation_id": feedback.consultation_id,
        "patient_id": feedback.patient_id,
        "doctor_id": feedback.doctor_id,
        "rating": feedback.rating,
        "is_accurate": feedback.is_accurate,
        "corrected_answer": feedback.corrected_answer,
        "content": feedback.content,
        "type": feedback.type,
        "related_entity_id": feedback.related_entity_id,
        "related_query_id": feedback.related_query_id,
        "title": feedback.title,
        "references": json_str_to_list(feedback.references),
        "status": feedback.status,
        "reply": feedback.reply,
        "resolved_at": feedback.resolved_at,
        "created_at": feedback.created_at
    })


@router.put("/feedbacks/{feedback_id}/reply", response_model=ResponseModel)
def reply_feedback(feedback_id: str, reply: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="反馈不存在")
    
    feedback.reply = reply
    feedback.status = "resolved"
    feedback.resolved_at = datetime.now()
    
    db.commit()
    
    log_operation(current_user, "reply", "feedback", feedback_id)
    
    return ResponseModel(message="回复成功")


@router.get("/unknown-questions", response_model=ResponseModel)
def get_unknown_questions(category: str = None, status: str = None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    query = db.query(UnknownQuestion)
    if category:
        query = query.filter(UnknownQuestion.category == category)
    if status:
        query = query.filter(UnknownQuestion.status == status)
    
    total = query.count()
    questions = query.order_by(UnknownQuestion.occur_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for q in questions:
        result.append({
            "question_id": q.question_id,
            "text": q.text,
            "source_role": q.source_role,
            "source_id": q.source_id,
            "category": q.category,
            "status": q.status,
            "occur_time": q.occur_time,
            "occur_count": q.occur_count,
            "related_conversation_id": q.related_conversation_id,
            "resolved_answer": q.resolved_answer,
            "resolved_at": q.resolved_at,
            "resolved_by": q.resolved_by
        })
    
    return ResponseModel(data={"list": result, "page": page, "page_size": page_size, "total": total})


@router.get("/unknown-questions/{question_id}", response_model=ResponseModel)
def get_unknown_question_detail(question_id: str, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    question = db.query(UnknownQuestion).filter(UnknownQuestion.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未知问题不存在")
    
    return ResponseModel(data={
        "question_id": question.question_id,
        "text": question.text,
        "source_role": question.source_role,
        "source_id": question.source_id,
        "category": question.category,
        "status": question.status,
        "occur_time": question.occur_time,
        "occur_count": question.occur_count,
        "related_conversation_id": question.related_conversation_id,
        "resolved_answer": question.resolved_answer,
        "resolved_at": question.resolved_at,
        "resolved_by": question.resolved_by
    })


@router.put("/unknown-questions/{question_id}/resolve", response_model=ResponseModel)
def resolve_unknown_question(question_id: str, request: ResolveUnknownQuestionRequest, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    question = db.query(UnknownQuestion).filter(UnknownQuestion.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未知问题不存在")
    
    question.resolved_answer = request.resolved_answer
    question.status = "resolved"
    question.resolved_at = datetime.now()
    question.resolved_by = current_user["user"].admin_id
    
    db.commit()
    
    log_operation(current_user, "resolve", "unknown_question", question_id)
    
    return ResponseModel(data={"question_id": question_id, "status": "resolved"})


@router.post("/unknown-questions/batch-resolve", response_model=ResponseModel)
def batch_resolve_questions(request: BatchResolveRequest, current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    if request.action == "resolve":
        updated = db.query(UnknownQuestion).filter(UnknownQuestion.question_id.in_(request.question_ids)).update({
            "resolved_answer": request.resolved_answer,
            "status": "resolved",
            "resolved_at": datetime.now(),
            "resolved_by": current_user["user"].admin_id
        })
    elif request.action == "ignore":
        updated = db.query(UnknownQuestion).filter(UnknownQuestion.question_id.in_(request.question_ids)).update({
            "status": "ignored"
        })
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的操作类型")
    
    db.commit()
    
    log_operation(current_user, "batch_resolve", "unknown_question", detail=f"处理{len(request.question_ids)}条记录")
    
    return ResponseModel(data={"updated_count": updated})


@router.get("/statistics/dashboard", response_model=ResponseModel)
def get_dashboard_stats(current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    patient_count = db.query(Patient).count()
    doctor_count = db.query(Doctor).count()
    admin_count = db.query(Admin).count()
    graph_db = get_graph_db()
    kg_stats = graph_db.get_statistics()
    entity_count = kg_stats.get('total_nodes', 0)
    relation_count = kg_stats.get('total_relationships', 0)
    feedback_count = db.query(Feedback).filter(Feedback.status == "pending").count()
    unknown_count = db.query(UnknownQuestion).filter(UnknownQuestion.status == "pending").count()
    
    return ResponseModel(data={
        "patient_count": patient_count,
        "doctor_count": doctor_count,
        "admin_count": admin_count,
        "entity_count": entity_count,
        "relation_count": relation_count,
        "pending_feedback_count": feedback_count,
        "pending_unknown_count": unknown_count,
        "daily_stats": {
            "new_patients": 15,
            "new_doctors": 2,
            "consultations": 45,
            "registrations": 12
        }
    })


@router.get("/statistics/consultations", response_model=ResponseModel)
def get_consultation_stats(start_date: str, end_date: str, dimension: str = "day", current_user: dict = Depends(get_admin_user)):
    stats = []
    for i in range(7):
        stats.append({
            "date": f"2024-01-{15+i}",
            "total": 40 + i * 5,
            "symptom": 20 + i * 3,
            "disease": 15 + i * 2,
            "drug": 5 + i * 1
        })
    
    return ResponseModel(data={"dimension": dimension, "stats": stats})


@router.get("/statistics/feedback", response_model=ResponseModel)
def get_feedback_stats(start_date: str, end_date: str, current_user: dict = Depends(get_admin_user)):
    return ResponseModel(data={
        "total_count": 120,
        "resolved_count": 95,
        "accuracy_rate": 0.85,
        "average_rating": 4.2,
        "by_type": {
            "knowledge_error": 30,
            "answer_error": 25,
            "suggestion": 40,
            "other": 25
        }
    })


@router.get("/statistics/knowledge", response_model=ResponseModel)
def get_knowledge_stats(current_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    graph_db = get_graph_db()
    stats = graph_db.get_statistics()

    type_counts = {}
    for item in stats.get('label_distribution', []):
        if isinstance(item, dict):
            type_counts[item.get('label', 'unknown')] = item.get('count', 0)

    return ResponseModel(data={
        "total_entities": stats.get('total_nodes', 0),
        "total_relations": stats.get('total_relationships', 0),
        "total_synonyms": 0,
        "total_versions": 0,
        "by_type": type_counts
    })