<template>
  <div>
    <div class="flex items-center gap-2 mb-2">
      <label class="text-xs text-on-surface-variant uppercase font-semibold tracking-wider">{{ title }}</label>
      <button @click="showInput = !showInput" class="text-primary hover:text-primary/80 flex items-center gap-0.5">
        <span class="material-symbols-outlined text-sm">{{ showInput ? 'remove' : 'add' }}</span>
        <span class="text-[10px]">{{ showInput ? '收起' : '添加' }}</span>
      </button>
    </div>

    <!-- Search + Add Input -->
    <div v-if="showInput" class="flex flex-col gap-1 mb-2">
      <input
        ref="inputRef"
        v-model="searchText"
        @input="onSearch"
        @keydown.enter="commitFromInput"
        class="flex-1 h-8 px-2 rounded border border-outline-variant bg-surface text-xs focus:border-primary outline-none"
        :placeholder="placeholder"
      />
      <!-- Suggestions dropdown -->
      <div v-if="suggestions.length && searchText.length >= 1"
        class="bg-surface border border-outline-variant rounded shadow-lg max-h-32 overflow-y-auto z-20">
        <button v-for="s in suggestions" :key="s" @click="commitSuggestion(s)"
          class="w-full text-left px-3 py-1.5 text-xs hover:bg-primary/10 hover:text-primary transition-colors border-b border-surface-variant/50 last:border-0">
          <span class="material-symbols-outlined text-[14px] align-middle mr-1">{{ icon }}</span>{{ s }}
        </button>
      </div>
    </div>

    <!-- Tag Chips -->
    <div class="flex flex-wrap gap-1 mt-1">
      <span v-for="(item, i) in items" :key="i"
        :class="['inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs border', colorClass]">
        {{ item }}
        <button @click="$emit('remove', i)" class="material-symbols-outlined text-[14px] hover:opacity-70">close</button>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  title: string
  icon: string
  items: string[]
  suggestions: string[]
  placeholder: string
  colorClass: string
}>()

const emit = defineEmits<{
  add: [value: string]
  remove: [index: number]
  search: [keyword: string]
}>()

const showInput = ref(false)
const searchText = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

function onSearch() {
  const kw = searchText.value.trim()
  if (kw) emit('search', kw)
}

function commitFromInput() {
  const val = searchText.value.trim()
  if (!val) return
  emit('add', val)
  searchText.value = ''
}

function commitSuggestion(val: string) {
  emit('add', val)
  searchText.value = ''
}

watch(showInput, (v) => {
  if (v) {
    setTimeout(() => inputRef.value?.focus(), 50)
  } else {
    searchText.value = ''
  }
})
</script>
