import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 300000, // 5分钟超时，因为文档处理可能需要较长时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加认证token等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    console.error('API请求错误:', error)

    let message = '请求失败'
    if (error.response) {
      message = error.response.data?.detail || error.response.statusText
    } else if (error.request) {
      message = '网络连接失败'
    } else {
      message = error.message
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API方法
export default {
  // 健康检查
  healthCheck () {
    return api.get('/health')
  },

  // 上传文档
  uploadDocument (formData) {
    return api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 开始处理
  startProcessing (data) {
    return api.post('/api/process', data)
  },

  // 获取处理状态
  getStatus (taskId) {
    return api.get(`/api/status/${taskId}`)
  },

  // 删除任务
  deleteTask (taskId) {
    return api.delete(`/api/task/${taskId}`)
  },

  // ========== 数据分析专用API接口 ==========

  // 获取论文基础信息
  getBasicInfo (taskId) {
    return api.get(`/api/analysis/${taskId}/basic-info`)
  },

  // 获取整体统计数据
  getOverallStats (taskId) {
    return api.get(`/api/analysis/${taskId}/overall-stats`)
  },

  // 获取章节详细统计（用于折线图）
  getChapterStats (taskId) {
    return api.get(`/api/analysis/${taskId}/chapter-stats`)
  },

  // 获取参考文献统计（用于饼图）
  getReferenceStats (taskId) {
    return api.get(`/api/analysis/${taskId}/reference-stats`)
  },

  // 获取评价维度数据（用于雷达图和详细评价）
  getEvaluation (taskId) {
    return api.get(`/api/analysis/${taskId}/evaluation`)
  },

  // 获取问题分析数据（用于环形图和问题列表）
  getIssues (taskId) {
    return api.get(`/api/analysis/${taskId}/issues`)
  },

  // ========== 文档预览专用API接口 ==========

  // 获取文档预览数据
  getDocumentPreview (taskId) {
    return api.get(`/api/preview/${taskId}/html`)
  },

  // 获取文档中的图片资源
  getDocumentImage (taskId, imagePath) {
    return api.get(`/api/preview/${taskId}/image`, {
      params: { path: imagePath },
      responseType: 'blob'
    })
  },

  // ========== 数据分析服务类 ==========

  // 并行加载所有数据分析数据
  async loadAllAnalysisData (taskId) {
    try {
      const [
        basicInfo,
        overallStats,
        chapterStats,
        referenceStats,
        evaluation,
        issues
      ] = await Promise.all([
        this.getBasicInfo(taskId),
        this.getOverallStats(taskId),
        this.getChapterStats(taskId),
        this.getReferenceStats(taskId),
        this.getEvaluation(taskId),
        this.getIssues(taskId)
      ])

      return {
        basic_info: basicInfo.data,
        overall_stats: overallStats.data,
        chapter_stats: chapterStats.data,
        reference_stats: referenceStats.data,
        evaluation: evaluation.data,
        issue_list: issues.data
      }
    } catch (error) {
      console.error('数据加载失败:', error)
      throw error
    }
  }
}
