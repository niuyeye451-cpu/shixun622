<template>
  <div class="p-[16px] md:p-[40px] max-w-[1600px] mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl md:text-3xl font-bold">知识库管理</h1>
      <button @click="openCreateEntity" class="bg-primary text-on-primary px-6 py-3 rounded-lg text-sm font-medium shadow-md flex items-center gap-1 hover:bg-primary/90">
        <span class="material-symbols-outlined text-lg">add</span> 新增实体
      </button>
    </div>
    <div class="flex gap-2 mb-6 border-b border-outline-variant overflow-x-auto">
      <button v-for="t in tabs" :key="t.key" @click="activeTab=t.key" :class="['px-4 py-2 rounded-t-lg text-sm font-medium border-b-2 transition-colors', activeTab===t.key?'border-primary text-primary bg-surface-container-lowest':'border-transparent text-on-surface-variant']">{{ t.label }}</button>
    </div>

    <!-- Entities -->
    <div v-if="activeTab==='entities'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b flex gap-2 flex-wrap">
        <input v-model="entSearch" @input="loadEntities" class="w-48 h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="搜索..." />
        <select v-model="entType" @change="loadEntities" class="h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm"><option value="">全部</option><option value="disease">疾病</option><option value="symptom">症状</option><option value="drug">药品</option><option value="department">科室</option></select>
      </div>
      <table class="w-full text-sm"><thead><tr class="bg-surface border-b"><th class="p-3 text-xs uppercase text-on-surface-variant">名称</th><th class="p-3 text-xs uppercase text-on-surface-variant">类型</th><th class="p-3 text-xs uppercase text-on-surface-variant">别名</th><th class="p-3 text-xs uppercase text-on-surface-variant">状态</th><th class="p-3 text-xs uppercase text-on-surface-variant text-right">操作</th></tr></thead>
      <tbody><tr v-if="entities.length===0"><td colspan="5" class="p-6 text-center">加载中...</td></tr>
        <tr v-for="e in entities" :key="e.entity_id" class="border-b hover:bg-surface-container/50">
          <td class="p-3 font-medium">{{ e.name }}</td><td class="p-3"><span class="px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary">{{ e.type }}</span></td>
          <td class="p-3 text-xs text-on-surface-variant">{{ (e.aliases||[]).join(', ') || '-' }}</td>
          <td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', e.status==='published'?'bg-secondary-container text-on-secondary-container':'bg-surface-container']">{{ e.status==='published'?'已发布':e.status }}</span></td>
          <td class="p-3 text-right"><button @click="editEntity(e)" class="text-primary text-xs mr-2">编辑</button><button @click="delEntity(e.entity_id)" class="text-error text-xs">删除</button></td>
        </tr>
      </tbody></table>
    </div>

    <!-- Relations -->
    <div v-if="activeTab==='relations'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b flex justify-between"><select v-model="relType" @change="loadRelations" class="h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm"><option value="">全部</option><option value="has_symptom">有症状</option><option value="belongs_to_department">属于科室</option><option value="treat_with_drug">用药物治疗</option><option value="complication">并发症</option><option value="contraindication">禁忌症</option></select><button @click="openCreateRelation" class="h-10 px-4 rounded-lg bg-primary text-on-primary text-xs">新增关系</button></div>
      <table class="w-full text-sm"><thead><tr class="bg-surface border-b"><th class="p-3 text-xs uppercase">源实体</th><th class="p-3 text-xs uppercase">关系</th><th class="p-3 text-xs uppercase">目标实体</th><th class="p-3 text-xs uppercase">描述</th><th class="p-3 text-xs uppercase text-right">操作</th></tr></thead>
      <tbody><tr v-if="relations.length===0"><td colspan="5" class="p-6 text-center">加载中...</td></tr>
        <tr v-for="r in relations" :key="r.relation_id" class="border-b hover:bg-surface-container/50">
          <td class="p-3">{{ r.source_entity_name }}</td><td class="p-3"><span class="px-2 py-0.5 rounded-full text-xs bg-tertiary/10 text-tertiary">{{ r.relation_name||r.relation_type }}</span></td>
          <td class="p-3">{{ r.target_entity_name }}</td><td class="p-3 text-xs text-on-surface-variant truncate max-w-[200px]">{{ r.text||'-' }}</td>
          <td class="p-3 text-right"><button @click="delRelation(r.relation_id)" class="text-error text-xs">删除</button></td>
        </tr>
      </tbody></table>
    </div>

    <!-- Synonyms -->
    <div v-if="activeTab==='synonyms'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b flex justify-between"><input v-model="synSearch" class="w-48 h-10 px-3 rounded-lg border border-outline-variant bg-surface text-sm" placeholder="搜索..." /><button @click="openCreateSynonym" class="h-10 px-4 rounded-lg bg-primary text-on-primary text-xs">新增同义词</button></div>
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase">别名</th><th class="p-3 text-xs uppercase">标准实体</th><th class="p-3 text-xs uppercase">来源</th><th class="p-3 text-xs uppercase">创建时间</th><th class="p-3 text-xs uppercase text-right">操作</th></tr></thead>
      <tbody><tr v-if="synonyms.length===0"><td colspan="5" class="p-6 text-center">暂无数据</td></tr>
        <tr v-for="s in synonyms" :key="s.synonym_id" class="border-b hover:bg-surface-container/50"><td class="p-3">{{ s.alias_term }}</td><td class="p-3">{{ s.standard_entity_name }}</td><td class="p-3 text-xs">{{ s.source }}</td><td class="p-3 text-xs">{{ s.created_at?.slice(0,10) }}</td><td class="p-3 text-right"><button @click="delSynonym(s.synonym_id)" class="text-error text-xs">删除</button></td></tr>
      </tbody></table>
    </div>

    <!-- Versions -->
    <div v-if="activeTab==='versions'" class="bg-surface-container-lowest rounded-xl border overflow-hidden">
      <div class="p-3 border-b flex justify-between"><h3 class="text-sm font-semibold">知识版本列表</h3><button @click="openCreateVersion" class="h-10 px-4 rounded-lg bg-primary text-on-primary text-xs">创建版本</button></div>
      <table class="w-full text-sm"><thead><tr class="bg-surface"><th class="p-3 text-xs uppercase">版本号</th><th class="p-3 text-xs uppercase">实体数</th><th class="p-3 text-xs uppercase">关系数</th><th class="p-3 text-xs uppercase">状态</th><th class="p-3 text-xs uppercase">发布时间</th><th class="p-3 text-xs uppercase text-right">操作</th></tr></thead>
      <tbody><tr v-if="versions.length===0"><td colspan="6" class="p-6 text-center">暂无版本</td></tr>
        <tr v-for="v in versions" :key="v.version_id" class="border-b hover:bg-surface-container/50"><td class="p-3 font-medium">{{ v.version_number }}</td><td class="p-3">{{ v.entity_count }}</td><td class="p-3">{{ v.relation_count }}</td><td class="p-3"><span :class="['px-2 py-0.5 rounded-full text-xs', v.status==='published'?'bg-secondary-container text-on-secondary-container':'bg-surface-container']">{{ v.status==='published'?'已发布':v.status }}</span></td><td class="p-3 text-xs">{{ v.published_at?.slice(0,10)||'-' }}</td><td class="p-3 text-right"><button v-if="v.status!=='published'" @click="pubVersion(v.version_id)" class="text-primary text-xs">发布</button></td></tr>
      </tbody></table>
    </div>

    <!-- Import -->
    <div v-if="activeTab==='import'" class="flex flex-col gap-6">
      <div class="border-2 border-dashed border-primary/30 bg-primary-fixed/30 rounded-xl p-12 flex flex-col items-center justify-center cursor-pointer hover:bg-primary-fixed/50 transition-colors">
        <span class="material-symbols-outlined text-6xl text-primary mb-3">cloud_upload</span><h3 class="text-lg font-semibold mb-1">拖拽文件至此，或点击上传</h3><p class="text-sm text-on-surface-variant">JSON, CSV, XML (最大 500MB)</p>
      </div>
      <!-- PRD: Data Pre-check Table with status badges -->
      <div class="bg-surface-container-lowest rounded-xl border overflow-hidden">
        <div class="p-3 border-b bg-surface-container-low flex justify-between items-center">
          <h3 class="text-sm font-semibold text-on-surface">预检任务列表</h3>
          <div class="flex gap-2">
            <span class="px-3 py-1 bg-surface text-on-surface-variant rounded-full text-xs border border-outline-variant">全部 (3)</span>
            <span class="px-3 py-1 bg-error-container text-on-error-container rounded-full text-xs border border-error/20">冲突 (1)</span>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead><tr class="bg-surface border-b"><th class="p-3 text-xs uppercase text-on-surface-variant">文件名</th><th class="p-3 text-xs uppercase text-on-surface-variant">实体数量</th><th class="p-3 text-xs uppercase text-on-surface-variant">状态</th><th class="p-3 text-xs uppercase text-on-surface-variant text-right">操作</th></tr></thead>
            <tbody>
              <tr class="border-b hover:bg-surface-container/50 transition-colors">
                <td class="p-3 text-on-surface flex items-center gap-2"><span class="material-symbols-outlined text-outline text-lg">description</span> cardiology_guidelines_2023.json</td>
                <td class="p-3 text-on-surface-variant">1,245</td>
                <td class="p-3"><span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-secondary-container text-on-secondary-container text-xs"><span class="material-symbols-outlined text-sm">check_circle</span> 校验通过</span></td>
                <td class="p-3 text-right"><button class="text-primary hover:underline text-xs">查看</button></td>
              </tr>
              <tr class="border-b bg-tertiary-fixed/20 hover:bg-tertiary-fixed/30 transition-colors">
                <td class="p-3 text-on-surface flex items-center gap-2"><span class="material-symbols-outlined text-tertiary text-lg">description</span> pediatric_dosage_v2.csv</td>
                <td class="p-3 text-on-surface-variant">890</td>
                <td class="p-3"><span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-tertiary-container text-on-tertiary text-xs"><span class="material-symbols-outlined text-sm">warning</span> 格式异常</span></td>
                <td class="p-3 text-right"><button class="text-primary hover:underline text-xs">修复</button></td>
              </tr>
              <tr class="border-b bg-error-container/30 hover:bg-error-container/50 transition-colors">
                <td class="p-3 text-on-surface flex items-center gap-2"><span class="material-symbols-outlined text-error text-lg">description</span> drug_interactions_db.xml</td>
                <td class="p-3 text-on-surface-variant">4,502</td>
                <td class="p-3"><span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-error text-on-error text-xs"><span class="material-symbols-outlined text-sm">error</span> 重复冲突</span></td>
                <td class="p-3 text-right"><button class="text-primary hover:underline text-xs">解决冲突</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="bg-surface-container-lowest rounded-xl border p-4 flex flex-col items-center">
          <h3 class="font-semibold mb-3">知识统计</h3>
          <div class="w-36 h-36 rounded-full border-[14px] border-surface-variant relative flex items-center justify-center" style="border-top-color:#003d9b;border-right-color:#7cf8da;border-bottom-color:#ffb950;transform:rotate(-45deg)"><div style="transform:rotate(45deg)" class="text-center"><span class="text-2xl font-bold">{{ entities.length||'-' }}</span><span class="text-xs block">实体总数</span></div></div>
        </div>
        <div class="lg:col-span-2 bg-surface-container-lowest rounded-xl border p-4"><h3 class="font-semibold mb-3">待一键补全未知问题</h3>
          <div class="space-y-2" v-if="unknownList.length"><div v-for="(q,i) in unknownList" :key="q.question_id" class="flex justify-between items-center p-3 rounded-lg bg-surface border"><div class="flex items-center gap-3"><span class="font-bold text-sm">{{ i+1 }}</span><span class="text-sm truncate max-w-[300px]">{{ q.text }}</span><span class="px-2 py-0.5 text-xs bg-tertiary-container text-on-tertiary rounded-full">频次:{{ q.occur_count }}</span></div><button @click="resolveUnknown(q.question_id)" class="px-3 py-1 bg-primary text-on-primary rounded-lg text-xs">一键补全</button></div></div>
          <p v-else class="text-center p-6 text-on-surface-variant">暂无待一键补全问题</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import { adminApi } from '@/api/admin'

