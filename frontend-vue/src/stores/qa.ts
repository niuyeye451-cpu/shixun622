import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message, Conversation, GraphData } from '@/types'
import { patientApi } from '@/api/patient'
import { doctorApi } from '@/api/doctor'

export const useQaStore = defineStore('qa', () => {
  const currentConversationId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const conversations = ref<Conversation[]>([])
  const isLoading = ref(false)
  const currentGraph = ref<GraphData | null>(null)

  const lastAssistantMessage = computed(() => {
    const msgs = messages.value
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === 'assistant') return msgs[i]
    }
    return null
  })

  // Patient: start or continue conversation
  async function sendPatientMessage(content: string) {
    isLoading.value = true
    try {
      let res
      if (!currentConversationId.value) {
        res = await patientApi.createConversation('symptom', content)
        if (res.code === 200) {
          currentConversationId.value = res.data.conversation_id
          messages.value = res.data.messages || []
        }
      } else {
        res = await patientApi.sendMessage(currentConversationId.value, content)
        if (res.code === 200) {
          messages.value.push(res.data)
          if (res.data.assistant_message) messages.value.push(res.data.assistant_message)
        }
      }
    } catch (e) { console.error(e) }
    finally { isLoading.value = false }
  }

  async function loadPatientMessages() {
    if (!currentConversationId.value) return
    const res = await patientApi.getMessages(currentConversationId.value)
    if (res.code === 200) messages.value = res.data.list
  }

  async function loadPatientConversations() {
    const res = await patientApi.getConversations(1, 50)
    if (res.code === 200) conversations.value = res.data.list
  }

  async function selectConversation(id: string) {
    currentConversationId.value = id
    await loadPatientMessages()
  }

  // Doctor case assist
  async function sendDoctorMessage(content: string) {
    isLoading.value = true
    try {
      let res
      if (!currentConversationId.value) {
        res = await doctorApi.createCaseConversation('differential_diagnosis', {}, content)
        if (res.code === 200) {
          currentConversationId.value = res.data.conversation_id
          messages.value = res.data.messages || []
        }
      } else {
        res = await doctorApi.sendCaseMessage(currentConversationId.value, content)
        if (res.code === 200) {
          messages.value.push(res.data)
          if (res.data.assistant_message) messages.value.push(res.data.assistant_message)
        }
      }
    } catch (e) { console.error(e) }
    finally { isLoading.value = false }
  }

  function reset() {
    currentConversationId.value = null
    messages.value = []
    conversations.value = []
    currentGraph.value = null
  }

  return { currentConversationId, messages, conversations, isLoading, currentGraph, lastAssistantMessage, sendPatientMessage, loadPatientMessages, loadPatientConversations, selectConversation, sendDoctorMessage, reset }
})
