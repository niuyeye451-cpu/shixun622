<template>
  <div class="h-full overflow-y-auto p-[16px] md:p-[40px] max-w-6xl mx-auto">
    <div class="flex gap-2 mb-6 border-b border-outline-variant overflow-x-auto">
      <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key" :class="['px-4 py-2 rounded-t-lg text-sm font-medium border-b-2 transition-colors whitespace-nowrap', activeTab === tab.key ? 'border-primary text-primary bg-surface-container-lowest' : 'border-transparent text-on-surface-variant']">{{ tab.label }}</button>
    </div>

    <!-- Profile Tab -->
    <div v-if="activeTab === 'profile'" class="bg-surface-container-lowest rounded-xl border border-outline-variant p-6 max-w-2xl">
      <h2 class="text-xl font-semibold mb-6 flex items-center gap-2"><span class="material-symbols-outlined text-primary">badge</span> 个人资料</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-on-surface-variant font-semibold">用户名</label>
          <input v-model="profile.user_name" class="w-full h-12 px-3 mt-1 rounded-lg border border-outline-variant bg-surface focus:border-primary outline-none" />
        </div>
        <div>
          <label class="text-xs text-on-surface-variant font-semibold">手机号</label>
          <input :value="profile.phone" disabled class="w-full h-12 px-3 mt-1 rounded-lg border border-outline-variant bg-surface-container text-on-surface-variant" />
        </div>
        <div>
          <label class="text-xs text-on-surface-variant font-semibold">性别</label>
          <select v-model="profile.gender" class="w-full h-12 px-3 mt-1 rounded-lg border border-outline-variant bg-surface focus:border-primary outline-none">
            <option value="">请选择</option>
            <option value="male">男</option>
            <option value="female">女</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-on-surface-variant font-semibold">年龄</label>
          <input v-model.number="profile.age" type="number" class="w-full h-12 px-3 mt-1 rounded-lg border border-outline-variant bg-surface focus:border-primary outline-none" />
        </div>
        <div>
          <label class="text-xs text-on-surface-variant font-semibold">血型</label>
          <select v-model="profile.blood_type" class="w-full h-12 px-3 mt-1 rounded-lg border border-outline-variant bg-surface focus:border-primary outline-none">
            <option value="">请选择</option><option value="A">A型</option><option value="B">B型</option><option value="AB">AB型</option><option value="O">O型</option>
          </select>
        </div>
        <div class="md:col-span-2">
          <label class="text-xs text-on-surface-variant font-semibold">地址</label>
          <input v-model="profile.address" class="w-full h-12 px-3 mt-1 rounded-lg border border-outline-variant bg-surface focus:border-primary outline-none" />
        </div>
      </div>
      <button @click="saveProfile" class="w-40 h-12 mt-6 rounded-lg bg-primary text-on-primary text-sm font-medium shadow-md hover:bg-primary/90 flex items-center justify-center gap-1">
        <span class="material-symbols-outlined text-lg">save</span> 保存修改
      </button>
    </div>

    <!-- History Tab -->
    <div v-if="activeTab === 'history'" class="bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden">
      <div class="p-3 border-b flex justify-between">
        <input v-model="historyKeyword" @input="loadHistory" class="w-48 h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="搜索..." />
      </div>
      <table class="w-full text-left text-sm">
        <thead><tr class="bg-surface border-b"><th class="p-3 text-xs text-on-surface-variant uppercase">日期</th><th class="p-3 text-xs text-on-surface-variant uppercase">咨询内容</th><th class="p-3 text-xs text-on-surface-variant uppercase">匹配疾病</th><th class="p-3 text-xs text-on-surface-variant uppercase">推荐科室</th></tr></thead>
        <tbody>
          <tr v-if="history.length === 0"><td colspan="4" class="p-6 text-center text-on-surface-variant">暂无记录</td></tr>
          <tr v-for="h in history" :key="h.consultation_id" class="border-b hover:bg-surface-container/50 transition-colors">
            <td class="p-3 text-on-surface-variant">{{ h.created_at?.slice(0, 10) }}</td>
            <td class="p-3 text-on-surface truncate max-w-[200px]">{{ h.symptom_text || '-' }}</td>
            <td class="p-3">{{ h.matched_disease || '-' }}</td>
            <td class="p-3 text-on-surface-variant">{{ h.matched_department || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Registrations Tab -->
    <div v-if="activeTab === 'registrations'" class="bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden">
      <div class="p-3 border-b flex gap-2">
        <select v-model="regStatusFilter" @change="loadRegistrations" class="h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm">
          <option value="">全部</option><option value="confirmed">已确认</option><option value="cancelled">已取消</option>
        </select>
      </div>
      <table class="w-full text-left text-sm">
        <thead><tr class="bg-surface border-b"><th class="p-3 text-xs text-on-surface-variant uppercase">日期</th><th class="p-3 text-xs text-on-surface-variant uppercase">医生</th><th class="p-3 text-xs text-on-surface-variant uppercase">科室</th><th class="p-3 text-xs text-on-surface-variant uppercase">时段</th><th class="p-3 text-xs text-on-surface-variant uppercase">状态</th><th class="p-3 text-xs text-on-surface-variant uppercase">操作</th></tr></thead>
        <tbody>
          <tr v-if="registrations.length === 0"><td colspan="6" class="p-6 text-center text-on-surface-variant">暂无记录</td></tr>
          <tr v-for="r in registrations" :key="r.registration_id" class="border-b hover:bg-surface-container/50 transition-colors">
            <td class="p-3">{{ r.date }}</td><td class="p-3">{{ r.doctor_name }}</td>
            <td class="p-3">{{ r.department }}</td><td class="p-3">{{ r.time_period }}</td>
            <td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', r.status === 'confirmed' ? 'bg-secondary-container text-on-secondary-container' : 'bg-error-container text-on-error-container']">{{ r.status === 'confirmed' ? '已确认' : '已取消' }}</span></td>
            <td class="p-3"><button v-if="r.status === 'confirmed'" @click="cancelReg(r.registration_id)" class="text-error text-xs">取消</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Appointment Tab -->
    <div v-if="activeTab === 'appointment'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-surface-container-lowest rounded-xl border p-6">
        <h3 class="font-semibold mb-4 flex items-center gap-1"><span class="material-symbols-outlined text-primary">search</span> 选择科室</h3>
        <div class="space-y-2">
          <div v-for="d in departments" :key="d.department_id" @click="selectDept(d.department_id)" class="flex justify-between items-center p-3 rounded-lg border hover:bg-surface-container transition-colors cursor-pointer">
            <span class="font-medium text-sm">{{ d.department_name }}</span>
            <span class="material-symbols-outlined text-outline">chevron_right</span>
          </div>
        </div>
      </div>
      <div class="bg-surface-container-lowest rounded-xl border p-6">
        <h3 class="font-semibold mb-4 flex items-center gap-1"><span class="material-symbols-outlined text-primary">person_search</span> 选择医生</h3>
        <div v-if="selectedDeptId" class="space-y-2 mb-4">
          <div v-for="d in doctors" :key="d.doctor_id" @click="selectDoctor(d)" class="p-3 rounded-lg border hover:bg-surface-container transition-colors cursor-pointer">
            <p class="font-medium text-sm">{{ d.doctor_name }} <span class="text-xs text-on-surface-variant">{{ d.title }}</span></p>
            <p class="text-xs text-on-surface-variant">{{ d.hospital }} | {{ d.specialty }}</p>
          </div>
        </div>
        <div v-if="selectedDoctor" class="border-t pt-4">
          <input v-model="aptForm.patient_name" class="w-full h-12 px-3 mb-3 rounded-lg border focus:border-primary outline-none text-sm" placeholder="姓名*" />
          <input v-model="aptForm.id_card" class="w-full h-12 px-3 mb-3 rounded-lg border focus:border-primary outline-none text-sm" placeholder="身份证号*" />
          <input v-model="aptForm.phone" class="w-full h-12 px-3 mb-3 rounded-lg border focus:border-primary outline-none text-sm" placeholder="电话*" />
          <textarea v-model="aptForm.symptom_description" class="w-full px-3 py-2 mb-4 rounded-lg border focus:border-primary outline-none text-sm" rows="2" placeholder="症状描述(可选)"></textarea>
          <button @click="submitAppointment" class="w-full h-12 rounded-lg bg-primary text-on-primary text-sm font-medium shadow-md">确认预约</button>
        </div>
        <p v-if="!selectedDeptId" class="text-center text-on-surface-variant p-6">请先选择科室</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { patientApi } from '@/api/patient'
import { commonApi } from '@/api/common'

const activeTab = ref('profile')
const tabs = [
  { key: 'profile', label: '个人信息' }, { key: 'history', label: '咨询记录' },
  { key: 'registrations', label: '挂号记录' }, { key: 'appointment', label: '预约挂号' },
]

// Profile
const profile = reactive<any>({ user_name: '', phone: '', gender: '', age: null, blood_type: '', address: '' })
const history = ref<any[]>([])
const historyKeyword = ref('')
const registrations = ref<any[]>([])
const regStatusFilter = ref('')
const departments = ref<any[]>([])
const doctors = ref<any[]>([])
const selectedDeptId = ref('')
const selectedDoctor = ref<any>(null)
const aptForm = reactive({ patient_name: '', id_card: '', phone: '', symptom_description: '' })

onMounted(async () => {
  try {
    const res = await patientApi.getProfile()
    if (res.code === 200) Object.assign(profile, res.data)
  } catch {}
  loadHistory()
  loadRegistrations()
  try {
    const res = await commonApi.getDepartments()
    if (res.code === 200) departments.value = res.data
  } catch {}
})

async function saveProfile() {
  try {
    await patientApi.updateProfile(profile)
    alert('保存成功')
  } catch (e: any) { alert('保存失败: ' + e.message) }
}

async function loadHistory() {
  try {
    const res = await patientApi.getConsultationHistory({ keyword: historyKeyword.value, page: 1, page_size: 50 })
    if (res.code === 200) history.value = res.data.list
  } catch {}
}

async function loadRegistrations() {
  try {
    const res = await patientApi.getRegistrations(regStatusFilter.value || undefined)
    if (res.code === 200) registrations.value = res.data.list
  } catch {}
}

async function cancelReg(id: string) {
  if (!confirm('确定取消？')) return
  try { await patientApi.cancelRegistration(id); loadRegistrations() } catch {}
}

async function selectDept(id: string) {
  selectedDeptId.value = id
  selectedDoctor.value = null
  try {
    const res = await patientApi.recommendDoctors(id)
    if (res.code === 200) doctors.value = res.data.list
  } catch {}
}

function selectDoctor(d: any) {
  selectedDoctor.value = d
  aptForm.phone = profile.phone || ''
  aptForm.patient_name = profile.user_name || ''
}

async function submitAppointment() {
  if (!aptForm.patient_name || !aptForm.id_card || !aptForm.phone) { alert('请填写必填信息'); return }
  try {
    const res = await patientApi.register({
      slot_id: 'slot_001', doctor_id: selectedDoctor.value.doctor_id,
      hospital_id: 'hosp_001', department_id: selectedDeptId.value,
      patient_name: aptForm.patient_name, id_card: aptForm.id_card,
      phone: aptForm.phone, symptom_description: aptForm.symptom_description,
    })
    if (res.code === 200) { alert('预约成功'); activeTab.value = 'registrations'; loadRegistrations() }
  } catch (e: any) { alert('预约失败: ' + e.message) }
}
</script>
