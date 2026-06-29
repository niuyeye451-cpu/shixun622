<template>
  <div class="h-full w-full flex flex-col overflow-y-auto p-[16px] md:p-[24px]">
    <h1 class="text-2xl font-bold mb-6 flex items-center gap-2 shrink-0"><span class="material-symbols-outlined text-primary">history</span> 检索历史</h1>

    <!-- Filters -->
    <div class="flex gap-2 mb-4 flex-wrap shrink-0">
      <input v-model="keyword" @keydown.enter="searchHistory" class="w-64 h-12 px-4 rounded-lg border border-outline-variant bg-surface focus:border-primary outline-none text-sm" placeholder="搜索历史记录..." />
      <select v-model="typeFilter" @change="searchHistory" class="h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm">
        <option value="">全部类型</option><option value="knowledge_search">知识检索</option><option value="differential_diagnosis">鉴别诊断</option><option value="multi_symptom">多症状分析</option><option value="drug_interaction">联合用药</option>
      </select>
      <button @click="searchHistory" class="h-12 px-6 rounded-lg bg-primary text-on-primary text-sm font-medium shadow-md">搜索</button>
    </div>

    <!-- Table -->
    <div class="flex-1 bg-surface-container-lowest rounded-xl border overflow-hidden flex flex-col min-h-0">
      <div class="flex-1 overflow-y-auto min-h-0">
        <table class="w-full text-left text-sm">
          <thead class="sticky top-0 bg-surface z-10"><tr class="border-b"><th class="p-3 text-xs text-on-surface-variant uppercase">日期</th><th class="p-3 text-xs text-on-surface-variant uppercase">类型</th><th class="p-3 text-xs text-on-surface-variant uppercase">查询内容</th><th class="p-3 text-xs text-on-surface-variant uppercase">AI摘要</th><th class="p-3 text-xs text-on-surface-variant uppercase text-right">操作</th></tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="5" class="p-8 text-center text-on-surface-variant"><span class="material-symbols-outlined animate-spin align-middle mr-1 text-sm">progress_activity</span> 加载中...</td></tr>
            <tr v-else-if="cases.length === 0"><td colspan="5" class="p-8 text-center text-on-surface-variant"><span class="material-symbols-outlined text-4xl mb-2 block opacity-30">search_off</span>暂无历史记录</td></tr>
            <tr v-for="c in cases" :key="c.conversation_id" class="border-b hover:bg-surface-container/50 transition-colors">
              <td class="p-3 text-on-surface-variant whitespace-nowrap">{{ c.started_at?.slice(0,10) }}</td>
              <td class="p-3 whitespace-nowrap"><span :class="['px-2 py-0.5 rounded-full text-xs', typeBadge(c.case_type)]">{{ caseTypeMap[c.case_type] || c.case_type || '其他' }}</span></td>
              <td class="p-3 text-on-surface max-w-[220px] truncate font-medium" :title="c.title">{{ c.title || c.last_message?.slice(0,40) || '-' }}</td>
              <td class="p-3 text-on-surface-variant max-w-[250px] truncate text-xs">{{ c.last_message || '-' }}</td>
              <td class="p-3 text-right whitespace-nowrap">
                <button @click="viewCase(c)" class="text-primary hover:underline text-xs mr-2">详情</button>
                <button @click="rerunAnalysis(c)" class="text-secondary hover:underline text-xs mr-2" v-if="c.case_type !== 'knowledge_search'">重跑</button>
                <button @click="deleteRecord(c.conversation_id)" class="text-error hover:underline text-xs">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div class="flex items-center justify-between p-3 border-t bg-surface shrink-0" v-if="totalPages > 1">
        <span class="text-xs text-on-surface-variant">共 {{ total }} 条</span>
        <div class="flex gap-1 items-center">
          <button @click="goPage(page-1)" :disabled="page<=1" class="px-2 py-1 rounded border text-xs disabled:opacity-20 hover:bg-surface-container">‹</button>
          <span class="px-2 text-xs">{{ page }}/{{ totalPages }}</span>
          <button @click="goPage(page+1)" :disabled="page>=totalPages" class="px-2 py-1 rounded border text-xs disabled:opacity-20 hover:bg-surface-container">›</button>
        </div>
      </div>
    </div>

    <!-- Detail modal -->
    <Teleport to="body">
      <div v-if="selectedCase" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="selectedCase = null">
        <div class="bg-surface-container-lowest rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col m-4">
          <div class="p-4 border-b flex justify-between items-center shrink-0">
            <h3 class="font-semibold flex items-center gap-1"><span class="material-symbols-outlined text-primary">description</span> 检索详情</h3>
            <button @click="selectedCase = null" class="material-symbols-outlined text-outline hover:text-on-surface">close</button>
          </div>
          <div class="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
            <div v-for="msg in caseMessages" :key="msg.message_id" :class="['p-3 rounded-lg max-w-[85%]', msg.role === 'user' ? 'bg-surface-container ml-auto' : 'bg-primary/5 border-l-4 border-primary']">
              <div class="flex items-center gap-2 mb-1">
                <p class="text-xs text-outline font-medium">{{ msg.role === 'user' ? '医师查询' : 'AI 回答' }}</p>
                <span v-if="msg.role === 'assistant' && msg.answer_source" class="text-[10px] px-1.5 py-0.5 rounded-full" :class="msg.answer_source === 'ai+kb' ? 'bg-secondary/10 text-secondary' : 'bg-surface-container text-on-surface-variant'">{{ msg.answer_source === 'ai+kb' ? 'AI+知识库' : '知识库' }}</span>
                <span v-if="msg.role === 'assistant' && msg.reasoning_path" class="text-[10px] text-outline/60">
                  {{ Array.isArray(msg.reasoning_path) ? msg.reasoning_path.join(' → ') : '' }}
                </span>
              </div>
              <p class="text-sm whitespace-pre-wrap">{{ msg.content }}</p>
            </div>
          </div>
          <!-- Action bar -->
          <div class="p-3 border-t bg-surface/50 flex gap-2 shrink-0">
            <button @click="openFeedback" class="text-xs px-3 py-1.5 rounded-lg bg-tertiary/10 text-tertiary hover:bg-tertiary/20 flex items-center gap-1">
              <span class="material-symbols-outlined text-sm">rate_review</span>提交纠错反馈
            </button>
            <button v-if="selectedCase.case_type !== 'knowledge_search'" @click="rerunAnalysis(selectedCase)" class="text-xs px-3 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 flex items-center gap-1">
              <span class="material-symbols-outlined text-sm">replay</span>重新执行分析
            </button>
            <button @click="copyContent" class="text-xs px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-highest flex items-center gap-1 ml-auto">
              <span class="material-symbols-outlined text-sm">content_copy</span>复制
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { doctorApi } from '@/api/doctor'

