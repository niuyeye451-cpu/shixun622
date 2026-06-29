<template>
  <div class="p-[16px] md:p-[40px] max-w-[1600px] mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl md:text-3xl font-bold">管理仪表盘</h1>
    </div>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div @click="$router.push('/admin/users')" class="bg-surface-container-lowest rounded-xl border p-4 cursor-pointer hover:shadow-md transition-shadow">
        <div class="w-12 h-12 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-2"><span class="material-symbols-outlined text-2xl">person</span></div>
        <p class="text-3xl font-bold text-on-surface">{{ stats.dashboard?.patient_count || '-' }}</p><p class="text-xs text-on-surface-variant">患者总数</p>
      </div>
      <div @click="$router.push('/admin/users')" class="bg-surface-container-lowest rounded-xl border p-4 cursor-pointer hover:shadow-md transition-shadow">
        <div class="w-12 h-12 bg-secondary/10 text-secondary rounded-full flex items-center justify-center mb-2"><span class="material-symbols-outlined text-2xl">stethoscope</span></div>
        <p class="text-3xl font-bold text-on-surface">{{ stats.dashboard?.doctor_count || '-' }}</p><p class="text-xs text-on-surface-variant">医师总数</p>
      </div>
      <div @click="$router.push('/admin/feedbacks')" class="bg-surface-container-lowest rounded-xl border p-4 cursor-pointer hover:shadow-md transition-shadow">
        <div class="w-12 h-12 bg-tertiary-container/30 text-tertiary rounded-full flex items-center justify-center mb-2"><span class="material-symbols-outlined text-2xl">rate_review</span></div>
        <p class="text-3xl font-bold text-on-surface">{{ stats.dashboard?.pending_feedback_count || '-' }}</p><p class="text-xs text-on-surface-variant">待处理反馈</p>
      </div>
      <div @click="$router.push('/admin/knowledge')" class="bg-surface-container-lowest rounded-xl border p-4 cursor-pointer hover:shadow-md transition-shadow">
        <div class="w-12 h-12 bg-error/10 text-error rounded-full flex items-center justify-center mb-2"><span class="material-symbols-outlined text-2xl">help</span></div>
        <p class="text-3xl font-bold text-on-surface">{{ stats.dashboard?.pending_unknown_count || '-' }}</p><p class="text-xs text-on-surface-variant">未知问题</p>
      </div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <div class="bg-surface-container-lowest rounded-xl border p-4">
        <h3 class="font-semibold mb-3">知识实体分布</h3>
        <div v-if="stats.entityStats" class="flex gap-3 flex-wrap">
          <div v-for="(cnt, t) in stats.entityStats.by_type" :key="t" class="bg-surface rounded-lg p-3 flex-1 min-w-[100px] text-center"><p class="text-2xl font-bold text-primary">{{ cnt }}</p><p class="text-xs text-on-surface-variant">{{ t }}</p></div>
        </div>
        <p v-else class="text-center text-on-surface-variant p-4">加载中...</p>
      </div>
      <div class="bg-surface-container-lowest rounded-xl border p-4">
        <h3 class="font-semibold mb-3">今日概览</h3>
        <div class="space-y-2" v-if="stats.dashboard?.daily_stats">
          <div class="flex justify-between p-3 bg-surface rounded-lg"><span>新增患者</span><span class="font-medium text-primary">{{ stats.dashboard.daily_stats.new_patients }}</span></div>
          <div class="flex justify-between p-3 bg-surface rounded-lg"><span>新增医师</span><span class="font-medium text-secondary">{{ stats.dashboard.daily_stats.new_doctors }}</span></div>
          <div class="flex justify-between p-3 bg-surface rounded-lg"><span>今日咨询</span><span class="font-medium text-tertiary">{{ stats.dashboard.daily_stats.consultations }}</span></div>
          <div class="flex justify-between p-3 bg-surface rounded-lg"><span>今日挂号</span><span class="font-medium text-primary">{{ stats.dashboard.daily_stats.registrations }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useStatsStore } from '@/stores/stats'; import { onMounted } from 'vue'
const stats = useStatsStore()
onMounted(async () => { await stats.loadDashboard(); await stats.loadEntityStats() })

</script>
