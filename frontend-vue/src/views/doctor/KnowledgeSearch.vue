<template>
  <div class="h-full overflow-y-auto p-[16px] md:p-[40px] max-w-7xl mx-auto">
    <div class="flex gap-2 mb-6 border-b border-outline-variant overflow-x-auto">
      <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key" :class="['px-4 py-2 rounded-t-lg text-sm font-medium border-b-2 transition-colors', activeTab === tab.key ? 'border-primary text-primary bg-surface-container-lowest' : 'border-transparent text-on-surface-variant']">{{ tab.label }}</button>
    </div>

    <!-- Knowledge Search -->
    <div v-if="activeTab === 'knowledge'" class="flex flex-col gap-4">
      <div class="flex gap-2">
        <input v-model="kqQuery" @keydown.enter="searchKnowledge" class="flex-1 h-12 px-4 rounded-lg border border-outline-variant bg-surface focus:border-primary outline-none" placeholder="高血压合并糖尿病的首选降压药物" />
        <select v-model="kqType" class="h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm"><option value="">全部</option><option value="diagnosis">诊断</option><option value="treatment">治疗</option><option value="medication">用药</option></select>
        <button @click="searchKnowledge" class="h-12 px-6 rounded-lg bg-primary text-on-primary text-sm font-medium shadow-md">检索</button>
      </div>
      <div v-if="kqResults.length" class="space-y-3">
        <div v-for="r in kqResults" :key="r.name" class="bg-surface-container-lowest rounded-xl border p-4">
          <div class="flex items-center gap-2 mb-2"><span class="px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary">{{ r.type }}</span><h3 class="font-semibold">{{ r.name }}</h3></div>
          <p class="text-sm text-on-surface-variant">{{ r.description || '暂无描述' }}</p>
          <div v-if="r.related_entities?.length" class="mt-3 pt-3 border-t flex flex-wrap gap-2">
            <span v-for="rel in r.related_entities.slice(0,10)" :key="rel.entity_id" class="px-2 py-1 rounded-full text-xs bg-surface-container border">{{ rel.name }}<span class="text-outline ml-1">{{ rel.relation_name || rel.relation_type }}</span></span>
          </div>
        </div>
      </div>
      <div v-else class="text-center p-12 text-on-surface-variant"><span class="material-symbols-outlined text-5xl mb-3 block">psychology</span><p class="text-lg">输入关键词检索医学知识</p></div>
    </div>

    <!-- Drug Interactions -->
    <div v-if="activeTab === 'drugs'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-surface-container-lowest rounded-xl border p-6">
        <h3 class="font-semibold mb-4"><span class="material-symbols-outlined text-primary align-middle">medication</span> 待检查药品</h3>
        <div class="flex gap-2 mb-4"><input v-model="drugInput" @keydown.enter="addDrug" class="flex-1 h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="药品名称，回车添加" /><button @click="addDrug" class="h-12 px-4 rounded-lg bg-primary text-on-primary text-sm">添加</button></div>
        <div class="flex flex-wrap gap-2 mb-4"><span v-for="(d,i) in drugList" :key="i" class="inline-flex items-center gap-1 bg-primary-fixed text-on-primary-fixed-variant px-3 py-1 rounded-full text-xs border border-primary/20">{{ d }}<button @click="drugList.splice(i,1)" class="material-symbols-outlined text-xs hover:text-error">close</button></span></div>
        <button @click="checkInteractions" :disabled="drugList.length<2" class="w-full h-12 rounded-lg bg-secondary text-on-secondary text-sm font-medium shadow-md disabled:opacity-50 flex items-center justify-center gap-1"><span class="material-symbols-outlined text-lg">science</span> 检查相互作用</button>
      </div>
      <div class="bg-surface-container-lowest rounded-xl border p-6">
        <h3 class="font-semibold mb-4">相互作用结果</h3>
        <div v-if="drugResults.length" class="space-y-2">
          <div v-for="(r,i) in drugResults" :key="i" :class="['rounded-lg p-3 border-l-4', r.level==='warning'?'border-error':'border-orange-600']">
            <p class="text-sm font-bold">{{ r.drug_a }} + {{ r.drug_b }}</p><p class="text-xs text-on-surface-variant">{{ r.description }}</p><p class="text-xs text-outline mt-1">建议: {{ r.recommendation }}</p>
          </div>
        </div>
        <p v-else class="text-center text-on-surface-variant p-6">添加药品并点击检查</p>
      </div>
    </div>

    <!-- Graph Browse -->
    <div v-if="activeTab === 'graph'" class="flex flex-col gap-4">
      <div class="flex gap-2"><input v-model="entityKeyword" @keydown.enter="searchEntities" class="flex-1 h-12 px-4 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="搜索医疗实体" /><select v-model="entityType" class="h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm"><option value="">全部</option><option value="disease">疾病</option><option value="symptom">症状</option><option value="drug">药品</option></select><button @click="searchEntities" class="h-12 px-6 rounded-lg bg-primary text-on-primary text-sm shadow-md">搜索</button></div>
      <div class="space-y-2"><div v-for="e in entityResults" :key="e.entity_id" @click="loadGraph(e.name)" class="flex justify-between items-center p-3 rounded-lg bg-surface-container-lowest border hover:bg-surface-container transition-colors cursor-pointer"><div><span class="px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary mr-2">{{ e.type }}</span><span class="text-sm font-medium">{{ e.name }}</span></div><span class="material-symbols-outlined text-outline">chevron_right</span></div></div>
      <div class="bg-slate-800 rounded-xl min-h-[300px] flex items-center justify-center p-6"><div v-if="graphNodes.length" class="flex flex-wrap gap-3 justify-center"><div v-for="n in graphNodes" :key="n.id" :class="['w-20 h-20 rounded-full border-2 flex items-center justify-center text-center p-1 cursor-pointer hover:scale-110 transition-transform', nodeColors[n.type]||'border-gray-400 bg-gray-800/50']" :title="n.description"><span class="text-[10px] text-white leading-tight">{{ n.name }}</span></div></div><p v-else class="text-white/50">搜索实体浏览图谱</p></div>
    </div>

    <!-- Feedback -->
    <div v-if="activeTab === 'feedback'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-surface-container-lowest rounded-xl border p-6"><h3 class="font-semibold mb-4">提交知识反馈</h3>
        <div class="space-y-3">
          <select v-model="fb.type" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm"><option value="knowledge_error">知识错误</option><option value="content_missing">内容缺失</option><option value="optimization">优化建议</option><option value="other">其他</option></select>
          <input v-model="fb.title" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="反馈标题*" /><textarea v-model="fb.content" class="w-full px-3 py-2 rounded-lg border border-outline-variant bg-surface text-sm" rows="4" placeholder="详细说明..."></textarea>
          <input v-model="fb.corrected_content" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="纠正内容(可选)" />
          <button @click="submitFb" class="w-full h-12 rounded-lg bg-primary text-on-primary text-sm font-medium shadow-md">提交反馈</button>
        </div>
      </div>
      <div class="bg-surface-container-lowest rounded-xl border overflow-hidden"><h3 class="font-semibold p-4 border-b">我的反馈记录</h3>
        <table class="w-full text-sm"><thead><tr class="bg-surface border-b"><th class="p-3 text-xs uppercase text-on-surface-variant">标题</th><th class="p-3 text-xs uppercase text-on-surface-variant">类型</th><th class="p-3 text-xs uppercase text-on-surface-variant">状态</th><th class="p-3 text-xs uppercase text-on-surface-variant">时间</th></tr></thead>
        <tbody><tr v-if="fbList.length===0"><td colspan="4" class="p-6 text-center">暂无反馈</td></tr>
          <tr v-for="f in fbList" :key="f.feedback_id" class="border-b"><td class="p-3 truncate max-w-[150px]">{{ f.title }}</td><td class="p-3 text-xs text-on-surface-variant">{{ typeMap[f.type]||f.type }}</td><td class="p-3"><span class="px-2 py-0.5 rounded-full text-xs" :class="f.status==='resolved'?'bg-secondary-container text-on-secondary-container':'bg-tertiary-container text-on-tertiary'">{{ f.status==='resolved'?'已解决':'待处理' }}</span></td><td class="p-3 text-xs text-on-surface-variant">{{ f.created_at?.slice(0,10) }}</td></tr>
        </tbody></table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { doctorApi } from '@/api/doctor'
