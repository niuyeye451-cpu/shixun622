import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo, UserRole, LoginResult } from '@/types'
import { authApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(sessionStorage.getItem('access_token') || '')
  const refreshToken = ref(sessionStorage.getItem('refresh_token') || '')
  const userInfo = ref<UserInfo | null>(JSON.parse(sessionStorage.getItem('user_info') || 'null'))
  const userRole = ref<UserRole | null>((sessionStorage.getItem('user_type') as UserRole) || null)

  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => userInfo.value?.user_name || userInfo.value?.phone || '')
  const userId = computed(() => {
    if (!userInfo.value) return ''
    return userInfo.value.patient_id || userInfo.value.doctor_id || userInfo.value.admin_id || ''
  })

  function setAuth(result: LoginResult, role: UserRole) {
    token.value = result.access_token
    refreshToken.value = result.refresh_token
    userInfo.value = result.user_info
    userRole.value = role
    sessionStorage.setItem('access_token', result.access_token)
    sessionStorage.setItem('refresh_token', result.refresh_token)
    sessionStorage.setItem('user_info', JSON.stringify(result.user_info))
    sessionStorage.setItem('user_type', role)
  }

  async function loginPatient(phone: string, code: string, smsId: string) {
    const res = await authApi.patientLogin(phone, code, smsId)
    if (res.code === 200) setAuth(res.data, 'patient')
    return res
  }

  async function loginDoctor(userName: string, passwordHash: string) {
    const res = await authApi.doctorLogin(userName, passwordHash)
    if (res.code === 200) setAuth(res.data, 'doctor')
    return res
  }

  async function loginAdmin(userName: string, passwordHash: string) {
    const res = await authApi.adminLogin(userName, passwordHash)
    if (res.code === 200) setAuth(res.data, 'admin')
    return res
  }

  async function logout() {
    try { await authApi.logout() } catch {}
    clearAuth()
  }

  function clearAuth() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    userRole.value = null
    sessionStorage.clear()
  }

  return { token, refreshToken, userInfo, userRole, isLoggedIn, userName, userId, loginPatient, loginDoctor, loginAdmin, logout, clearAuth }
})
