<template>
  <el-dialog
    v-model="visible"
    title="论文分析处理中"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    center
  >
    <div class="processing-container">
      <!-- 处理状态显示 -->
      <div class="status-section">
        <div class="status-icon">
          <el-icon v-if="status === 'processing'" class="rotating">
            <Loading />
          </el-icon>
          <el-icon v-else-if="status === 'completed'" class="success">
            <Check />
          </el-icon>
          <el-icon v-else-if="status === 'error'" class="error">
            <Close />
          </el-icon>
          <el-icon v-else>
            <Document />
          </el-icon>
        </div>

        <div class="status-text">
          <h3>{{ statusTitle }}</h3>
          <p class="status-message">{{ currentMessage }}</p>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-section">
        <el-progress
          :percentage="Math.round(progress * 100)"
          :status="progressStatus"
          :stroke-width="8"
          :show-text="true"
        />
        <div class="progress-details">
          <span class="progress-text">{{ Math.round(progress * 100) }}%</span>
          <span class="time-info" v-if="elapsedTime > 0">
            已用时: {{ formatTime(elapsedTime) }}
          </span>
        </div>
      </div>

      <!-- 处理步骤 -->
      <div class="steps-section">
        <el-steps :active="currentStep" direction="vertical" :space="60">
          <el-step
            v-for="(step, index) in processingSteps"
            :key="index"
            :title="step.title"
            :description="step.description"
            :status="getStepStatus(index)"
          >
            <template #icon>
              <el-icon v-if="getStepStatus(index) === 'finish'">
                <Check />
              </el-icon>
              <el-icon v-else-if="getStepStatus(index) === 'process'" class="rotating">
                <Loading />
              </el-icon>
              <el-icon v-else>
                <Document />
              </el-icon>
            </template>
          </el-step>
        </el-steps>
      </div>

      <!-- 模型信息 -->
      <div class="model-info" v-if="modelName">
        <el-tag type="info" size="small">
          <el-icon><Cpu /></el-icon>
          使用模型: {{ modelName }}
        </el-tag>
      </div>

      <!-- 错误信息 -->
      <div class="error-section" v-if="status === 'error'">
        <el-alert
          :title="errorMessage"
          type="error"
          :closable="false"
          show-icon
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button
          v-if="status === 'error'"
          type="primary"
          @click="$emit('retry')"
        >
          重试
        </el-button>
        <el-button
          v-if="status === 'completed'"
          type="primary"
          @click="$emit('complete')"
        >
          查看结果
        </el-button>
        <el-button
          v-if="status === 'processing'"
          @click="$emit('cancel')"
        >
          取消
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Loading, Check, Close, Document, Cpu } from '@element-plus/icons-vue'

export default {
  name: 'ProcessingDialog',
  components: {
    Loading,
    Check,
    Close,
    Document,
    Cpu
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    status: {
      type: String,
      default: 'pending' // pending, processing, completed, error
    },
    progress: {
      type: Number,
      default: 0
    },
    message: {
      type: String,
      default: ''
    },
    modelName: {
      type: String,
      default: ''
    },
    error: {
      type: String,
      default: ''
    }
  },
  emits: ['update:modelValue', 'retry', 'complete', 'cancel'],
  setup (props, { emit }) {
    const visible = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    const startTime = ref(null)
    const elapsedTime = ref(0)
    const timer = ref(null)

    const processingSteps = ref([
      {
        title: '文档上传',
        description: '正在上传并验证文档格式'
      },
      {
        title: '文档解析',
        description: '提取文档内容和结构信息'
      },
      {
        title: '大模型分析',
        description: '使用AI模型进行深度内容分析'
      },
      {
        title: '生成报告',
        description: '整合分析结果并生成评估报告'
      },
      {
        title: '完成处理',
        description: '处理完成，准备展示结果'
      }
    ])

    const currentStep = computed(() => {
      if (props.status === 'error') return -1
      if (props.status === 'completed') return processingSteps.value.length
      return Math.floor(props.progress * processingSteps.value.length)
    })

    const currentMessage = computed(() => {
      return props.message || getDefaultMessage()
    })

    const statusTitle = computed(() => {
      switch (props.status) {
        case 'pending':
          return '准备开始处理'
        case 'processing':
          return '正在分析论文'
        case 'completed':
          return '分析完成'
        case 'error':
          return '处理失败'
        default:
          return '处理中'
      }
    })

    const progressStatus = computed(() => {
      switch (props.status) {
        case 'completed':
          return 'success'
        case 'error':
          return 'exception'
        default:
          return undefined
      }
    })

    const errorMessage = computed(() => {
      return props.error || '处理过程中发生未知错误'
    })

    const getDefaultMessage = () => {
      const step = currentStep.value
      if (step >= 0 && step < processingSteps.value.length) {
        return processingSteps.value[step].description
      }
      return '正在处理中...'
    }

    const getStepStatus = (index) => {
      const current = currentStep.value
      if (props.status === 'error') {
        return index < current ? 'finish' : 'wait'
      }
      if (index < current) return 'finish'
      if (index === current) return 'process'
      return 'wait'
    }

    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`
    }

    const startTimer = () => {
      startTime.value = Date.now()
      timer.value = setInterval(() => {
        elapsedTime.value = Math.floor((Date.now() - startTime.value) / 1000)
      }, 1000)
    }

    const stopTimer = () => {
      if (timer.value) {
        clearInterval(timer.value)
        timer.value = null
      }
    }

    watch(() => props.status, (newStatus, oldStatus) => {
      if (newStatus === 'processing' && oldStatus !== 'processing') {
        startTimer()
      } else if (newStatus !== 'processing' && oldStatus === 'processing') {
        stopTimer()
      }
    })

    onMounted(() => {
      if (props.status === 'processing') {
        startTimer()
      }
    })

    onUnmounted(() => {
      stopTimer()
    })

    return {
      visible,
      currentStep,
      currentMessage,
      statusTitle,
      progressStatus,
      errorMessage,
      processingSteps,
      elapsedTime,
      getStepStatus,
      formatTime
    }
  }
}
</script>

<style scoped>
.processing-container {
  padding: 20px 0;
}

.status-section {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.status-icon {
  margin-right: 20px;
  font-size: 48px;
}

.status-icon .rotating {
  animation: rotate 2s linear infinite;
  color: #409eff;
}

.status-icon .success {
  color: #67c23a;
}

.status-icon .error {
  color: #f56c6c;
}

.status-text h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.status-message {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.progress-section {
  margin-bottom: 30px;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.steps-section {
  margin-bottom: 20px;
}

.model-info {
  text-align: center;
  margin-bottom: 20px;
}

.error-section {
  margin-top: 20px;
}

.dialog-footer {
  text-align: center;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

:deep(.el-step__title) {
  font-size: 14px;
  font-weight: 500;
}

:deep(.el-step__description) {
  font-size: 12px;
  color: #999;
}
</style>
