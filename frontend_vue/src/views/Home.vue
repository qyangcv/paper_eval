<template>
  <div class="page-container">
    <div class="container">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <div class="welcome-content">
          <div class="welcome-text">
            <h1>📄 Word文档分析器</h1>
            <p class="subtitle">智能分析论文质量，提供专业评估建议</p>
            <div class="features">
              <div class="feature-item">
                <el-icon><Document /></el-icon>
                <span>智能预览</span>
              </div>
              <div class="feature-item">
                <el-icon><Search /></el-icon>
                <span>结构分析</span>
              </div>
              <div class="feature-item">
                <el-icon><Star /></el-icon>
                <span>质量评估</span>
              </div>
              <div class="feature-item">
                <el-icon><Check /></el-icon>
                <span>智能优化</span>
              </div>
            </div>
          </div>

          <!-- 上传区域 -->
          <div class="upload-section">
            <el-upload
              ref="uploadRef"
              class="upload-dragger"
              drag
              :auto-upload="false"
              :show-file-list="false"
              accept=".docx"
              :on-change="handleFileChange"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将Word文档拖拽到此处，或<em>点击上传</em>
              </div>
              <div class="el-upload__tip">
                仅支持 .docx 格式，文件大小不超过 10MB
              </div>
            </el-upload>

            <!-- 文件信息 -->
            <div v-if="selectedFile" class="file-info">
              <div class="file-item">
                <el-icon><Document /></el-icon>
                <span class="file-name">{{ selectedFile.name }}</span>
                <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="removeFile"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>

            <!-- 模型配置 -->
            <div class="model-config">
              <div class="config-row">
                <label>分析模型：</label>
                <el-select
                  v-model="selectedModel"
                  placeholder="选择模型"
                  style="width: 200px"
                >
                  <el-option label="DeepSeek Chat" value="deepseek-chat" />
                  <el-option label="DeepSeek Reasoner" value="deepseek-reasoner" />
                  <el-option label="Gemini" value="gemini" />
                  <el-option label="GPT" value="gpt" />
                  <el-option label="无模型分析" value="none" />
                </el-select>
                <el-button
                  type="primary"
                  text
                  @click="showApiDialog = true"
                  :icon="Setting"
                >
                  配置API密钥
                </el-button>
              </div>
              <div class="api-status" v-if="getApiStatus()">
                <el-tag :type="getApiStatus().type" size="small">
                  {{ getApiStatus().message }}
                </el-tag>
              </div>
            </div>

            <!-- 开始分析按钮 -->
            <div class="action-buttons">
              <el-button
                type="primary"
                size="large"
                :disabled="!selectedFile || isProcessing"
                :loading="isProcessing"
                @click="startAnalysis"
              >
                <el-icon><DataAnalysis /></el-icon>
                {{ isProcessing ? '分析中...' : '开始分析' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>

    <!-- 处理过程对话框 -->
    <ProcessingDialog
      v-model="showProcessingDialog"
      :status="processingStatus"
      :progress="processingProgress"
      :message="processingMessage"
      :model-name="selectedModel"
      :error="processingError"
      @retry="retryProcessing"
      @complete="viewResults"
      @cancel="cancelProcessing"
    />
    </div>

    <!-- API配置对话框 -->
    <el-dialog
      v-model="showApiDialog"
      title="配置API密钥"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="api-config">
        <el-form label-width="120px">
          <el-form-item label="DeepSeek API:">
            <el-input
              v-model="apiKeys.deepseek"
              type="password"
              placeholder="sk-e6068e4723e74a4b8a8e2788cf7ac055"
              show-password
            />
            <div class="api-hint">
              支持 deepseek-chat 和 deepseek-reasoner 模型
            </div>
          </el-form-item>
          <el-form-item label="Gemini API:">
            <el-input
              v-model="apiKeys.gemini"
              type="password"
              placeholder="输入Gemini API密钥"
              show-password
            />
          </el-form-item>
          <el-form-item label="GPT API:">
            <el-input
              v-model="apiKeys.gpt"
              type="password"
              placeholder="输入OpenAI API密钥"
              show-password
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showApiDialog = false">取消</el-button>
        <el-button type="primary" @click="saveApiConfig">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  Search,
  Star,
  Check,
  UploadFilled,
  Delete,
  Setting,
  DataAnalysis,
  Loading
} from '@element-plus/icons-vue'
import { useDocumentStore } from '../stores/document'
import ProcessingDialog from '../components/ProcessingDialog.vue'
import axios from 'axios'

export default {
  name: 'Home',
  components: {
    Document,
    Search,
    Star,
    Check,
    UploadFilled,
    Delete,
    Setting,
    DataAnalysis,
    Loading,
    ProcessingDialog
  },
  setup () {
    const router = useRouter()
    const documentStore = useDocumentStore()

    const selectedFile = ref(null)
    const showApiDialog = ref(false)
    const showProcessingDialog = ref(false)
    const selectedModel = ref(documentStore.selectedModel)

    // API密钥管理
    const apiKeys = ref({
      deepseek: documentStore.apiKeys.deepseek || 'sk-e6068e4723e74a4b8a8e2788cf7ac055',
      gemini: documentStore.apiKeys.gemini || '',
      gpt: documentStore.apiKeys.gpt || ''
    })

    // 监听和同步选择的模型到store
    watch(selectedModel, (newValue) => {
      documentStore.setSelectedModel(newValue)
    })

    // 处理状态
    const isProcessing = ref(false)
    const processingStatus = ref('pending') // pending, processing, completed, error
    const processingProgress = ref(0)
    const processingMessage = ref('')
    const processingError = ref('')
    const currentTaskId = ref(null)

    // API状态检查
    const getApiStatus = () => {
      const model = selectedModel.value
      if (model === 'none') return null

      let key = ''
      if (model.startsWith('deepseek')) {
        key = apiKeys.value.deepseek
      } else if (model === 'gemini') {
        key = apiKeys.value.gemini
      } else if (model === 'gpt') {
        key = apiKeys.value.gpt
      }

      if (!key) {
        return { type: 'warning', message: '请配置API密钥' }
      }
      return { type: 'success', message: 'API密钥已配置' }
    }

    const handleFileChange = (file) => {
      if (file.size > 10 * 1024 * 1024) {
        ElMessage.error('文件大小不能超过10MB')
        return
      }
      selectedFile.value = file.raw
    }

    const removeFile = () => {
      selectedFile.value = null
    }

    const formatFileSize = (size) => {
      if (size < 1024) return size + ' B'
      if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
      return (size / (1024 * 1024)).toFixed(1) + ' MB'
    }

    const saveApiConfig = () => {
      // 保存到localStorage
      localStorage.setItem('apiKeys', JSON.stringify(apiKeys.value))

      // 更新store中的API密钥
      documentStore.setApiKey('deepseek', apiKeys.value.deepseek)
      documentStore.setApiKey('gemini', apiKeys.value.gemini)
      documentStore.setApiKey('gpt', apiKeys.value.gpt)

      ElMessage.success('API密钥配置已保存')
      showApiDialog.value = false
    }

    const startAnalysis = async () => {
      if (!selectedFile.value) {
        ElMessage.error('请先选择文档')
        return
      }

      // 检查API密钥
      if (selectedModel.value !== 'none') {
        const status = getApiStatus()
        if (status?.type === 'warning') {
          ElMessage.error('请先配置API密钥')
          showApiDialog.value = true
          return
        }
      }

      try {
        // 重置状态
        processingStatus.value = 'pending'
        processingProgress.value = 0
        processingMessage.value = '准备上传文档...'
        processingError.value = ''
        isProcessing.value = true
        showProcessingDialog.value = true

        // 同步当前API密钥到store
        documentStore.setSelectedModel(selectedModel.value)
        if (selectedModel.value.startsWith('deepseek')) {
          documentStore.setApiKey('deepseek', apiKeys.value.deepseek)
        } else if (selectedModel.value === 'gemini') {
          documentStore.setApiKey('gemini', apiKeys.value.gemini)
        } else if (selectedModel.value === 'gpt') {
          documentStore.setApiKey('gpt', apiKeys.value.gpt)
        }

        // 1. 上传文档
        processingStatus.value = 'processing'
        processingMessage.value = '正在上传文档...'

        // 上传文档
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        const uploadResponse = await axios.post('http://localhost:8000/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        currentTaskId.value = uploadResponse.data.task_id
        processingProgress.value = 0.1
        processingMessage.value = '文档上传成功，准备开始分析...'

        // 2. 开始处理 - 直接使用axios发送请求
        const modelName = selectedModel.value
        let apiKey = apiKeys.value[modelName] || ''

        // 如果是deepseek模型且没有设置API密钥，使用默认密钥
        if (modelName.startsWith('deepseek') && !apiKey) {
          apiKey = 'sk-e6068e4723e74a4b8a8e2788cf7ac055'
          console.log('使用默认DeepSeek API密钥')
        }

        const processRequestData = {
          task_id: currentTaskId.value,
          model_config: {
            model_name: modelName,
            api_key: apiKey
          }
        }

        console.log('发送处理请求:', JSON.stringify(processRequestData))
        await axios.post('http://localhost:8000/api/process', processRequestData)

        // 3. 轮询状态
        await pollProcessingStatus()
      } catch (error) {
        console.error('分析失败:', error)
        processingStatus.value = 'error'
        processingError.value = error.response?.data?.detail || error.message || '分析失败'
        ElMessage.error('分析失败：' + processingError.value)
      }
    }

    const pollProcessingStatus = async () => {
      const pollInterval = setInterval(async () => {
        try {
          const response = await axios.get(`http://localhost:8000/api/status/${currentTaskId.value}`)
          const status = response.data

          processingProgress.value = status.progress
          processingMessage.value = status.message

          if (status.status === 'completed') {
            clearInterval(pollInterval)
            processingStatus.value = 'completed'
            processingProgress.value = 1.0
            processingMessage.value = '分析完成！'

            // 保存结果到store
            documentStore.setProcessingResult(status.result)

            ElMessage.success('文档分析完成！')
          } else if (status.status === 'error') {
            clearInterval(pollInterval)
            processingStatus.value = 'error'
            processingError.value = status.error || '处理失败'
            ElMessage.error('分析失败：' + processingError.value)
          }
        } catch (error) {
          console.error('轮询状态失败:', error)
          clearInterval(pollInterval)
          processingStatus.value = 'error'
          processingError.value = '无法获取处理状态'
        }
      }, 1000)
    }

    const retryProcessing = () => {
      showProcessingDialog.value = false
      setTimeout(() => {
        startAnalysis()
      }, 500)
    }

    const viewResults = () => {
      showProcessingDialog.value = false
      isProcessing.value = false
      router.push('/preview')
    }

    const cancelProcessing = () => {
      if (currentTaskId.value) {
        // 可以调用取消API
        axios.delete(`http://localhost:8000/api/task/${currentTaskId.value}`)
          .catch(error => console.error('取消任务失败:', error))
      }

      showProcessingDialog.value = false
      isProcessing.value = false
      processingStatus.value = 'pending'
      processingProgress.value = 0
      currentTaskId.value = null
    }

    onMounted(() => {
      // 加载保存的API密钥
      const savedKeys = localStorage.getItem('apiKeys')
      if (savedKeys) {
        try {
          const parsed = JSON.parse(savedKeys)
          apiKeys.value = { ...apiKeys.value, ...parsed }

          // 同步到store
          if (parsed.deepseek) documentStore.setApiKey('deepseek', parsed.deepseek)
          if (parsed.gemini) documentStore.setApiKey('gemini', parsed.gemini)
          if (parsed.gpt) documentStore.setApiKey('gpt', parsed.gpt)
        } catch (error) {
          console.error('加载API密钥失败:', error)
        }
      }

      // 重置状态
      documentStore.resetState()
    })

    onUnmounted(() => {
      // 清理
    })

    return {
      documentStore,
      selectedFile,
      showApiDialog,
      showProcessingDialog,
      selectedModel,
      apiKeys,
      isProcessing,
      processingStatus,
      processingProgress,
      processingMessage,
      processingError,
      handleFileChange,
      removeFile,
      formatFileSize,
      getApiStatus,
      saveApiConfig,
      startAnalysis,
      retryProcessing,
      viewResults,
      cancelProcessing
    }
  }
}
</script>

<style scoped>
.welcome-section {
  margin-bottom: 30px;
}

.welcome-content {
  display: flex;
  gap: 40px;
  align-items: flex-start;
}

.welcome-text {
  flex: 1;
}

.welcome-text h1 {
  font-size: 32px;
  color: #303133;
  margin-bottom: 12px;
  font-weight: 700;
}

.subtitle {
  font-size: 18px;
  color: #606266;
  margin-bottom: 24px;
  line-height: 1.6;
}

.features {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #67c23a;
  font-size: 14px;
  font-weight: 500;
}

.upload-section {
  flex: 0 0 400px;
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background-color: #fafafa;
  transition: all 0.3s ease;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: #1e3c72;
  background-color: #f0f4ff;
}

.upload-dragger :deep(.el-icon--upload) {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-dragger :deep(.el-upload__text) {
  color: #606266;
  font-size: 16px;
  margin-bottom: 8px;
}

.upload-dragger :deep(.el-upload__tip) {
  color: #909399;
  font-size: 12px;
}

.file-info {
  margin: 16px 0;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

.model-config {
  margin: 20px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.config-row label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.action-buttons {
  text-align: center;
  margin-top: 24px;
}

.progress-section {
  margin-top: 30px;
}

.waiting-messages {
  margin-top: 20px;
  text-align: center;
}

.waiting-message {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.api-config {
  padding: 20px 0;
}

.api-status {
  margin-top: 8px;
  text-align: center;
}

.api-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .welcome-content {
    flex-direction: column;
    gap: 20px;
  }

  .upload-section {
    flex: none;
  }

  .welcome-text h1 {
    font-size: 24px;
  }

  .subtitle {
    font-size: 16px;
  }

  .features {
    gap: 15px;
  }

  .config-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
