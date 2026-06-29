import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DashboardStats, EntityTypeStats } from '@/types'
import { adminApi } from '@/api/admin'

export const useStatsStore = defineStore('stats', () => {
  const dashboard = ref<DashboardStats | null>(null)
  const entityStats = ref<EntityTypeStats | null>(null)
  const patientList = ref<any[]>([])
  const doctorList = ref<any[]>([])
  const adminList = ref<any[]>([])
  const feedbackList = ref<any[]>([])

  async function loadDashboard() {
    const res = await adminApi.getDashboardStats()
    if (res.code === 200) dashboard.value = res.data
  }

  async function loadEntityStats() {
    const res = await adminApi.getKnowledgeStats()
    if (res.code === 200) entityStats.value = res.data
  }

  async function loadPatients(keyword?: string) {
    const res = await adminApi.getPatients({ keyword, page: 1, page_size: 200 })
    if (res.code === 200) patientList.value = res.data.list
  }

  async function loadDoctors(keyword?: string) {
    const res = await adminApi.getDoctors({ keyword, page: 1, page_size: 200 })
    if (res.code === 200) doctorList.value = res.data.list
  }

  async function loadAdmins() {
    const res = await adminApi.getAdmins({ page: 1, page_size: 200 })
    if (res.code === 200) adminList.value = res.data.list
  }

  async function loadFeedbacks(status?: string, type?: string) {
    const res = await adminApi.getFeedbacks({ status, type, page: 1, page_size: 200 })
    if (res.code === 200) feedbackList.value = res.data.list
  }

  return { dashboard, entityStats, patientList, doctorList, adminList, feedbackList, loadDashboard, loadEntityStats, loadPatients, loadDoctors, loadAdmins, loadFeedbacks }
})
