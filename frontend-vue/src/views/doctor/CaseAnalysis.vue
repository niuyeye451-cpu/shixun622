<template>
  <div class="h-full flex flex-col md:flex-row overflow-hidden p-4 gap-4">
    <!-- ===== LEFT: Clinical Feature Entry (30%) ===== -->
    <aside class="w-full md:w-[380px] xl:w-[420px] flex flex-col bg-surface-container-lowest rounded-xl border border-surface-variant flex-shrink-0">
      <div class="p-4 border-b flex items-center gap-2">
        <span class="material-symbols-outlined text-primary">assignment</span>
        <h2 class="font-semibold">临床特征录入</h2>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- Patient Demographics -->
        <div>
          <label class="text-xs text-on-surface-variant uppercase font-semibold tracking-wider">患者基本信息</label>
          <div class="grid grid-cols-2 gap-3 mt-2">
            <div>
              <span class="text-xs text-outline">年龄</span>
              <input v-model.number="form.age" type="number" min="0" max="150"
                class="w-full bg-surface-container px-3 py-2 rounded mt-0.5 text-sm border border-outline-variant focus:border-primary outline-none" />
            </div>
            <div>
              <span class="text-xs text-outline">性别</span>
              <select v-model="form.gender"
                class="w-full bg-surface-container px-3 py-2 rounded mt-0.5 text-sm border border-outline-variant focus:border-primary outline-none">
                <option value="">--</option>
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
            </div>
            <div class="col-span-2">
              <span class="text-xs text-outline">主诉</span>
              <input v-model="form.complaint"
                class="w-full bg-surface-container px-3 py-2 rounded mt-0.5 text-sm border border-outline-variant focus:border-primary outline-none"
                placeholder="例：反复胸痛3天，加重1天" />
            </div>
            <div class="col-span-2">
              <span class="text-xs text-outline">检验/检查结果</span>
              <textarea v-model="form.examResults" rows="2"
                class="w-full bg-surface-container px-3 py-2 rounded mt-0.5 text-sm border border-outline-variant focus:border-primary outline-none resize-none"
                placeholder="例：血压160/95mmHg，心电图ST段压低" />
            </div>
          </div>
        </div>

        <!-- Symptoms Tags -->
        <ClinicalTagGroup
          title="临床症状"
          icon="symptoms"
          :items="form.symptoms"
          :suggestions="symptomSuggestions"
          placeholder="搜索添加症状..."
          color-class="bg-red-50 text-red-700 border-red-700/20"
          @add="(v) => form.symptoms.push(v)"
          @remove="(i) => form.symptoms.splice(i, 1)"
          @search="(kw) => searchEntities(kw, 'symptom')"
        />

        <!-- Diagnoses Tags -->
        <ClinicalTagGroup
          title="当前诊断 (ICD-10)"
          icon="clinical_notes"
          :items="form.diagnoses"
          :suggestions="diagnosisSuggestions"
          placeholder="搜索添加诊断..."
          color-class="bg-primary-fixed text-on-primary-fixed-variant border-primary/20"
          @add="(v) => form.diagnoses.push(v)"
          @remove="(i) => form.diagnoses.splice(i, 1)"
          @search="(kw) => searchEntities(kw, 'disease')"
        />

        <!-- Medications Tags -->
        <ClinicalTagGroup
          title="在用药物"
          icon="medication"
          :items="form.medications"
          :suggestions="drugSuggestions"
          placeholder="搜索添加药品+剂量..."
          color-class="bg-emerald-50 text-emerald-700 border-emerald-700/20"
          @add="(v) => form.medications.push(v)"
          @remove="(i) => form.medications.splice(i, 1)"
          @search="(kw) => searchEntities(kw, 'drug')"
        />
      </div>

      <!-- Action Buttons -->
      <div class="p-4 border-t bg-surface-container-lowest rounded-b-xl space-y-2">
        <button @click="runDrugInteraction" :disabled="analyzing"
          class="w-full bg-primary hover:bg-primary/90 text-on-primary text-sm font-medium py-3 rounded-lg flex items-center justify-center gap-2 shadow-md transition-all active:scale-95 disabled:opacity-50">
          <span v-if="analyzing === 'drug'" class="material-symbols-outlined animate-spin text-lg">progress_activity</span>
          <span v-else class="material-symbols-outlined text-lg">science</span>
          {{ analyzing === 'drug' ? '分析中...' : '联合用药安全分析' }}
        </button>
        <div class="flex gap-2">
          <button @click="runDifferentialDiagnosis" :disabled="!!analyzing"
            class="flex-1 bg-secondary/10 hover:bg-secondary/20 text-secondary text-sm font-medium py-2.5 rounded-lg flex items-center justify-center gap-1 transition-all active:scale-95 disabled:opacity-50">
            <span v-if="analyzing === 'diff'" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
            <span v-else class="material-symbols-outlined text-sm">psychology</span>
            鉴别诊断
          </button>
          <button @click="runMultiSymptomAnalysis" :disabled="!!analyzing"
            class="flex-1 bg-tertiary/10 hover:bg-tertiary/20 text-tertiary text-sm font-medium py-2.5 rounded-lg flex items-center justify-center gap-1 transition-all active:scale-95 disabled:opacity-50">
            <span v-if="analyzing === 'multi'" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
            <span v-else class="material-symbols-outlined text-sm">account_tree</span>
            多症状分析
          </button>
        </div>
      </div>
    </aside>

    <!-- ===== RIGHT: Graph + Results (70%) ===== -->
    <section class="flex-1 flex flex-col gap-4 min-w-0">
      <!-- Multi-hop Reasoning Graph -->
      <div class="flex-[5] bg-surface-container-lowest rounded-xl border border-surface-variant overflow-hidden flex flex-col relative">
        <div class="absolute top-3 left-3 glass-panel z-10 flex items-center gap-3 flex-wrap">
          <h3 class="text-sm font-semibold flex items-center gap-1">
            <span class="material-symbols-outlined text-primary text-lg">account_tree</span>
            多跳推理图谱
          </h3>
          <div v-if="graphData" class="flex gap-2 text-[10px]">
            <span class="text-outline">{{ graphData.nodes?.length || 0 }} 实体 · {{ graphData.edges?.length || 0 }} 关系</span>
            <button @click="resetGraph" class="text-primary hover:underline">重置</button>
          </div>
        </div>
        <div class="flex-1">
          <KnowledgeGraphCanvas
            v-if="graphData && graphData.nodes?.length"
            :graphData="graphData"
            @nodeClick="onNodeClick"
          />
          <div v-else class="flex-1 h-full flex items-center justify-center">
            <div class="text-center">
              <span class="material-symbols-outlined text-6xl text-outline/30 mb-3 block">account_tree</span>
              <p class="text-on-surface-variant text-sm">输入临床特征并启动分析<br/>图谱将展示疾病-症状-药物关联</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Results: Drug Risk Alerts + Differential Diagnosis + Multi-symptom -->
      <div class="flex-[4] flex flex-col bg-surface-container-lowest rounded-xl border border-surface-variant overflow-hidden">
        <!-- Tab bar -->
        <div class="flex-shrink-0 flex border-b bg-surface/50">
          <button v-for="t in resultTabs" :key="t.key" @click="activeResultTab = t.key"
            :class="['flex-1 py-2.5 text-sm font-medium transition-colors border-b-2 flex items-center justify-center gap-1', activeResultTab === t.key ? 'border-primary text-primary bg-surface-container-lowest' : 'border-transparent text-on-surface-variant']">
            <span class="material-symbols-outlined text-sm">{{ t.icon }}</span>{{ t.label }}
            <span v-if="t.count" class="text-[10px] px-1.5 py-0.5 rounded-full" :class="t.countClass">{{ t.count }}</span>
          </button>
        </div>

        <!-- Drug Interaction Panel -->
        <div v-if="activeResultTab === 'drug'" class="flex-1 overflow-y-auto p-3 space-y-2">
          <div v-if="drugInteractions.length" class="flex items-center justify-between mb-2">
            <span class="text-xs text-on-surface-variant">共 {{ drugInteractions.length }} 项相互作用</span>
            <div class="flex gap-1">
              <button @click="exportPDF" class="text-xs px-2 py-1 rounded bg-primary/10 text-primary hover:bg-primary/20 flex items-center gap-1">
                <span class="material-symbols-outlined text-xs">picture_as_pdf</span>导出PDF
              </button>
              <button @click="openFeedback" class="text-xs px-2 py-1 rounded bg-tertiary/10 text-tertiary hover:bg-tertiary/20 flex items-center gap-1">
                <span class="material-symbols-outlined text-xs">feedback</span>纠错反馈
              </button>
            </div>
          </div>
          <div v-for="(ix, i) in drugInteractions" :key="i"
            :class="['rounded-lg p-3 flex items-start gap-3 shadow-sm cursor-pointer transition-all hover:shadow-md', interactionCardClass(ix)]">
            <span class="material-symbols-outlined text-lg mt-0.5" :class="interactionIconClass(ix)">{{ interactionIcon(ix) }}</span>
            <div class="flex-1">
              <div class="flex justify-between items-start mb-1">
                <h4 class="text-sm font-bold" :class="interactionLabelClass(ix)">{{ ix.drug_a }} + {{ ix.drug_b }}</h4>
                <label class="flex items-center gap-2 text-xs text-outline cursor-pointer select-none">
                  <input type="checkbox" class="rounded text-primary text-sm" /> 已阅知
                </label>
              </div>
              <p class="text-sm text-on-surface-variant mb-1">{{ ix.description }}</p>
              <p class="text-xs text-outline"><span class="font-semibold">建议: </span>{{ ix.recommendation }}</p>
            </div>
          </div>
          <div v-if="!drugInteractions.length && !analyzing" class="flex-1 flex items-center justify-center p-8 text-on-surface-variant text-sm">
            点击"联合用药安全分析"按钮开始检查
          </div>
        </div>

        <!-- Differential Diagnosis Panel -->
        <div v-if="activeResultTab === 'diff'" class="flex-1 overflow-y-auto p-3 space-y-2">
          <div v-if="diffResults.length" class="text-xs text-on-surface-variant mb-2">共 {{ diffResults.length }} 种可能疾病</div>
          <div v-for="(d, i) in diffResults" :key="i"
            class="rounded-lg p-3 bg-surface-container-low border border-outline-variant/50 hover:border-primary/30 transition-colors cursor-pointer"
            :class="{ 'border-primary/50 bg-primary/5': d.probability >= 0.7 }">
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-semibold flex items-center gap-2">
                <span class="text-sm">{{ i + 1 }}.</span>
                <span :class="d.probability >= 0.7 ? 'text-primary' : ''">{{ d.disease_name }}</span>
                <span :class="['text-xs px-1.5 py-0.5 rounded-full', d.probability >= 0.7 ? 'bg-error/10 text-error' : d.probability >= 0.5 ? 'bg-orange-100 text-orange-700' : 'bg-yellow-50 text-yellow-700']">
                  {{ (d.probability * 100).toFixed(0) }}%
                </span>
              </h4>
              <button @click="loadDiseaseGraph(d.disease_name)" class="text-xs text-primary hover:underline flex items-center gap-0.5">
                <span class="material-symbols-outlined text-xs">account_tree</span>图谱
              </button>
            </div>
            <div class="flex flex-wrap gap-2 text-xs mb-2">
              <span class="px-2 py-0.5 rounded-full bg-surface-container-highest">
                <span class="text-outline">典型发病: </span>{{ d.typical_onset || '--' }}
              </span>
              <span class="px-2 py-0.5 rounded-full bg-surface-container-highest">
                <span class="text-outline">关键检查: </span>{{ d.key_examination || '--' }}
              </span>
            </div>
            <div class="text-xs">
              <p v-if="d.supporting_symptoms?.length"><span class="text-secondary font-medium">支持症状: </span>
                <span v-for="s in d.supporting_symptoms" :key="s" class="inline-block px-1.5 py-0.5 bg-secondary/10 text-secondary rounded mr-1 mb-1">{{ s }}</span>
              </p>
              <p v-if="d.conflicting_symptoms?.length" class="mt-1"><span class="text-error font-medium">矛盾症状: </span>
                <span v-for="s in d.conflicting_symptoms" :key="s" class="inline-block px-1.5 py-0.5 bg-error/10 text-error rounded mr-1 mb-1">{{ s }}</span>
              </p>
            </div>
            <p class="text-xs text-on-surface-variant mt-2">治疗原则: {{ d.treatment_principle || '--' }}</p>
          </div>
          <div v-if="diffResults.length && diffSummary.recommended_next_step" class="rounded-lg p-3 bg-primary/5 border border-primary/20 mt-3">
            <p class="text-sm font-semibold text-primary mb-1">临床建议</p>
            <p class="text-sm">{{ diffSummary.recommended_next_step }}</p>
            <p v-if="diffSummary.emergency_flag" class="text-sm text-error font-bold mt-1">⚠️ 需紧急处理</p>
          </div>
          <div v-if="!diffResults.length && !analyzing" class="flex-1 flex items-center justify-center p-8 text-on-surface-variant text-sm">
            点击"鉴别诊断"按钮，基于临床症状进行疾病鉴别
          </div>
        </div>

        <!-- Multi-symptom Analysis Panel -->
        <div v-if="activeResultTab === 'multi'" class="flex-1 overflow-y-auto p-3 space-y-2">
          <div v-if="multiSymptomResults.length">
            <div class="text-xs text-on-surface-variant mb-2">关联分析结果</div>
            <div v-for="(d, i) in multiSymptomResults" :key="i"
              class="rounded-lg p-3 bg-surface-container-low border border-outline-variant/50 hover:border-primary/30 transition-colors mb-2">
              <div class="flex items-center justify-between mb-2">
                <h4 class="font-semibold text-sm">{{ d.disease_name }}</h4>
                <button @click="loadDiseaseGraph(d.disease_name)" class="text-xs text-primary hover:underline flex items-center gap-0.5">
                  <span class="material-symbols-outlined text-xs">account_tree</span>查看图谱
                </button>
              </div>
              <p v-if="d.description" class="text-xs text-on-surface-variant mb-2">{{ d.description?.slice(0, 200) }}</p>
              <div class="flex flex-wrap gap-1 text-xs">
                <span v-if="d.related_symptoms?.length" class="px-2 py-0.5 rounded bg-red-50 text-red-600">
                  症状: {{ d.related_symptoms.map((s: any) => s.name).join(', ') }}
                </span>
                <span v-if="d.related_drugs?.length" class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-600">
                  药物: {{ d.related_drugs.map((s: any) => s.name).join(', ') }}
                </span>
                <span v-if="d.related_treatments?.length" class="px-2 py-0.5 rounded bg-blue-50 text-blue-600">
                  治疗: {{ d.related_treatments.map((s: any) => s.name).join(', ') }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="!multiSymptomResults.length && !analyzing" class="flex-1 flex items-center justify-center p-8 text-on-surface-variant text-sm">
            点击"多症状分析"按钮，基于多个诊断名称进行关联分析
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { doctorApi } from '@/api/doctor'
import { commonApi } from '@/api/common'
import KnowledgeGraphCanvas from '@/components/graph/KnowledgeGraphCanvas.vue'
import ClinicalTagGroup from '@/components/common/ClinicalTagGroup.vue'

// ---- Refs & Form State ----
const form = reactive({
  age: 68,
  gender: '男',
  complaint: '反复胸痛3天，加重1天',
  examResults: '血压160/95mmHg，心电图示ST段压低',
  symptoms: ['胸痛', '心悸', '呼吸困难'] as string[],
  diagnoses: ['2型糖尿病', '原发性高血压(3级)', '高脂血症'] as string[],
  medications: ['二甲双胍 500mg', '氨氯地平 5mg', '辛伐他汀 20mg', '胺碘酮 200mg'] as string[],
})

const analyzing = ref<string | false>(false)
const activeResultTab = ref('drug')
const graphData = ref<any>(null)

// Drug interaction results
const drugInteractions = ref<any[]>([])

// Differential diagnosis results
const diffResults = ref<any[]>([])
const diffSummary = reactive({ recommended_next_step: '', emergency_flag: false })

// Multi-symptom analysis results
const multiSymptomResults = ref<any[]>([])

// Search suggestions
const symptomSuggestions = ref<string[]>([])
const diagnosisSuggestions = ref<string[]>([])
const drugSuggestions = ref<string[]>([])
let searchTimer: ReturnType<typeof setTimeout> | null = null

// ---- Computed ----
const resultTabs = computed(() => [
  { key: 'drug', label: '用药风险', icon: 'warning', count: drugInteractions.value.length, countClass: drugInteractions.value.length ? 'bg-error/10 text-error' : '' },
  { key: 'diff', label: '鉴别诊断', icon: 'psychology', count: diffResults.value.length, countClass: diffResults.value.length ? 'bg-primary/10 text-primary' : '' },
  { key: 'multi', label: '多症状', icon: 'account_tree', count: multiSymptomResults.value.length, countClass: multiSymptomResults.value.length ? 'bg-tertiary/10 text-tertiary' : '' },
])

// ---- Entity Autocomplete ----
async function searchEntities(keyword: string, entityType: string) {
  if (!keyword || keyword.length < 1) { clearSuggestions(entityType); return }
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const res = await commonApi.searchEntities(keyword, entityType, 6)
      if (res.code === 200) {
        const items = (res.data as any).entities?.map((e: any) => e.name) || []
        setSuggestions(entityType, items)
      }
    } catch { /* ignore */ }
  }, 300)
}

