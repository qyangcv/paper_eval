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

  // 获取处理结果
  getResult (taskId) {
    return api.get(`/api/result/${taskId}`)
  },

  // 删除任务
  deleteTask (taskId) {
    return api.delete(`/api/task/${taskId}`)
  }
}
