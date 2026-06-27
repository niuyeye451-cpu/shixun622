from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil

from app.database import get_db
from app.models import Patient, Doctor, Admin, LoginLog, Feedback, MedicalEntity, MedicalRelation
from app.schemas import (
    SmsSendRequest, PatientLoginRequest, DoctorLoginRequest, AdminLoginRequest,
    RefreshTokenRequest, ChangePasswordRequest, FeedbackCreate, ResponseModel,
    GraphResponse, GraphNode, GraphEdge, EntitySearchResponse, EntityDetailResponse,
    RelationQueryResponse, RelationPath
)
from app.utils import generate_id, create_access_token, create_refresh_token, decode_token, list_to_json_str, json_str_to_list, json_str_to_dict
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/common", tags=["common"])

sms_store = {}


@router.post("/auth/sms/send", response_model=ResponseModel)
def send_sms(request: SmsSendRequest):
    sms_id = generate_id("sms_")
    sms_store[sms_id] = {"phone": request.phone, "code": "123456", "type": request.type, "created_at": datetime.now()}
    return ResponseModel(data={"sms_id": sms_id, "expire_seconds": 300})


@router.post("/auth/patient/login", response_model=ResponseModel)
def patient_login(request: PatientLoginRequest, db: Session = Depends(get_db)):
    sms_data = sms_store.get(request.sms_id)
    if not sms_data or sms_data["code"] != request.code or sms_data["phone"] != request.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")

    patient = db.query(Patient).filter(Patient.phone == request.phone).first()
    if not patient:
        patient = Patient(
            patient_id=generate_id("pat_"),
            user_name=request.phone[-4:],
            phone=request.phone,
            status=1
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

    access_token = create_access_token(data={"user_id": patient.patient_id, "user_type": "patient"})
    refresh_token = create_refresh_token(data={"user_id": patient.patient_id, "user_type": "patient"})

    return ResponseModel(data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 7200,
        "user_info": {
            "patient_id": patient.patient_id,
            "user_name": patient.user_name,
            "phone": patient.phone,
            "status": patient.status,
            "created_at": patient.created_at
        }
    })


@router.post("/auth/doctor/login", response_model=ResponseModel)
def doctor_login(request: DoctorLoginRequest, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.user_name == request.user_name).first()
    if not doctor or doctor.password_hash != request.password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")

    access_token = create_access_token(data={"user_id": doctor.doctor_id, "user_type": "doctor"})
    refresh_token = create_refresh_token(data={"user_id": doctor.doctor_id, "user_type": "doctor"})

    return ResponseModel(data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 7200,
        "user_info": {
            "doctor_id": doctor.doctor_id,
            "user_name": doctor.user_name,
            "phone": doctor.phone,
            "department": doctor.department,
            "title": doctor.title,
            "is_first_login": doctor.is_first_login,
            "created_at": doctor.created_at
        }
    })


@router.post("/auth/admin/login", response_model=ResponseModel)
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.user_name == request.user_name).first()
    if not admin or admin.password_hash != request.password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")

    access_token = create_access_token(data={"user_id": admin.admin_id, "user_type": "admin"})
    refresh_token = create_refresh_token(data={"user_id": admin.admin_id, "user_type": "admin"})

    return ResponseModel(data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 7200,
        "user_info": {
            "admin_id": admin.admin_id,
            "user_name": admin.user_name,
            "role_level": admin.role_level,
            "status": admin.status,
            "created_at": admin.created_at
        }
    })


@router.post("/auth/token/refresh", response_model=ResponseModel)
def refresh_token(request: RefreshTokenRequest):
    payload = decode_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的refresh token")

    access_token = create_access_token(data={"user_id": payload["user_id"], "user_type": payload["user_type"]})
    return ResponseModel(data={"access_token": access_token, "expires_in": 7200})


@router.post("/auth/logout", response_model=ResponseModel)
def logout(current_user: dict = Depends(get_current_user)):
    return ResponseModel(message="登出成功")


@router.put("/auth/password", response_model=ResponseModel)
def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = current_user["user"]
    if user.password_hash != request.old_password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误")
    
    user.password_hash = request.new_password_hash
    db.commit()
    return ResponseModel(message="密码修改成功")


@router.get("/departments", response_model=ResponseModel)
def get_departments(keyword: str = None):
    departments = [
        {"department_id": "dept_001", "department_name": "内科", "description": "内科诊疗", "sort_order": 1},
        {"department_id": "dept_002", "department_name": "外科", "description": "外科诊疗", "sort_order": 2},
        {"department_id": "dept_003", "department_name": "妇产科", "description": "妇产科诊疗", "sort_order": 3},
        {"department_id": "dept_004", "department_name": "儿科", "description": "儿科诊疗", "sort_order": 4},
        {"department_id": "dept_005", "department_name": "神经内科", "description": "神经内科诊疗", "sort_order": 5},
        {"department_id": "dept_006", "department_name": "心血管内科", "description": "心血管内科诊疗", "sort_order": 6},
        {"department_id": "dept_007", "department_name": "消化内科", "description": "消化内科诊疗", "sort_order": 7},
        {"department_id": "dept_008", "department_name": "骨科", "description": "骨科诊疗", "sort_order": 8},
    ]
    if keyword:
        departments = [d for d in departments if keyword in d["department_name"]]
    return ResponseModel(data=departments)


