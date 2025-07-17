import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import DocumentPreview from '../views/DocumentPreview.vue'
import DataAnalysis from '../views/DataAnalysis.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: '首页'
    }
  },
  {
    path: '/preview/:taskId',
    name: 'DocumentPreview',
    component: DocumentPreview,
    meta: {
      title: '论文预览'
    }
  },
  {
    path: '/analysis/:taskId',
    name: 'DataAnalysis',
    component: DataAnalysis,
    meta: {
      title: '数据分析'
    }
  },
  // 兼容旧路由（无taskId参数）
  {
    path: '/preview',
    redirect: '/'
  },
  {
    path: '/analysis',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 路由守卫，设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 北邮本科论文质量评价分析`
  }
  next()
})

export default router
