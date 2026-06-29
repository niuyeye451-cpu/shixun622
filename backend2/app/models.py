from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(32), primary_key=True, index=True)
    user_name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(100), nullable=True)
    avatar = Column(String(255), nullable=True)
    gender = Column(String(10), nullable=True)
    age = Column(Integer, nullable=True)
    address = Column(String(255), nullable=True)
    blood_type = Column(String(10), nullable=True)
    allergy_history = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    status = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    consultations = relationship("Consultation", back_populates="patient")
    registrations = relationship("Registration", back_populates="patient")
    conversations = relationship("Conversation", back_populates="patient")
    messages = relationship("Message", back_populates="patient")
    feedbacks = relationship("Feedback", back_populates="patient")


class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id = Column(String(32), primary_key=True, index=True)
    user_name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    department = Column(String(50), nullable=True)
    title = Column(String(50), nullable=True)
    hospital = Column(String(100), nullable=True)
    specialty = Column(String(255), nullable=True)
    introduction = Column(Text, nullable=True)
    avatar = Column(String(255), nullable=True)
    is_first_login = Column(Boolean, default=True)
    status = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    consultations = relationship("Consultation", back_populates="doctor")
    conversations = relationship("Conversation", back_populates="doctor")
    messages = relationship("Message", back_populates="doctor")
    feedbacks = relationship("Feedback", back_populates="doctor")


class Admin(Base):
    __tablename__ = "admins"

    admin_id = Column(String(32), primary_key=True, index=True)
    user_name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    role_level = Column(Integer, default=1)
    status = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Consultation(Base):
    __tablename__ = "consultations"

    consultation_id = Column(String(32), primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.patient_id"), nullable=False)
    doctor_id = Column(String(32), ForeignKey("doctors.doctor_id"), nullable=True)
    symptom_text = Column(Text, nullable=True)
    matched_disease = Column(String(100), nullable=True)
    matched_department = Column(String(50), nullable=True)
    recommendation_detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="consultations")
    doctor = relationship("Doctor", back_populates="consultations")
    registration = relationship("Registration", uselist=False, back_populates="consultation")


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(String(32), primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.patient_id"), nullable=True)
    doctor_id = Column(String(32), ForeignKey("doctors.doctor_id"), nullable=True)
    session_type = Column(String(20), nullable=False)
    case_type = Column(String(30), nullable=True)
    status = Column(String(20), default="active")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", back_populates="conversations")
    doctor = relationship("Doctor", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String(32), primary_key=True, index=True)
    conversation_id = Column(String(32), ForeignKey("conversations.conversation_id"), nullable=False)
    patient_id = Column(String(32), ForeignKey("patients.patient_id"), nullable=True)
    doctor_id = Column(String(32), ForeignKey("doctors.doctor_id"), nullable=True)
    sender_role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    image_ids = Column(String(500), nullable=True)
    reasoning_path = Column(String(500), nullable=True)
    answer_source = Column(String(20), nullable=True)
    message_type = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
    patient = relationship("Patient", back_populates="messages")
    doctor = relationship("Doctor", back_populates="messages")


class Registration(Base):
    __tablename__ = "registrations"

    registration_id = Column(String(32), primary_key=True, index=True)
    consultation_id = Column(String(32), ForeignKey("consultations.consultation_id"), nullable=True)
    patient_id = Column(String(32), ForeignKey("patients.patient_id"), nullable=False)
    doctor_id = Column(String(32), ForeignKey("doctors.doctor_id"), nullable=False)
    department = Column(String(50), nullable=False)
    hospital_id = Column(String(32), nullable=False)
    hospital_system_id = Column(String(100), nullable=True)
    date = Column(String(20), nullable=False)
    time_period = Column(String(20), nullable=False)
    start_time = Column(String(20), nullable=False)
    consultation_room = Column(String(100), nullable=True)
    registration_fee = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    patient_name = Column(String(50), nullable=False)
    id_card = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    symptom_description = Column(Text, nullable=True)
    qr_code = Column(String(500), nullable=True)
    registration_time = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="registrations")
    consultation = relationship("Consultation", back_populates="registration")


