<template>
  <div class="page-container">
    <div class="container">
      <!-- 无数据状态 -->
      <div v-if="!documentStore.documentResult" class="empty-container">
        <el-icon size="64" color="#c0c4cc"><Document /></el-icon>
        <div class="empty-text">
          <p>暂无文档数据</p>
          <p>请先在首页上传并分析文档</p>
        </div>
        <el-button type="primary" @click="$router.push('/')">
          <el-icon><Upload /></el-icon>
          上传文档
        </el-button>
      </div>

      <!-- 文档预览 -->
      <div v-else class="preview-layout">
        <!-- 左侧目录导航 -->
        <div class="toc-sidebar">
          <div class="sidebar-header">
            <h3>文档目录</h3>
            <el-button
              type="primary"
              text
              size="small"
              @click="toggleFullscreen"
            >
              <el-icon><FullScreen /></el-icon>
              全屏预览
            </el-button>
          </div>

          <div class="toc-content">
            <div
              v-for="(item, index) in tocItems"
              :key="index"
              class="toc-item"
              :class="{ active: activeChapter === index }"
              @click="scrollToChapter(index)"
            >
              <div class="toc-text">{{ item.text }}</div>
              <div class="toc-level">{{ item.level }}</div>
            </div>
          </div>
        </div>

        <!-- 右侧文档内容 -->
        <div class="document-main">
          <div class="document-header">
            <div class="document-title">
              <el-icon><Document /></el-icon>
              {{ documentStore.documentResult?.filename || '文档预览' }}
            </div>
            <div class="document-actions">
              <el-button
                type="primary"
                @click="$router.push('/analysis')"
                :disabled="!hasEvaluation"
              >
                <el-icon><DataAnalysis /></el-icon>
                查看分析结果
              </el-button>
            </div>
          </div>

          <div
            ref="documentContent"
            class="document-preview"
            :class="{ fullscreen: isFullscreen }"
          >
            <div
              class="document-content"
              v-html="documentStore.documentResult?.html_content"
            ></div>
          </div>
        </div>
      </div>

      <!-- 全屏遮罩 -->
      <div
        v-if="isFullscreen"
        class="fullscreen-overlay"
        @click="toggleFullscreen"
      >
        <div class="fullscreen-content" @click.stop>
          <div class="fullscreen-header">
            <h3>{{ documentStore.documentResult?.filename || '文档预览' }}</h3>
            <el-button
              type="primary"
              text
              @click="toggleFullscreen"
            >
              <el-icon><Close /></el-icon>
              退出全屏
            </el-button>
          </div>
          <div
            class="fullscreen-document"
            v-html="documentStore.documentResult?.html_content"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  Upload,
  FullScreen,
  Close,
  DataAnalysis
} from '@element-plus/icons-vue'
import { useDocumentStore } from '../stores/document'

