import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 600000, // 10分钟超时，考虑到分析需要5-7分钟
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
  async error => {
    console.error('API请求错误:', error)

    const config = error.config

    // 如果是超时错误且配置了重试，则进行重试
    if (error.code === 'ECONNABORTED' && config && config.retry > 0) {
      config.retry -= 1
      console.log(`请求超时，正在重试... 剩余重试次数: ${config.retry}`)
      console.log('注意：分析通常需要5-7分钟，请耐心等待')

      // 等待一段时间后重试
      if (config.retryDelay) {
        await new Promise(resolve => setTimeout(resolve, config.retryDelay))
      }

      return api(config)
    }

    let message = '请求失败'
    if (error.response) {
      message = error.response.data?.detail || error.response.statusText
    } else if (error.request) {
      if (error.code === 'ECONNABORTED') {
        message = '请求超时，请稍后重试'
      } else {
        message = '网络连接失败'
      }
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
    return api.get(`/api/analysis/${taskId}/issues`, {
      timeout: 480000, // 8分钟超时，给分析留足时间
      // 添加重试机制
      retry: 2, // 减少重试次数，避免过长等待
      retryDelay: 5000 // 增加重试延迟到5秒
    })
  },

  // 获取评估状态
  getEvaluationStatus (taskId) {
    return api.get(`/api/analysis/${taskId}/evaluation-status`, {
      timeout: 15000 // 15秒超时，状态查询应该很快
    })
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
      // 使用Promise.allSettled来处理部分API可能失败的情况（如无模型分析）
      const results = await Promise.allSettled([
        this.getBasicInfo(taskId),
        this.getOverallStats(taskId),
        this.getChapterStats(taskId),
        this.getReferenceStats(taskId),
        this.getEvaluation(taskId),
        this.getIssues(taskId)
      ])

      // 处理结果，为失败的请求提供默认值
      const [
        basicInfoResult,
        overallStatsResult,
        chapterStatsResult,
        referenceStatsResult,
        evaluationResult,
        issuesResult
      ] = results

      return {
        basic_info: basicInfoResult.status === 'fulfilled'
          ? basicInfoResult.value.data
          : {
              title: '未知标题',
              author: '未知作者',
              school: '未知学院',
              advisor: '未知导师',
              keywords: []
            },
        overall_stats: overallStatsResult.status === 'fulfilled'
          ? overallStatsResult.value.data
          : {
              total_words: 0,
              total_chapters: 0,
              total_paragraphs: 0,
              total_images: 0,
              total_tables: 0,
              total_formulas: 0,
              total_references: 0
            },
        chapter_stats: chapterStatsResult.status === 'fulfilled'
          ? chapterStatsResult.value.data
          : {
              chapters: []
            },
        reference_stats: referenceStatsResult.status === 'fulfilled'
          ? referenceStatsResult.value.data
          : {
              total_references: 0,
              by_type: {},
              by_language: {},
              recent_years: {}
            },
        evaluation: evaluationResult.status === 'fulfilled'
          ? evaluationResult.value.data
          : {
              dimensions: [],
              overall_score: 0,
              summary: '无模型分析，未进行质量评估'
            },
        issue_list: issuesResult.status === 'fulfilled'
          ? issuesResult.value.data
          : {
              summary: { total_issues: 0, severity_distribution: {} },
              by_chapter: {}
            }
      }
    } catch (error) {
      console.error('数据加载失败:', error)
      throw error
    }
  }
}
