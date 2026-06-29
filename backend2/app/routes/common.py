from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil

from app.database import get_db
from app.models import Patient, Doctor, Admin, LoginLog, Feedback, Department, Hospital, MedicalEntity, MedicalRelation
from app.schemas import (
    SmsSendRequest, PatientLoginRequest, PatientPasswordLoginRequest,
    PatientRegisterRequest, DoctorLoginRequest, DoctorRegisterRequest,
    AdminLoginRequest, RefreshTokenRequest, ChangePasswordRequest, FeedbackCreate,
    ResponseModel, GraphResponse, GraphNode, GraphEdge, EntitySearchResponse,
    EntityDetailResponse, RelationQueryResponse, RelationPath
)
from app.utils import (
    generate_id, create_access_token, create_refresh_token, decode_token,
    list_to_json_str, json_str_to_list, json_str_to_dict, get_password_hash,
    verify_password
)
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


@router.post("/auth/patient/register", response_model=ResponseModel)
def patient_register(request: PatientRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.phone == request.phone).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该手机号已注册")

    hashed_password = get_password_hash(request.password)
    patient = Patient(
        patient_id=generate_id("pat_"),
        user_name=request.user_name if request.user_name else request.phone[-4:],
        phone=request.phone,
        password_hash=hashed_password,
        gender=request.gender,
        age=request.age,
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
            "gender": patient.gender,
            "age": patient.age,
            "status": patient.status,
            "created_at": patient.created_at
        }
    }, message="注册成功")


@router.post("/auth/patient/login-password", response_model=ResponseModel)
def patient_password_login(request: PatientPasswordLoginRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.phone == request.phone).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在")
    if not patient.password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请使用短信验证码登录")
    if not verify_password(request.password, patient.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码错误")
    if patient.status != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号已被禁用")

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
    if not doctor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    if not verify_password(request.password, doctor.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    if doctor.status != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号已被禁用")

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


@router.post("/auth/doctor/register", response_model=ResponseModel)
def doctor_register(request: DoctorRegisterRequest, db: Session = Depends(get_db)):
    existing_username = db.query(Doctor).filter(Doctor.user_name == request.user_name).first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该用户名已存在")

    existing_phone = db.query(Doctor).filter(Doctor.phone == request.phone).first()
    if existing_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该手机号已注册")

    hashed_password = get_password_hash(request.password)
    doctor = Doctor(
        doctor_id=generate_id("doc_"),
        user_name=request.user_name,
        phone=request.phone,
        password_hash=hashed_password,
        department=request.department,
        title=request.title,
        hospital=request.hospital,
        specialty=None,
        is_first_login=True,
        status=1
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

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
            "hospital": doctor.hospital,
            "is_first_login": doctor.is_first_login,
            "status": doctor.status,
            "created_at": doctor.created_at
        }
    }, message="注册成功")


@router.post("/auth/admin/login", response_model=ResponseModel)
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.user_name == request.user_name).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    if admin.status != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号已被禁用")

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token无效或已过期")

    user_id = payload.get("user_id")
    user_type = payload.get("user_type")
    if not user_id or not user_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token无效")

    new_access_token = create_access_token(data={"user_id": user_id, "user_type": user_type})
    new_refresh_token = create_refresh_token(data={"user_id": user_id, "user_type": user_type})

    return ResponseModel(data={
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "expires_in": 7200
    })


@router.post("/auth/logout", response_model=ResponseModel)
def logout(current_user: dict = Depends(get_current_user)):
    """Clear token (stateless JWT — client should discard token)"""
    return ResponseModel(data={"message": "已退出登录"}, message="退出成功")


