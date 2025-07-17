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
  const imageCache = ref(new Map()) // 图片缓存
  const imageList = ref([]) // 当前任务的图片列表

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
      const apiKey = apiKeys.value[modelName] || ''

      // 检查API密钥是否设置
      if (!apiKey && modelName !== 'none') {
        throw new Error(`请先设置${modelName}模型的API密钥`)
      }

      const requestData = {
        task_id: currentTask.value.task_id,
        model_config: {
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
          // 直接从状态响应获取结果，不需要额外的API调用
          documentResult.value = response.data.result
        } else if (response.data.status === 'error') {
          clearInterval(pollInterval)
        }
      } catch (error) {
        console.error('获取状态失败:', error)
        clearInterval(pollInterval)
      }
    }, 1000) // 每秒轮询一次
  }

  const resetState = () => {
    currentTask.value = null
    processingStatus.value = null
    documentResult.value = null
    clearImageCache()
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

  // 更新任务完成状态
  const setTaskCompleted = (taskId) => {
    if (!currentTask.value) {
      currentTask.value = { task_id: taskId }
    }
    processingStatus.value = {
      status: 'completed',
      progress: 1.0,
      message: '分析完成！'
    }
  }

  // 图片相关方法
  const getImageUrl = async (imageName) => {
    if (!currentTask.value) return null

    const cacheKey = `${currentTask.value.task_id}_${imageName}`

    // 检查缓存
    if (imageCache.value.has(cacheKey)) {
      return imageCache.value.get(cacheKey)
    }

    try {
      const response = await api.getDocumentImage(currentTask.value.task_id, `images/${imageName}`)
      const imageBlob = response.data
      const imageUrl = URL.createObjectURL(imageBlob)

      // 缓存图片URL
      imageCache.value.set(cacheKey, imageUrl)
      return imageUrl
    } catch (error) {
      console.error('获取图片失败:', error)
      return null
    }
  }

  const clearImageCache = () => {
    // 释放所有缓存的图片URL
    imageCache.value.forEach(url => {
      URL.revokeObjectURL(url)
    })
    imageCache.value.clear()
    imageList.value = []
  }

  const preloadImages = async () => {
    if (!documentResult.value?.html_content) return
    if (!currentTask.value) return

    const htmlContent = documentResult.value.html_content
    const imgRegex = /<img[^>]+src=["']images\/([^"']+)["'][^>]*>/g
    const imageNames = []
    let match

    while ((match = imgRegex.exec(htmlContent)) !== null) {
      imageNames.push(match[1])
    }

    // 预加载所有图片
    const preloadPromises = imageNames.map(imageName => getImageUrl(imageName))

    try {
      await Promise.all(preloadPromises)
      console.log('图片预加载完成')
    } catch (error) {
      console.error('图片预加载失败:', error)
    }
  }

  return {
    // 状态
    currentTask,
    processingStatus,
    documentResult,
    selectedModel,
    apiKeys,
    imageCache,
    imageList,

    // 计算属性
    isProcessing,
    isCompleted,
    hasError,

    // 方法
    uploadDocument,
    startProcessing,
    resetState,
    setApiKey,
    setSelectedModel,
    setProcessingResult,
    setTaskCompleted,
    getImageUrl,
    clearImageCache,
    preloadImages
  }
})
