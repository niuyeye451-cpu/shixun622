<template>
  <div class="h-screen flex flex-col overflow-hidden bg-surface">
    <header class="bg-white/80 backdrop-blur border-b border-outline-variant h-16 flex items-center justify-between px-4 md:px-10 flex-shrink-0">
      <div class="flex items-center gap-6 flex-shrink-0">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-2xl">medical_services</span>
          <span class="text-primary font-bold text-xl tracking-tight">MedGraph AI</span>
        </div>
        <nav class="hidden md:flex gap-1">
          <router-link to="/doctor/case" class="px-3 py-1.5 rounded-lg text-sm font-medium text-on-surface-variant hover:bg-surface-container transition-colors" active-class="!bg-primary/10 !text-primary">病例分析</router-link>
          <router-link to="/doctor/search" class="px-3 py-1.5 rounded-lg text-sm font-medium text-on-surface-variant hover:bg-surface-container transition-colors" active-class="!bg-primary/10 !text-primary">知识检索</router-link>
          <router-link to="/doctor/history" class="px-3 py-1.5 rounded-lg text-sm font-medium text-on-surface-variant hover:bg-surface-container transition-colors" active-class="!bg-primary/10 !text-primary">检索历史</router-link>
        </nav>
      </div>
      <!-- Global search -->
      <div class="hidden md:flex items-center flex-1 max-w-md mx-4">
        <div class="relative w-full">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-lg">search</span>
          <input class="w-full h-10 pl-10 pr-12 rounded-lg border border-outline-variant bg-surface-container text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" placeholder="搜索医学知识、药品相互作用..." />
          <button class="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-surface-container text-on-surface-variant" title="语音搜索">
            <span class="material-symbols-outlined text-lg">mic</span>
          </button>
        </div>
      </div>
      <div class="flex items-center gap-1 flex-shrink-0">
        <button class="p-2 rounded-full md:hidden hover:bg-surface-container-highest/50 transition-colors text-on-surface-variant" title="语音输入">
          <span class="material-symbols-outlined text-xl">mic</span>
        </button>
        <button class="p-2 rounded-full hover:bg-surface-container-highest/50 transition-colors text-on-surface-variant" title="通知">
          <span class="material-symbols-outlined text-xl">notifications</span>
        </button>
        <div class="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center ml-1">
          <span class="material-symbols-outlined text-sm">person</span>
        </div>
        <button @click="doLogout" class="px-3 py-1.5 rounded-lg bg-error/10 text-error hover:bg-error/20 text-sm ml-1">退出</button>
      </div>
    </header>
    <main class="flex-1 overflow-hidden flex flex-col">
      <router-view class="flex-1 overflow-hidden" />
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
