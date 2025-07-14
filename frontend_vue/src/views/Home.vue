<template>
  <div class="page-container">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
      </div>
    </div>

    <div class="container">
      <!-- 主标题区域 -->
      <div class="hero-section">
        <div class="hero-content">
          <div class="hero-badge">
            <span class="badge-text">🎓 AI驱动</span>
          </div>
          <h1 class="hero-title">
            <span class="title-gradient">北邮本科论文</span>
            <span class="title-highlight">质量评价分析系统</span>
          </h1>
          <p class="hero-subtitle">
            基于人工智能技术，为您的学术论文提供专业、全面的质量评估与优化建议
          </p>

          <!-- 特性展示 -->
          <div class="features-grid">
            <div class="feature-card" v-for="(feature, index) in features" :key="index"
                 :style="{ animationDelay: `${index * 0.1}s` }">
              <div class="feature-icon">
                <el-icon>
                  <TrendCharts v-if="feature.title === '智能分析'" />
                  <ChatDotRound v-else-if="feature.title === '专业评估'" />
                  <MagicStick v-else-if="feature.title === '优化建议'" />
                  <Star v-else-if="feature.title === '快速预览'" />
                </el-icon>
              </div>
              <div class="feature-content">
                <h3>{{ feature.title }}</h3>
                <p>{{ feature.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 上传分析区域 -->
      <div class="analysis-section">
        <div class="analysis-container">
          <div class="section-header">
            <h2>📄 开始分析您的论文</h2>
            <p>上传您的Word文档，让AI为您提供专业的质量评估</p>
          </div>

          <div class="upload-area">
            <el-upload
              ref="uploadRef"
              class="upload-dragger"
              drag
              :auto-upload="false"
              :show-file-list="false"
              accept=".docx"
              :on-change="handleFileChange"
            >
              <div class="upload-content">
                <div class="upload-icon">
                  <el-icon class="upload-icon-element"><upload-filled /></el-icon>
                </div>
                <div class="upload-text">
                  <h3>拖拽文档到此处</h3>
                  <p>或 <span class="upload-link">点击选择文件</span></p>
                </div>
                <div class="upload-tips">
                  <span class="tip-item">📄 支持 .docx 格式</span>
                  <span class="tip-item">📏 文件大小 ≤ 10MB</span>
                  <span class="tip-item">⚡ 智能快速分析</span>
                </div>
              </div>
            </el-upload>

            <!-- 文件信息卡片 -->
            <transition name="slide-up" appear>
              <div v-if="selectedFile" class="file-card">
                <div class="file-header">
                  <div class="file-icon">
                    <el-icon><Document /></el-icon>
                  </div>
                  <div class="file-details">
                    <h4 class="file-name">{{ selectedFile.name }}</h4>
                    <p class="file-meta">
                      <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
                      <span class="file-type">Word文档</span>
                    </p>
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    circle
                    @click="removeFile"
                    class="remove-btn"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </transition>

            <!-- 配置面板 -->
            <div class="config-panel">
              <div class="config-section">
                <h3 class="config-title">🤖 AI模型配置</h3>
                <div class="model-selector">
                  <el-select
                    v-model="selectedModel"
                    placeholder="选择分析模型"
                    class="model-select"
                    size="large"
                  >
                    <el-option
                      v-for="model in modelOptions"
                      :key="model.value"
                      :label="model.label"
                      :value="model.value"
                    >
                      <div class="model-option">
                        <span class="model-name">{{ model.label }}</span>
                        <span class="model-desc">{{ model.description }}</span>
                      </div>
                    </el-option>
                  </el-select>

                  <el-button
                    type="primary"
                    plain
                    @click="showApiDialog = true"
                    class="config-btn"
                  >
                    <el-icon><Setting /></el-icon>
                    配置密钥
                  </el-button>
                </div>

                <div class="api-status-card" v-if="getApiStatus()">
                  <el-tag
                    :type="getApiStatus().type"
                    size="large"
                    class="status-tag"
                  >
                    <el-icon class="status-icon">
                      <component :is="getApiStatus().type === 'success' ? 'Check' : 'Warning'" />
                    </el-icon>
                    {{ getApiStatus().message }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 分析按钮 -->
            <div class="action-section">
              <div class="action-buttons">
                <el-button
                  type="primary"
                  size="large"
                  :disabled="!selectedFile || isProcessing"
                  :loading="isProcessing"
                  @click="startAnalysis"
                  class="analysis-btn"
                >
                  <el-icon v-if="!isProcessing"><DataAnalysis /></el-icon>
                  <span>{{ isProcessing ? '正在分析中...' : '🚀 开始智能分析' }}</span>
                </el-button>

                <el-button
                  type="success"
                  size="large"
                  plain
                  @click="loadTestPreview"
                  class="test-btn"
                >
                  <el-icon><Document /></el-icon>
                  <span>📖 测试预览</span>
                </el-button>
              </div>

              <div class="analysis-info" v-if="!selectedFile">
                <p>💡 请先上传Word文档以开始分析，或点击"测试预览"查看示例</p>
              </div>
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
  Loading,
  TrendCharts,
  ChatDotRound,
  MagicStick,
  Warning
} from '@element-plus/icons-vue'
import { useDocumentStore } from '../stores/document'
import ProcessingDialog from '../components/ProcessingDialog.vue'
import api from '../services/api'

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
    TrendCharts,
    ChatDotRound,
    MagicStick,
    Warning,
    ProcessingDialog
  },
  setup () {
    const router = useRouter()
    const documentStore = useDocumentStore()

    const selectedFile = ref(null)
    const showApiDialog = ref(false)
    const showProcessingDialog = ref(false)
    const selectedModel = ref(documentStore.selectedModel)

    // 特性数据
    const features = ref([
      {
        title: '智能分析',
        description: '深度解析论文结构与内容质量'
      },
      {
        title: '专业评估',
        description: '基于学术标准的全面质量评价'
      },
      {
        title: '优化建议',
        description: '提供针对性的改进方案'
      },
      {
        title: '快速预览',
        description: '一键生成可视化分析报告'
      }
    ])

    // 模型选项
    const modelOptions = ref([
      {
        value: 'deepseek-chat',
        label: 'DeepSeek Chat',
        description: '通用对话模型，适合基础分析'
      },
      {
        value: 'deepseek-reasoner',
        label: 'DeepSeek Reasoner',
        description: '推理模型，适合深度分析'
      },
      {
        value: 'gemini',
        label: 'Gemini',
        description: 'Google AI模型，多模态分析'
      },
      {
        value: 'gpt',
        label: 'GPT',
        description: 'OpenAI模型，强大的语言理解'
      },
      {
        value: 'none',
        label: '无模型分析',
        description: '基础结构分析，无需API'
      }
    ])

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
        const uploadResponse = await api.uploadDocument(formData)

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
        await api.startProcessing(processRequestData)

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
          const response = await api.getStatus(currentTaskId.value)
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
        api.deleteTask(currentTaskId.value)
          .catch(error => console.error('取消任务失败:', error))
      }

      showProcessingDialog.value = false
      isProcessing.value = false
      processingStatus.value = 'pending'
      processingProgress.value = 0
      currentTaskId.value = null
    }

    // 加载测试预览
    const loadTestPreview = async () => {
      try {
        const success = await documentStore.loadTestFile()
        if (success) {
          ElMessage.success('测试文件加载成功！')
          router.push('/preview')
        } else {
          ElMessage.error('测试文件加载失败')
        }
      } catch (error) {
        console.error('加载测试文件失败:', error)
        ElMessage.error('测试文件加载失败')
      }
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
      features,
      modelOptions,
      handleFileChange,
      removeFile,
      formatFileSize,
      getApiStatus,
      saveApiConfig,
      startAnalysis,
      retryProcessing,
      viewResults,
      cancelProcessing,
      loadTestPreview
    }
  }
}
</script>

