// ========== User Types ==========
export type UserRole = 'patient' | 'doctor' | 'admin'

export interface UserInfo {
  patient_id?: string
  doctor_id?: string
  admin_id?: string
  user_name: string
  phone: string
  avatar?: string
  status: number
  created_at: string
  // patient specific
  gender?: string
  age?: number
  address?: string
  blood_type?: string
  allergy_history?: string[]
  medical_history?: string[]
  // doctor specific
  department?: string
  title?: string
  hospital?: string
  specialty?: string
  introduction?: string
  is_first_login?: boolean
  // admin specific
  role_level?: number
}

// ========== API Response ==========
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: string
}

export interface PageData<T> {
  list: T[]
  page: number
  page_size: number
  total: number
}

// ========== Auth ==========
export interface LoginResult {
  access_token: string
  refresh_token: string
  expires_in: number
  user_info: UserInfo
}

// ========== Conversation ==========
export interface Message {
  message_id: string
  role: 'user' | 'assistant'
  content: string
  image_ids?: string[]
  reasoning_path?: string[]
  answer_source?: string
  matched_disease?: string
  matched_department?: string
  recommendation_detail?: string
  related_diseases?: Array<{ entity_id: string; name: string; probability: number }>
  created_at: string
}

export interface Conversation {
  conversation_id: string
  session_type: string
  case_type?: string
  status: 'active' | 'ended'
  title?: string
  last_message?: string
  matched_disease?: string
  matched_department?: string
  started_at: string
  ended_at?: string
}

// ========== Knowledge Graph ==========
export interface GraphNode {
  id: string
  name: string
  type: string
  description?: string
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  relation: string
  relation_name?: string
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  center_node?: string
}

export interface MedicalEntity {
  entity_id: string
  name: string
  type: string
  aliases?: string[]
  description?: string
  attributes?: Record<string, any>
  source_version?: string
  version_number?: string
  status: string
  created_at: string
  updated_at?: string
}

export interface MedicalRelation {
  relation_id: string
  source_entity_id: string
  source_entity_name?: string
  target_entity_id: string
  target_entity_name?: string
  relation_type: string
  relation_name?: string
  text?: string
  created_at: string
}

export interface Synonym {
  synonym_id: string
  alias_term: string
  standard_entity_id: string
  standard_entity_name?: string
  source: string
  created_at: string
}

export interface KnowledgeVersion {
  version_id: string
  version_number: string
  entity_count: number
  relation_count: number
  status: string
  update_content?: string
  change_log?: string
  published_at?: string
  created_at: string
}

// ========== Registration ==========
export interface Registration {
  registration_id: string
  doctor_name: string
  department: string
  hospital: string
  date: string
  time_period: string
  status: string
  created_at: string
}

// ========== Consultation ==========
export interface Consultation {
  consultation_id: string
  title: string
  symptom_text?: string
  matched_disease?: string
  matched_department?: string
  recommendation_detail?: string
  created_at: string
}

// ========== Feedback ==========
export interface Feedback {
  feedback_id: string
  type?: string
  title?: string
  content: string
  rating?: number
  is_accurate?: boolean
  status: string
  patient_name?: string
  doctor_name?: string
  reply?: string
  resolved_at?: string
  created_at: string
}

// ========== Dashboard ==========
export interface DashboardStats {
  patient_count: number
  doctor_count: number
  admin_count: number
  entity_count: number
  relation_count: number
  pending_feedback_count: number
  pending_unknown_count: number
  daily_stats: {
    new_patients: number
    new_doctors: number
    consultations: number
    registrations: number
  }
}

export interface EntityTypeStats {
  total_entities: number
  total_relations: number
  total_synonyms: number
  total_versions: number
  by_type: Record<string, number>
}
