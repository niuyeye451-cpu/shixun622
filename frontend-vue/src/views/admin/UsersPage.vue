<template>
  <div class="h-full w-full flex flex-col overflow-y-auto p-[16px] md:p-[24px]">
    <h1 class="text-[24px] md:text-[32px] font-semibold text-on-background mb-[24px]">用户管理</h1>
    <div class="flex gap-2 mb-[24px] border-b border-outline-variant overflow-x-auto">
      <button v-for="t in tabs" :key="t.key" @click="activeTab=t.key" :class="['px-4 py-2 rounded-t-lg text-sm font-medium border-b-2 transition-colors', activeTab===t.key?'border-primary text-primary bg-surface-container-lowest':'border-transparent text-on-surface-variant']">{{ t.label }}</button>
    </div>

    <!-- Patients -->
    <div v-if="activeTab==='patients'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b"><input v-model="patSearch" @input="loadPatients" class="w-48 h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="搜索..." /></div>
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase text-on-surface-variant">用户名</th><th class="p-3 text-xs uppercase text-on-surface-variant">手机号</th><th class="p-3 text-xs uppercase text-on-surface-variant">性别</th><th class="p-3 text-xs uppercase text-on-surface-variant">年龄</th><th class="p-3 text-xs uppercase text-on-surface-variant">状态</th><th class="p-3 text-xs uppercase text-on-surface-variant text-right">操作</th></tr></thead>
      <tbody><tr v-if="patients.length===0"><td colspan="6" class="p-6 text-center text-on-surface-variant">加载中...</td></tr>
        <tr v-for="p in patients" :key="p.patient_id" class="border-b hover:bg-surface-container/50 cursor-pointer" @click="viewPatient(p.patient_id)"><td class="p-3 text-on-surface">{{ p.user_name }}</td><td class="p-3 text-on-surface-variant">{{ p.phone }}</td><td class="p-3 text-on-surface-variant">{{ p.gender==='male'?'男':p.gender==='female'?'女':'-' }}</td><td class="p-3 text-on-surface-variant">{{ p.age||'-' }}</td><td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', p.status===1?'bg-secondary-container text-on-secondary-container':'bg-error-container text-on-error-container']">{{ p.status===1?'正常':'禁用' }}</span></td>
        <td class="p-3 text-right" @click.stop><button @click="toggleStatus('patient',p.patient_id,p.status)" class="text-primary text-xs hover:underline">{{ p.status===1?'禁用':'启用' }}</button></td></tr>
      </tbody></table>
    </div>

    <!-- Doctors -->
    <div v-if="activeTab==='doctors'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b"><input v-model="docSearch" @input="loadDoctors" class="w-48 h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="搜索..." /></div>
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase text-on-surface-variant">用户名</th><th class="p-3 text-xs uppercase text-on-surface-variant">科室</th><th class="p-3 text-xs uppercase text-on-surface-variant">职称</th><th class="p-3 text-xs uppercase text-on-surface-variant">医院</th><th class="p-3 text-xs uppercase text-on-surface-variant">状态</th><th class="p-3 text-xs uppercase text-on-surface-variant text-right">操作</th></tr></thead>
      <tbody><tr v-if="doctors.length===0"><td colspan="6" class="p-6 text-center text-on-surface-variant">加载中...</td></tr>
        <tr v-for="d in doctors" :key="d.doctor_id" class="border-b hover:bg-surface-container/50 cursor-pointer" @click="viewDoctor(d.doctor_id)"><td class="p-3 text-on-surface">{{ d.user_name }}</td><td class="p-3 text-on-surface-variant">{{ d.department||'-' }}</td><td class="p-3 text-on-surface-variant">{{ d.title||'-' }}</td><td class="p-3 text-on-surface-variant">{{ d.hospital||'-' }}</td><td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', d.status===1?'bg-secondary-container text-on-secondary-container':'bg-error-container text-on-error-container']">{{ d.status===1?'正常':'禁用' }}</span></td>
        <td class="p-3 text-right" @click.stop><button @click="toggleStatus('doctor',d.doctor_id,d.status)" class="text-primary text-xs hover:underline">{{ d.status===1?'禁用':'启用' }}</button></td></tr>
      </tbody></table>
    </div>

    <!-- Admins -->
    <div v-if="activeTab==='admins'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase text-on-surface-variant">用户名</th><th class="p-3 text-xs uppercase text-on-surface-variant">手机号</th><th class="p-3 text-xs uppercase text-on-surface-variant">角色等级</th><th class="p-3 text-xs uppercase text-on-surface-variant">状态</th><th class="p-3 text-xs uppercase text-on-surface-variant">创建时间</th></tr></thead>
      <tbody><tr v-if="admins.length===0"><td colspan="5" class="p-6 text-center text-on-surface-variant">加载中...</td></tr>
        <tr v-for="a in admins" :key="a.admin_id" class="border-b hover:bg-surface-container/50"><td class="p-3 text-on-surface">{{ a.user_name }}</td><td class="p-3 text-on-surface-variant">{{ a.phone }}</td><td class="p-3 text-on-surface-variant">{{ a.role_level}}</td><td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', a.status===1?'bg-secondary-container text-on-secondary-container':'bg-error-container text-on-error-container']">{{ a.status===1?'正常':'禁用' }}</span></td><td class="p-3 text-xs text-on-surface-variant">{{ a.created_at?.slice(0,10) }}</td></tr>
      </tbody></table>
    </div>

    <!-- Add Doctor -->
    <div v-if="activeTab==='add-doctor'" class="bg-surface-container-lowest rounded-xl border p-6 max-w-xl">
      <h3 class="font-semibold text-on-surface mb-4">新增医师账号</h3>
      <div class="space-y-3">
        <input v-model="newDoc.user_name" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm focus:border-primary outline-none" placeholder="用户名*" />
        <input v-model="newDoc.phone" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm focus:border-primary outline-none" placeholder="手机号*" />
        <input v-model="newDoc.password_hash" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm focus:border-primary outline-none" placeholder="密码*" type="password" />
        <input v-model="newDoc.department" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm focus:border-primary outline-none" placeholder="科室" />
        <input v-model="newDoc.title" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm focus:border-primary outline-none" placeholder="职称" />
        <input v-model="newDoc.hospital" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm focus:border-primary outline-none" placeholder="医院" />
        <button @click="createDoctor" class="w-full h-12 rounded-lg bg-primary text-on-primary text-sm font-medium shadow-md hover:bg-primary/90 transition-all active:scale-95">创建医师</button>
      </div>
    </div>

    <!-- Patient Detail Modal -->
    <div v-if="pDetail" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="pDetail = null">
      <div class="bg-surface-container-lowest rounded-xl shadow-2xl border border-outline-variant max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto animate-fade-in">
        <div class="p-4 border-b flex justify-between items-center">
          <h3 class="font-semibold text-on-surface flex items-center gap-2"><span class="material-symbols-outlined text-primary">person</span> 患者详情</h3>
          <button @click="pDetail = null" class="p-1 rounded-full hover:bg-surface-container text-on-surface-variant"><span class="material-symbols-outlined">close</span></button>
        </div>
        <div class="p-4 space-y-3 text-sm">
          <div class="flex justify-between"><span class="text-on-surface-variant">用户名</span><span class="font-medium text-on-surface">{{ pDetail.user_name }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">手机号</span><span class="text-on-surface-variant">{{ pDetail.phone }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">性别</span><span>{{ pDetail.gender==='male'?'男':pDetail.gender==='female'?'女':'-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">年龄</span><span>{{ pDetail.age||'-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">血型</span><span>{{ pDetail.blood_type||'-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">地址</span><span class="text-right max-w-[60%] text-on-surface">{{ pDetail.address||'-' }}</span></div>
          <div><span class="text-on-surface-variant block mb-1">过敏史</span><div class="flex flex-wrap gap-1"><span v-for="a in (pDetail.allergy_history||[])" :key="a" class="px-2 py-0.5 rounded-full text-xs bg-error-container text-on-error-container">{{ a }}</span><span v-if="!(pDetail.allergy_history||[]).length" class="text-xs text-on-surface-variant">无</span></div></div>
          <div><span class="text-on-surface-variant block mb-1">既往病史</span><div class="flex flex-wrap gap-1"><span v-for="m in (pDetail.medical_history||[])" :key="m" class="px-2 py-0.5 rounded-full text-xs bg-tertiary-container text-on-tertiary">{{ m }}</span><span v-if="!(pDetail.medical_history||[]).length" class="text-xs text-on-surface-variant">无</span></div></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">注册时间</span><span class="text-on-surface-variant">{{ pDetail.created_at?.slice(0,19) }}</span></div>
        </div>
      </div>
    </div>

    <!-- Doctor Detail Modal -->
    <div v-if="dDetail" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="dDetail = null">
      <div class="bg-surface-container-lowest rounded-xl shadow-2xl border border-outline-variant max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto animate-fade-in">
        <div class="p-4 border-b flex justify-between items-center">
          <h3 class="font-semibold text-on-surface flex items-center gap-2"><span class="material-symbols-outlined text-primary">stethoscope</span> 医师详情</h3>
          <button @click="dDetail = null" class="p-1 rounded-full hover:bg-surface-container text-on-surface-variant"><span class="material-symbols-outlined">close</span></button>
        </div>
        <div class="p-4 space-y-3 text-sm">
          <div class="flex justify-between"><span class="text-on-surface-variant">用户名</span><span class="font-medium text-on-surface">{{ dDetail.user_name }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">手机号</span><span class="text-on-surface-variant">{{ dDetail.phone }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">科室</span><span class="text-on-surface-variant">{{ dDetail.department||'-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">职称</span><span class="text-on-surface-variant">{{ dDetail.title||'-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">医院</span><span class="text-on-surface-variant">{{ dDetail.hospital||'-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">专长</span><span class="text-right max-w-[60%] text-on-surface">{{ dDetail.specialty||'-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">简介</span><span class="text-right max-w-[60%] text-on-surface">{{ dDetail.introduction||'-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">首次登录</span><span>{{ dDetail.is_first_login ? '是（未修改初始密码）' : '否' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">注册时间</span><span class="text-on-surface-variant">{{ dDetail.created_at?.slice(0,19) }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { adminApi } from '@/api/admin'

const activeTab = ref('patients'); const tabs = [{key:'patients',label:'患者管理'},{key:'doctors',label:'医师管理'},{key:'admins',label:'管理员'},{key:'add-doctor',label:'添加医师'}]
const patSearch = ref(''); const docSearch = ref(''); const patients = ref<any[]>([]); const doctors = ref<any[]>([]); const admins = ref<any[]>([])
const newDoc = reactive({user_name:'',phone:'',password_hash:'',department:'',title:'',hospital:''})
const pDetail = ref<any>(null); const dDetail = ref<any>(null)

async function loadPatients() { try { const r = await adminApi.getPatients({keyword:patSearch.value||undefined,page_size:200}); if(r.code===200) patients.value=r.data.list } catch {} }
async function loadDoctors() { try { const r = await adminApi.getDoctors({keyword:docSearch.value||undefined,page_size:200}); if(r.code===200) doctors.value=r.data.list } catch {} }
async function loadAdmins() { try { const r = await adminApi.getAdmins({page_size:200}); if(r.code===200) admins.value=r.data.list } catch {} }
async function toggleStatus(type:string,id:string,cur:number) { const s=cur===1?0:1; if(!confirm('确定'+(s?'启用':'禁用')+'吗?')) return
  try { if(type==='patient') await adminApi.updatePatientStatus(id,s); else await adminApi.updateDoctorStatus(id,s); loadPatients(); loadDoctors() } catch(e:any){alert(e.message)} }
async function createDoctor() { if(!newDoc.user_name||!newDoc.phone||!newDoc.password_hash){alert('请填写必填项');return}
  try { await adminApi.createDoctor(newDoc); alert('创建成功'); Object.assign(newDoc,{user_name:'',phone:'',password_hash:'',department:'',title:'',hospital:''}); loadDoctors() } catch(e:any){alert(e.message)} }
async function viewPatient(id:string) { try { const r = await adminApi.getPatientDetail(id); if (r.code===200) pDetail.value = r.data } catch(e:any){alert(e.message)} }
async function viewDoctor(id:string) { try { const r = await adminApi.getDoctorDetail(id); if (r.code===200) dDetail.value = r.data } catch(e:any){alert(e.message)} }

onMounted(async () => { await loadPatients(); await loadDoctors(); await loadAdmins() })
</script>
