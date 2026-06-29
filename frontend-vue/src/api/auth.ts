import { request } from './http'
import type { LoginResult } from '@/types'

export const authApi = {
  sendSms(phone: string, type = 'login') {
    return request<{ sms_id: string; expire_seconds: number }>('post', '/common/auth/sms/send', { phone, type })
  },

  /** Patient SMS code login (auto-register) */
  patientLogin(phone: string, code: string, smsId: string) {
    return request<LoginResult>('post', '/common/auth/patient/login', { phone, code, sms_id: smsId })
  },

  /** Patient password login */
  patientPasswordLogin(phone: string, password: string) {
    return request<LoginResult>('post', '/common/auth/patient/login-password', { phone, password })
  },

  /** Patient register with password */
  patientRegister(data: { phone: string; password: string; user_name?: string; gender?: string; age?: number }) {
    return request<LoginResult>('post', '/common/auth/patient/register', data)
  },

  /** Doctor login (bcrypt password) */
  doctorLogin(userName: string, password: string) {
    return request<LoginResult>('post', '/common/auth/doctor/login', { user_name: userName, password })
  },

  /** Admin login (bcrypt password) */
  adminLogin(userName: string, password: string) {
    return request<LoginResult>('post', '/common/auth/admin/login', { user_name: userName, password })
  },

  logout() {
    return request('post', '/common/auth/logout')
  },

  refreshToken(refreshToken: string) {
    return request<{ access_token: string; expires_in: number }>('post', '/common/auth/token/refresh', { refresh_token: refreshToken })
  },

  changePassword(oldPwd: string, newPwd: string) {
    return request('put', '/common/auth/password/change', { old_password_hash: oldPwd, new_password_hash: newPwd })
  },
}
