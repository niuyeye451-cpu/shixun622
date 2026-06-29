import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  // ========== Auth ==========
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginPage.vue'),
    meta: { guest: true },
  },

  // ========== Patient ==========
  {
    path: '/patient',
    component: () => import('@/components/common/PatientLayout.vue'),
    meta: { requiresAuth: true, role: 'patient' },
    children: [
      { path: '', redirect: '/patient/qa' },
      { path: 'qa', name: 'PatientQA', component: () => import('@/views/patient/QAHome.vue') },
      { path: 'profile', name: 'PatientProfile', component: () => import('@/views/patient/ProfilePage.vue') },
    ],
  },

  // ========== Doctor ==========
  {
    path: '/doctor',
    component: () => import('@/components/common/DoctorLayout.vue'),
    meta: { requiresAuth: true, role: 'doctor' },
    children: [
      { path: '', redirect: '/doctor/case' },
      { path: 'case', name: 'DoctorCase', component: () => import('@/views/doctor/CaseAnalysis.vue') },
      { path: 'search', name: 'DoctorSearch', component: () => import('@/views/doctor/KnowledgeSearch.vue') },
      { path: 'history', name: 'DoctorHistory', component: () => import('@/views/doctor/SearchHistory.vue') },
    ],
  },

  // ========== Admin ==========
  {
    path: '/admin',
    component: () => import('@/components/common/AdminLayout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('@/views/admin/DashboardPage.vue') },
      { path: 'knowledge', name: 'AdminKnowledge', component: () => import('@/views/admin/KnowledgePage.vue') },
      { path: 'users', name: 'AdminUsers', component: () => import('@/views/admin/UsersPage.vue') },
      { path: 'feedbacks', name: 'AdminFeedbacks', component: () => import('@/views/admin/FeedbacksPage.vue') },
      { path: 'settings', name: 'AdminSettings', component: () => import('@/views/admin/SettingsPage.vue') },
    ],
  },

  // ========== Root ==========
  { path: '/', redirect: '/login' },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()

  // Guest-only routes (login)
  if (to.meta.guest) {
    if (userStore.isLoggedIn) {
      const roleMap: Record<string, string> = { patient: '/patient/qa', doctor: '/doctor/case', admin: '/admin/dashboard' }
      return next(roleMap[userStore.userRole!] || '/login')
    }
    return next()
  }

  // Auth-required routes
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) return next('/login')
    if (to.meta.role && userStore.userRole !== to.meta.role) {
      const roleMap: Record<string, string> = { patient: '/patient/qa', doctor: '/doctor/case', admin: '/admin/dashboard' }
      return next(roleMap[userStore.userRole!] || '/login')
    }
    return next()
  }

  next()
})

export default router