function clearSuggestions(type: string) {
  if (type === 'symptom') symptomSuggestions.value = []
  else if (type === 'disease') diagnosisSuggestions.value = []
  else if (type === 'drug') drugSuggestions.value = []
}

function setSuggestions(type: string, items: string[]) {
  if (type === 'symptom') symptomSuggestions.value = items
  else if (type === 'disease') diagnosisSuggestions.value = items
  else if (type === 'drug') drugSuggestions.value = items
}

// ---- Analysis Actions ----
async function runDrugInteraction() {
  const drugNames = form.medications.map(m => m.split(' ')[0]).filter(Boolean)
  if (drugNames.length < 2) { alert('至少需要2种药物进行相互作用分析'); return }
  analyzing.value = 'drug'
  activeResultTab.value = 'drug'
  try {
    const res = await doctorApi.checkDrugInteraction(undefined, drugNames)
    if (res.code === 200) drugInteractions.value = res.data.interactions || []
    // Also load graph
    await loadInteractionGraph(drugNames)
  } catch (e: any) { alert('分析失败: ' + e.message) }
  finally { analyzing.value = false }
}

async function runDifferentialDiagnosis() {
  if (!form.complaint && !form.symptoms.length) { alert('请先填写主诉或临床症状'); return }
  analyzing.value = 'diff'
  activeResultTab.value = 'diff'
  try {
    const res = await doctorApi.differentialDiagnosis(
      form.complaint,
      form.symptoms,
      { age: form.age, gender: form.gender, exam_results: form.examResults },
      {}
    )
    if (res.code === 200) {
      diffResults.value = res.data.differential_list || []
      diffSummary.recommended_next_step = res.data.recommended_next_step || ''
      diffSummary.emergency_flag = !!res.data.emergency_flag
    }
  } catch (e: any) { alert('分析失败: ' + e.message) }
  finally { analyzing.value = false }
}

