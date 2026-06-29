<template>
  <div class="h-full w-full flex flex-col overflow-y-auto p-[16px] md:p-[24px]">
    <h1 class="text-2xl md:text-3xl font-bold mb-6">系统设置</h1>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-surface-container-lowest rounded-xl border p-6">
        <h3 class="font-semibold mb-4 flex items-center gap-1"><span class="material-symbols-outlined text-primary">tune</span> 问答设置</h3>
        <div class="space-y-3">
          <div class="flex justify-between items-center"><span class="text-sm">最大并发会话</span><span class="font-medium text-primary">{{ config.qa.maxSessions }}</span></div>
          <div class="flex justify-between items-center"><span class="text-sm">会话超时(分钟)</span><span class="font-medium text-primary">{{ config.qa.sessionTimeout }}</span></div>
          <div class="flex justify-between items-center"><span class="text-sm">启用流式响应</span><span :class="config.qa.streamResponse?'text-secondary':'text-outline'">{{ config.qa.streamResponse?'开启':'关闭' }}</span></div>
        </div>
      </div>
      <div class="bg-surface-container-lowest rounded-xl border p-6">
        <h3 class="font-semibold mb-4 flex items-center gap-1"><span class="material-symbols-outlined text-primary">hub</span> 知识设置</h3>
        <div class="space-y-3">
          <div class="flex justify-between items-center"><span class="text-sm">当前版本</span><span class="font-medium text-primary">{{ config.knowledge.version }}</span></div>
          <div class="flex justify-between items-center"><span class="text-sm">RAG Top-K</span><span class="font-medium text-primary">{{ config.knowledge.ragTopK }}</span></div>
          <div class="flex justify-between items-center"><span class="text-sm">图谱深度限制</span><span class="font-medium text-primary">{{ config.knowledge.graphDepth }}</span></div>
        </div>
      </div>
      <div class="bg-surface-container-lowest rounded-xl border p-6">
        <h3 class="font-semibold mb-4 flex items-center gap-1"><span class="material-symbols-outlined text-primary">notifications</span> 通知设置</h3>
        <div class="space-y-3">
          <div class="flex justify-between items-center"><span class="text-sm">短信通知</span><span :class="config.notification.sms?'text-secondary':'text-outline'">{{ config.notification.sms?'开启':'关闭' }}</span></div>
          <div class="flex justify-between items-center"><span class="text-sm">挂号提醒(小时前)</span><span class="font-medium text-primary">{{ config.notification.reminderHours }}</span></div>
        </div>
      </div>
      <div class="bg-surface-container-lowest rounded-xl border p-6">
        <h3 class="font-semibold mb-4 flex items-center gap-1"><span class="material-symbols-outlined text-primary">security</span> 安全设置</h3>
        <div class="space-y-3">
          <div class="flex justify-between items-center"><span class="text-sm">二次验证(管理员敏感操作)</span><span class="text-secondary">开启</span></div>
          <div class="flex justify-between items-center"><span class="text-sm">JWT令牌有效期(秒)</span><span class="font-medium text-primary">7200</span></div>
          <div class="flex justify-between items-center"><span class="text-sm">密码最小长度</span><span class="font-medium text-primary">8</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
const config = reactive({
  qa: { maxSessions: 10, sessionTimeout: 30, streamResponse: true },
  knowledge: { version: '2.1.0', ragTopK: 5, graphDepth: 5 },
  notification: { sms: true, reminderHours: 24 }
})
</script>
