<template>
  <div class="h-full flex flex-col md:flex-row overflow-hidden p-[16px] md:p-[40px] gap-[24px]">
    <!-- Left: Chat (50%) -->
    <section class="w-full md:w-1/2 flex flex-col bg-surface-container-lowest rounded-xl border border-outline-variant/50 overflow-hidden">
      <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        <div v-if="qa.messages.length === 0" class="flex-1 flex items-center justify-center text-on-surface-variant">
          <div class="text-center">
            <span class="material-symbols-outlined text-5xl mb-2 block">psychology</span>
            <p class="text-lg font-medium">智能症状问答</p>
            <p class="text-sm">请输入您的症状描述开始咨询</p>
          </div>
        </div>
        <template v-for="msg in qa.messages" :key="msg.message_id">
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="bg-surface-container px-4 py-2 rounded-2xl rounded-tr-none max-w-[80%]">
              <p class="text-on-surface">{{ msg.content }}</p>
            </div>
          </div>
          <div v-else class="flex justify-start">
            <div class="bg-surface-container-lowest border border-outline-variant/30 rounded-2xl rounded-tl-none p-4 max-w-[90%] relative">
              <div class="absolute left-0 top-4 bottom-4 w-1 bg-primary rounded-r-full"></div>
              <div class="flex items-center gap-1 text-primary mb-2">
                <span class="material-symbols-outlined text-lg">smart_toy</span>
                <span class="text-sm font-bold">MedGraph 分析结果</span>
              </div>
              <p class="text-on-surface-variant leading-relaxed">{{ msg.content }}</p>
              <div v-if="msg.matched_disease" class="mt-3 flex flex-wrap gap-2">
                <span class="bg-primary/10 text-primary px-3 py-1 rounded-full text-xs border border-primary/20">{{ msg.matched_disease }}</span>
              </div>
              <div class="bg-surface-variant/30 rounded p-2 mt-3 flex items-start gap-1">
                <span class="material-symbols-outlined text-sm text-outline mt-0.5">info</span>
                <p class="text-xs text-outline">免责声明：本分析基于知识图谱生成，仅供参考，不作为最终临床诊断依据。</p>
              </div>
              <div v-if="msg.answer_source" class="flex items-center gap-1 text-xs text-outline mt-2 pt-2 border-t border-outline-variant/30">
                <span class="material-symbols-outlined text-sm">menu_book</span>
                Source: {{ msg.answer_source.toUpperCase() }} · MedGraph Knowledge Base v1.0
              </div>
            </div>
          </div>
        </template>
        <div v-if="qa.isLoading" class="flex justify-start">
          <div class="bg-surface-container-lowest border rounded-2xl p-4">
            <span class="material-symbols-outlined animate-spin align-middle text-lg">progress_activity</span> 分析中...
          </div>
        </div>
      </div>
      <div class="p-4 border-t border-outline-variant/50">
        <div class="relative flex items-end bg-surface-container-low border border-outline-variant rounded-xl">
          <textarea v-model="inputText" @keydown.enter.prevent="send" class="w-full bg-transparent border-none focus:ring-0 resize-none p-3 text-on-surface placeholder-on-surface-variant/50" placeholder="描述您的症状或输入医学问题..." rows="2" maxlength="500"></textarea>
          <div class="p-2 flex gap-2">
            <button @click="send" :disabled="!inputText.trim() || qa.isLoading" class="p-2 rounded-full bg-primary text-on-primary hover:bg-primary-container transition-colors shadow-md disabled:opacity-50">
              <span class="material-symbols-outlined">send</span>
            </button>
          </div>
        </div>
        <p class="text-xs text-on-surface-variant mt-1 text-right">{{ inputText.length }}/500</p>
      </div>
    </section>

    <!-- Center: Graph (30%) -->
    <KnowledgeGraphCanvas :graph-data="qa.currentGraph" class="w-full md:w-[30%] h-64 md:h-full" @node-click="onGraphNodeClick" />

    <!-- Right: Details & Recommendations (20%) -->
    <section class="w-full md:w-[20%] flex flex-col gap-4 overflow-y-auto">
      <!-- Entity Detail (when a graph node is clicked) -->
      <div v-if="entityDetail" class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4">
        <div class="flex items-center gap-1 mb-3">
          <span class="px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary">{{ entityDetail.type }}</span>
          <h3 class="font-semibold text-on-surface text-sm">{{ entityDetail.name }}</h3>
          <button @click="entityDetail = null" class="ml-auto p-0.5 rounded hover:bg-surface-container text-on-surface-variant"><span class="material-symbols-outlined text-sm">close</span></button>
        </div>
        <p class="text-xs text-on-surface-variant mb-3">{{ entityDetail.description || '暂无描述' }}</p>
        <div v-if="entityDetail.attributes" class="space-y-2">
          <div v-if="entityDetail.attributes.common_symptoms" class="text-xs">
            <span class="text-on-surface-variant block mb-1">常见症状</span>
            <div class="flex flex-wrap gap-1"><span v-for="s in entityDetail.attributes.common_symptoms" :key="s" class="px-1.5 py-0.5 rounded bg-error-container/30 text-on-error-container text-[10px]">{{ s }}</span></div>
          </div>
          <div v-if="entityDetail.attributes.treatment_methods" class="text-xs">
            <span class="text-on-surface-variant block mb-1">治疗方法</span>
            <div class="flex flex-wrap gap-1"><span v-for="t in entityDetail.attributes.treatment_methods" :key="t" class="px-1.5 py-0.5 rounded bg-secondary-container/30 text-on-secondary-container text-[10px]">{{ t }}</span></div>
          </div>
          <div v-if="entityDetail.attributes.high_risk_groups" class="text-xs">
            <span class="text-on-surface-variant block mb-1">高危人群</span>
            <div class="flex flex-wrap gap-1"><span v-for="r in entityDetail.attributes.high_risk_groups" :key="r" class="px-1.5 py-0.5 rounded bg-tertiary-container/30 text-on-tertiary text-[10px]">{{ r }}</span></div>
          </div>
        </div>
        <p class="text-[10px] text-outline mt-2 pt-2 border-t border-outline-variant/30">
          <span class="material-symbols-outlined text-[10px] align-middle">menu_book</span>
          Source: {{ entityDetail.source_version || 'MedGraph KB' }} v{{ entityDetail.version_number || '1.0' }}
        </p>
      </div>

      <h3 class="font-semibold text-on-surface">{{ entityDetail ? '相关推荐' : '智能导诊推荐' }}</h3>
      <div v-if="qa.lastAssistantMessage" class="bg-gradient-to-br from-blue-50 to-white border border-primary/20 rounded-xl p-4 flex flex-col items-center text-center">
        <div class="w-12 h-12 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-2">
          <span class="material-symbols-outlined text-2xl">monitor_heart</span>
        </div>
        <h4 class="font-semibold text-on-surface text-sm mb-1">{{ qa.lastAssistantMessage.matched_department || '推荐科室' }}</h4>
        <p class="text-xs text-on-surface-variant">匹配度: 高</p>
      </div>
      <router-link to="/patient/profile" class="w-full bg-primary text-on-primary text-sm font-medium py-3 px-4 rounded-xl shadow-md text-center flex items-center justify-center gap-2 hover:bg-primary/90 transition-all active:scale-95">
        <span class="material-symbols-outlined text-lg">calendar_month</span> 一键预约挂号
      </router-link>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useQaStore } from '@/stores/qa'