async function runMultiSymptomAnalysis() {
  if (!form.diagnoses.length) { alert('请先添加诊断'); return }
  analyzing.value = 'multi'
  activeResultTab.value = 'multi'
  try {
    const res = await doctorApi.analyzeMultiSymptom(form.diagnoses, form.symptoms, 3)
    if (res.code === 200) {
      multiSymptomResults.value = res.data.results || []
    }
  } catch (e: any) { alert('分析失败: ' + e.message) }
  finally { analyzing.value = false }
}

// ---- Graph Loading ----
async function loadInteractionGraph(drugNames: string[]) {
  if (!drugNames.length) return
  try {
    const nodes: any[] = []; const nodeIds = new Set<string>(); const edges: any[] = []; let edgeId = 0
    for (const drugName of drugNames) {
      const res = await commonApi.searchEntities(drugName, 'drug', 1)
      if (res.code === 200) {
        const entities = (res.data as any).entities || []
        for (const e of entities) {
          if (!nodeIds.has(e.entity_id)) {
            nodeIds.add(e.entity_id)
            nodes.push({ id: e.entity_id, name: e.name, type: 'drug', description: e.description })
          }
        }
      }
    }
    // Add interactions as edges
    for (const ix of drugInteractions.value) {
      const drugA = nodes.find(n => n.name === ix.drug_a)
      const drugB = nodes.find(n => n.name === ix.drug_b)
      if (drugA && drugB && ix.level === 'warning') {
        edges.push({ id: `edge_${edgeId++}`, source: drugA.id, target: drugB.id, relation: 'contraindication', relation_name: '配伍禁忌' })
      }
    }
    if (nodes.length) {
      graphData.value = { nodes, edges, center_node: nodes[0]?.id }
    }
  } catch { /* ignore */ }
}

