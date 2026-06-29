import { request } from './http'
import type { GraphData, MedicalEntity } from '@/types'

export const commonApi = {
  getDepartments(keyword?: string) {
    return request('get', '/common/departments', keyword ? { keyword } : undefined)
  },

  getHospitals(params?: Record<string, any>) {
    return request('get', '/common/hospitals', params)
  },

  uploadImage(file: File, scene = 'other') {
    const fd = new FormData()
    fd.append('file', file)
    return request<{ file_id: string; file_url: string; file_size: number }>('post', '/common/upload', fd)
  },

  submitFeedback(data: { consultation_id?: string; rating?: number; is_accurate?: boolean; corrected_answer?: string; content: string }) {
    return request<{ feedback_id: string }>('post', '/common/feedback', data)
  },

  getDiseaseGraph(diseaseName: string, maxDepth = 2) {
    return request<GraphData>('get', '/common/knowledge-graph/disease-graph', { disease_name: diseaseName, max_depth: maxDepth })
  },

  searchEntities(keyword: string, entityType?: string, limit = 10) {
    return request<any>('get', '/common/knowledge-graph/entities/search', { keyword, entity_type: entityType, limit })
  },

  getEntityDetail(entityId: string) {
    return request<MedicalEntity>('get', `/common/knowledge-graph/entities/${entityId}`)
  },

  /** Get entity relations (system3: directional with relation_type filter) */
  getEntityRelations(entityId: string, relationType?: string, direction = 'both') {
    return request('get', `/common/knowledge-graph/entities/${entityId}/relations`, { relation_type: relationType, direction })
  },

  /** Get knowledge graph statistics */
  getGraphStatistics() {
    return request<{ total_entities: number; total_relations: number; entity_type_counts: Record<string, number>; relation_type_counts: Record<string, number> }>(
      'get', '/common/knowledge-graph/statistics'
    )
  },
}