const router = useRouter()
const cases = ref<any[]>([])
const keyword = ref(''); const typeFilter = ref(''); const loading = ref(false)
const selectedCase = ref<any>(null); const caseMessages = ref<any[]>([])
const page = ref(1); const total = ref(0); const pageSize = 15
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const caseTypeMap: Record<string,string> = {
  knowledge_search:'知识检索', differential_diagnosis:'鉴别诊断',
  multi_symptom:'多症状分析', drug_interaction:'联合用药',
  treatment_plan:'治疗方案', case:'病例分析'
}

function typeBadge(t: string) {
  const m: Record<string,string> = {
    knowledge_search:'bg-blue-100 text-blue-700', differential_diagnosis:'bg-primary/10 text-primary',
    multi_symptom:'bg-tertiary/10 text-tertiary', drug_interaction:'bg-red-50 text-red-600'
  }
  return m[t] || 'bg-surface-container text-on-surface-variant'
}

async function searchHistory() {
  loading.value = true
  try {
    const res = await doctorApi.getCaseConversations(page.value, pageSize, typeFilter.value || undefined)
    if (res.code === 200) {
      let list = res.data.list || []
      // Client-side keyword filter
      if (keyword.value.trim()) {
        const kw = keyword.value.trim().toLowerCase()
        list = list.filter((c: any) =>
          (c.title || '').toLowerCase().includes(kw) ||
          (c.last_message || '').toLowerCase().includes(kw)
        )
      }
      cases.value = list
      total.value = res.data.total
    }
  } catch {}
  loading.value = false
}

function goPage(p: number) { page.value = p; searchHistory() }

async function viewCase(c: any) {
  selectedCase.value = c
  try {
    const res = await doctorApi.getCaseMessages(c.conversation_id)
    if (res.code === 200) caseMessages.value = res.data.list || []
  } catch {}
}

async function deleteRecord(id: string) {
  if (!confirm('确定删除这条记录？')) return
  try {
    // Conversations don't have a delete API yet, use end conversation
    await doctorApi.endCaseConversation(id)
    cases.value = cases.value.filter(c => c.conversation_id !== id)
    selectedCase.value = null
  } catch {}
}

function rerunAnalysis(c: any) {
  router.push('/doctor/case')
  // Store the case info so CaseAnalysis can prefill
  sessionStorage.setItem('rerun_case', JSON.stringify(c))
}

function openFeedback() {
  if (!selectedCase.value) return
  const msgs = caseMessages.value
  const userMsg = msgs.find((m: any) => m.role === 'user')
  const aiMsg = msgs.find((m: any) => m.role === 'assistant')
  const content = `历史记录反馈\n类型: ${caseTypeMap[selectedCase.value.case_type] || '未知'}\n查询: ${userMsg?.content || ''}\nAI回答: ${(aiMsg?.content || '').slice(0, 300)}`

  doctorApi.submitFeedback({
    type: 'knowledge_error',
    title: `[历史记录反馈] ${(userMsg?.content || '').slice(0, 50)}`,
    content,
    references: selectedCase.value.case_type === 'knowledge_search' ? [] : undefined,
  } as any).then(res => {
    if (res.code === 200) alert('反馈已提交，管理端将进行审核。感谢您的贡献！')
  }).catch(() => alert('提交失败，请重试'))
}

function copyContent() {
  const msgs = caseMessages.value
  const text = msgs.map((m: any) => `[${m.role === 'user' ? '医师' : 'AI'}] ${m.content}`).join('\n\n')
  navigator.clipboard.writeText(text).then(() => alert('已复制到剪贴板')).catch(() => alert('复制失败'))
}

onMounted(searchHistory)
</script>
</Teleport>