export default {
  name: 'DocumentPreview',
  components: {
    Document,
    Upload,
    FullScreen,
    Close,
    DataAnalysis
  },
  setup () {
    const router = useRouter()
    const documentStore = useDocumentStore()

    const documentContent = ref(null)
    const isFullscreen = ref(false)
    const activeChapter = ref(0)

    const tocItems = computed(() => {
      return documentStore.documentResult?.toc_items || []
    })

    const hasEvaluation = computed(() => {
      return documentStore.documentResult?.evaluation &&
             Object.keys(documentStore.documentResult.evaluation).length > 0
    })

    const scrollToChapter = (index) => {
      activeChapter.value = index
      const chapterElement = document.querySelector(`[data-chapter="${index}"]`)
      if (chapterElement) {
        chapterElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
      }
    }

    const toggleFullscreen = () => {
      isFullscreen.value = !isFullscreen.value
      if (isFullscreen.value) {
        document.body.style.overflow = 'hidden'
      } else {
        document.body.style.overflow = 'auto'
      }
    }

    const handleScroll = () => {
      // 根据滚动位置更新活动章节
      const chapters = document.querySelectorAll('[data-chapter]')
      let currentChapter = 0

      chapters.forEach((chapter, index) => {
        const rect = chapter.getBoundingClientRect()
        if (rect.top <= 100) {
          currentChapter = index
        }
      })

      activeChapter.value = currentChapter
    }

    onMounted(async () => {
      // 如果没有文档数据，尝试从路由参数获取或重定向到首页
      if (!documentStore.documentResult) {
        ElMessage.warning('请先上传并分析文档')
        router.push('/')
        return
      }

      // 等待DOM更新后添加滚动监听
      await nextTick()
      if (documentContent.value) {
        documentContent.value.addEventListener('scroll', handleScroll)
      }

      // 为文档内容添加章节标记
      setTimeout(() => {
        addChapterMarkers()
      }, 100)
    })

    onUnmounted(() => {
      if (documentContent.value) {
        documentContent.value.removeEventListener('scroll', handleScroll)
      }
      document.body.style.overflow = 'auto'
    })

    const addChapterMarkers = () => {
      // 为文档中的标题添加章节标记，便于导航
      const headings = document.querySelectorAll('.document-content h1, .document-content h2, .document-content h3')
      headings.forEach((heading, index) => {
        heading.setAttribute('data-chapter', index)
        heading.style.scrollMarginTop = '20px'
      })
    }

    return {
      documentStore,
      documentContent,
      isFullscreen,
      activeChapter,
      tocItems,
      hasEvaluation,
      scrollToChapter,
      toggleFullscreen
    }
  }
}
</script>

<style scoped>
.preview-layout {
  display: flex;
  gap: 20px;
  height: calc(100vh - 100px);
}

.toc-sidebar {
  flex: 0 0 280px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  max-height: 100%;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
  font-weight: 600;
}

.toc-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
}

.toc-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.toc-item:hover {
  background-color: #f5f7fa;
}

.toc-item.active {
  background-color: #ecf5ff;
  border-left-color: #1e3c72;
}

.toc-text {
  flex: 1;
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toc-item.active .toc-text {
  color: #1e3c72;
  font-weight: 500;
}

.toc-level {
  font-size: 12px;
  color: #c0c4cc;
  margin-left: 8px;
}

.document-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.document-header {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.document-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.document-preview {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.document-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  line-height: 1.8;
  font-size: 16px;
}

/* 全屏样式 */
.fullscreen-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.fullscreen-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  height: 90%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.fullscreen-header {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.fullscreen-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
  font-weight: 600;
}

.fullscreen-document {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  line-height: 1.8;
  font-size: 16px;
}

/* 文档内容样式 */
.document-content :deep(h1),
.document-content :deep(h2),
.document-content :deep(h3),
.document-content :deep(h4),
.document-content :deep(h5),
.document-content :deep(h6) {
  margin: 24px 0 16px 0;
  color: #303133;
  font-weight: 600;
}

.document-content :deep(h1) {
  font-size: 24px;
  border-bottom: 2px solid #1e3c72;
  padding-bottom: 8px;
}

.document-content :deep(h2) {
  font-size: 20px;
}

.document-content :deep(h3) {
  font-size: 18px;
}

.document-content :deep(p) {
  margin-bottom: 16px;
  text-align: justify;
  color: #606266;
}

.document-content :deep(img) {
  max-width: 100%;
  height: auto;
  margin: 16px 0;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.document-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.document-content :deep(th),
.document-content :deep(td) {
  border: 1px solid #ebeef5;
  padding: 8px 12px;
  text-align: left;
}

.document-content :deep(th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .preview-layout {
    flex-direction: column;
    height: auto;
  }

  .toc-sidebar {
    flex: none;
    max-height: 200px;
  }

  .document-content {
    padding: 20px;
    font-size: 14px;
  }

  .fullscreen-content {
    width: 95%;
    height: 95%;
  }

  .fullscreen-document {
    padding: 20px;
    font-size: 14px;
  }
}
</style>
