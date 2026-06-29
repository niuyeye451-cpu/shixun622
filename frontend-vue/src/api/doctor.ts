import { request } from './http'
import type { Conversation, Message, UserInfo, Feedback } from '@/types'

export const doctorApi = {
  // Case Assist
  createCaseConversation(caseType: string, patientInfo?: Record<string, any>, initialQuery?: string) {
    return request<Conversation & { messages: Message[] }>('post', '/doctor/consultation/conversations', { case_type: caseType, patient_info: patientInfo, initial_query: initialQuery })
  },

  sendCaseMessage(conversationId: string, content: string) {
    return request<Message & { assistant_message: Message }>('post', `/doctor/consultation/conversations/${conversationId}/messages?content=${encodeURIComponent(content)}`)
  },

  getCaseMessages(conversationId: string, lastMessageId?: string, limit = 20) {
    return request<{ list: Message[]; has_more: boolean }>('get', `/doctor/consultation/conversations/${conversationId}/messages`, { last_message_id: lastMessageId, limit })
  },

  endCaseConversation(conversationId: string) {
    return request('put', `/doctor/consultation/conversations/${conversationId}/end`)
  },

  getCaseConversations(page = 1, pageSize = 10, caseType?: string) {
    return request<{ list: Conversation[]; page: number; page_size: number; total: number }>('get', '/doctor/consultation/conversations', { page, page_size: pageSize, case_type: caseType })
  },

  // Multi-symptom & Differential Diagnosis
  analyzeMultiSymptom(diseases: string[], symptoms?: string[], depth = 3) {
    return request('post', '/doctor/consultation/multi-symptom', { diseases, symptoms, analysis_depth: depth })
  },

  differentialDiagnosis(chiefComplaint: string, symptoms: string[], patientInfo?: Record<string, any>, examResults?: Record<string, string>) {
    return request('post', '/doctor/consultation/differential-diagnosis', { chief_complaint: chiefComplaint, symptoms, patient_info: patientInfo, exam_results: examResults })
  },

  // Knowledge
  queryKnowledge(query: string, queryType?: string, context?: string) {
    return request('post', '/doctor/knowledge/query', { query, query_type: queryType, context })
  },

  checkDrugInteraction(drugIds?: string[], drugNames?: string[]) {
    return request('post', '/doctor/knowledge/drug-interaction', { drug_ids: drugIds, drug_names: drugNames })
  },

  // Profile
  getProfile() {
    return request<UserInfo>('get', '/doctor/profile')
  },

  updateProfile(data: Record<string, any>) {
    return request('put', '/doctor/profile', data)
  },

  // Feedback
  submitFeedback(data: Record<string, any>) {
    return request<{ feedback_id: string; status: string }>('post', '/doctor/feedback', data)
  },

  getFeedbackList(status?: string, page = 1, pageSize = 10) {
    return request<{ list: Feedback[]; page: number; page_size: number; total: number }>('get', '/doctor/feedback', { status, page, page_size: pageSize })
  },
}
