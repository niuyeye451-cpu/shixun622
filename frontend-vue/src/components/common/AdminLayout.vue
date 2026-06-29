<template>
  <div class="h-screen flex overflow-hidden bg-background">
    <nav class="hidden md:flex flex-col h-screen p-4 bg-inverse-surface text-white w-64 flex-shrink-0">
      <div class="text-secondary-fixed font-bold text-xl mb-8 flex items-center gap-2">
        <span class="material-symbols-outlined">medical_information</span> MedGraph AI
      </div>
      <div class="flex items-center gap-3 mb-8 p-3 bg-white/10 rounded-lg">
        <div class="w-10 h-10 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center flex-shrink-0">
          <span class="material-symbols-outlined">shield_person</span>
        </div>
        <div>
          <div class="text-secondary-fixed text-sm font-medium">{{ user.userName }}</div>
          <div class="text-surface-variant text-xs">管理员</div>
        </div>
      </div>
      <div class="flex flex-col gap-1 flex-grow">
        <router-link to="/admin/dashboard" class="flex items-center gap-3 p-3 rounded-lg text-surface-variant hover:text-white hover:bg-white/10 transition-all text-sm" active-class="!bg-secondary-container !text-on-secondary-container !font-bold">
          <span class="material-symbols-outlined text-lg">dashboard</span> Dashboard
        </router-link>
        <router-link to="/admin/knowledge" class="flex items-center gap-3 p-3 rounded-lg text-surface-variant hover:text-white hover:bg-white/10 transition-all text-sm" active-class="!bg-secondary-container !text-on-secondary-container !font-bold">
          <span class="material-symbols-outlined text-lg">hub</span> Knowledge Base
        </router-link>
        <router-link to="/admin/users" class="flex items-center gap-3 p-3 rounded-lg text-surface-variant hover:text-white hover:bg-white/10 transition-all text-sm" active-class="!bg-secondary-container !text-on-secondary-container !font-bold">
          <span class="material-symbols-outlined text-lg">group</span> Users
        </router-link>
        <router-link to="/admin/feedbacks" class="flex items-center gap-3 p-3 rounded-lg text-surface-variant hover:text-white hover:bg-white/10 transition-all text-sm" active-class="!bg-secondary-container !text-on-secondary-container !font-bold">
          <span class="material-symbols-outlined text-lg">rate_review</span> Feedback
        </router-link>
        <router-link to="/admin/settings" class="flex items-center gap-3 p-3 rounded-lg text-surface-variant hover:text-white hover:bg-white/10 transition-all text-sm" active-class="!bg-secondary-container !text-on-secondary-container !font-bold">
          <span class="material-symbols-outlined text-lg">settings</span> Settings
        </router-link>
      </div>
      <button @click="doLogout" class="w-full mt-4 py-3 bg-error/20 text-error rounded-lg text-sm hover:bg-error/30 transition-colors flex items-center justify-center gap-2">
        <span class="material-symbols-outlined text-lg">logout</span> Sign Out
      </button>
    </nav>
    <main class="flex-1 overflow-y-auto flex flex-col">
      <router-view class="flex-1" />
      <footer class="flex-shrink-0 border-t border-outline-variant/30 bg-surface-container-low/50 px-4 py-1.5 text-center">
        <p class="text-[11px] text-outline">医疗免责声明：本系统仅供授权医务人员及研究者使用。AI生成内容仅供参考，不构成临床诊断依据。所有操作全程审计记录。</p>
      </footer>
    </main>
  </div>
</template>
<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
const user = useUserStore()
const router = useRouter()
async function doLogout() { await user.logout(); router.push('/login') }
</script>
