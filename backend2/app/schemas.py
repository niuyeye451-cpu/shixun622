from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[str] = None
    user_type: Optional[str] = None


class SmsSendRequest(BaseModel):
    phone: str
    type: str = Field(..., description="login/register/reset")


class PatientLoginRequest(BaseModel):
    phone: str
    code: str
    sms_id: str


class PatientPasswordLoginRequest(BaseModel):
    phone: str
    password: str


class PatientRegisterRequest(BaseModel):
    phone: str
    password: str
    user_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None


class DoctorLoginRequest(BaseModel):
    user_name: str
    password: str


class DoctorRegisterRequest(BaseModel):
    user_name: str
    password: str
    phone: str
    real_name: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    hospital: Optional[str] = None


class AdminLoginRequest(BaseModel):
    user_name: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password_hash: str
    new_password_hash: str


class PatientProfile(BaseModel):
    patient_id: str
    user_name: str
    phone: str
    avatar: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergy_history: Optional[List[str]] = None
    medical_history: Optional[List[str]] = None
    status: int
    created_at: datetime


class PatientProfileUpdate(BaseModel):
    user_name: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergy_history: Optional[List[str]] = None
    medical_history: Optional[List[str]] = None


class DoctorProfile(BaseModel):
    doctor_id: str
    user_name: str
    phone: str
    avatar: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    hospital: Optional[str] = None
    specialty: Optional[str] = None
    introduction: Optional[str] = None
    is_first_login: bool
    status: int
    created_at: datetime


class DoctorProfileUpdate(BaseModel):
    avatar: Optional[str] = None
    specialty: Optional[str] = None
    introduction: Optional[str] = None


class FeedbackCreate(BaseModel):
    consultation_id: Optional[str] = None
    rating: Optional[int] = None
    is_accurate: Optional[bool] = None
    corrected_answer: Optional[str] = None
    content: str


class DoctorFeedbackCreate(BaseModel):
    type: str
    related_entity_id: Optional[str] = None
    related_query_id: Optional[str] = None
    title: str
    content: str
    corrected_content: Optional[str] = None
    references: Optional[List[str]] = None


class DepartmentResponse(BaseModel):
    department_id: str
    department_name: str
    description: Optional[str] = None
    sort_order: Optional[int] = None


class HospitalResponse(BaseModel):
    hospital_id: str
    hospital_name: str
    hospital_level: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class UploadResponse(BaseModel):
    file_id: str
    file_url: str
    file_size: int


class CreateConversationRequest(BaseModel):
    session_type: str = Field(..., description="symptom/disease/drug")
    initial_message: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str
    image_ids: Optional[List[str]] = None


class MessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    image_ids: Optional[List[str]] = None
    reasoning_path: Optional[List[str]] = None
    answer_source: Optional[str] = None
    created_at: datetime


class ConversationResponse(BaseModel):
    conversation_id: str
    session_type: str
    status: str
    started_at: datetime
    messages: Optional[List[MessageResponse]] = None


class QuickSymptomRequest(BaseModel):
    symptom_text: str
    age: Optional[int] = None
    gender: Optional[str] = None


class QuickSymptomResponse(BaseModel):
    answer: str
    matched_diseases: List[Dict[str, Any]]
    recommended_department: Optional[str] = None


class DepartmentRecommendationRequest(BaseModel):
    symptoms: List[str]
    duration: Optional[str] = None
    severity: Optional[str] = None


class DepartmentRecommendationResponse(BaseModel):
    recommended_departments: List[Dict[str, Any]]
    urgency_level: str
    suggestion: str


class RecommendationFilter(BaseModel):
    department_id: str
    city: Optional[str] = None
    hospital_id: Optional[str] = None


class RegistrationSlotsRequest(BaseModel):
    doctor_id: str
    date: Optional[str] = None


class RegistrationRequest(BaseModel):
    slot_id: str
    doctor_id: str
    hospital_id: str
    department_id: str
    consultation_id: Optional[str] = None
    patient_name: str
    id_card: str
    phone: str
    symptom_description: Optional[str] = None


