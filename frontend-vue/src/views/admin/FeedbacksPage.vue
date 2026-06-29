<template>
  <div class="p-[16px] md:p-[40px] max-w-[1600px] mx-auto">
    <h1 class="text-2xl md:text-3xl font-bold mb-6">反馈管理</h1>
    <div class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b flex gap-2">
        <select v-model="fbStatus" @change="load" class="h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm"><option value="">全部状态</option><option value="pending">待处理</option><option value="resolved">已解决</option></select>
        <select v-model="fbType" @change="load" class="h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm"><option value="">全部类型</option><option value="knowledge_error">知识错误</option><option value="content_missing">内容缺失</option><option value="optimization">优化建议</option><option value="other">其他</option></select>
      </div>
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase">时间</th><th class="p-3 text-xs uppercase">来源</th><th class="p-3 text-xs uppercase">类型</th><th class="p-3 text-xs uppercase">标题</th><th class="p-3 text-xs uppercase">内容</th><th class="p-3 text-xs uppercase">状态</th><th class="p-3 text-xs uppercase text-right">操作</th></tr></thead>
      <tbody><tr v-if="list.length===0"><td colspan="7" class="p-6 text-center">暂无数据</td></tr>
        <tr v-for="f in list" :key="f.feedback_id" class="border-b hover:bg-surface-container/50">
          <td class="p-3 text-xs">{{ f.created_at?.slice(0,10) }}</td>
          <td class="p-3 text-xs">{{ f.patient_name || f.doctor_name || '-' }}</td>
          <td class="p-3"><span class="px-2 py-0.5 rounded-full text-xs bg-surface-container">{{ typeMap[f.type]||'-' }}</span></td>
          <td class="p-3 truncate max-w-[120px]">{{ f.title||'-' }}</td>
          <td class="p-3 truncate max-w-[200px] text-xs text-on-surface-variant">{{ f.content||'-' }}</td>
          <td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', f.status==='pending'?'bg-tertiary-container text-on-tertiary':'bg-secondary-container text-on-secondary-container']">{{ f.status==='pending'?'待处理':'已解决' }}</span></td>
          <td class="p-3 text-right"><button v-if="f.status==='pending'" @click="replyFb(f.feedback_id)" class="text-primary text-xs">回复</button><span v-else class="text-xs text-on-surface-variant">{{ f.reply?.slice(0,20)||'已处理' }}</span></td>
        </tr>
      </tbody></table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
const list = ref<any[]>([]); const fbStatus = ref(''); const fbType = ref('')
const typeMap: Record<string,string> = {knowledge_error:'知识错误',content_missing:'内容缺失',optimization:'优化建议',other:'其他'}
async function load() { try { const r = await adminApi.getFeedbacks({status:fbStatus.value||undefined,type:fbType.value||undefined,page_size:200}); if(r.code===200) list.value=r.data.list } catch {} }
async function replyFb(id:string) { const reply = prompt('回复内容:'); if(!reply) return; try { await adminApi.replyFeedback(id, reply); load(); alert('回复成功') } catch(e:any){alert(e.message)} }
onMounted(load)
</script>
