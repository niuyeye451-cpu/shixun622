import { request } from './http'

export const llmApi = {
  /** LLM natural language query for medical Q&A */
  query(query: string, context?: string) {
    return request('post', '/llm/query', { query, context })
  },

  /** Graph-enhanced reasoning analysis */
  graphAnalysis(query: string, entities?: string[]) {
    return request('post', '/llm/graph-analysis', { query, entities })
  },

  /** RAG-based document search */
  ragSearch(query: string, topK = 5) {
    return request('post', '/llm/rag/search', { query, top_k: topK })
  },

  /** Symptom-to-diagnosis mapping */
  symptomDiagnosis(symptoms: string[], age?: number, gender?: string) {
    return request('get', '/llm/symptom-diagnosis', { symptoms: symptoms.join(','), age, gender })
  },

  /** Drug recommendation based on disease */
  drugRecommendation(disease: string, contraindications?: string[]) {
    return request('get', '/llm/drug-recommendation', { disease, contraindications: contraindications?.join(',') })
  },

  /** Health check */
  health() {
    return request('get', '/llm/health')
  },
}
