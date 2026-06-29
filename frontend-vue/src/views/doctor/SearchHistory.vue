<template>
  <div class="h-full w-full flex flex-col overflow-y-auto p-[16px] md:p-[24px]">
    <h1 class="text-2xl font-bold mb-6 flex items-center gap-2"><span class="material-symbols-outlined text-primary">history</span> 检索历史</h1>
    <div class="flex gap-2 mb-4">
      <input v-model="keyword" @input="loadHistory" class="w-64 h-12 px-4 rounded-lg border border-outline-variant bg-surface focus:border-primary outline-none text-sm" placeholder="搜索病例记录..." />
      <select v-model="typeFilter" @change="loadHistory" class="h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm">
        <option value="">全部类型</option><option value="differential_diagnosis">鉴别诊断</option><option value="multi_symptom">多病症关联</option><option value="treatment_plan">治疗方案</option>
      </select>
    </div>
    <div class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <table class="w-full text-left text-sm">
        <thead><tr class="bg-surface border-b"><th class="p-3 text-xs text-on-surface-variant uppercase">日期</th><th class="p-3 text-xs text-on-surface-variant uppercase">类型</th><th class="p-3 text-xs text-on-surface-variant uppercase">标题</th><th class="p-3 text-xs text-on-surface-variant uppercase">最后消息</th><th class="p-3 text-xs text-on-surface-variant uppercase">状态</th><th class="p-3 text-xs text-on-surface-variant uppercase text-right">操作</th></tr></thead>
        <tbody>
          <tr v-if="cases.length === 0"><td colspan="6" class="p-8 text-center text-on-surface-variant">暂无历史记录</td></tr>
          <tr v-for="c in cases" :key="c.conversation_id" class="border-b hover:bg-surface-container/50 transition-colors">
            <td class="p-3 text-on-surface-variant">{{ c.started_at?.slice(0,10) }}</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary">{{ caseTypeMap[c.case_type] || c.case_type || '-' }}</span></td>
            <td class="p-3 text-on-surface">{{ c.title || '病例分析' }}</td>
            <td class="p-3 text-on-surface-variant truncate max-w-[200px]">{{ c.last_message || '-' }}</td>
            <td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', c.status === 'active' ? 'bg-secondary-container text-on-secondary-container' : 'bg-surface-container text-on-surface-variant']">{{ c.status === 'active' ? '进行中' : '已结束' }}</span></td>
            <td class="p-3 text-right"><button @click="viewCase(c)" class="text-primary hover:underline text-xs">查看</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Case detail modal -->
    <div v-if="selectedCase" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="selectedCase = null">
      <div class="bg-surface-container-lowest rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col m-4">
        <div class="p-4 border-b flex justify-between items-center">
          <h3 class="font-semibold flex items-center gap-1"><span class="material-symbols-outlined text-primary">description</span> 病例详情</h3>
          <button @click="selectedCase = null" class="material-symbols-outlined text-outline hover:text-on-surface">close</button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
          <div v-for="msg in caseMessages" :key="msg.message_id" :class="['p-3 rounded-lg max-w-[80%]', msg.role === 'user' ? 'bg-surface-container ml-auto' : 'bg-primary/5 border-l-4 border-primary']">
            <p class="text-xs text-outline mb-1">{{ msg.role === 'user' ? '医师' : 'AI助手' }}</p>
            <p class="text-sm">{{ msg.content }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { doctorApi } from '@/api/doctor'
const cases = ref<any[]>([])
const keyword = ref(''); const typeFilter = ref('')
const selectedCase = ref<any>(null); const caseMessages = ref<any[]>([])
const caseTypeMap: Record<string,string> = {differential_diagnosis:'鉴别诊断',multi_symptom:'多病症关联',treatment_plan:'治疗方案'}
async function loadHistory() { try { const res = await doctorApi.getCaseConversations(1, 50, typeFilter.value || undefined); if (res.code === 200) cases.value = res.data.list } catch {} }
async function viewCase(c: any) { selectedCase.value = c; try { const res = await doctorApi.getCaseMessages(c.conversation_id); if (res.code === 200) caseMessages.value = res.data.list } catch {} }
onMounted(loadHistory)
</script>