async function loadDiseaseGraph(diseaseName: string) {
  try {
    const res = await commonApi.getDiseaseGraph(diseaseName, 2)
    if (res.code === 200) {
      graphData.value = res.data
    }
  } catch { alert('加载图谱失败') }
}

function onNodeClick(node: any) {
  loadDiseaseGraph(node.name)
}

function resetGraph() {
  graphData.value = null
}

// ---- Interaction Card Helpers ----
function interactionCardClass(ix: any) {
  if (ix.level === 'warning') return 'bg-surface-container-lowest border-l-4 border-error'
  if (ix.severity === '中') return 'bg-surface-container-lowest border-l-4 border-orange-600'
  return 'bg-surface-container-lowest border-l-4 border-yellow-500'
}

function interactionIconClass(ix: any) {
  if (ix.level === 'warning') return 'text-error'
  if (ix.severity === '中') return 'text-orange-600'
  return 'text-yellow-600'
}

function interactionLabelClass(ix: any) {
  if (ix.level === 'warning') return 'text-error'
  if (ix.severity === '中') return 'text-orange-600'
  return 'text-yellow-600'
}

function interactionIcon(ix: any) {
  if (ix.level === 'warning') return 'block'
  return 'warning_amber'
}

// ---- PDF Export & Feedback ----
function exportPDF() {
  window.print()
}

function openFeedback() {
  const fbContent = `用药相互作用分析反馈\n药品: ${form.medications.join(', ')}\n发现 ${drugInteractions.value.length} 项相互作用`
  doctorApi.submitFeedback({
    type: 'knowledge_error',
    title: '联合用药安全分析反馈',
    content: fbContent,
    related_entity_id: undefined,
    references: [],
  } as any).then(res => {
    if (res.code === 200) alert('反馈已提交，感谢您的贡献！')
  }).catch(() => alert('提交失败，请重试'))
}
</script>

<style scoped>
.glass-panel {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 8px 12px;
  border-radius: 8px;
}
</style>