import { commonApi } from '@/api/common'
import KnowledgeGraphCanvas from '@/components/graph/KnowledgeGraphCanvas.vue'
import type { GraphNode } from '@/types'
const qa = useQaStore()
const inputText = ref('')
const entityDetail = ref<any>(null)
const chatContainer = ref<HTMLElement | null>(null)

async function send() {
  const text = inputText.value.trim()
  if (!text || qa.isLoading) return
  inputText.value = ''
  await qa.sendPatientMessage(text)
  await nextTick()
  if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
}

onMounted(async () => {
  await qa.loadPatientConversations()
  if (qa.conversations.length > 0) {
    const active = qa.conversations.find(c => c.status === 'active')
    if (active) await qa.selectConversation(active.conversation_id)
  }
  // Auto-load graph if disease was matched
  loadGraphForLast()
})

async function onGraphNodeClick(node: GraphNode) {
  // Load entity detail
  if (node.id) {
    try {
      const detailRes = await commonApi.getEntityDetail(node.id)
      if (detailRes.code === 200) entityDetail.value = detailRes.data
    } catch { entityDetail.value = null }
  }
  // Also reload subgraph
  if (node.name) {
    const res = await commonApi.getDiseaseGraph(node.name)
    if (res.code === 200) qa.currentGraph = res.data
  }
}

async function loadGraphForLast() {
  const last = qa.lastAssistantMessage
  if (last?.matched_disease) {
    try {
      const res = await commonApi.getDiseaseGraph(last.matched_disease)
      if (res.code === 200) qa.currentGraph = res.data
    } catch {}
  }
}
</script>