@router.get("/hospitals", response_model=ResponseModel)
def get_hospitals(department_id: str = None, city: str = None, page: int = 1, page_size: int = 10):
    hospitals = [
        {"hospital_id": "hosp_001", "hospital_name": "XX人民医院", "hospital_level": "三级甲等", "address": "北京市XX区XX路1号", "phone": "010-12345678"},
        {"hospital_id": "hosp_002", "hospital_name": "XX协和医院", "hospital_level": "三级甲等", "address": "北京市XX区XX路2号", "phone": "010-23456789"},
        {"hospital_id": "hosp_003", "hospital_name": "XX中医院", "hospital_level": "三级甲等", "address": "北京市XX区XX路3号", "phone": "010-34567890"},
    ]
    total = len(hospitals)
    start = (page - 1) * page_size
    end = start + page_size
    return ResponseModel(data={"list": hospitals[start:end], "page": page, "page_size": page_size, "total": total})


@router.post("/upload/image", response_model=ResponseModel)
async def upload_image(file: UploadFile = File(...), scene: str = "other"):
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_id = generate_id("file_")
    file_ext = file.filename.split(".")[-1]
    file_path = os.path.join(upload_dir, f"{file_id}.{file_ext}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return ResponseModel(data={"file_id": file_id, "file_url": f"/uploads/{file_id}.{file_ext}", "file_size": os.path.getsize(file_path)})


@router.post("/feedback", response_model=ResponseModel)
def submit_feedback(request: FeedbackCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = current_user["user"]
    user_type = current_user["user_type"]
    
    feedback = Feedback(
        feedback_id=generate_id("fb_"),
        consultation_id=request.consultation_id,
        patient_id=user.patient_id if user_type == "patient" else None,
        doctor_id=user.doctor_id if user_type == "doctor" else None,
        rating=request.rating,
        is_accurate=request.is_accurate,
        corrected_answer=request.corrected_answer,
        content=request.content
    )
    db.add(feedback)
    db.commit()
    return ResponseModel(data={"feedback_id": feedback.feedback_id})


@router.get("/graph/disease/{disease_name}", response_model=ResponseModel)
def get_disease_graph(disease_name: str, depth: int = 2, relation_types: str = None, db: Session = Depends(get_db)):
    disease = db.query(MedicalEntity).filter(MedicalEntity.name == disease_name, MedicalEntity.type == "disease").first()
    if not disease:
        return ResponseModel(data={"nodes": [], "edges": []})
    
    relations = db.query(MedicalRelation).filter(
        (MedicalRelation.source_entity_id == disease.entity_id) |
        (MedicalRelation.target_entity_id == disease.entity_id)
    ).limit(20).all()
    
    nodes = [GraphNode(id=disease.entity_id, name=disease.name, type=disease.type, description=disease.description)]
    edges = []
    
    for rel in relations:
        target_entity = db.query(MedicalEntity).filter(MedicalEntity.entity_id == rel.target_entity_id).first()
        if target_entity:
            nodes.append(GraphNode(id=target_entity.entity_id, name=target_entity.name, type=target_entity.type, description=target_entity.description))
            edges.append(GraphEdge(
                id=rel.relation_id,
                source=rel.source_entity_id,
                target=rel.target_entity_id,
                relation=rel.relation_type,
                relation_name=rel.relation_name
            ))
    
    return ResponseModel(data=GraphResponse(nodes=nodes, edges=edges, center_node=disease.entity_id))


@router.get("/graph/entities/search", response_model=ResponseModel)
def search_entities(keyword: str, entity_type: str = None, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(MedicalEntity).filter(MedicalEntity.name.like(f"%{keyword}%"))
    if entity_type:
        query = query.filter(MedicalEntity.type == entity_type)
    
    entities = query.limit(limit).all()
    results = []
    for entity in entities:
        results.append(EntitySearchResponse(
            entity_id=entity.entity_id,
            name=entity.name,
            type=entity.type,
            aliases=json_str_to_list(entity.aliases),
            description=entity.description
        ))
    return ResponseModel(data=results)


@router.get("/graph/entities/{entity_id}", response_model=ResponseModel)
def get_entity_detail(entity_id: str, db: Session = Depends(get_db)):
    entity = db.query(MedicalEntity).filter(MedicalEntity.entity_id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="实体不存在")
    
    return ResponseModel(data=EntityDetailResponse(
        entity_id=entity.entity_id,
        name=entity.name,
        type=entity.type,
        aliases=json_str_to_list(entity.aliases),
        description=entity.description,
        source_version=entity.source_version,
        version_number=entity.version_number,
        attributes=json_str_to_dict(entity.attributes)
    ))


@router.get("/graph/relations", response_model=ResponseModel)
def query_relations(source_entity: str, target_entity: str, max_depth: int = 3, db: Session = Depends(get_db)):
    source = db.query(MedicalEntity).filter(
        (MedicalEntity.entity_id == source_entity) | (MedicalEntity.name == source_entity)
    ).first()
    target = db.query(MedicalEntity).filter(
        (MedicalEntity.entity_id == target_entity) | (MedicalEntity.name == target_entity)
    ).first()
    
    if not source or not target:
        return ResponseModel(data={"paths": [], "total_paths": 0})
    
    relations = db.query(MedicalRelation).filter(
        (MedicalRelation.source_entity_id == source.entity_id) |
        (MedicalRelation.source_entity_id == target.entity_id)
    ).limit(10).all()
    
    paths = []
    for rel in relations:
        paths.append(RelationPath(
            path_id=generate_id("path_"),
            length=1,
            nodes=[source.entity_id, rel.target_entity_id],
            edges=[rel.relation_id],
            confidence=0.95
        ))
    
    return ResponseModel(data=RelationQueryResponse(paths=paths, total_paths=len(paths)))