<style scoped>
/* 背景装饰 */
.background-decoration {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: -1;
  overflow: hidden;
}

.floating-shapes {
  position: relative;
  width: 100%;
  height: 100%;
}

.shape {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(30, 60, 114, 0.1), rgba(42, 82, 152, 0.05));
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 120px;
  height: 120px;
  top: 20%;
  right: 15%;
  animation-delay: 1s;
}

.shape-3 {
  width: 60px;
  height: 60px;
  bottom: 30%;
  left: 20%;
  animation-delay: 2s;
}

.shape-4 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  right: 25%;
  animation-delay: 3s;
}

.shape-5 {
  width: 40px;
  height: 40px;
  top: 50%;
  left: 50%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

/* 主标题区域 */
.hero-section {
  text-align: center;
  padding: 30px 0 40px 0;
  margin-bottom: 20px;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-badge {
  display: inline-block;
  margin-bottom: 20px;
  animation: slideInDown 0.8s ease-out;
}

.badge-text {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  color: white;
  padding: 8px 20px;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(30, 60, 114, 0.3);
}

.hero-title {
  font-size: 48px;
  font-weight: 800;
  margin-bottom: 20px;
  line-height: 1.2;
  animation: slideInUp 0.8s ease-out 0.2s both;
}

.title-gradient {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: block;
}

.title-highlight {
  color: #303133;
  display: block;
  margin-top: 10px;
}

.hero-subtitle {
  font-size: 20px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 40px;
  animation: slideInUp 0.8s ease-out 0.4s both;
}

/* 特性网格 */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 30px;
}

.feature-card {
  background: white;
  border-radius: 16px;
  padding: 30px 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  animation: slideInUp 0.6s ease-out both;
  border: 1px solid rgba(30, 60, 114, 0.1);
  text-align: center;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
}

.feature-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px auto;
  color: white;
  font-size: 24px;
}

