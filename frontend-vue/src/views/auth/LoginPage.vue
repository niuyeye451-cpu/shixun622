<template>
  <div class="h-screen w-screen flex flex-col md:flex-row overflow-hidden" style="font-family: 'Inter', sans-serif;">
    <!-- Left: Brand Panel (60% desktop, hidden mobile) -->
    <div class="hidden md:flex md:w-[60%] relative bg-primary overflow-hidden items-center justify-center flex-col text-on-primary">
      <div class="absolute inset-0 z-0 opacity-40 mix-blend-overlay" style="background-image: radial-gradient(circle at center, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 32px 32px;">
        <svg class="pulse-network absolute inset-0 z-0" width="100%" height="100%">
          <defs>
            <pattern id="network" patternUnits="userSpaceOnUse" width="100" height="100" x="0" y="0">
              <line stroke="rgba(255,255,255,0.2)" stroke-width="1" x1="20" y1="20" x2="80" y2="80"></line>
              <line stroke="rgba(255,255,255,0.2)" stroke-width="1" x1="80" y1="20" x2="20" y2="80"></line>
              <circle cx="20" cy="20" r="3" fill="rgba(255,255,255,0.5)"></circle>
              <circle cx="80" cy="80" r="3" fill="rgba(255,255,255,0.5)"></circle>
              <circle cx="80" cy="20" r="3" fill="rgba(255,255,255,0.5)"></circle>
              <circle cx="20" cy="80" r="3" fill="rgba(255,255,255,0.5)"></circle>
              <circle cx="50" cy="50" r="4" fill="rgba(255,255,255,0.8)"></circle>
            </pattern>
          </defs>
          <rect fill="url(#network)" width="100%" height="100%"></rect>
        </svg>
      </div>
      <div class="z-10 text-center px-12 max-w-2xl -mt-12">
        <div class="mb-12">
          <h1 class="text-[48px] font-bold tracking-tight flex items-center justify-center gap-3 mb-3" style="font-family: 'Inter', sans-serif;">
            <span class="material-symbols-outlined text-[56px]" style="font-variation-settings: 'FILL' 1;">hub</span>
            MedGraph AI
          </h1>
          <p class="text-2xl font-light text-on-primary-container" style="font-family: 'Inter', sans-serif;">构建精准医疗知识图谱，赋能临床决策与科研创新。</p>
        </div>
        <div class="flex flex-col gap-4 w-full max-w-md mx-auto">
          <div v-for="role in roles" :key="role.key" @click="switchRole(role.key)"
            :class="['flex items-center gap-4 p-4 rounded-xl transition-all cursor-pointer',
              selectedRole === role.key ? 'bg-surface-container-lowest/20 border-2 border-on-primary shadow-lg' : 'bg-white/5 border border-white/20 hover:bg-white/10']">
            <div class="w-16 h-16 rounded-lg overflow-hidden bg-surface-container-lowest flex-shrink-0">
              <img :alt="role.label" class="w-full h-full object-cover" :src="roleAvatar(role.key)" />
            </div>
            <span class="text-xl font-semibold" style="font-family: 'Inter', sans-serif;">{{ role.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Login Form (40% desktop, 100% mobile) -->
    <div class="w-full md:w-[40%] bg-surface-container-lowest h-full flex flex-col justify-center items-center relative" style="padding: 16px;">
      <!-- Mobile-only: compact role selector + logo -->
      <div class="md:hidden w-full max-w-md mb-4">
        <div class="text-center mb-4">
          <h1 class="text-2xl text-primary font-bold flex items-center justify-center gap-1">
            <span class="material-symbols-outlined text-3xl" style="font-variation-settings: 'FILL' 1;">hub</span> MedGraph AI
          </h1>
        </div>
        <div class="flex gap-1 p-1 bg-surface-container rounded-lg">
          <button v-for="role in roles" :key="role.key" @click="switchRole(role.key)"
            :class="['flex-1 py-2 rounded-md text-sm font-medium transition-all',
              selectedRole === role.key ? 'bg-surface-container-lowest text-primary shadow-sm' : 'text-on-surface-variant']">
            <span class="material-symbols-outlined text-lg">{{ role.icon }}</span>
          </button>
        </div>
      </div>

      <div class="w-full max-w-md bg-surface-container-lowest border border-surface-variant rounded-xl p-8 flex flex-col gap-6 shadow-sm">
        <div class="text-center">
          <h2 class="text-[24px] md:text-[32px] text-on-surface font-semibold" style="font-family: 'Inter', sans-serif;">{{ roleLabel }}登录</h2>
          <p class="text-base text-on-surface-variant mt-1">{{ roleDesc }}</p>
          <p v-if="selectedRole !== 'patient'" class="text-outline text-xs mt-1 bg-surface-container px-2 py-1 rounded inline-block">测试账号: <b>{{ selectedRole === 'doctor' ? 'doctor01' : 'admin' }}</b> / 密码: <b>123456</b></p>
        </div>

        <form @submit.prevent="handleLogin" class="flex flex-col gap-4">
          <div v-if="selectedRole === 'patient'">
            <label class="text-xs text-on-surface-variant font-semibold" style="font-family: 'JetBrains Mono', monospace;">手机号码</label>
            <div class="relative mt-1">
              <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">phone_iphone</span>
              <input v-model="phone" class="w-full h-12 pl-10 pr-4 rounded-lg border border-outline-variant bg-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" placeholder="请输入11位手机号码" type="tel" maxlength="11" />
            </div>
          </div>
          <div v-if="selectedRole === 'patient'">
            <label class="text-xs text-on-surface-variant font-semibold" style="font-family: 'JetBrains Mono', monospace;">验证码 (演示: <b>123456</b>)</label>
            <div class="flex gap-2 mt-1">
              <div class="relative flex-1">
                <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">lock</span>
                <input v-model="code" class="w-full h-12 pl-10 pr-4 rounded-lg border border-outline-variant bg-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" placeholder="6位验证码" maxlength="6" />
              </div>
              <button type="button" @click="sendSms" :disabled="smsCountdown > 0" class="px-4 h-12 rounded-lg border border-primary text-primary hover:bg-primary-container whitespace-nowrap text-sm font-medium" style="font-family: 'JetBrains Mono', monospace;">
                {{ smsCountdown > 0 ? `${smsCountdown}s后重发` : '获取验证码' }}
              </button>
            </div>
          </div>

          <div v-if="selectedRole !== 'patient'">
            <label class="text-xs text-on-surface-variant font-semibold" style="font-family: 'JetBrains Mono', monospace;">用户名</label>
            <div class="relative mt-1">
              <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">person</span>
              <input v-model="username" class="w-full h-12 pl-10 pr-4 rounded-lg border border-outline-variant bg-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" :placeholder="selectedRole === 'doctor' ? 'doctor01' : 'admin'" />
            </div>
          </div>
          <div v-if="selectedRole !== 'patient'">
            <label class="text-xs text-on-surface-variant font-semibold" style="font-family: 'JetBrains Mono', monospace;">密码</label>
            <div class="relative mt-1">
              <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">lock</span>
              <input v-model="password" class="w-full h-12 pl-10 pr-4 rounded-lg border border-outline-variant bg-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" placeholder="123456" type="password" />
            </div>
          </div>

          <button type="submit" :disabled="loading" class="w-full h-12 mt-2 rounded-lg bg-primary text-on-primary hover:bg-primary/90 active:scale-[0.98] transition-all font-medium shadow-[0_4px_12px_rgba(0,61,155,0.15)] flex justify-center items-center gap-2" style="font-family: 'JetBrains Mono', monospace;">
            <span v-if="loading" class="material-symbols-outlined animate-spin text-lg">progress_activity</span>
            {{ loading ? '登录中...' : '登 录' }}
          </button>
        </form>
      </div>

      <!-- Disclaimer -->
      <div class="absolute bottom-4 md:bottom-10 w-full text-center px-6">
        <p class="text-xs text-outline" style="font-family: 'Inter', sans-serif;">非法访问与医疗数据免责警告：本系统仅供授权医务人员及研究者使用。所有操作均被记录审计。未授权访问将面临法律追责。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const roles = [
  { key: 'patient', label: '我是用户', icon: 'person' },
  { key: 'doctor', label: '我是医生', icon: 'stethoscope' },
  { key: 'admin', label: '我是管理员', icon: 'shield_person' },
]
const selectedRole = ref('patient')
const phone = ref('')
const code = ref('')
const username = ref('')
const password = ref('')
const loading = ref(false)
const smsCountdown = ref(0)
const smsId = ref('')

const roleLabel = computed(() => roles.find(r => r.key === selectedRole.value)?.label ?? '')
const roleDesc = computed(() => selectedRole.value === 'patient' ? '请输入您的手机号码及验证码以进入系统。' : '请输入您的用户名及密码以进入系统。')

const avatarUrls: Record<string, string> = {
  patient: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCkqHke7itBhNqE8yjubc--1E-IsUdtwHyC56kORVudzrLKsCrw9Qs_2hIuqGTmsZKtN1D8S6rSBPGN2Wf30vKzi_m7diYlza66cNY7cv1K24l93ClYEkvZKRqLuTTyhm6wuJ48fCfMV-WXy_p9NuVTKU9OMYMoR3l3_QsobxN4Gr5QqZULXOXfCcQnCgiafQ6meXizeDhDXobl-iakzUVu-7KYjYE_H_5JEMMuURmur5DgbVuwCIU8pajxZFeZX-bgLc8jUAB2WAw',
  doctor: 'https://lh3.googleusercontent.com/aida-public/AB6AXuALritO6--0GLJwS_aWI2UrBLyNCnxczQF7zOOu-lgAPswSOnukEfxscribHQNPvC5LnDrjsBuQHdVbj_rczQYS2CJ9neCjNIaluvbp72N_dKApjTX7yvDMJ4banMILMGMYD4OE3oxjlSo91RHAPK6HNgF-ZaJQEE4gNszdAXGwED-hCMaZXeZabWL3ZNI2fwTfB_Rgl-Bqqde3ssIYuzTRhmYNlllfoaTL-sHG5jvdGBFmRbNULHUGS11Bp1-lKII2lMP6ZgbcaLc',
  admin: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCeevu_D34yGHNqGjKTdRdNMM_u9YbWarn72tqJIE3CbmeIf0yzTU0eJK2QYpfMFMQxbdHeGrQOcjqgLcRwxckdg8TCCEBnSCNFUg-YD9eryBxuwqBvQ4hRIMsJbT0J6ueYtGwV-2nHCQSqTP05Q-ABxy-QNopGyS0xs-HhJr1kW6-ziUlsr2RI6I4xwC0_yHEa1xNHRGreeLxa72bduVoR9Cd8aQJExxEj5R7HGQH8O5eV-4DJJHeX4l-VZUEXREOx57VYB9imIH4',
}
function roleAvatar(key: string) { return avatarUrls[key] || '' }

function switchRole(role: string) {
  selectedRole.value = role
}

async function sendSms() {
  if (phone.value.length !== 11) { alert('请输入正确的11位手机号码'); return }
  try {
    const res = await authApi.sendSms(phone.value)
    if (res.code === 200) {
      smsId.value = res.data.sms_id
      smsCountdown.value = 60
      const t = setInterval(() => { smsCountdown.value--; if (smsCountdown.value <= 0) clearInterval(t) }, 1000)
      alert('验证码已发送 (演示: 123456)')
    }
  } catch (e: any) { alert('发送失败: ' + e.message) }
}

async function handleLogin() {
  loading.value = true
  try {
    const roleMap: Record<string, string> = { patient: '/patient/qa', doctor: '/doctor/case', admin: '/admin/dashboard' }
    if (selectedRole.value === 'patient') {
      if (!phone.value || !code.value) { alert('请填写手机号和验证码'); loading.value = false; return }
      await userStore.loginPatient(phone.value, code.value, smsId.value)
    } else if (selectedRole.value === 'doctor') {
      if (!username.value || !password.value) { alert('请填写用户名和密码'); loading.value = false; return }
      await userStore.loginDoctor(username.value, password.value)
    } else {
      if (!username.value || !password.value) { alert('请填写用户名和密码'); loading.value = false; return }
      await userStore.loginAdmin(username.value, password.value)
    }
    router.push(roleMap[selectedRole.value])
  } catch (e: any) {
    alert('登录失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}
</script>
