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
      let apiKey = apiKeys.value[modelName] || ''

      // 如果是deepseek模型且没有设置API密钥，使用默认密钥
      if (modelName.startsWith('deepseek') && !apiKey) {
        apiKey = 'sk-e6068e4723e74a4b8a8e2788cf7ac055'
        console.log('使用默认DeepSeek API密钥')
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

  // 图片相关方法
  const getImageUrl = async (imageName) => {
    // 如果是测试模式，直接返回public文件夹中的图片路径
    if (documentResult.value?.isTestMode) {
      return `/images/${imageName}`
    }

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

  // 加载测试文件
  const loadTestFile = async () => {
    try {
      // 加载test_file.html内容
      const response = await fetch('/test_file.html')
      if (!response.ok) {
        throw new Error('无法加载测试文件')
      }

      const htmlContent = await response.text()

      // 提取HTML body内容
      const bodyMatch = htmlContent.match(/<body[^>]*>([\s\S]*?)<\/body>/i)
      const bodyContent = bodyMatch ? bodyMatch[1] : htmlContent

      // 生成简单的目录结构
      const tocItems = []
      const headingRegex = /<h([1-6])[^>]*>(.*?)<\/h[1-6]>/gi
      let match
      let index = 0

      while ((match = headingRegex.exec(bodyContent)) !== null) {
        const level = parseInt(match[1])
        const text = match[2].replace(/<[^>]*>/g, '').trim()
        if (text) {
          tocItems.push({
            level,
            text,
            index: index++
          })
        }
      }

      // 设置文档结果
      documentResult.value = {
        filename: 'test_file.docx',
        html_content: bodyContent,
        toc_items: tocItems,
        isTestMode: true,
        evaluation: {
          // 模拟评估数据
          dimensions: {
            研究内容: { score: 85, weight: 0.3 },
            研究方法: { score: 78, weight: 0.25 },
            论文结构: { score: 92, weight: 0.2 },
            语言表达: { score: 88, weight: 0.15 },
            创新性: { score: 75, weight: 0.1 }
          }
        }
      }

      console.log('测试文件加载成功')
      return true
    } catch (error) {
      console.error('加载测试文件失败:', error)
      return false
    }
  }

  const preloadImages = async () => {
    if (!documentResult.value?.html_content) return

    // 如果是测试模式，不需要预加载
    if (documentResult.value?.isTestMode) {
      console.log('测试模式：跳过图片预加载')
      return
    }

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
    getImageUrl,
    clearImageCache,
    preloadImages,
    loadTestFile
  }
})