@router.post("/auth/password/change", response_model=ResponseModel)
def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_type = current_user.get("user_type")
    user_id = current_user.get("user_id")

    if user_type == "patient":
        user = db.query(Patient).filter(Patient.patient_id == user_id).first()
    elif user_type == "doctor":
        user = db.query(Doctor).filter(Doctor.doctor_id == user_id).first()
    elif user_type == "admin":
        user = db.query(Admin).filter(Admin.admin_id == user_id).first()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户类型错误")

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if user.password_hash and not verify_password(request.old_password_hash, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误")

    user.password_hash = get_password_hash(request.new_password_hash)
    db.commit()

    return ResponseModel(data={"message": "密码修改成功"})


@router.get("/departments", response_model=ResponseModel)
def get_departments(keyword: str = None, db: Session = Depends(get_db)):
    query = db.query(Department).filter(Department.status == 1)
    if keyword:
        query = query.filter(Department.dept_name.like(f"%{keyword}%"))
    departments = query.order_by(Department.sort_order).all()
    return ResponseModel(data=[
        {
            "dept_id": d.dept_id,
            "dept_name": d.dept_name,
            "dept_desc": d.dept_desc,
            "parent_id": d.parent_id
        }
        for d in departments
    ])


@router.get("/departments/tree", response_model=ResponseModel)
def get_department_tree(db: Session = Depends(get_db)):
    departments = db.query(Department).filter(Department.status == 1).order_by(Department.sort_order).all()

    dept_map = {}
    for d in departments:
        dept_map[d.dept_id] = {
            "dept_id": d.dept_id,
            "dept_name": d.dept_name,
            "dept_desc": d.dept_desc,
            "parent_id": d.parent_id,
            "children": []
        }

    tree = []
    for d in dept_map.values():
        if d["parent_id"] and d["parent_id"] in dept_map:
            dept_map[d["parent_id"]]["children"].append(d)
        else:
            tree.append(d)

    return ResponseModel(data=tree)


@router.get("/hospitals", response_model=ResponseModel)
def get_hospitals(dept_id: str = None, department_id: str = None, level: str = None, city: str = None, db: Session = Depends(get_db)):
    # Support both dept_id and department_id param names (frontend sends department_id)
    effective_dept_id = dept_id or department_id
    query = db.query(Hospital).filter(Hospital.status == 1)

    if effective_dept_id:
        query = query.filter(Hospital.dept_list.like(f"%{effective_dept_id}%"))
    if level:
        query = query.filter(Hospital.hospital_level == level)
    if city:
        query = query.filter(Hospital.address.like(f"%{city}%"))

    hospitals = query.all()
    return ResponseModel(data=[
        {
            "hospital_id": h.hospital_id,
            "hospital_name": h.hospital_name,
            "hospital_level": h.hospital_level,
            "address": h.address,
            "phone": h.phone
        }
        for h in hospitals
    ])


@router.post("/upload", response_model=ResponseModel)
def upload_file(file: UploadFile = File(...)):
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    file_ext = os.path.splitext(file.filename)[1]
    file_id = generate_id("file_")
    file_name = f"{file_id}{file_ext}"
    file_path = os.path.join("uploads", file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    return ResponseModel(data={
        "file_id": file_id,
        "file_name": file.filename,
        "file_url": f"/uploads/{file_name}",
        "file_size": file_size,
        "file_type": file_ext
    })


@router.post("/feedback", response_model=ResponseModel)
def submit_feedback(request: FeedbackCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_type = current_user.get("user_type")
    user_id = current_user.get("user_id")

    feedback = Feedback(
        feedback_id=generate_id("fb_"),
        consultation_id=request.consultation_id,
        patient_id=user_id if user_type == "patient" else None,
        doctor_id=user_id if user_type == "doctor" else None,
        rating=request.rating,
        is_accurate=request.is_accurate,
        corrected_answer=request.corrected_answer,
        content=request.content,
        type=request.type,
        related_entity_id=request.related_entity_id,
        related_query_id=request.related_query_id,
        title=request.title,
        references=list_to_json_str(request.references) if request.references else None,
        status="pending"
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return ResponseModel(data={"feedback_id": feedback.feedback_id, "status": feedback.status})


