import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useDocumentStore = defineStore('document', () => {
  // 状态
  const currentTask = ref(null)
  const processingStatus = ref(null)
  const documentResult = ref(null)
  const selectedModel = ref('deepseek')
  const apiKeys = ref({
    deepseek: '',
    gemini: '',
    gpt: ''
  })

  // 计算属性
  const isProcessing = computed(() => {
    return processingStatus.value?.status === 'processing'
  })

  const isCompleted = computed(() => {
    return processingStatus.value?.status === 'completed'
  })

  const hasError = computed(() => {
    return processingStatus.value?.status === 'error'
  })

  // 方法
  const uploadDocument = async (file) => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.uploadDocument(formData)
      currentTask.value = response.data
      return response.data
    } catch (error) {
      console.error('文档上传失败:', error)
      throw error
    }
  }

  const startProcessing = async () => {
    if (!currentTask.value) {
      throw new Error('没有待处理的任务')
    }

    try {
      // 确保deepseek模型有API密钥
      const modelName = selectedModel.value
      let apiKey = apiKeys.value[modelName] || ''

      // 如果是deepseek模型且没有设置API密钥，使用默认密钥
      if (modelName.startsWith('deepseek') && !apiKey) {
        apiKey = 'sk-e6068e4723e74a4b8a8e2788cf7ac055'
        console.log('使用默认DeepSeek API密钥')
      }

      const requestData = {
        task_id: currentTask.value.task_id,
        model_settings: {
          model_name: modelName,
          api_key: apiKey
        }
      }

      console.log('发送处理请求:', JSON.stringify(requestData))
      await api.startProcessing(requestData)

      // 开始轮询状态
      startStatusPolling()
    } catch (error) {
      console.error('开始处理失败:', error)
      throw error
    }
  }

  const startStatusPolling = () => {
    if (!currentTask.value) return

    const pollInterval = setInterval(async () => {
      try {
        const response = await api.getStatus(currentTask.value.task_id)
        processingStatus.value = response.data

        if (response.data.status === 'completed') {
          clearInterval(pollInterval)
          await fetchResult()
        } else if (response.data.status === 'error') {
          clearInterval(pollInterval)
        }
      } catch (error) {
        console.error('获取状态失败:', error)
        clearInterval(pollInterval)
      }
    }, 1000) // 每秒轮询一次
  }

  const fetchResult = async () => {
    if (!currentTask.value) return

    try {
      const response = await api.getResult(currentTask.value.task_id)
      documentResult.value = response.data
    } catch (error) {
      console.error('获取结果失败:', error)
      throw error
    }
  }

  const resetState = () => {
    currentTask.value = null
    processingStatus.value = null
    documentResult.value = null
  }

  const setApiKey = (model, key) => {
    apiKeys.value[model] = key
  }

  const setSelectedModel = (model) => {
    selectedModel.value = model
  }

  const setProcessingResult = (result) => {
    documentResult.value = result
  }

  return {
    // 状态
    currentTask,
    processingStatus,
    documentResult,
    selectedModel,
    apiKeys,

    // 计算属性
    isProcessing,
    isCompleted,
    hasError,

    // 方法
    uploadDocument,
    startProcessing,
    fetchResult,
    resetState,
    setApiKey,
    setSelectedModel,
    setProcessingResult
  }
})
