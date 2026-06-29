import { request } from './http'
import type { Conversation, Message, Consultation, Registration, UserInfo } from '@/types'

export const patientApi = {
  // Consultation
  createConversation(sessionType: string, initialMessage?: string) {
    return request<Conversation & { messages: Message[] }>('post', '/patient/consultation/conversations', { session_type: sessionType, initial_message: initialMessage })
  },

  sendMessage(conversationId: string, content: string, imageIds?: string[]) {
    return request<Message & { assistant_message: Message }>('post', `/patient/consultation/conversations/${conversationId}/messages`, { content, image_ids: imageIds || [] })
  },

  getMessages(conversationId: string, lastMessageId?: string, limit = 20) {
    return request<{ list: Message[]; has_more: boolean }>('get', `/patient/consultation/conversations/${conversationId}/messages`, { last_message_id: lastMessageId, limit })
  },

  endConversation(conversationId: string) {
    return request<{ consultation_id: string; summary: string }>('put', `/patient/consultation/conversations/${conversationId}/end`)
  },

  getConversations(page = 1, pageSize = 10, sessionType?: string) {
    return request<{ list: Conversation[]; page: number; page_size: number; total: number }>('get', '/patient/consultation/conversations', { page, page_size: pageSize, session_type: sessionType })
  },

  quickSymptomQuery(symptomText: string, age?: number, gender?: string) {
    return request('post', '/patient/consultation/symptom/quick', { symptom_text: symptomText, age, gender })
  },

  // Recommendation
  recommendDepartment(symptoms: string[], duration?: string, severity?: string) {
    return request('post', '/patient/recommendation/department', { symptoms, duration, severity })
  },

  recommendHospitals(departmentId: string, city?: string) {
    return request('get', '/patient/recommendation/hospitals', { department_id: departmentId, city })
  },

  recommendDoctors(departmentId: string, hospitalId?: string) {
    return request('get', '/patient/recommendation/doctors', { department_id: departmentId, hospital_id: hospitalId })
  },

  // Registration
  getSlots(doctorId: string, date?: string) {
    return request('get', '/patient/registration/slots', { doctor_id: doctorId, date })
  },

  register(data: Record<string, any>) {
    return request<Registration>('post', '/patient/registration', data)
  },

  getRegistrations(status?: string, page = 1, pageSize = 10) {
    return request<{ list: Registration[]; page: number; page_size: number; total: number }>('get', '/patient/registration', { status, page, page_size: pageSize })
  },

  cancelRegistration(id: string) {
    return request<{ refund_amount: number }>('put', `/patient/registration/${id}/cancel`)
  },

  // Profile
  getProfile() {
    return request<UserInfo>('get', '/patient/profile')
  },

  updateProfile(data: Record<string, any>) {
    return request('put', '/patient/profile', data)
  },

  // History
  getConsultationHistory(params?: Record<string, any>) {
    return request<{ list: Consultation[]; page: number; page_size: number; total: number }>('get', '/patient/history/consultations', params)
  },

  getConsultationDetail(id: string) {
    return request<Consultation>('get', `/patient/history/consultations/${id}`)
  },

  // Reminders
  getReminders(params?: Record<string, any>) {
    return request('get', '/patient/reminders', params)
  },

  markReminderRead(id: string) {
    return request('put', `/patient/reminders/${id}/read`)
  },

  markAllRead() {
    return request('put', '/patient/reminders/read-all')
  },
}