class Department(Base):
    __tablename__ = "departments"

    dept_id = Column(String(32), primary_key=True, index=True)
    dept_name = Column(String(50), nullable=False)
    dept_desc = Column(Text, nullable=True)
    parent_id = Column(String(32), nullable=True)
    sort_order = Column(Integer, default=0)
    status = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Hospital(Base):
    __tablename__ = "hospitals"

    hospital_id = Column(String(32), primary_key=True, index=True)
    hospital_name = Column(String(100), nullable=False)
    hospital_level = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    dept_list = Column(Text, nullable=True)
    status = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MedicalEntity(Base):
    __tablename__ = "medical_entities"

    entity_id = Column(String(32), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(30), nullable=False)
    aliases = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    attributes = Column(Text, nullable=True)
    source_version = Column(String(20), nullable=True)
    version_number = Column(String(20), nullable=True)
    status = Column(String(20), default="published")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class MedicalRelation(Base):
    __tablename__ = "medical_relations"

    relation_id = Column(String(32), primary_key=True, index=True)
    source_entity_id = Column(String(32), ForeignKey("medical_entities.entity_id"), nullable=False)
    target_entity_id = Column(String(32), ForeignKey("medical_entities.entity_id"), nullable=False)
    relation_type = Column(String(30), nullable=False)
    relation_name = Column(String(50), nullable=True)
    text = Column(Text, nullable=True)
    source_version = Column(String(20), nullable=True)
    version_number = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Synonym(Base):
    __tablename__ = "synonyms"

    synonym_id = Column(String(32), primary_key=True, index=True)
    alias_term = Column(String(100), nullable=False)
    standard_entity_id = Column(String(32), ForeignKey("medical_entities.entity_id"), nullable=False)
    source = Column(String(20), default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"

    version_id = Column(String(32), primary_key=True, index=True)
    version_number = Column(String(20), unique=True, nullable=False)
    status = Column(String(20), default="draft")
    entity_count = Column(Integer, default=0)
    relation_count = Column(Integer, default=0)
    operator_id = Column(String(32), ForeignKey("admins.admin_id"), nullable=True)
    update_content = Column(Text, nullable=True)
    change_log = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Feedback(Base):
    __tablename__ = "feedbacks"

    feedback_id = Column(String(32), primary_key=True, index=True)
    consultation_id = Column(String(32), ForeignKey("consultations.consultation_id"), nullable=True)
    patient_id = Column(String(32), ForeignKey("patients.patient_id"), nullable=True)
    doctor_id = Column(String(32), ForeignKey("doctors.doctor_id"), nullable=True)
    rating = Column(Integer, nullable=True)
    is_accurate = Column(Boolean, nullable=True)
    corrected_answer = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    type = Column(String(30), nullable=True)
    related_entity_id = Column(String(32), nullable=True)
    related_query_id = Column(String(32), nullable=True)
    title = Column(String(100), nullable=True)
    references = Column(String(500), nullable=True)
    status = Column(String(20), default="pending")
    reply = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="feedbacks")
    doctor = relationship("Doctor", back_populates="feedbacks")


class UnknownQuestion(Base):
    __tablename__ = "unknown_questions"

    question_id = Column(String(32), primary_key=True, index=True)
    text = Column(Text, nullable=False)
    source_role = Column(String(20), nullable=False)
    source_id = Column(String(32), nullable=False)
    category = Column(String(50), nullable=True)
    status = Column(String(20), default="pending")
    occur_time = Column(DateTime(timezone=True), server_default=func.now())
    occur_count = Column(Integer, default=1)
    related_conversation_id = Column(String(32), nullable=True)
    resolved_answer = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(32), nullable=True)


class LoginLog(Base):
    __tablename__ = "login_logs"

    log_id = Column(String(32), primary_key=True, index=True)
    user_type = Column(String(20), nullable=False)
    user_id = Column(String(32), nullable=False)
    ip = Column(String(50), nullable=True)
    address = Column(String(100), nullable=True)
    login_time = Column(DateTime(timezone=True), server_default=func.now())
    login_result = Column(Integer, nullable=False)
    user_agent = Column(String(500), nullable=True)


class OperationLog(Base):
    __tablename__ = "operation_logs"

    log_id = Column(String(32), primary_key=True, index=True)
    operator_id = Column(String(32), nullable=False)
    operator_type = Column(String(20), nullable=False)
    operator_name = Column(String(50), nullable=True)
    action = Column(String(30), nullable=False)
    target = Column(String(30), nullable=False)
    target_id = Column(String(32), nullable=True)
    detail = Column(Text, nullable=True)
    ip = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnowledgeTask(Base):
    __tablename__ = "knowledge_tasks"

    task_id = Column(String(32), primary_key=True, index=True)
    task_type = Column(String(30), nullable=False)
    task_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    target_entity_id = Column(String(32), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    reason = Column(String(200), nullable=True)
    approved_by = Column(String(32), nullable=True)
    version_number = Column(String(20), nullable=True)
    progress = Column(Integer, default=0)
    params = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Statistics(Base):
    __tablename__ = "statistics"

    stat_id = Column(String(32), primary_key=True, index=True)
    date = Column(String(20), nullable=False)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    dimension = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
