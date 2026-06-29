<template>
  <div class="p-[16px] md:p-[40px] max-w-[1600px] mx-auto">
    <h1 class="text-[24px] md:text-[32px] font-semibold text-on-background mb-[24px]">反馈管理</h1>
    <div class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b flex gap-2">
        <select v-model="fbStatus" @change="load" class="h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm"><option value="">全部状态</option><option value="pending">待处理</option><option value="resolved">已解决</option></select>
        <select v-model="fbType" @change="load" class="h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm"><option value="">全部类型</option><option value="knowledge_error">知识错误</option><option value="content_missing">内容缺失</option><option value="optimization">优化建议</option><option value="other">其他</option></select>
      </div>
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase text-on-surface-variant">时间</th><th class="p-3 text-xs uppercase text-on-surface-variant">来源</th><th class="p-3 text-xs uppercase text-on-surface-variant">类型</th><th class="p-3 text-xs uppercase text-on-surface-variant">标题</th><th class="p-3 text-xs uppercase text-on-surface-variant">内容</th><th class="p-3 text-xs uppercase text-on-surface-variant">状态</th><th class="p-3 text-xs uppercase text-on-surface-variant text-right">操作</th></tr></thead>
      <tbody><tr v-if="list.length===0"><td colspan="7" class="p-6 text-center text-on-surface-variant">暂无数据</td></tr>
        <tr v-for="f in list" :key="f.feedback_id" class="border-b hover:bg-surface-container/50 cursor-pointer" @click="viewDetail(f.feedback_id)">
          <td class="p-3 text-xs text-on-surface-variant">{{ f.created_at?.slice(0,10) }}</td>
          <td class="p-3 text-xs text-on-surface-variant">{{ f.patient_name || f.doctor_name || '-' }}</td>
          <td class="p-3"><span class="px-2 py-0.5 rounded-full text-xs bg-surface-container text-on-surface-variant">{{ typeMap[f.type]||'-' }}</span></td>
          <td class="p-3 truncate max-w-[120px] text-on-surface">{{ f.title||'-' }}</td>
          <td class="p-3 truncate max-w-[200px] text-xs text-on-surface-variant">{{ f.content||'-' }}</td>
          <td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', f.status==='pending'?'bg-tertiary-container text-on-tertiary':'bg-secondary-container text-on-secondary-container']">{{ f.status==='pending'?'待处理':'已解决' }}</span></td>
          <td class="p-3 text-right" @click.stop><button v-if="f.status==='pending'" @click="replyFb(f.feedback_id)" class="text-primary text-xs hover:underline">回复</button><span v-else class="text-xs text-on-surface-variant">{{ f.reply?.slice(0,20)||'已处理' }}</span></td>
        </tr>
      </tbody></table>
    </div>

    <!-- Detail Modal -->
    <div v-if="detail" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="detail = null">
      <div class="bg-surface-container-lowest rounded-xl shadow-2xl border border-outline-variant max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto animate-fade-in">
        <div class="p-4 border-b border-outline-variant flex justify-between items-center">
          <h3 class="font-semibold text-on-surface flex items-center gap-2"><span class="material-symbols-outlined text-primary">rate_review</span> 反馈详情</h3>
          <button @click="detail = null" class="p-1 rounded-full hover:bg-surface-container text-on-surface-variant"><span class="material-symbols-outlined">close</span></button>
        </div>
        <div class="p-4 space-y-3 text-sm">
          <div class="flex justify-between"><span class="text-on-surface-variant">类型</span><span class="px-2 py-0.5 rounded-full text-xs bg-surface-container text-on-surface-variant">{{ typeMap[detail.type]||'-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">标题</span><span class="font-medium text-on-surface text-right max-w-[60%]">{{ detail.title||'-' }}</span></div>
          <div><span class="text-on-surface-variant block mb-1">详细内容</span><p class="bg-surface-container rounded-lg p-3 text-on-surface">{{ detail.content||'-' }}</p></div>
          <div v-if="detail.corrected_answer"><span class="text-on-surface-variant block mb-1">纠正内容</span><p class="bg-error-container/20 rounded-lg p-3 text-on-surface">{{ detail.corrected_answer }}</p></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">评分</span><span>{{ detail.rating ? '★'.repeat(detail.rating) : '-' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">是否准确</span><span :class="detail.is_accurate ? 'text-secondary' : 'text-error'">{{ detail.is_accurate ? '是' : detail.is_accurate === false ? '否' : '-' }}</span></div>
          <div v-if="detail.references?.length" class="flex justify-between"><span class="text-on-surface-variant">参考文献</span><span class="text-right max-w-[60%]">{{ detail.references.join(', ') }}</span></div>
          <div v-if="detail.reply" class="flex justify-between"><span class="text-on-surface-variant">回复</span><span class="text-secondary">{{ detail.reply }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">状态</span><span :class="['px-2 py-0.5 rounded-full text-xs', detail.status==='pending'?'bg-tertiary-container text-on-tertiary':'bg-secondary-container text-on-secondary-container']">{{ detail.status==='pending'?'待处理':'已解决' }}</span></div>
          <div class="flex justify-between"><span class="text-on-surface-variant">提交时间</span><span class="text-on-surface-variant">{{ detail.created_at?.slice(0,19) }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
const list = ref<any[]>([]); const fbStatus = ref(''); const fbType = ref(''); const detail = ref<any>(null)
const typeMap: Record<string,string> = {knowledge_error:'知识错误',content_missing:'内容缺失',optimization:'优化建议',other:'其他'}
async function load() { try { const r = await adminApi.getFeedbacks({status:fbStatus.value||undefined,type:fbType.value||undefined,page_size:200}); if(r.code===200) list.value=r.data.list } catch {} }
async function viewDetail(id:string) { try { const r = await adminApi.getFeedbackDetail(id); if (r.code===200) detail.value = r.data } catch(e:any){alert(e.message)} }
async function replyFb(id:string) { const reply = prompt('回复内容:'); if(!reply) return; try { await adminApi.replyFeedback(id, reply); load(); alert('回复成功') } catch(e:any){alert(e.message)} }
onMounted(load)
</script>
