<template>
  <div class="h-full flex flex-col md:flex-row overflow-hidden p-4 gap-4">
    <!-- Left: Clinical Features (30%) -->
    <aside class="w-full md:w-[350px] xl:w-[400px] flex flex-col bg-surface-container-lowest rounded-xl border border-surface-variant flex-shrink-0">      <div class="p-4 border-b flex items-center gap-2">
        <span class="material-symbols-outlined text-primary">assignment</span>
        <h2 class="font-semibold">临床特征录入</h2>
      </div>
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <div>
          <label class="text-xs text-on-surface-variant uppercase font-semibold tracking-wider">患者基本信息</label>
          <div class="grid grid-cols-2 gap-3 mt-2">
            <div><span class="text-xs text-outline">年龄</span><div class="bg-surface-container px-3 py-1.5 rounded mt-0.5 text-sm">{{ patientInfo.age || '-' }}岁</div></div>
            <div><span class="text-xs text-outline">性别</span><div class="bg-surface-container px-3 py-1.5 rounded mt-0.5 text-sm">{{ patientInfo.gender || '-' }}</div></div>
            <div class="col-span-2"><span class="text-xs text-outline">主诉</span><div class="bg-surface-container px-3 py-1.5 rounded mt-0.5 text-sm">{{ patientInfo.complaint || '-' }}</div></div>
          </div>
        </div>
        <div>
          <label class="text-xs text-on-surface-variant uppercase font-semibold tracking-wider flex justify-between">当前诊断 (ICD-10) <button @click="addTag('diagnosis')" class="text-primary"><span class="material-symbols-outlined text-sm">add</span></button></label>
          <div class="flex flex-wrap gap-1 mt-2">
            <span v-for="(d,i) in diagnoses" :key="i" class="inline-flex items-center gap-1 bg-primary-fixed text-on-primary-fixed-variant px-2 py-1 rounded-full text-xs border border-primary/20">{{ d }}<button @click="diagnoses.splice(i,1)" class="material-symbols-outlined text-xs hover:text-primary">close</button></span>
          </div>
        </div>
        <div>
          <label class="text-xs text-on-surface-variant uppercase font-semibold tracking-wider flex justify-between">在用药物 <button @click="addTag('med')" class="text-primary"><span class="material-symbols-outlined text-sm">add</span></button></label>
          <div class="flex flex-wrap gap-1 mt-2">
            <span v-for="(m,i) in medications" :key="i" class="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 px-2 py-1 rounded-full text-xs border border-emerald-700/20">{{ m }}<button @click="medications.splice(i,1)" class="material-symbols-outlined text-xs hover:text-emerald-900">close</button></span>
          </div>
        </div>
      </div>
      <div class="p-4 border-t bg-surface-container-lowest rounded-b-xl">
        <button @click="runAnalysis" :disabled="analyzing" class="w-full bg-primary hover:bg-primary-container text-on-primary text-sm font-medium py-3 rounded-lg flex items-center justify-center gap-2 shadow-md transition-all active:scale-95 disabled:opacity-50">
          <span v-if="analyzing" class="material-symbols-outlined animate-spin text-lg">progress_activity</span>
          <span v-else class="material-symbols-outlined text-lg">science</span>
          {{ analyzing ? '分析中...' : '启动联合用药安全分析' }}
        </button>
      </div>
    </aside>

    <!-- Right: Graph + Alerts (70%) -->
    <section class="flex-1 flex flex-col gap-4 min-w-0">
      <div class="flex-[3] bg-surface-container-lowest rounded-xl border border-surface-variant overflow-hidden flex flex-col relative" style="background-image:linear-gradient(to right,rgba(0,0,0,0.03) 1px,transparent 1px),linear-gradient(to bottom,rgba(0,0,0,0.03) 1px,transparent 1px);background-size:20px 20px;">
        <div class="absolute top-3 left-3 bg-white/85 backdrop-blur px-3 py-1.5 rounded shadow-sm z-10">
          <h3 class="text-sm font-semibold flex items-center gap-1"><span class="material-symbols-outlined text-primary text-lg">account_tree</span> 多跳推理图谱</h3>
        </div>
        <button @click="handleExportPDF" class="absolute top-3 right-3 bg-white/85 backdrop-blur p-2 rounded shadow-sm z-10 hover:bg-surface-container transition-colors text-on-surface-variant text-xs flex items-center gap-1" title="导出PDF报告">
          <span class="material-symbols-outlined text-lg">picture_as_pdf</span> 导出PDF
        </button>
        <div class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <span class="material-symbols-outlined text-6xl text-outline/30 mb-3 block">account_tree</span>
            <p class="text-on-surface-variant text-sm">输入临床特征后开始分析</p>
          </div>
        </div>
      </div>

      <div class="flex-[2] bg-surface-container-lowest rounded-xl border border-surface-variant overflow-hidden">
        <div class="p-3 border-b bg-surface/50 flex justify-between items-center">
          <h3 class="font-semibold flex items-center gap-2"><span class="material-symbols-outlined text-error">warning</span> 风险预警面板</h3>
          <span v-if="interactions.length" class="bg-error-container text-on-error-container text-xs px-2 py-1 rounded-full font-bold">{{ interactions.length }} 项冲突</span>
        </div>
        <div class="overflow-y-auto p-3 space-y-2" v-if="interactions.length">
          <div v-for="(ix, i) in interactions" :key="i" :class="['rounded-lg p-3 flex items-start gap-3 shadow-sm', ix.level === 'warning' ? 'bg-surface-container-lowest border-l-4 border-error' : ix.severity === '中' ? 'bg-surface-container-lowest border-l-4 border-orange-600' : 'bg-surface-container-lowest border-l-4 border-yellow-500']">
            <span class="material-symbols-outlined text-lg mt-0.5" :class="ix.level === 'warning' ? 'text-error' : 'text-orange-600'">{{ ix.level === 'warning' ? 'block' : 'warning_amber' }}</span>
            <div class="flex-1">
              <div class="flex justify-between items-start mb-1">
                <h4 class="text-sm font-bold" :class="ix.level === 'warning' ? 'text-error' : 'text-orange-600'">{{ ix.drug_a }} + {{ ix.drug_b }}</h4>
                <label class="flex items-center gap-2 text-xs text-outline cursor-pointer"><input type="checkbox" class="rounded text-primary text-sm" /> 已阅知</label>
              </div>
              <p class="text-sm text-on-surface-variant mb-2">{{ ix.description }}</p>
              <p class="text-xs text-outline">建议: {{ ix.recommendation }}</p>
            </div>
          </div>
        </div>
        <div v-else class="flex-1 flex items-center justify-center p-8 text-on-surface-variant text-sm">点击分析按钮开始药物相互作用检查</div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { doctorApi } from '@/api/doctor'

const patientInfo = reactive({ age: 68, gender: '男', complaint: '反复胸痛3天' })
const diagnoses = ref(['2型糖尿病', '原发性高血压(3级)', '高脂血症'])
const medications = ref(['二甲双胍 500mg', '氨氯地平 5mg', '辛伐他汀 20mg', '胺碘酮 200mg'])
const interactions = ref<any[]>([])
const analyzing = ref(false)
function handleExportPDF() { alert('PDF报告导出功能开发中（Phase 3）') }

function addTag(type: string) {
  const val = prompt(type === 'diagnosis' ? '添加诊断:' : '添加药物:')
  if (val) { if (type === 'diagnosis') diagnoses.value.push(val); else medications.value.push(val) }
}

async function runAnalysis() {
  if (medications.value.length < 2) { alert('至少需要2种药物'); return }
  analyzing.value = true
  try {
    const res = await doctorApi.checkDrugInteraction(undefined, medications.value.map(m => m.split(' ')[0]))
    if (res.code === 200) interactions.value = res.data.interactions || []
  } catch (e: any) { alert('分析失败: ' + e.message) }
  finally { analyzing.value = false }
}
</script>