import { commonApi } from '@/api/common'

const activeTab = ref('knowledge'); const tabs = [{key:'knowledge',label:'知识检索'},{key:'drugs',label:'药品相互作用'},{key:'graph',label:'知识图谱浏览'},{key:'feedback',label:'知识反馈'}]
const typeMap: Record<string,string> = {knowledge_error:'知识错误',content_missing:'内容缺失',optimization:'优化建议',other:'其他'}
const nodeColors: Record<string,string> = {disease:'border-blue-400 bg-blue-900/50',symptom:'border-red-400 bg-red-900/50',drug:'border-emerald-400 bg-emerald-900/50',department:'border-purple-400 bg-purple-900/50'}
const kqQuery = ref(''); const kqType = ref(''); const kqResults = ref<any[]>([])
const drugInput = ref(''); const drugList = ref<string[]>([]); const drugResults = ref<any[]>([])
const entityKeyword = ref(''); const entityType = ref(''); const entityResults = ref<any[]>([]); const graphNodes = ref<any[]>([])
const fb = reactive({type:'knowledge_error',title:'',content:'',corrected_content:''}); const fbList = ref<any[]>([])

async function searchKnowledge() { if (!kqQuery.value) return; try { const res = await doctorApi.queryKnowledge(kqQuery.value, kqType.value||undefined); if (res.code===200) kqResults.value = res.data.results||[] } catch {} }
function addDrug() { const v = drugInput.value.trim(); if (v && !drugList.value.includes(v)) drugList.value.push(v); drugInput.value = '' }
async function checkInteractions() { try { const res = await doctorApi.checkDrugInteraction(undefined, drugList.value); if (res.code===200) drugResults.value = res.data.interactions||[] } catch {} }
async function searchEntities() { if (!entityKeyword.value) return; try { const res = await commonApi.searchEntities(entityKeyword.value, entityType.value||undefined); if (res.code===200) entityResults.value = res.data||[] } catch {} }
async function loadGraph(name: string) { try { const res = await commonApi.getDiseaseGraph(name); if (res.code===200) graphNodes.value = res.data.nodes||[] } catch {} }
async function submitFb() { if (!fb.title || !fb.content) { alert('请填写标题和内容'); return }; try { await doctorApi.submitFeedback(fb); alert('提交成功'); fb.title=''; fb.content=''; loadFbList() } catch (e: any) { alert('提交失败: '+e.message) } }
async function loadFbList() { try { const res = await doctorApi.getFeedbackList(); if (res.code===200) fbList.value = res.data.list } catch {} }
onMounted(loadFbList)
</script>
