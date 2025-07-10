<template>
  <div id="app">
    <!-- 导航栏 -->
    <NavBar />

    <!-- 主要内容区域 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
import NavBar from './components/NavBar.vue'

export default {
  name: 'App',
  components: {
    NavBar
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
</style>
