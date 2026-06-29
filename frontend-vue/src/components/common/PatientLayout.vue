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
          <input class="w-full h-10 pl-10 pr-12 rounded-lg border border-outline-variant bg-surface-container text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" placeholder="搜索疾病、症状、药品..." />
          <button class="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-surface-container text-on-surface-variant" title="语音搜索">
            <span class="material-symbols-outlined text-lg">mic</span>
          </button>
        </div>
      </div>
      <div class="flex items-center gap-1 flex-shrink-0">
        <button class="p-2 rounded-full hover:bg-surface-container-highest/50 transition-colors text-on-surface-variant md:hidden" title="语音输入">
          <span class="material-symbols-outlined text-xl">mic</span>
        </button>
        <button class="p-2 rounded-full hover:bg-surface-container-highest/50 transition-colors text-on-surface-variant" title="通知">
          <span class="material-symbols-outlined text-xl">notifications</span>
        </button>
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
      <router-view class="flex-1 overflow-hidden" />
      <!-- PRD: mandatory legal disclaimer on all screens -->
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
