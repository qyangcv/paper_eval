<template>
  <nav class="navbar">
    <div class="navbar-container">
      <!-- 左侧标题 -->
      <div class="navbar-brand">
        <h1>北邮本科论文质量评价分析</h1>
      </div>

      <!-- 右侧菜单 -->
      <div class="navbar-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.disabled ? '#' : item.path"
          class="navbar-item"
          :class="{
            active: $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/'),
            disabled: item.disabled
          }"
          @click="item.disabled && $event.preventDefault()"
        >
          <el-icon class="menu-icon">
            <component :is="item.icon" />
          </el-icon>
          {{ item.name }}
        </router-link>
      </div>
    </div>
  </nav>
</template>

<script>
import { House, Document, DataAnalysis } from '@element-plus/icons-vue'
import { useDocumentStore } from '../stores/document'
import { computed } from 'vue'

export default {
  name: 'NavBar',
  setup () {
    const documentStore = useDocumentStore()

    const menuItems = computed(() => {
      const currentTaskId = documentStore.currentTask?.task_id
      const isCompleted = documentStore.isCompleted

      return [
        {
          name: '首页',
          path: '/',
          icon: House
        },
        {
          name: '论文预览',
          path: currentTaskId ? `/preview/${currentTaskId}` : '/preview',
          icon: Document,
          disabled: !currentTaskId || !isCompleted
        },
        {
          name: '数据分析',
          path: currentTaskId ? `/analysis/${currentTaskId}` : '/analysis',
          icon: DataAnalysis,
          disabled: !currentTaskId || !isCompleted
        }
      ]
    })

    return {
      menuItems
    }
  },
  components: {
    House,
    Document,
    DataAnalysis
  }
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.navbar-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.navbar-brand h1 {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 1px;
}

.navbar-menu {
  display: flex;
  align-items: center;
  gap: 30px;
}

.navbar-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-size: 16px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.3s ease;
  position: relative;
}

.navbar-item:hover {
  color: white;
  background-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.navbar-item.active {
  color: white;
  background-color: rgba(255, 255, 255, 0.15);
}

.navbar-item.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background-color: #ffd700;
  border-radius: 1px;
}

.menu-icon {
  font-size: 18px;
}

/* 禁用状态样式 */
.navbar-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.navbar-item.disabled:hover {
  background-color: transparent;
  color: rgba(255, 255, 255, 0.8);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navbar-container {
    padding: 0 15px;
  }

  .navbar-brand h1 {
    font-size: 16px;
  }

  .navbar-menu {
    gap: 15px;
  }

  .navbar-item {
    font-size: 14px;
    padding: 6px 12px;
  }

  .menu-icon {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .navbar-brand h1 {
    font-size: 14px;
  }

  .navbar-menu {
    gap: 10px;
  }

  .navbar-item {
    font-size: 12px;
    padding: 4px 8px;
  }

  .navbar-item span {
    display: none; /* 在小屏幕上只显示图标 */
  }
}
</style>
