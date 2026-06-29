<template>
  <div class="h-screen flex flex-col overflow-hidden bg-surface">
    <header class="bg-white/80 backdrop-blur border-b border-outline-variant h-16 flex items-center justify-between px-4 md:px-10 flex-shrink-0">
      <div class="flex items-center gap-2 flex-shrink-0">
        <span class="material-symbols-outlined text-primary text-2xl">medical_information</span>
        <span class="text-primary font-bold text-xl tracking-tight hidden sm:inline">MedGraph AI</span>
      </div>
      <!-- PRD: unified global search with voice input -->
      <div class="hidden md:flex items-center flex-1 max-w-lg mx-4">
        <div class="relative w-full">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-lg">search</span>
          <input v-model="searchQuery" @keydown.enter="doSearch" class="w-full h-10 pl-10 pr-4 rounded-lg border border-outline-variant bg-surface-container text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" placeholder="搜索疾病、症状、药品..." />
        </div>
      </div>
      <div class="flex items-center gap-1 flex-shrink-0">
        <div class="relative">
          <button class="p-2 rounded-full hover:bg-surface-container-highest/50 transition-colors text-on-surface-variant relative" title="通知" @click="toggleNotifications">
            <span class="material-symbols-outlined text-xl">notifications</span>
            <span v-if="unreadCount > 0" class="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-error text-on-error text-[10px] font-bold flex items-center justify-center leading-none">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
          </button>
          <!-- Notification Dropdown -->
          <div v-if="showNotifPanel" class="absolute right-0 top-full mt-2 w-80 bg-surface-container-lowest rounded-xl shadow-2xl border border-outline-variant z-50 overflow-hidden animate-fade-in">
            <div class="p-3 border-b flex justify-between items-center bg-surface-container-low">
              <h4 class="text-sm font-semibold text-on-surface">消息提醒</h4>
              <button v-if="unreadCount > 0" @click="markAllRead" class="text-xs text-primary hover:underline">全部标为已读</button>
            </div>
            <div class="max-h-80 overflow-y-auto">
              <div v-if="notifications.length === 0" class="p-6 text-center text-on-surface-variant text-sm">暂无通知</div>
              <div v-for="n in notifications" :key="n.reminder_id" :class="['p-3 border-b border-outline-variant/30 hover:bg-surface-container cursor-pointer transition-colors', !n.is_read ? 'bg-primary/5' : '']" @click="markRead(n.reminder_id)">
                <div class="flex items-start gap-2">
                  <span class="material-symbols-outlined text-lg mt-0.5" :class="n.type === 'registration' ? 'text-primary' : n.type === 'medication' ? 'text-secondary' : 'text-tertiary'">{{ n.type === 'registration' ? 'event_note' : n.type === 'medication' ? 'medication' : 'notifications' }}</span>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-on-surface">{{ n.title }}</p>
                    <p class="text-xs text-on-surface-variant mt-0.5 line-clamp-2">{{ n.content }}</p>
                    <p class="text-[11px] text-outline mt-1">{{ n.remind_time?.slice(0,16) || n.created_at?.slice(0,16) }}</p>
                  </div>
                  <span v-if="!n.is_read" class="w-2 h-2 rounded-full bg-error flex-shrink-0 mt-1.5"></span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <button class="p-2 rounded-full hover:bg-surface-container-highest/50 transition-colors text-on-surface-variant" title="个人中心" @click="$router.push('/patient/profile')">
          <span class="material-symbols-outlined text-xl">account_circle</span>
        </button>
        <router-link to="/patient/qa" class="px-3 py-1.5 rounded-lg hover:bg-surface-container text-on-surface-variant text-sm flex items-center gap-1 ml-2">
          <span class="material-symbols-outlined text-lg">chat</span> 智能问诊
        </router-link>
        <button @click="doLogout" class="px-3 py-1.5 rounded-lg bg-error/10 text-error hover:bg-error/20 text-sm flex items-center gap-1">
          <span class="material-symbols-outlined text-lg">logout</span> 退出
        </button>
      </div>
    </header>
    <main class="flex-1 overflow-hidden flex flex-col">
      <router-view v-slot="{ Component }" class="flex-1 overflow-hidden">
        <keep-alive><component :is="Component" /></keep-alive>
      </router-view>
      <!-- PRD: mandatory legal disclaimer on all screens -->
      <footer class="flex-shrink-0 border-t border-outline-variant/30 bg-surface-container-low/50 px-4 py-1.5 text-center">
        <p class="text-[11px] text-outline">医疗免责声明：本系统仅供授权医务人员及研究者使用。AI生成内容仅供参考，不构成临床诊断依据。所有操作全程审计记录。</p>
      </footer>
    </main>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { commonApi } from '@/api/common'
import { patientApi } from '@/api/patient'
const user = useUserStore()
const router = useRouter()
const searchQuery = ref('')
const unreadCount = ref(0)
const showNotifPanel = ref(false)
const notifications = ref<any[]>([])

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  try {
    const res = await commonApi.searchEntities(q)
    if (res.code === 200 && res.data?.length) {
      const names = (Array.isArray(res.data) ? res.data : (res.data as any).entities || []).map((e: any) => e.name).slice(0, 5).join('、')
      showToast(`找到: ${names || '无结果'}`, 'success')
    } else {
      showToast('未找到匹配的医学实体', 'info')
    }
  } catch { showToast('搜索失败，请重试', 'info') }
}

async function toggleNotifications() {
  showNotifPanel.value = !showNotifPanel.value
  if (showNotifPanel.value) {
    try {
      const res = await patientApi.getReminders({ page: 1, page_size: 20 })
      if (res.code === 200) {
        const data = res.data as any
        notifications.value = data.list || []
        unreadCount.value = data.unread_count || 0
      }
    } catch { notifications.value = [] }
  }
}

async function markRead(reminderId: string) {
  try {
    await patientApi.markReminderRead(reminderId)
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    const found = notifications.value.find((n: any) => n.reminder_id === reminderId)
    if (found) found.is_read = true
  } catch {}
}

async function markAllRead() {
  try {
    await patientApi.markAllRead()
    unreadCount.value = 0
    notifications.value.forEach((n: any) => n.is_read = true)
  } catch {}
}

function showToast(msg: string, type = 'info') {
  const color = type === 'error' ? 'bg-error' : type === 'success' ? 'bg-secondary' : 'bg-primary'
  const d = document.createElement('div')
  d.className = `fixed top-4 right-4 z-[9999] ${color} text-white px-4 py-2 rounded-lg text-sm shadow-lg animate-fade-in`
  d.textContent = msg
  document.body.appendChild(d)
  setTimeout(() => { d.style.opacity = '0'; d.style.transition = 'opacity .3s'; setTimeout(() => d.remove(), 300) }, 3000)
}
async function doLogout() { await user.logout(); router.push('/login') }
</script>