.feature-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.feature-content p {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

/* 分析区域 */
.analysis-section {
  background: white;
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 40px;
  margin-top: 20px;
}

.analysis-container {
  padding: 30px;
}

.section-header {
  text-align: center;
  margin-bottom: 30px;
}

.section-header h2 {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 12px;
}

.section-header p {
  font-size: 16px;
  color: #606266;
  line-height: 1.6;
}

/* 上传区域 */
.upload-area {
  margin-bottom: 30px;
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  width: 100%;
  height: auto;
  min-height: 200px;
  border: 3px dashed #e4e7ed;
  border-radius: 20px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  transition: all 0.4s ease;
  padding: 40px 20px;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: #1e3c72;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8f0ff 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(30, 60, 114, 0.15);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.upload-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 2s infinite;
}

.upload-icon-element {
  font-size: 36px;
  color: white;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(30, 60, 114, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(30, 60, 114, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(30, 60, 114, 0);
  }
}

.upload-text h3 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.upload-text p {
  font-size: 16px;
  color: #606266;
  margin: 8px 0 0 0;
}

.upload-link {
  color: #1e3c72;
  font-weight: 600;
  cursor: pointer;
}

.upload-tips {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
}

.tip-item {
  background: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  color: #606266;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(30, 60, 114, 0.1);
}

/* 文件卡片 */
.file-card {
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  border-radius: 16px;
  padding: 20px;
  margin: 20px 0;
  border: 1px solid rgba(30, 60, 114, 0.1);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.file-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.file-meta {
  display: flex;
  gap: 12px;
  margin: 0;
}

.file-size, .file-type {
  font-size: 14px;
  color: #606266;
  background: white;
  padding: 4px 12px;
  border-radius: 12px;
  border: 1px solid rgba(30, 60, 114, 0.1);
}

.remove-btn {
  background: #f56c6c;
  border-color: #f56c6c;
  color: white;
}

.remove-btn:hover {
  background: #f78989;
  border-color: #f78989;
}

/* 配置面板 */
.config-panel {
  background: #f8f9ff;
  border-radius: 16px;
  padding: 24px;
  margin: 20px 0;
  border: 1px solid rgba(30, 60, 114, 0.1);
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.model-selector {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.model-select {
  flex: 1;
  min-width: 250px;
}

.model-select :deep(.el-input__wrapper) {
  border-radius: 12px;
  border: 2px solid #e4e7ed;
  transition: all 0.3s ease;
}

.model-select :deep(.el-input__wrapper:hover) {
  border-color: #1e3c72;
}

.model-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.model-name {
  font-weight: 600;
  color: #303133;
}

.model-desc {
  font-size: 12px;
  color: #909399;
}

.config-btn {
  border-radius: 12px;
  border: 2px solid #1e3c72;
  color: #1e3c72;
  font-weight: 600;
}

.config-btn:hover {
  background: #1e3c72;
  color: white;
}

.api-status-card {
  display: flex;
  justify-content: center;
}

.status-tag {
  padding: 8px 16px;
  border-radius: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-icon {
  font-size: 16px;
}

/* 操作区域 */
.action-section {
  text-align: center;
  margin-top: 30px;
}

.action-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
}

.analysis-btn {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  border: none;
  border-radius: 16px;
  padding: 16px 40px;
  font-size: 18px;
  font-weight: 600;
  color: white;
  box-shadow: 0 8px 25px rgba(30, 60, 114, 0.3);
  transition: all 0.3s ease;
}

.analysis-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(30, 60, 114, 0.4);
}

.analysis-btn:disabled {
  background: #c0c4cc;
  box-shadow: none;
}

.test-btn {
  border-radius: 16px;
  padding: 16px 32px;
  font-size: 18px;
  font-weight: 600;
  border: 2px solid #67c23a;
  color: #67c23a;
  background: white;
  box-shadow: 0 8px 25px rgba(103, 194, 58, 0.2);
  transition: all 0.3s ease;
}

.test-btn:hover {
  background: #67c23a;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(103, 194, 58, 0.3);
}

.analysis-info {
  margin-top: 16px;
}

.analysis-info p {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

/* 动画效果 */
@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Vue过渡动画 */
.slide-up-enter-active {
  transition: all 0.4s ease-out;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

/* API配置对话框样式 */
.api-config {
  padding: 20px 0;
}

.api-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .analysis-container {
    padding: 30px;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 36px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .features-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .feature-card {
    padding: 20px 16px;
  }

  .analysis-container {
    padding: 20px;
  }

  .section-header h2 {
    font-size: 24px;
  }

  .upload-content {
    gap: 16px;
  }

  .upload-icon {
    width: 60px;
    height: 60px;
  }

  .upload-icon-element {
    font-size: 28px;
  }

  .upload-text h3 {
    font-size: 18px;
  }

  .upload-tips {
    gap: 12px;
  }

  .tip-item {
    font-size: 12px;
    padding: 6px 12px;
  }

  .model-selector {
    flex-direction: column;
    align-items: stretch;
  }

  .model-select {
    min-width: auto;
  }

  .analysis-btn {
    padding: 14px 32px;
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .hero-section {
    padding: 40px 0;
  }

  .hero-title {
    font-size: 28px;
  }

  .hero-subtitle {
    font-size: 16px;
  }

  .badge-text {
    font-size: 12px;
    padding: 6px 16px;
  }

  .feature-icon {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }

  .upload-dragger :deep(.el-upload-dragger) {
    padding: 30px 15px;
    min-height: 160px;
  }

  .upload-tips {
    flex-direction: column;
    gap: 8px;
  }

  .file-header {
    gap: 12px;
  }

  .file-icon {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }

  .config-panel {
    padding: 20px;
  }

  .analysis-btn {
    padding: 12px 24px;
    font-size: 14px;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .shape {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  }
}
</style>
