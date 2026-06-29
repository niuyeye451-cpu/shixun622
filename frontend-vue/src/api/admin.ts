import { request } from './http'
import type { MedicalEntity, MedicalRelation, Synonym, KnowledgeVersion, Feedback, DashboardStats, EntityTypeStats } from '@/types'

export const adminApi = {
  // Users
  getPatients(params?: Record<string, any>) {
    return request('get', '/admin/users/patients', params)
  },

  getPatientDetail(id: string) {
    return request('get', `/admin/users/patients/${id}`)
  },

  updatePatientStatus(id: string, status: number) {
    return request('put', `/admin/users/patients/${id}/status`, { status })
  },

  getDoctors(params?: Record<string, any>) {
    return request('get', '/admin/users/doctors', params)
  },

  createDoctor(data: Record<string, any>) {
    return request('post', '/admin/users/doctors', data)
  },

  getDoctorDetail(id: string) {
    return request('get', `/admin/users/doctors/${id}`)
  },

  updateDoctorStatus(id: string, status: number) {
    return request('put', `/admin/users/doctors/${id}/status`, { status })
  },

  getAdmins(params?: Record<string, any>) {
    return request('get', '/admin/users/admins', params)
  },

  // Knowledge Entities
  createEntity(data: Record<string, any>) {
    return request<MedicalEntity>('post', '/admin/knowledge/entities', data)
  },

  getEntities(params?: Record<string, any>) {
    return request<{ list: MedicalEntity[]; page: number; page_size: number; total: number }>('get', '/admin/knowledge/entities', params)
  },

  getEntityDetail(id: string) {
    return request<MedicalEntity>('get', `/admin/knowledge/entities/${id}`)
  },

  updateEntity(id: string, data: Record<string, any>) {
    return request('put', `/admin/knowledge/entities/${id}`, data)
  },

  deleteEntity(id: string) {
    return request('delete', `/admin/knowledge/entities/${id}`)
  },

  // Relations
  createRelation(data: Record<string, any>) {
    return request<MedicalRelation>('post', '/admin/knowledge/relations', data)
  },

  getRelations(params?: Record<string, any>) {
    return request<{ list: MedicalRelation[]; page: number; page_size: number; total: number }>('get', '/admin/knowledge/relations', params)
  },

  deleteRelation(id: string) {
    return request('delete', `/admin/knowledge/relations/${id}`)
  },

  // Synonyms
  createSynonym(data: Record<string, any>) {
    return request<Synonym>('post', '/admin/knowledge/synonyms', data)
  },

  getSynonyms(params?: Record<string, any>) {
    return request<{ list: Synonym[]; page: number; page_size: number; total: number }>('get', '/admin/knowledge/synonyms', params)
  },

  deleteSynonym(id: string) {
    return request('delete', `/admin/knowledge/synonyms/${id}`)
  },

  // Versions
  createVersion(data: Record<string, any>) {
    return request<KnowledgeVersion>('post', '/admin/knowledge/versions', data)
  },

  getVersions(params?: Record<string, any>) {
    return request<{ list: KnowledgeVersion[]; page: number; page_size: number; total: number }>('get', '/admin/knowledge/versions', params)
  },

  publishVersion(id: string) {
    return request('put', `/admin/knowledge/versions/${id}/publish`)
  },

  // Feedbacks
  getFeedbacks(params?: Record<string, any>) {
    return request<{ list: Feedback[]; page: number; page_size: number; total: number }>('get', '/admin/feedbacks', params)
  },

  replyFeedback(id: string, reply: string) {
    return request('put', `/admin/feedbacks/${id}/reply?reply=${encodeURIComponent(reply)}`)
  },

  getFeedbackDetail(id: string) {
    return request<Feedback>('get', `/admin/feedbacks/${id}`)
  },

  // Unknown Questions
  getUnknownQuestionDetail(id: string) {
    return request('get', `/admin/unknown-questions/${id}`)
  },
  getUnknownQuestions(params?: Record<string, any>) {
    return request('get', '/admin/unknown-questions', params)
  },

  resolveUnknownQuestion(id: string, data: Record<string, any>) {
    return request('put', `/admin/unknown-questions/${id}/resolve`, data)
  },

  batchResolveQuestions(data: Record<string, any>) {
    return request('post', '/admin/unknown-questions/batch-resolve', data)
  },

  // Statistics
  getDashboardStats() {
    return request<DashboardStats>('get', '/admin/statistics/dashboard')
  },

  getConsultationStats(startDate: string, endDate: string, dimension = 'day') {
    return request('get', '/admin/statistics/consultations', { start_date: startDate, end_date: endDate, dimension })
  },

  getFeedbackStats(startDate: string, endDate: string) {
    return request('get', '/admin/statistics/feedback', { start_date: startDate, end_date: endDate })
  },

  getKnowledgeStats() {
    return request<EntityTypeStats>('get', '/admin/statistics/knowledge')
  },
}
