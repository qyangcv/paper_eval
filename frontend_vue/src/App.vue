<template>
  <div id="app">
    <!-- 导航栏 -->
    <NavBar />

    <!-- 主要内容区域 -->
    <main class="main-content">
      <router-view v-slot="{ Component, route }">
        <transition :name="getTransitionName(route)" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script>
import NavBar from './components/NavBar.vue'

export default {
  name: 'App',
  components: {
    NavBar
  },
  methods: {
    getTransitionName (route) {
      // 对于DocumentPreview页面，不使用路由过渡动画，让组件内部的浮现动画独立工作
      if (route.name === 'DocumentPreview') {
        return ''
      }
      return 'page-fade'
    }
  }
}
</script>

<style>
#app {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.main-content {
  padding-top: 60px; /* 为固定导航栏留出空间 */
  min-height: calc(100vh - 60px);
}

/* 现代化页面过渡动效 */
.page-fade-enter-active {
  transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.page-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.55, 0.055, 0.675, 0.19);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.95);
  filter: blur(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(1.05);
  filter: blur(4px);
}
</style>