class RegistrationResponse(BaseModel):
    registration_id: str
    hospital_system_id: Optional[str] = None
    status: str
    doctor_name: str
    department: str
    hospital: str
    date: str
    time_period: str
    start_time: str
    consultation_room: Optional[str] = None
    registration_fee: float
    qr_code: Optional[str] = None
    created_at: datetime


class ConsultationResponse(BaseModel):
    consultation_id: str
    title: str
    symptom_text: Optional[str] = None
    matched_disease: Optional[str] = None
    matched_department: Optional[str] = None
    created_at: datetime


class ReminderResponse(BaseModel):
    reminder_id: str
    type: str
    title: str
    content: str
    related_id: Optional[str] = None
    is_read: bool
    remind_time: datetime
    created_at: datetime


class CreateCaseConversationRequest(BaseModel):
    case_type: str = Field(..., description="differential_diagnosis/multi_symptom/treatment_plan")
    patient_info: Optional[Dict[str, Any]] = None
    initial_query: Optional[str] = None


class MultiSymptomAnalyzeRequest(BaseModel):
    diseases: List[str]
    symptoms: Optional[List[str]] = None
    analysis_depth: Optional[int] = 3


class DifferentialDiagnosisRequest(BaseModel):
    chief_complaint: str
    symptoms: List[str]
    patient_info: Optional[Dict[str, Any]] = None
    exam_results: Optional[Dict[str, str]] = None


class KnowledgeQueryRequest(BaseModel):
    query: str
    query_type: Optional[str] = None
    context: Optional[str] = None


class DrugInteractionRequest(BaseModel):
    drug_ids: Optional[List[str]] = None
    drug_names: Optional[List[str]] = None


class MedicalEntityCreate(BaseModel):
    name: str
    type: str
    aliases: Optional[List[str]] = None
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    version_number: Optional[str] = None


class MedicalEntityUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[List[str]] = None
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class MedicalRelationCreate(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    text: Optional[str] = None
    version_number: Optional[str] = None


class SynonymCreate(BaseModel):
    alias_term: str
    standard_entity_id: str
    source: Optional[str] = "manual"


class KnowledgeVersionCreate(BaseModel):
    version_number: str
    base_version_id: Optional[str] = None
    description: Optional[str] = None
    update_content: Optional[str] = None


class ResolveUnknownQuestionRequest(BaseModel):
    resolved_answer: str
    related_entity_id: Optional[str] = None
    add_to_knowledge: bool = False
    knowledge_category: Optional[str] = None


class BatchResolveRequest(BaseModel):
    question_ids: List[str]
    action: str
    resolved_answer: Optional[str] = None
    add_to_knowledge: bool = False


class CreateDoctorRequest(BaseModel):
    user_name: str
    phone: str
    password_hash: str
    department: Optional[str] = None
    title: Optional[str] = None
    hospital: Optional[str] = None


class UpdateUserStatusRequest(BaseModel):
    status: int
    reason: Optional[str] = None


class UpdateConfigRequest(BaseModel):
    config_key: str
    config_value: Dict[str, Any]


class CreateKnowledgeTaskRequest(BaseModel):
    task_type: str
    task_name: str
    description: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class ExportReportRequest(BaseModel):
    report_type: str
    start_date: str
    end_date: str
    format: Optional[str] = "excel"
    dimensions: Optional[List[str]] = None


class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    relation_name: Optional[str] = None


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    center_node: Optional[str] = None


class EntitySearchResponse(BaseModel):
    entity_id: str
    name: str
    type: str
    aliases: Optional[List[str]] = None
    description: Optional[str] = None


class EntityDetailResponse(BaseModel):
    entity_id: str
    name: str
    type: str
    aliases: Optional[List[str]] = None
    description: Optional[str] = None
    source_version: Optional[str] = None
    version_number: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class RelationPath(BaseModel):
    path_id: str
    length: int
    nodes: List[str]
    edges: List[str]
    confidence: float


class RelationQueryResponse(BaseModel):
    paths: List[RelationPath]
    total_paths: int


class PageResponse(BaseModel):
    page: int
    page_size: int
    total: int


class ResponseModel(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