const store = useKnowledgeStore()
const activeTab = ref('entities')
const tabs = [{key:'entities',label:'实体管理'},{key:'relations',label:'关系管理'},{key:'synonyms',label:'同义词库'},{key:'versions',label:'版本管理'},{key:'import',label:'数据导入'}]
const entSearch = ref(''); const entType = ref(''); const relType = ref(''); const synSearch = ref('')
const unknownList = ref<any[]>([])
const entities = computed(() => store.entities); const relations = computed(() => store.relations)
const synonyms = computed(() => store.synonyms); const versions = computed(() => store.versions)

async function loadEntities() { await store.loadEntities({ keyword: entSearch.value || undefined, type: entType.value || undefined }) }
async function loadRelations() { await store.loadRelations({ relation_type: relType.value || undefined }) }
async function loadSynonyms() { await store.loadSynonyms() }
async function loadVersions() { await store.loadVersions() }
async function loadUnknown() { try { const r = await adminApi.getUnknownQuestions({status:'pending',page_size:10}); if (r.code===200) unknownList.value = r.data.list } catch {} }

function openCreateEntity() { const n=prompt('名称:'); if (!n) return; const t=prompt('类型(disease/symptom/drug/department):','disease'); if (!t) return; adminApi.createEntity({name:n,type:t,description:prompt('描述:')||'',aliases:[],attributes:{}}).then(()=>loadEntities()).catch(e=>alert(e.message)) }
function editEntity(e:any) { const n=prompt('名称:',e.name); if (!n) return; const d=prompt('描述:',e.description||''); adminApi.updateEntity(e.entity_id,{name:n,description:d||'',status:e.status}).then(()=>loadEntities()).catch(err=>alert(err.message)) }
async function delEntity(id:string) { if(!confirm('确定删除?')) return; try { await adminApi.deleteEntity(id); loadEntities() } catch(e:any) { alert(e.message) } }
function openCreateRelation() { const s=prompt('源实体ID:'); if(!s) return; const t=prompt('目标实体ID:'); if(!t) return; const r=prompt('关系类型:','has_symptom'); if(!r) return; adminApi.createRelation({source_entity_id:s,target_entity_id:t,relation_type:r,text:prompt('描述:')||''}).then(()=>loadRelations()).catch(e=>alert(e.message)) }
async function delRelation(id:string) { if(!confirm('确定删除?')) return; try { await adminApi.deleteRelation(id); loadRelations() } catch(e:any){alert(e.message)} }
function openCreateSynonym() { const a=prompt('别名:'); if(!a) return; const e=prompt('标准实体ID:'); if(!e) return; adminApi.createSynonym({alias_term:a,standard_entity_id:e}).then(()=>loadSynonyms()).catch(err=>alert(err.message)) }
async function delSynonym(id:string) { if(!confirm('确定删除?')) return; try { await adminApi.deleteSynonym(id); loadSynonyms() } catch(e:any){alert(e.message)} }
function openCreateVersion() { const v=prompt('版本号:'); if(!v) return; adminApi.createVersion({version_number:v,update_content:prompt('描述:')||''}).then(()=>loadVersions()).catch(e=>alert(e.message)) }
async function pubVersion(id:string) { try { await adminApi.publishVersion(id); loadVersions(); alert('发布成功') } catch(e:any){alert(e.message)} }
async function resolveUnknown(id:string) { const a=prompt('答案:'); if(!a) return; try { await adminApi.resolveUnknownQuestion(id,{resolved_answer:a,add_to_knowledge:false}); loadUnknown(); alert('一键补全成功') } catch(e:any){alert(e.message)} }

onMounted(async () => { await loadEntities(); await loadRelations(); await loadSynonyms(); await loadVersions(); await loadUnknown() })
</script>
