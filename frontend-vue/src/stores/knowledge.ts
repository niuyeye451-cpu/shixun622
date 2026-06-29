import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MedicalEntity, MedicalRelation, Synonym, KnowledgeVersion, GraphData } from '@/types'
import { adminApi } from '@/api/admin'
import { commonApi } from '@/api/common'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const entities = ref<MedicalEntity[]>([])
  const relations = ref<MedicalRelation[]>([])
  const synonyms = ref<Synonym[]>([])
  const versions = ref<KnowledgeVersion[]>([])
  const graph = ref<GraphData | null>(null)
  const entityPage = ref(1)
  const entityTotal = ref(0)
  const loading = ref(false)

  async function loadEntities(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await adminApi.getEntities({ page: entityPage.value, page_size: 20, ...params })
      if (res.code === 200) {
        entities.value = res.data.list
        entityTotal.value = res.data.total
      }
    } finally { loading.value = false }
  }

  async function loadRelations(params?: Record<string, any>) {
    const res = await adminApi.getRelations({ page: 1, page_size: 50, ...params })
    if (res.code === 200) relations.value = res.data.list
  }

  async function loadSynonyms() {
    const res = await adminApi.getSynonyms({ page: 1, page_size: 100 })
    if (res.code === 200) synonyms.value = res.data.list
  }

  async function loadVersions() {
    const res = await adminApi.getVersions({ page: 1, page_size: 20 })
    if (res.code === 200) versions.value = res.data.list
  }

  async function loadGraph(entityName: string) {
    const res = await commonApi.getDiseaseGraph(entityName, 2)
    if (res.code === 200) graph.value = res.data
  }

  async function searchEntities(keyword: string, type?: string) {
    const res = await commonApi.searchEntities(keyword, type)
    if (res.code === 200) return res.data
    return []
  }

  function reset() {
    entities.value = []
    relations.value = []
    synonyms.value = []
    versions.value = []
    graph.value = null
    entityPage.value = 1
    entityTotal.value = 0
  }

  return { entities, relations, synonyms, versions, graph, entityPage, entityTotal, loading, loadEntities, loadRelations, loadSynonyms, loadVersions, loadGraph, searchEntities, reset }
})
