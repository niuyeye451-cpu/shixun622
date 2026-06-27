from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Patient, Doctor, Admin
from app.utils import decode_token

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("user_id")
    user_type: str = payload.get("user_type")
    if user_id is None or user_type is None:
        raise credentials_exception
    
    if user_type == "patient":
        user = db.query(Patient).filter(Patient.patient_id == user_id).first()
    elif user_type == "doctor":
        user = db.query(Doctor).filter(Doctor.doctor_id == user_id).first()
    elif user_type == "admin":
        user = db.query(Admin).filter(Admin.admin_id == user_id).first()
    else:
        raise credentials_exception
    
    if user is None or user.status != 1:
        raise credentials_exception
    
    return {"user": user, "user_type": user_type}


def get_patient_user(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated as patient"
        )
    return current_user


def get_doctor_user(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated as doctor"
        )
    return current_user


def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated as admin"
        )
    return current_user
