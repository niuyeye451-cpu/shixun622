<template>
  <div class="p-[16px] md:p-[40px] max-w-[1600px] mx-auto">
    <h1 class="text-2xl md:text-3xl font-bold mb-6">用户管理</h1>
    <div class="flex gap-2 mb-6 border-b border-outline-variant overflow-x-auto">
      <button v-for="t in tabs" :key="t.key" @click="activeTab=t.key" :class="['px-4 py-2 rounded-t-lg text-sm font-medium border-b-2 transition-colors', activeTab===t.key?'border-primary text-primary bg-surface-container-lowest':'border-transparent text-on-surface-variant']">{{ t.label }}</button>
    </div>

    <!-- Patients -->
    <div v-if="activeTab==='patients'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b"><input v-model="patSearch" @input="loadPatients" class="w-48 h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="搜索..." /></div>
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase">用户名</th><th class="p-3 text-xs uppercase">手机号</th><th class="p-3 text-xs uppercase">性别</th><th class="p-3 text-xs uppercase">年龄</th><th class="p-3 text-xs uppercase">状态</th><th class="p-3 text-xs uppercase text-right">操作</th></tr></thead>
      <tbody><tr v-if="patients.length===0"><td colspan="6" class="p-6 text-center">加载中...</td></tr>
        <tr v-for="p in patients" :key="p.patient_id" class="border-b hover:bg-surface-container/50"><td class="p-3">{{ p.user_name }}</td><td class="p-3">{{ p.phone }}</td><td class="p-3">{{ p.gender==='male'?'男':p.gender==='female'?'女':'-' }}</td><td class="p-3">{{ p.age||'-' }}</td><td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', p.status===1?'bg-secondary-container text-on-secondary-container':'bg-error-container text-on-error-container']">{{ p.status===1?'正常':'禁用' }}</span></td>
        <td class="p-3 text-right"><button @click="toggleStatus('patient',p.patient_id,p.status)" class="text-primary text-xs">{{ p.status===1?'禁用':'启用' }}</button></td></tr>
      </tbody></table>
    </div>

    <!-- Doctors -->
    <div v-if="activeTab==='doctors'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b"><input v-model="docSearch" @input="loadDoctors" class="w-48 h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="搜索..." /></div>
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase">用户名</th><th class="p-3 text-xs uppercase">科室</th><th class="p-3 text-xs uppercase">职称</th><th class="p-3 text-xs uppercase">医院</th><th class="p-3 text-xs uppercase">状态</th><th class="p-3 text-xs uppercase text-right">操作</th></tr></thead>
      <tbody><tr v-if="doctors.length===0"><td colspan="6" class="p-6 text-center">加载中...</td></tr>
        <tr v-for="d in doctors" :key="d.doctor_id" class="border-b hover:bg-surface-container/50"><td class="p-3">{{ d.user_name }}</td><td class="p-3">{{ d.department||'-' }}</td><td class="p-3">{{ d.title||'-' }}</td><td class="p-3">{{ d.hospital||'-' }}</td><td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', d.status===1?'bg-secondary-container text-on-secondary-container':'bg-error-container text-on-error-container']">{{ d.status===1?'正常':'禁用' }}</span></td>
        <td class="p-3 text-right"><button @click="toggleStatus('doctor',d.doctor_id,d.status)" class="text-primary text-xs">{{ d.status===1?'禁用':'启用' }}</button></td></tr>
      </tbody></table>
    </div>

    <!-- Admins -->
    <div v-if="activeTab==='admins'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase">用户名</th><th class="p-3 text-xs uppercase">手机号</th><th class="p-3 text-xs uppercase">角色等级</th><th class="p-3 text-xs uppercase">状态</th><th class="p-3 text-xs uppercase">创建时间</th></tr></thead>
      <tbody><tr v-if="admins.length===0"><td colspan="5" class="p-6 text-center">加载中...</td></tr>
        <tr v-for="a in admins" :key="a.admin_id" class="border-b hover:bg-surface-container/50"><td class="p-3">{{ a.user_name }}</td><td class="p-3">{{ a.phone }}</td><td class="p-3">{{ a.role_level}}</td><td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', a.status===1?'bg-secondary-container text-on-secondary-container':'bg-error-container text-on-error-container']">{{ a.status===1?'正常':'禁用' }}</span></td><td class="p-3 text-xs">{{ a.created_at?.slice(0,10) }}</td></tr>
      </tbody></table>
    </div>

    <!-- Add Doctor -->
    <div v-if="activeTab==='add-doctor'" class="bg-surface-container-lowest rounded-xl border p-6 max-w-xl">
      <h3 class="font-semibold mb-4">新增医师账号</h3>
      <div class="space-y-3">
        <input v-model="newDoc.user_name" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="用户名*" />
        <input v-model="newDoc.phone" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="手机号*" />
        <input v-model="newDoc.password_hash" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="密码*" type="password" />
        <input v-model="newDoc.department" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="科室" />
        <input v-model="newDoc.title" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="职称" />
        <input v-model="newDoc.hospital" class="w-full h-12 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="医院" />
        <button @click="createDoctor" class="w-full h-12 rounded-lg bg-primary text-on-primary text-sm font-medium shadow-md">创建医师</button>
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

async function loadPatients() { try { const r = await adminApi.getPatients({keyword:patSearch.value||undefined,page_size:200}); if(r.code===200) patients.value=r.data.list } catch {} }
async function loadDoctors() { try { const r = await adminApi.getDoctors({keyword:docSearch.value||undefined,page_size:200}); if(r.code===200) doctors.value=r.data.list } catch {} }
async function loadAdmins() { try { const r = await adminApi.getAdmins({page_size:200}); if(r.code===200) admins.value=r.data.list } catch {} }
async function toggleStatus(type:string,id:string,cur:number) { const s=cur===1?0:1; if(!confirm('确定'+(s?'启用':'禁用')+'吗?')) return
  try { if(type==='patient') await adminApi.updatePatientStatus(id,s); else await adminApi.updateDoctorStatus(id,s); loadPatients(); loadDoctors() } catch(e:any){alert(e.message)} }
async function createDoctor() { if(!newDoc.user_name||!newDoc.phone||!newDoc.password_hash){alert('请填写必填项');return}
  try { await adminApi.createDoctor(newDoc); alert('创建成功'); Object.assign(newDoc,{user_name:'',phone:'',password_hash:'',department:'',title:'',hospital:''}); loadDoctors() } catch(e:any){alert(e.message)} }

onMounted(async () => { await loadPatients(); await loadDoctors(); await loadAdmins() })
</script>
