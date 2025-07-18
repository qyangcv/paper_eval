<template>
  <div class="document-preview-container" :class="{ 'loaded': isLoaded }">
    <!-- 左侧目录导航 -->
    <div class="sidebar-left">
      <div class="sidebar-header">
        <h3>📚 文档目录</h3>
      </div>
      <div class="directory-tree">
        <div
          v-for="chapter in documentStructure"
          :key="chapter.id"
          class="chapter-item"
          :class="{
            active: activeChapter === chapter.id,
            scrolling: isScrolling && activeChapter === chapter.id
          }"
          @click="scrollToChapter(chapter.id)"
        >
          <div class="chapter-title">
            <i class="chapter-icon">📖</i>
            {{ chapter.title }}
          </div>
          <div v-if="chapter.sections" class="sections">
            <div
              v-for="section in chapter.sections"
              :key="section.id"
              class="section-item"
              :class="{
                active: activeSection === section.id,
                scrolling: isScrolling && activeSection === section.id
              }"
              @click.stop="scrollToSection(section.id)"
            >
              <i class="section-icon">📄</i>
              {{ section.title }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 中间HTML预览区域 -->
    <div class="main-content">
      <div class="content-header">
        <h2>📖 文档预览</h2>

        <!-- 分析状态指示器 -->
        <div v-if="isAnalyzing" class="analysis-status">
          <div class="analysis-indicator">
            <div class="spinner"></div>
            <span class="analysis-text">{{ analysisMessage }}</span>
          </div>
          <div class="analysis-tip">
            <i class="tip-icon">💡</i>
            <span>分析通常需要5-7分钟，页面将自动刷新显示结果</span>
          </div>
        </div>

        <div class="header-actions">
          <button
            class="analysis-button"
            @click="goToDataAnalysis"
            :disabled="!isTaskCompleted"
            :title="isTaskCompleted ? '查看数据分析' : '任务处理中，请稍候...'"
          >
            <i class="analysis-icon">📊</i>
            <span>查看数据分析</span>
          </button>
        </div>
      </div>
      <div class="html-preview" ref="htmlPreview">
        <div v-html="htmlContent" class="document-content"></div>
      </div>
    </div>

    <!-- 右侧问题列表 -->
    <div class="sidebar-right" ref="issuePanel">
      <div class="sidebar-header">
        <h3>⚠️ 问题分析</h3>
      </div>
      <!-- 问题统计 -->
      <div class="issue-stats">
        <div class="stat-item">
          <span class="severity-badge total">总</span>
          <span class="count">{{ issueData.summary?.total_issues || 0 }}</span>
        </div>
        <div class="stat-item" v-for="(count, severity) in issueData.summary?.severity_distribution" :key="severity">
          <span class="severity-badge" :class="severity">{{ severity }}</span>
          <span class="count">{{ count }}</span>
        </div>
      </div>

      <!-- 问题列表 -->
      <div class="issues-list">
        <div v-for="(issues, chapter) in issueData.by_chapter" :key="chapter" class="chapter-issues">
          <div class="chapter-header">
            <h4>{{ chapter }}</h4>
          </div>
          <div
            v-for="issue in issues"
            :key="issue.id"
            class="issue-item"
            :class="issue.severity"
            :data-issue-id="issue.id"
            @click="highlightIssue(issue)"
          >
            <div class="issue-header">
              <span class="issue-type">{{ issue.type }}</span>
              <span class="severity-tag" :class="issue.severity">{{ issue.severity }}</span>
              <!-- 移除模糊匹配徽章，让模糊匹配和正确匹配看起来一样 -->
            </div>
            <div class="issue-location">{{ issue.sub_chapter }}</div>
            <div class="issue-detail">{{ issue.detail }}</div>
            <div class="issue-suggestion">
              <strong>建议：</strong>{{ issue.suggestion }}
            </div>
            <!-- 移除模糊匹配信息显示，让模糊匹配和正确匹配看起来一样 -->
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useDocumentStore } from '../stores/document'
import api from '../services/api'

export default {
  name: 'DocumentPreview',
  data () {
    return {
      htmlContent: '',
      issueData: { summary: { total_issues: 0, severity_distribution: {} }, by_chapter: {} },
      documentFilename: '',
      documentStore: useDocumentStore(),
      activeChapter: null,
      activeSection: null,
      isScrolling: false,
      lastScrollTime: 0,
      scrollTimeout: null,
      scrollDebounceTimeout: null,
      scrollHandlers: [],
      documentStructure: [], // 动态从HTML解析或后端获取
      isLoaded: false, // 控制加载动效
      isTaskCompleted: false, // 任务是否完成
      lastClickTime: 0, // 记录上次点击时间，用于防抖
      documentContent: null, // 文档内容（用于模糊匹配）
      autoRefreshTimer: null, // 自动刷新定时器
      isAnalyzing: false, // 是否正在分析
      analysisProgress: 0, // 分析进度（0-100）
      analysisMessage: '', // 分析状态消息
      api, // 添加API服务
      // HTML高亮缓存机制
      htmlCache: new Map(), // 缓存原始HTML内容，key为元素的唯一标识，value为原始HTML
      highlightedElements: new Set(), // 记录已高亮的元素
      currentHighlightId: null // 当前高亮的issue ID
    }
  },
  watch: {
    issueData: {
      handler (newVal, oldVal) {
        console.log(`[${new Date().toISOString()}] issueData变化:`, {
          old: oldVal,
          new: newVal,
          byChapterKeys: Object.keys(newVal?.by_chapter || {})
        })
      },
      deep: true,
      immediate: true
    }
  },
  mounted () {
    // 延迟一帧以确保DOM渲染完成，然后触发加载动效
    this.$nextTick(() => {
      setTimeout(() => {
        this.isLoaded = true
      }, 50) // 短暂延迟让初始状态生效
    })
    this.initializeMathJax()
    this.initializeComponent()
  },
  beforeUnmount () {
    // 清理事件监听器
    const preview = this.$refs.htmlPreview
    if (preview) {
      preview.removeEventListener('scroll', this.handleScroll)
      preview.removeEventListener('scroll', this.handlePreviewScroll)
    }

    // 清理右侧issue面板滚动监听器
    const issuePanel = this.$refs.issuePanel
    if (issuePanel) {
      issuePanel.removeEventListener('scroll', this.handleIssueScroll)
    }

    // 清理自动刷新定时器
    if (this.autoRefreshTimer) {
      clearTimeout(this.autoRefreshTimer)
      this.autoRefreshTimer = null
    }

    // 清理连接线滚动监听器
    if (this.scrollHandlers) {
      this.scrollHandlers.forEach(({ element, handler }) => {
        element.removeEventListener('scroll', handler)
      })
      this.scrollHandlers = []
    }

    // 清理动画帧
    if (this.updateLinesTimeout) {
      cancelAnimationFrame(this.updateLinesTimeout)
    }

    // 清理高亮和连接线
    this.clearHighlights()

    // 清理超时
    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout)
    }
    if (this.scrollDebounceTimeout) {
      clearTimeout(this.scrollDebounceTimeout)
    }
  },
  methods: {
    async initializeComponent () {
      try {
        await this.loadHtmlContent()
        await this.loadIssueData()
        this.setupScrollListener()
      } catch (error) {
        console.error('组件初始化失败:', error)
      }
    },
    async loadHtmlContent () {
      try {
        // 获取task_id，必须从路由参数获取
        const taskId = this.$route.params.taskId || this.$route.query.taskId

        if (!taskId) {
          throw new Error('缺少任务ID参数')
        }

        // 首先检查任务状态
        const statusResponse = await fetch(`/api/status/${taskId}`)
        if (statusResponse.ok) {
          const statusData = await statusResponse.json()
          console.log('任务状态:', statusData)

          // 更新任务完成状态
          this.isTaskCompleted = statusData.status === 'completed'

          // 如果任务还在处理中，显示处理中的消息
          if (statusData.status === 'processing' || statusData.status === 'pending') {
            this.htmlContent = `
              <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
                <div style="font-size: 48px; margin-bottom: 20px;">⏳</div>
                <h2 style="color: #409eff; margin-bottom: 10px;">文档正在处理中</h2>
                <p style="color: #666; font-size: 16px; margin-bottom: 20px;">${statusData.message || '正在分析文档内容...'}</p>
                <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 15px; margin: 20px auto; max-width: 400px;">
                  <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    <strong>进度:</strong> ${Math.round(statusData.progress * 100)}%
                  </p>
                </div>
                <p style="color: #999; font-size: 14px;">页面将在处理完成后自动刷新</p>
              </div>
            `
            this.documentFilename = '处理中...'

            // 设置定时器，每3秒检查一次状态
            setTimeout(() => {
              this.loadHtmlContent()
            }, 3000)
            return
          }

          // 如果任务失败，显示错误信息
          if (statusData.status === 'error') {
            this.htmlContent = `
              <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
                <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                <h2 style="color: #f56c6c; margin-bottom: 10px;">文档处理失败</h2>
                <p style="color: #666; font-size: 16px; margin-bottom: 20px;">${statusData.error || '处理过程中发生错误'}</p>
                <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; margin: 20px auto; max-width: 400px;">
                  <p style="margin: 0; color: #dc2626; font-size: 14px;">
                    请返回首页重新上传文档
                  </p>
                </div>
              </div>
            `
            this.documentFilename = '处理失败'
            this.$message?.error('文档处理失败：' + (statusData.error || '未知错误'))
            return
          }
        }

        // 使用新的API接口路径
        const response = await fetch(`/api/preview/${taskId}/html`)

        if (!response.ok) {
          // 如果是404错误，可能是文档还没处理完成
          if (response.status === 404) {
            this.htmlContent = `
              <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
                <div style="font-size: 48px; margin-bottom: 20px;">📄</div>
                <h2 style="color: #409eff; margin-bottom: 10px;">文档准备中</h2>
                <p style="color: #666; font-size: 16px; margin-bottom: 20px;">文档正在生成预览内容，请稍候...</p>
                <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 15px; margin: 20px auto; max-width: 400px;">
                  <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    页面将自动重试加载
                  </p>
                </div>
              </div>
            `
            this.documentFilename = '准备中...'

            // 3秒后重试
            setTimeout(() => {
              this.loadHtmlContent()
            }, 3000)
            return
          }
          throw new Error(`API请求失败: ${response.status}`)
        }

        const data = await response.json()

        // 根据最新API文档，后端直接返回html_content和toc_items
        if (data.html_content) {
          this.htmlContent = data.html_content
          // 立即渲染MathJax公式
          this.$nextTick(() => {
            this.renderMathJax()
          })
        } else {
          throw new Error('后端未返回HTML内容')
        }

        // 从document store获取filename，如果没有则使用默认值
        const currentTask = this.documentStore.currentTask
        this.documentFilename = currentTask?.filename
          ? currentTask.filename.replace('.docx', '')
          : '文档预览'

        // 处理图片标记，将图片占位符替换为实际的图片标签
        this.htmlContent = this.processImagePlaceholders(this.htmlContent, taskId)

        // 处理HTML中的图片路径，使用新的图片API接口
        // 匹配 src="images/image_X.png" 格式的图片路径（支持任意数字编号）
        this.htmlContent = this.htmlContent.replace(
          /src="images\/image_(\d+)\.png"/g,
          `src="/api/preview/${taskId}/image?path=images/image_$1.png"`
        )

        // 处理其他可能的图片格式和扩展名
        this.htmlContent = this.htmlContent.replace(
          /src="images\/([^"]+\.(png|jpg|jpeg|gif|bmp|webp))"/gi,
          `src="/api/preview/${taskId}/image?path=images/$1"`
        )

        // 处理没有扩展名的图片引用
        this.htmlContent = this.htmlContent.replace(
          /src="images\/([^".]+)"/g,
          `src="/api/preview/${taskId}/image?path=images/$1.png"`
        )

        // 添加图片加载错误处理和调试信息
        this.htmlContent = this.htmlContent.replace(
          /<img([^>]*?)src="(\/api\/preview\/[^"]*)"([^>]*?)>/g,
          (_, before, src, after) => {
            return `<img${before}src="${src}"${after} onerror="console.warn('图片加载失败:', this.src); this.style.border='2px dashed #ccc'; this.style.padding='10px'; this.alt='图片加载失败: ' + this.src;" onload="console.log('图片加载成功:', this.src);">`
          }
        )

        // 优先从HTML内容解析目录结构，如果解析失败则使用后端返回的toc_items
        this.$nextTick(() => {
          const parsedStructure = this.parseHtmlStructure()
          if (parsedStructure.length > 0) {
            this.documentStructure = parsedStructure
            console.log('使用前端HTML解析的目录结构')
          } else if (data.toc_items && data.toc_items.length > 0) {
            this.updateDocumentStructure(data.toc_items)
            console.log('使用后端返回的目录结构')
          } else {
            console.warn('无法获取文档目录结构')
          }

          // 重新渲染MathJax公式
          this.renderMathJax()
        })
      } catch (error) {
        console.error('加载HTML文件失败:', error)
        this.htmlContent = `
          <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
            <div style="font-size: 48px; margin-bottom: 20px;">⚠️</div>
            <h2 style="color: #f56c6c; margin-bottom: 10px;">文档加载失败</h2>
            <p style="color: #666; font-size: 16px; margin-bottom: 20px;">无法加载文档内容</p>
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; margin: 20px auto; max-width: 400px;">
              <p style="margin: 0; color: #dc2626; font-size: 14px;">
                <strong>错误详情:</strong> ${error.message}
              </p>
            </div>
            <p style="color: #999; font-size: 14px;">请检查任务ID是否正确，或返回首页重新上传</p>
          </div>
        `
        this.documentFilename = '加载失败'
        // 可以在这里添加用户友好的错误提示
        this.$message?.error('文档加载失败：' + error.message)
      }
    },
    parseHtmlStructure () {
      // 从HTML内容中解析目录结构
      const preview = this.$refs.htmlPreview
      if (!preview) return []

      const headers = preview.querySelectorAll('h1, h2, h3, h4, h5, h6')
      const structure = []
      let currentChapter = null
      let chapterIndex = 0
      let sectionIndex = 0

      headers.forEach((header) => {
        const headerText = header.textContent.trim()
        const level = parseInt(header.tagName.substring(1)) // h1 -> 1, h2 -> 2, etc.

        if (level === 1 || headerText.match(/第[一二三四五六七八九十\d]+章/)) {
          // 一级标题或章节标题
          currentChapter = {
            id: `chapter-${chapterIndex++}`,
            title: headerText,
            sections: []
          }
          structure.push(currentChapter)
        } else if (level === 2 && currentChapter && headerText.match(/\d+\.\d+/)) {
          // 二级标题且符合小节格式
          currentChapter.sections.push({
            id: `section-${sectionIndex++}`,
            title: headerText
          })
        }
      })

      return structure
    },
    updateDocumentStructure (tocItems) {
      // 将后端返回的toc_items转换为前端使用的documentStructure格式
      const structure = []
      let currentChapter = null

      tocItems.forEach((item, index) => {
        if (item.level === 1) {
          // 一级标题作为章节
          currentChapter = {
            id: `chapter-${index}`,
            title: item.text,
            sections: []
          }
          structure.push(currentChapter)
        } else if (item.level === 2 && currentChapter) {
          // 二级标题作为小节
          currentChapter.sections.push({
            id: `section-${index}`,
            title: item.text
          })
        }
      })

      if (structure.length > 0) {
        this.documentStructure = structure
      }
    },
    processImagePlaceholders (htmlContent, taskId) {
      // 处理图片占位符，将其替换为实际的图片标签
      // 支持多种占位符格式，兼容不同的后端生成方式

      // 格式1：带有data-image-number属性的完整格式
      const placeholderPattern1 = /<span class="image-placeholder" data-image-src="([^"]+)" data-image-id="([^"]+)" data-image-number="([^"]+)">\{IMAGE_PLACEHOLDER_[^}]+\}<\/span>/g

      // 格式2：不带data-image-number属性的格式
      const placeholderPattern2 = /<span class="image-placeholder" data-image-src="([^"]+)" data-image-id="([^"]+)">\{IMAGE_PLACEHOLDER_[^}]+\}<\/span>/g

      // 格式3：简单的占位符格式
      const placeholderPattern3 = /\{IMAGE_PLACEHOLDER_(\d+)\}/g

      let processedContent = htmlContent

      // 处理格式1（完整格式）
      processedContent = processedContent.replace(placeholderPattern1, (_, imageSrc, imageId, imageNumber) => {
        const apiImageSrc = `/api/preview/${taskId}/image?path=${imageSrc}`
        return `<div class="image-container" style="text-align: center; margin: 15px 0;">
          <img src="${apiImageSrc}" alt="图片 ${imageNumber}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);" data-image-id="${imageId}" data-image-number="${imageNumber}" onerror="this.style.display='none'; console.warn('图片加载失败:', this.src);" />
        </div>`
      })

      // 处理格式2（不带编号）
      processedContent = processedContent.replace(placeholderPattern2, (_, imageSrc, imageId) => {
        const apiImageSrc = `/api/preview/${taskId}/image?path=${imageSrc}`
        // 从imageSrc中提取图片编号
        const imageNumberMatch = imageSrc.match(/image_(\d+)/)
        const imageNumber = imageNumberMatch ? imageNumberMatch[1] : '未知'
        return `<div class="image-container" style="text-align: center; margin: 15px 0;">
          <img src="${apiImageSrc}" alt="图片 ${imageNumber}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);" data-image-id="${imageId}" data-image-number="${imageNumber}" onerror="this.style.display='none'; console.warn('图片加载失败:', this.src);" />
        </div>`
      })

      // 处理格式3（简单占位符）
      processedContent = processedContent.replace(placeholderPattern3, (_, imageNumber) => {
        const apiImageSrc = `/api/preview/${taskId}/image?path=images/image_${imageNumber}.png`
        return `<div class="image-container" style="text-align: center; margin: 15px 0;">
          <img src="${apiImageSrc}" alt="图片 ${imageNumber}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);" data-image-number="${imageNumber}" onerror="this.style.display='none'; console.warn('图片加载失败:', this.src);" />
        </div>`
      })

      // 处理图片和标题的对应关系
      processedContent = this.processImageTitleAlignment(processedContent)

      return processedContent
    },
    processImageTitleAlignment (htmlContent) {
      // 处理图片和标题的对应关系，确保先显示图片，然后是对应的标题
      // 修复逻辑：根据实际情况，图片可能在标题前面或后面，需要智能匹配

      // 查找所有图片容器和可能的图片标题
      const imageContainerPattern = /<div class="image-container"[^>]*>[\s\S]*?<\/div>/g
      const imageTitlePattern = /<p[^>]*>(\s*图\s*[\d\-.]+[^<]*)<\/p>/g

      let processedContent = htmlContent
      const imageContainers = []
      const imageTitles = []

      // 收集所有图片容器
      let match
      while ((match = imageContainerPattern.exec(htmlContent)) !== null) {
        imageContainers.push({
          content: match[0],
          index: match.index,
          endIndex: match.index + match[0].length
        })
      }

      // 收集所有图片标题
      imageTitlePattern.lastIndex = 0 // 重置正则表达式的lastIndex
      while ((match = imageTitlePattern.exec(htmlContent)) !== null) {
        imageTitles.push({
          content: match[0],
          titleText: match[1].trim(),
          index: match.index,
          endIndex: match.index + match[0].length
        })
      }

      // 为每个图片标题找到最近的图片容器
      // 根据后端逻辑，图片通常插入在标题段落后面，所以优先查找标题后面的图片
      const processedImages = new Set()
      const processedTitles = new Set()

      imageTitles.forEach(title => {
        if (processedTitles.has(title.index)) return

        // 首先查找标题后面的图片（这是最常见的情况）
        let nearestImage = null
        let minDistance = Infinity

        imageContainers.forEach(image => {
          if (processedImages.has(image.index)) return

          // 优先查找标题后面的图片
          if (image.index > title.endIndex) {
            const distance = image.index - title.endIndex
            if (distance < minDistance) {
              minDistance = distance
              nearestImage = image
            }
          }
        })

        // 如果没有找到标题后面的图片，再查找标题前面的图片
        if (!nearestImage) {
          imageContainers.forEach(image => {
            if (processedImages.has(image.index)) return

            if (image.endIndex < title.index) {
              const distance = title.index - image.endIndex
              if (distance < minDistance) {
                minDistance = distance
                nearestImage = image
              }
            }
          })
        }

        if (nearestImage) {
          // 创建图片和标题的组合，确保图片在前，标题在后
          const imageWithTitle = `
            <div class="image-with-title" style="text-align: center; margin: 20px 0;">
              ${nearestImage.content.replace('<div class="image-container"', '<div class="image-display"')}
              <p class="image-title" style="margin-top: 10px; color: #666; font-size: 14px; font-weight: 500;">${title.titleText}</p>
            </div>
          `

          // 标记这个图片和标题已处理
          processedImages.add(nearestImage.index)
          processedTitles.add(title.index)

          // 确定替换位置：判断图片和标题的相对位置
          const isImageFirst = nearestImage.index < title.index

          if (isImageFirst) {
            // 图片在标题前面：替换图片位置为组合，移除标题
            processedContent = processedContent.replace(nearestImage.content, imageWithTitle)
            processedContent = processedContent.replace(title.content, '')
          } else {
            // 图片在标题后面：替换标题位置为组合，移除图片
            processedContent = processedContent.replace(title.content, imageWithTitle)
            processedContent = processedContent.replace(nearestImage.content, '')
          }
        }
      })

      return processedContent
    },
    async loadIssueData () {
      try {
        // 获取task_id，必须从路由参数获取
        const taskId = this.$route.params.taskId || this.$route.query.taskId

        if (!taskId) {
          throw new Error('缺少任务ID参数')
        }

        console.log(`[${new Date().toISOString()}] 开始加载问题数据，任务ID:`, taskId)

        // 首先检查任务状态 - 使用API服务而不是直接fetch
        try {
          const statusResponse = await this.api.getStatus(taskId)
          const statusData = statusResponse.data
          console.log('任务状态:', statusData)

          // 如果任务还在处理中或失败，不加载问题数据
          if (statusData.status === 'processing' || statusData.status === 'pending' || statusData.status === 'error') {
            console.log('任务状态不适合加载问题数据:', statusData.status)
            this.issueData = { summary: { total_issues: 0, severity_distribution: {} }, by_chapter: {} }
            return
          }

          // 如果任务已完成，停止任何轮询
          if (statusData.status === 'completed') {
            console.log('任务已完成，停止轮询')
            this.isAnalyzing = false
            this.analysisMessage = ''
            // 清除任何现有的自动刷新定时器
            if (this.autoRefreshTimer) {
              clearTimeout(this.autoRefreshTimer)
              this.autoRefreshTimer = null
            }
          }
        } catch (statusError) {
          console.error('获取任务状态失败:', statusError)
          // 继续尝试加载问题数据
        }

        // 检查评估状态
        try {
          const evalStatusResponse = await this.api.getEvaluationStatus(taskId)
          const evalStatus = evalStatusResponse.data
          console.log('评估状态:', evalStatus)

          // 检查是否所有评估都已完成
          const allEvaluationsCompleted = evalStatus.hard_eval_completed &&
                                        evalStatus.soft_eval_completed &&
                                        evalStatus.img_eval_completed &&
                                        evalStatus.ref_eval_completed

          // 如果所有评估都已完成，停止轮询
          if (allEvaluationsCompleted && !evalStatus.background_task_running) {
            console.log('所有评估已完成，停止轮询')
            this.isAnalyzing = false
            this.analysisMessage = ''
            // 清除任何现有的自动刷新定时器
            if (this.autoRefreshTimer) {
              clearTimeout(this.autoRefreshTimer)
              this.autoRefreshTimer = null
            }
          } else if (evalStatus.background_task_running) {
            console.log('后台评估任务正在运行，分析通常需要5-7分钟，将在2分钟后自动刷新')
            this.isAnalyzing = true
            this.analysisMessage = '正在进行深度分析，预计需要5-7分钟...'
            this.scheduleAutoRefresh(120000) // 2分钟后刷新，给分析充足时间
          } else if (!evalStatus.hard_eval_completed) {
            // 如果评估还未完成但没有后台任务，可能需要启动
            console.log('评估未完成，将在1分钟后检查状态')
            this.isAnalyzing = true
            this.analysisMessage = '准备开始分析...'
            this.scheduleAutoRefresh(60000) // 1分钟后检查
          } else {
            // 分析已完成
            this.isAnalyzing = false
            this.analysisMessage = ''
          }
        } catch (evalStatusError) {
          console.error('获取评估状态失败:', evalStatusError)
          // 继续尝试加载问题数据
        }

        console.log('开始请求问题数据API')
        // 使用API服务，添加超时和降级处理
        try {
          const response = await this.api.getIssues(taskId)
          const data = response.data

          console.log(`[${new Date().toISOString()}] 问题数据API响应:`, data)
          console.log(`[${new Date().toISOString()}] API响应中的by_chapter:`, data.by_chapter)
          console.log(`[${new Date().toISOString()}] by_chapter键数量:`, Object.keys(data.by_chapter || {}).length)
          this.issueData = data
          console.log(`[${new Date().toISOString()}] 问题数据加载成功:`, this.issueData)
          console.log(`[${new Date().toISOString()}] 设置后的by_chapter:`, this.issueData.by_chapter)
          console.log(`[${new Date().toISOString()}] 设置后的by_chapter键数量:`, Object.keys(this.issueData.by_chapter || {}).length)
        } catch (apiError) {
          console.error('API请求失败:', apiError)

          // 处理不同类型的错误
          if (apiError.response && apiError.response.status === 404) {
            console.log('问题分析数据还未生成，使用空数据')
            this.issueData = { summary: { total_issues: 0, severity_distribution: {} }, by_chapter: {} }
            return
          } else if (apiError.response && apiError.response.status === 400) {
            console.log('文档尚未处理完成，使用空数据')
            this.issueData = { summary: { total_issues: 0, severity_distribution: {} }, by_chapter: {} }
            return
          } else if (apiError.code === 'ECONNABORTED' || apiError.message.includes('timeout')) {
            console.log('请求超时，分析可能仍在进行中')
            this.isAnalyzing = true
            this.analysisMessage = '分析正在进行中，通常需要5-7分钟完成'
            this.issueData = {
              summary: {
                total_issues: 0,
                severity_distribution: {},
                message: '分析正在进行中（通常需要5-7分钟），请稍后刷新页面查看结果'
              },
              by_chapter: {}
            }
            this.$message?.warning('分析正在进行中，通常需要5-7分钟完成。页面将自动刷新显示结果。')
            // 设置较长的自动刷新时间
            this.scheduleAutoRefresh(180000) // 3分钟后自动刷新
            return
          }
          throw apiError
        }
      } catch (error) {
        console.error('加载问题数据失败:', error)
        this.issueData = {
          summary: {
            total_issues: 0,
            severity_distribution: {},
            message: '数据加载失败'
          },
          by_chapter: {}
        }
        // 只在非预期错误时显示错误提示
        if (!error.message.includes('404') && !error.message.includes('timeout')) {
          this.$message?.error('问题数据加载失败：' + (error.message || '未知错误'))
        }
      }
    },
    scheduleAutoRefresh (delay = 120000) { // 默认2分钟
      // 清除之前的定时器
      if (this.autoRefreshTimer) {
        clearTimeout(this.autoRefreshTimer)
      }

      // 设置新的定时器
      this.autoRefreshTimer = setTimeout(async () => {
        console.log('自动刷新问题数据...')

        // 在刷新前先检查任务状态和评估状态，避免不必要的刷新
        try {
          const taskId = this.$route.params.taskId || this.$route.query.taskId
          if (taskId) {
            // 首先检查任务状态
            const statusResponse = await this.api.getStatus(taskId)
            const statusData = statusResponse.data

            // 如果任务已完成，停止轮询
            if (statusData.status === 'completed') {
              console.log('任务已完成，取消自动刷新')
              this.isAnalyzing = false
              this.analysisMessage = ''
              return
            }

            // 然后检查评估状态
            const evalStatusResponse = await this.api.getEvaluationStatus(taskId)
            const evalStatus = evalStatusResponse.data

            // 如果所有评估都已完成，不再刷新
            const allEvaluationsCompleted = evalStatus.hard_eval_completed &&
                                          evalStatus.soft_eval_completed &&
                                          evalStatus.img_eval_completed &&
                                          evalStatus.ref_eval_completed

            if (allEvaluationsCompleted && !evalStatus.background_task_running) {
              console.log('评估已完成，取消自动刷新')
              this.isAnalyzing = false
              this.analysisMessage = ''
              return
            }
          }
        } catch (error) {
          console.error('检查状态失败:', error)
        }

        // 如果评估未完成，继续刷新
        this.loadIssueData()
      }, delay)

      const minutes = Math.floor(delay / 60000)
      const seconds = Math.floor((delay % 60000) / 1000)
      console.log(`已设置 ${minutes}分${seconds}秒后自动刷新`)

      // 显示用户友好的提示
      if (delay >= 60000) {
        this.$message?.info(`分析正在进行中，将在${minutes}分钟后自动刷新结果`)
      }
    },
    setupScrollListener () {
      const preview = this.$refs.htmlPreview
      if (preview) {
        preview.addEventListener('scroll', this.handleScroll)
        // 添加连接线更新监听器
        preview.addEventListener('scroll', this.handlePreviewScroll)
      }

      // 添加右侧issue面板的滚动监听
      const issuePanel = this.$refs.issuePanel
      if (issuePanel) {
        issuePanel.addEventListener('scroll', this.handleIssueScroll)
      }
    },
    // 防抖的滚动处理函数
    debouncedHandleScroll () {
      const now = Date.now()

      // 如果正在程序化滚动，或者距离上次程序化滚动时间太近，则不更新导航状态
      if (this.isScrolling || (now - this.lastScrollTime < 1000)) {
        return
      }

      const preview = this.$refs.htmlPreview
      if (!preview) return

      const scrollTop = preview.scrollTop
      const headers = preview.querySelectorAll('h1, h2, h3, h4, h5, h6')

      let activeChapter = null
      let activeSection = null

      // 遍历所有标题，找到当前可见的章节
      for (let i = 0; i < headers.length; i++) {
        const header = headers[i]
        const headerTop = header.offsetTop - preview.offsetTop

        if (headerTop <= scrollTop + 100) { // 100px的偏移量
          const headerText = header.textContent.trim()

          // 匹配章节格式
          if (headerText.match(/第[一二三四五六七八九十\d]+章/)) {
            activeChapter = this.findChapterIdByTitle(headerText)
            activeSection = null // 重置小节
          } else if (headerText.match(/\d+\.\d+/)) {
            activeSection = this.findSectionIdByTitle(headerText)
          }
        }
      }

      // 只有当检测到的section与当前激活的不同时才更新
      if (activeChapter !== this.activeChapter) {
        this.activeChapter = activeChapter
      }
      if (activeSection !== this.activeSection) {
        this.activeSection = activeSection
      }
    },
    // 滚动监听，自动更新导航栏激活状态
    handleScroll () {
      // 清除之前的防抖超时
      if (this.scrollDebounceTimeout) {
        clearTimeout(this.scrollDebounceTimeout)
      }

      // 设置新的防抖超时
      this.scrollDebounceTimeout = setTimeout(() => {
        this.debouncedHandleScroll()
      }, 50) // 50ms防抖延迟
    },
    scrollToChapter (chapterId) {
      // 如果已经是当前激活的项，则不需要滚动
      if (this.activeChapter === chapterId && !this.isScrolling) {
        return
      }

      // 清除之前的超时
      if (this.scrollTimeout) {
        clearTimeout(this.scrollTimeout)
      }
      if (this.scrollDebounceTimeout) {
        clearTimeout(this.scrollDebounceTimeout)
      }

      // 设置滚动状态，暂时禁用滚动监听
      this.isScrolling = true
      this.lastScrollTime = Date.now()

      // 立即更新导航状态
      this.activeChapter = chapterId
      this.activeSection = null // 清除小节选择

      // 查找对应的章节标题
      const chapter = this.documentStructure.find(ch => ch.id === chapterId)
      if (!chapter) {
        this.isScrolling = false
        return
      }

      this.scrollToElement(chapter.title)
    },
    scrollToSection (sectionId) {
      // 如果已经是当前激活的项，则不需要滚动
      if (this.activeSection === sectionId && !this.isScrolling) {
        return
      }

      // 清除之前的超时
      if (this.scrollTimeout) {
        clearTimeout(this.scrollTimeout)
      }
      if (this.scrollDebounceTimeout) {
        clearTimeout(this.scrollDebounceTimeout)
      }

      // 设置滚动状态，暂时禁用滚动监听
      this.isScrolling = true
      this.lastScrollTime = Date.now()

      // 立即更新导航状态
      this.activeSection = sectionId

      // 查找对应的小节标题
      let sectionTitle = null
      for (const chapter of this.documentStructure) {
        if (chapter.sections) {
          const section = chapter.sections.find(sec => sec.id === sectionId)
          if (section) {
            sectionTitle = section.title
            this.activeChapter = chapter.id // 同时激活父章节
            break
          }
        }
      }

      if (sectionTitle) {
        this.scrollToElement(sectionTitle)
      } else {
        this.isScrolling = false
      }
    },
    scrollToElement (titleText) {
      const preview = this.$refs.htmlPreview
      if (!preview) {
        this.isScrolling = false
        return
      }

      // 查找包含指定文本的标题元素
      const headers = preview.querySelectorAll('h1, h2, h3, h4, h5, h6')
      let targetHeader = null
      let bestMatch = null
      let bestMatchScore = 0

      for (const header of headers) {
        const headerText = header.textContent.trim()

        // 精确匹配优先
        if (headerText === titleText) {
          targetHeader = header
          break
        }

        // 计算匹配度分数，优先选择最佳匹配
        let matchScore = 0

        // 如果标题文本完全包含目标文本，且长度差异不大
        if (headerText.includes(titleText)) {
          matchScore = titleText.length / headerText.length
        } else if (titleText.includes(headerText)) {
          matchScore = headerText.length / titleText.length * 0.8 // 降低权重
        }

        // 额外检查：如果是章节编号匹配，提高匹配度
        const titleNumberMatch = titleText.match(/(\d+\.)*\d+/)
        const headerNumberMatch = headerText.match(/(\d+\.)*\d+/)

        if (titleNumberMatch && headerNumberMatch && titleNumberMatch[0] === headerNumberMatch[0]) {
          matchScore += 0.5
        }

        // 选择最佳匹配
        if (matchScore > bestMatchScore && matchScore > 0.3) { // 设置最低匹配阈值
          bestMatchScore = matchScore
          bestMatch = header
        }
      }

      // 使用最佳匹配
      targetHeader = targetHeader || bestMatch

      if (targetHeader) {
        console.log(`章节跳转: "${titleText}" -> "${targetHeader.textContent.trim()}" (匹配度: ${bestMatchScore.toFixed(2)})`)

        // 直接跳转到目标位置，无动画
        const targetTop = targetHeader.offsetTop - preview.offsetTop - 20 // 20px的偏移量
        preview.scrollTo({
          top: targetTop,
          behavior: 'smooth'
        })

        // 设置超时来重置滚动状态
        this.scrollTimeout = setTimeout(() => {
          this.isScrolling = false
        }, 500) // 给滚动动画足够的时间
      } else {
        this.isScrolling = false
        console.warn('未找到对应的标题:', titleText)
      }
    },
    findChapterIdByTitle (title) {
      let bestMatch = null
      let bestMatchScore = 0

      for (const chapter of this.documentStructure) {
        // 精确匹配优先
        if (title === chapter.title) {
          return chapter.id
        }

        // 计算匹配度分数
        let matchScore = 0

        if (chapter.title.includes(title)) {
          matchScore = title.length / chapter.title.length
        } else if (title.includes(chapter.title)) {
          matchScore = chapter.title.length / title.length * 0.8
        }

        // 章节编号匹配检查
        const titleNumberMatch = title.match(/第[一二三四五六七八九十\d]+章|(\d+\.)*\d+/)
        const chapterNumberMatch = chapter.title.match(/第[一二三四五六七八九十\d]+章|(\d+\.)*\d+/)

        if (titleNumberMatch && chapterNumberMatch && titleNumberMatch[0] === chapterNumberMatch[0]) {
          matchScore += 0.5
        }

        if (matchScore > bestMatchScore && matchScore > 0.3) {
          bestMatchScore = matchScore
          bestMatch = chapter.id
        }
      }

      return bestMatch
    },
    findSectionIdByTitle (title) {
      let bestMatch = null
      let bestMatchScore = 0

      for (const chapter of this.documentStructure) {
        if (chapter.sections) {
          for (const section of chapter.sections) {
            // 精确匹配优先
            if (title === section.title) {
              return section.id
            }

            // 计算匹配度分数
            let matchScore = 0

            if (section.title.includes(title)) {
              matchScore = title.length / section.title.length
            } else if (title.includes(section.title)) {
              matchScore = section.title.length / title.length * 0.8
            }

            // 小节编号匹配检查（如 1.2.4, 2.4 等）
            const titleNumberMatch = title.match(/(\d+\.)*\d+/)
            const sectionNumberMatch = section.title.match(/(\d+\.)*\d+/)

            if (titleNumberMatch && sectionNumberMatch && titleNumberMatch[0] === sectionNumberMatch[0]) {
              matchScore += 0.5
            }

            if (matchScore > bestMatchScore && matchScore > 0.3) {
              bestMatchScore = matchScore
              bestMatch = section.id
            }
          }
        }
      }

      return bestMatch
    },

    async highlightIssue (issue) {
      // 防抖：避免快速连续点击
      const now = Date.now()
      if (now - this.lastClickTime < 300) {
        console.log('点击过于频繁，忽略此次点击')
        return
      }
      this.lastClickTime = now

      // 高亮显示对应的问题文本
      console.log('高亮问题:', issue)

      const preview = this.$refs.htmlPreview
      if (!preview) {
        console.warn('无法找到预览区域')
        return
      }

      // 清除之前的高亮
      this.clearHighlights()

      // 等待DOM更新完成后再进行查找
      await this.$nextTick()

      // 简化的文本搜索和定位逻辑
      this.simpleTextSearchAndPosition(issue, preview)
    },

    simpleTextSearchAndPosition (issue, preview) {
      // 在HTML内容中查找原文
      const documentHtmlContent = preview.querySelector('.document-content')
      if (!documentHtmlContent) {
        console.warn('无法找到文档内容区域')
        return
      }

      let originalText = issue.original_text
      let targetElement = null

      // 直接查找原文
      if (originalText && originalText.trim()) {
        targetElement = this.findTextInDocument(documentHtmlContent, originalText)
        console.log('直接查找结果:', targetElement ? '找到' : '未找到')
      }

      // 如果没有找到原文，尝试模糊匹配
      if (!targetElement) {
        console.log('未找到确切原文，尝试模糊匹配...')
        console.log('问题详情:', {
          type: issue.type,
          chapter: issue.chapter,
          sub_chapter: issue.sub_chapter,
          detail: issue.detail,
          suggestion: issue.suggestion,
          original_text: issue.original_text
        })

        try {
          // 首先尝试在指定章节和小节中搜索
          let searchScope = this.getSearchScopeByChapter(documentHtmlContent, issue.chapter, issue.sub_chapter)
          let searchScopeText = ''

          if (searchScope && searchScope.length > 0) {
            // 如果找到了指定的章节/小节，在其中搜索
            searchScopeText = searchScope.map(el => el.textContent || el.innerText || '').join(' ')
            console.log('在指定章节/小节中搜索，范围长度:', searchScopeText.length)
            console.log('搜索范围:', issue.chapter, '->', issue.sub_chapter)
          } else {
            // 如果没有找到指定章节，回退到全文搜索
            searchScopeText = documentHtmlContent.textContent || documentHtmlContent.innerText || ''
            searchScope = [documentHtmlContent]
            console.log('未找到指定章节，使用全文搜索，长度:', searchScopeText.length)
          }

          if (searchScopeText.length > 0) {
            const queryText = this.extractQueryFromIssue(issue)
            console.log('提取的查询文本:', queryText)

            if (queryText && queryText.length > 3) {
              // 在限定范围内进行模糊匹配
              const fuzzyResult = this.findBestMatchInScope(queryText, searchScopeText, searchScope)
              console.log('限定范围模糊匹配结果:', fuzzyResult)

              if (fuzzyResult && fuzzyResult.element) {
                targetElement = fuzzyResult.element
                originalText = fuzzyResult.actualMatchedText || fuzzyResult.matchedText
                console.log(`限定范围模糊匹配成功，相似度: ${(fuzzyResult.similarity * 100).toFixed(1)}%`)
                console.log('查询文本:', queryText)
                console.log('匹配的句子:', fuzzyResult.matchedText)
                console.log('实际高亮文本:', originalText)
              } else if (searchScope.length === 1 && searchScope[0] === documentHtmlContent) {
                // 如果已经是全文搜索还没找到，尝试备用匹配
                console.log('全文模糊匹配未找到结果，尝试使用问题描述进行匹配...')
                const fallbackResult = this.tryFallbackMatching(issue, documentHtmlContent)
                if (fallbackResult) {
                  targetElement = fallbackResult.element
                  originalText = fallbackResult.text
                  console.log('备用匹配成功:', fallbackResult)
                }
              } else {
                // 如果在限定范围内没找到，尝试全文搜索
                console.log('限定范围内未找到，尝试全文搜索...')
                const fullTextResult = this.findBestMatchInHtmlContent(queryText, documentHtmlContent.textContent || documentHtmlContent.innerText || '', documentHtmlContent)
                if (fullTextResult && fullTextResult.element) {
                  targetElement = fullTextResult.element
                  originalText = fullTextResult.actualMatchedText || fullTextResult.matchedText
                  console.log('全文搜索成功:', fullTextResult)
                }
              }
            }
          }
        } catch (error) {
          console.error('模糊匹配失败:', error)
        }
      }

      if (!targetElement) {
        console.warn('未找到对应的原文:', originalText || '无原文')
        this.$message?.warning('未找到对应的原文内容，可能需要手动查找')
        return
      }

      // 高亮原文
      this.highlightText(targetElement, originalText, issue.id)

      // 等待DOM更新完成后，基于高亮元素进行定位
      this.$nextTick(() => {
        const highlightElement = this.findHighlightElement(issue.id)
        if (highlightElement) {
          console.log('基于高亮元素进行定位')
          this.scrollToTarget(highlightElement)
          this.createConnectionLine(issue.id, highlightElement)
        } else {
          console.log('未找到高亮元素，使用原始目标元素')
          this.scrollToTarget(targetElement)
          this.createConnectionLine(issue.id, targetElement)
        }
      })
    },

    findHighlightElement (issueId) {
      // 查找指定issue的高亮元素
      const preview = this.$refs.htmlPreview
      if (!preview) return null

      const highlightElement = preview.querySelector(`.issue-highlight[data-issue-id="${issueId}"]`)
      if (highlightElement) {
        console.log('找到高亮元素:', highlightElement)
        return highlightElement
      }

      console.warn('未找到高亮元素，issueId:', issueId)
      return null
    },

    clearHighlights () {
      // 使用缓存机制清除所有高亮标记
      const preview = this.$refs.htmlPreview
      if (!preview) return

      // 记录当前滚动位置，避免清除高亮时影响滚动
      const currentScrollTop = preview.scrollTop

      // 使用缓存恢复原始HTML内容
      this.restoreOriginalHtml()

      // 清除连接线
      const lines = document.querySelectorAll('.connection-line')
      lines.forEach(line => line.remove())

      // 重置高亮状态
      this.currentHighlightId = null

      // 恢复滚动位置，确保清除高亮不会影响当前视图
      if (preview.scrollTop !== currentScrollTop) {
        preview.scrollTop = currentScrollTop
      }
    },

    /**
     * 恢复原始HTML内容
     */
    restoreOriginalHtml () {
      // 遍历所有缓存的元素，恢复其原始HTML内容
      for (const [elementId, originalHtml] of this.htmlCache.entries()) {
        const element = document.querySelector(`[data-cache-id="${elementId}"]`)
        if (element && originalHtml) {
          element.innerHTML = originalHtml
          console.log('恢复元素HTML:', elementId)
        }
      }

      // 清空缓存和高亮记录
      this.htmlCache.clear()
      this.highlightedElements.clear()
    },

    /**
     * 缓存元素的原始HTML内容
     * @param {Element} element 要缓存的元素
     * @returns {string} 元素的唯一标识ID
     */
    cacheElementHtml (element) {
      if (!element) return null

      // 生成唯一标识ID
      const elementId = `cache_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`

      // 缓存原始HTML内容
      this.htmlCache.set(elementId, element.innerHTML)

      // 给元素添加缓存标识
      element.setAttribute('data-cache-id', elementId)

      // 记录已高亮的元素
      this.highlightedElements.add(elementId)

      console.log('缓存元素HTML:', elementId, element.innerHTML.substring(0, 100))
      return elementId
    },

    /**
     * 根据章节和小节信息获取搜索范围
     * @param {Element} documentContent 文档内容元素
     * @param {string} targetChapter 目标章节
     * @param {string} targetSubChapter 目标小节
     * @returns {Array<Element>} 搜索范围元素数组
     */
    getSearchScopeByChapter (documentContent, targetChapter, targetSubChapter) {
      if (!documentContent || !targetChapter) {
        return []
      }

      // 查找章节标题元素（通常是h1, h2等）
      const headings = documentContent.querySelectorAll('h1, h2, h3, h4, h5, h6')
      let chapterStartElement = null
      let chapterEndElement = null

      // 寻找匹配的章节标题
      for (let i = 0; i < headings.length; i++) {
        const heading = headings[i]
        const headingText = heading.textContent || heading.innerText || ''

        if (this.isChapterMatch(headingText, targetChapter)) {
          chapterStartElement = heading
          // 找到下一个同级或更高级的标题作为结束点
          const currentLevel = parseInt(heading.tagName.charAt(1))
          for (let j = i + 1; j < headings.length; j++) {
            const nextHeading = headings[j]
            const nextLevel = parseInt(nextHeading.tagName.charAt(1))
            if (nextLevel <= currentLevel) {
              chapterEndElement = nextHeading
              break
            }
          }
          break
        }
      }

      if (!chapterStartElement) {
        console.log('未找到匹配的章节:', targetChapter)
        return []
      }

      // 如果指定了小节，进一步缩小范围
      if (targetSubChapter) {
        const subChapterElements = this.findSubChapterInRange(chapterStartElement, chapterEndElement, targetSubChapter)
        if (subChapterElements.length > 0) {
          console.log('找到匹配的小节:', targetSubChapter)
          return subChapterElements
        }
      }

      // 获取章节范围内的所有元素
      const chapterElements = this.getElementsInRange(chapterStartElement, chapterEndElement)
      console.log('章节范围内元素数量:', chapterElements.length)
      return chapterElements
    },

    /**
     * 检查章节名是否匹配
     */
    isChapterMatch (headingText, targetChapter) {
      if (!headingText || !targetChapter) return false

      // 直接匹配
      if (headingText.includes(targetChapter) || targetChapter.includes(headingText)) return true

      // 去除空格和下划线后匹配
      const normalizedHeading = headingText.replace(/[\s_]/g, '')
      const normalizedTarget = targetChapter.replace(/[\s_]/g, '')
      if (normalizedHeading.includes(normalizedTarget) || normalizedTarget.includes(normalizedHeading)) return true

      return false
    },

    /**
     * 在指定范围内查找小节
     */
    findSubChapterInRange (startElement, endElement, targetSubChapter) {
      const elements = this.getElementsInRange(startElement, endElement)

      let subChapterStart = null
      let subChapterEnd = null

      for (let i = 0; i < elements.length; i++) {
        const element = elements[i]
        if (element.tagName && element.tagName.match(/^H[2-6]$/)) {
          const headingText = element.textContent || element.innerText || ''
          if (this.isSubChapterMatch(headingText, targetSubChapter)) {
            subChapterStart = element
            // 找到下一个同级或更高级的标题
            const currentLevel = parseInt(element.tagName.charAt(1))
            for (let j = i + 1; j < elements.length; j++) {
              const nextElement = elements[j]
              if (nextElement.tagName && nextElement.tagName.match(/^H[1-6]$/)) {
                const nextLevel = parseInt(nextElement.tagName.charAt(1))
                if (nextLevel <= currentLevel) {
                  subChapterEnd = nextElement
                  break
                }
              }
            }
            break
          }
        }
      }

      if (subChapterStart) {
        return this.getElementsInRange(subChapterStart, subChapterEnd)
      }

      return []
    },

    /**
     * 检查小节名是否匹配
     */
    isSubChapterMatch (headingText, targetSubChapter) {
      if (!headingText || !targetSubChapter) return false

      // 直接匹配
      if (headingText.includes(targetSubChapter) || targetSubChapter.includes(headingText)) return true

      // 去除空格和下划线后匹配
      const normalizedHeading = headingText.replace(/[\s_]/g, '')
      const normalizedTarget = targetSubChapter.replace(/[\s_]/g, '')
      if (normalizedHeading.includes(normalizedTarget) || normalizedTarget.includes(normalizedHeading)) return true

      return false
    },

    /**
     * 获取两个元素之间的所有元素
     */
    getElementsInRange (startElement, endElement) {
      const elements = []
      let currentElement = startElement

      while (currentElement && currentElement !== endElement) {
        elements.push(currentElement)
        currentElement = currentElement.nextElementSibling
      }

      return elements
    },

    /**
     * 在指定范围内进行模糊匹配
     */
    findBestMatchInScope (queryText, scopeText, scopeElements) {
      if (!queryText || !scopeText || !scopeElements || scopeElements.length === 0) {
        return null
      }

      // 将范围文本按句子分割
      const sentences = scopeText.split(/[。！？；\n]/).filter(s => s.trim().length > 5)
      let bestSimilarity = 0
      let bestMatch = null

      for (const sentence of sentences) {
        const trimmedSentence = sentence.trim()
        const similarity = this.calculateTextSimilarity(queryText, trimmedSentence)
        if (similarity > bestSimilarity && similarity > 0.2) {
          bestSimilarity = similarity
          // 在范围元素中找到包含这个句子的元素
          const element = this.findElementContainingTextInScope(scopeElements, trimmedSentence)
          if (element) {
            const actualMatchedText = this.findActualMatchableText(element, queryText, trimmedSentence)
            bestMatch = {
              element,
              matchedText: trimmedSentence,
              actualMatchedText: actualMatchedText || trimmedSentence,
              similarity: bestSimilarity
            }
          }
        }
      }

      return bestMatch
    },

    /**
     * 在指定范围的元素中查找包含文本的元素
     */
    findElementContainingTextInScope (scopeElements, searchText) {
      for (const element of scopeElements) {
        const elementText = element.textContent || element.innerText || ''
        if (elementText.includes(searchText)) {
          return element
        }

        // 也检查子元素
        const childElement = this.findTextInDocument(element, searchText)
        if (childElement) {
          return childElement
        }
      }
      return null
    },

    findTextInDocument (container, searchText) {
      // 递归查找包含指定文本的元素
      if (!container || !searchText) return null

      const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null,
        false
      )

      let bestMatch = null
      let bestMatchScore = 0
      let node

      // eslint-disable-next-line no-cond-assign
      while ((node = walker.nextNode())) {
        const nodeText = node.textContent
        if (nodeText.includes(searchText)) {
          // 精确匹配，直接返回
          return node.parentElement
        }

        // 计算相似度，寻找最佳匹配
        if (searchText.length > 10 && nodeText.length > 10) {
          const similarity = this.calculateTextSimilarity(searchText, nodeText)
          if (similarity > bestMatchScore && similarity > 0.6) {
            bestMatchScore = similarity
            bestMatch = node.parentElement
          }
        }
      }

      // 如果没有精确匹配，返回最佳相似匹配
      if (bestMatch && bestMatchScore > 0.6) {
        console.log(`使用相似匹配，相似度: ${(bestMatchScore * 100).toFixed(1)}%`)
        return bestMatch
      }

      return null
    },

    findTextInDocumentPartial (container, searchText) {
      // 部分匹配查找，支持更灵活的文本匹配
      if (!searchText || searchText.length < 5) return null

      const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null,
        false
      )

      let bestMatch = null
      let bestScore = 0

      let node
      // eslint-disable-next-line no-cond-assign
      while ((node = walker.nextNode())) {
        const nodeText = node.textContent.trim()
        if (nodeText.length < 5) continue

        // 计算相似度
        const similarity = this.calculateTextSimilarity(searchText, nodeText)
        if (similarity > bestScore && similarity > 0.3) {
          bestScore = similarity
          bestMatch = node.parentElement
        }

        // 也尝试部分包含匹配
        const words = searchText.split(/\s+/).filter(word => word.length > 2)
        if (words.length > 0) {
          const matchedWords = words.filter(word => nodeText.includes(word))
          const wordMatchRatio = matchedWords.length / words.length
          if (wordMatchRatio > 0.5 && wordMatchRatio > bestScore) {
            bestScore = wordMatchRatio
            bestMatch = node.parentElement
          }
        }
      }

      return bestMatch
    },

    tryFallbackMatching (issue, documentContent) {
      // 备用匹配策略：基于问题描述进行匹配
      const searchTexts = []

      // 从问题详情中提取关键词
      if (issue.detail) {
        // 提取引号内的内容
        const quotedMatches = issue.detail.match(/["'""]([^"'""]*)["'"]/g)
        if (quotedMatches) {
          quotedMatches.forEach(match => {
            const cleaned = match.replace(/^["'""]|["'""]$/g, '').trim()
            if (cleaned.length > 3) {
              searchTexts.push(cleaned)
            }
          })
        }

        // 提取较长的词组
        const words = issue.detail.split(/[，。；！？\s]+/).filter(word => word.length > 5)
        searchTexts.push(...words.slice(0, 3))
      }

      // 从建议中提取关键词
      if (issue.suggestion) {
        const words = issue.suggestion.split(/[，。；！？\s]+/).filter(word => word.length > 5)
        searchTexts.push(...words.slice(0, 2))
      }

      // 尝试每个搜索文本
      for (const searchText of searchTexts) {
        const element = this.findTextInDocumentPartial(documentContent, searchText)
        if (element) {
          return {
            element,
            text: searchText,
            similarity: 0.4 // 备用匹配的默认相似度
          }
        }
      }

      return null
    },

    calculateTextSimilarity (text1, text2) {
      // 简单的文本相似度计算
      if (!text1 || !text2) return 0

      const len1 = text1.length
      const len2 = text2.length
      const maxLen = Math.max(len1, len2)

      if (maxLen === 0) return 1

      // 计算编辑距离
      const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0))

      for (let i = 0; i <= len1; i++) matrix[i][0] = i
      for (let j = 0; j <= len2; j++) matrix[0][j] = j

      for (let i = 1; i <= len1; i++) {
        for (let j = 1; j <= len2; j++) {
          const cost = text1[i - 1] === text2[j - 1] ? 0 : 1
          matrix[i][j] = Math.min(
            matrix[i - 1][j] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j - 1] + cost
          )
        }
      }

      return (maxLen - matrix[len1][len2]) / maxLen
    },

    extractQueryFromIssue (issue) {
      // 从问题信息中提取查询文本
      const queries = []

      // 优先从detail中提取引号内容
      const detail = issue.detail || ''
      if (detail) {
        const quotedText = this.extractQuotedText(detail)
        if (quotedText && quotedText.length > 3) {
          queries.push(quotedText)
        }

        // 提取detail中的关键短语
        const cleanDetail = detail.replace(/建议|应该|需要|可以|问题|错误|不当|不合适/g, '')
        const phrases = cleanDetail.split(/[，。；！？\s]+/).filter(phrase => phrase.length > 5)
        queries.push(...phrases.slice(0, 3))
      }

      // 从suggestion中提取
      const suggestion = issue.suggestion || ''
      if (suggestion) {
        const quotedText = this.extractQuotedText(suggestion)
        if (quotedText && quotedText.length > 3) {
          queries.push(quotedText)
        }
      }

      // 如果已有原文，使用原文
      if (issue.original_text && issue.original_text.trim()) {
        queries.unshift(issue.original_text.trim())
      }

      // 使用问题类型作为备用查询
      if (issue.type && issue.type.length > 2) {
        queries.push(issue.type)
      }

      // 返回最长的有效查询文本
      const validQueries = queries.filter(q => q && q.length > 3)
      if (validQueries.length === 0) return ''

      return validQueries.reduce((longest, current) =>
        current.length > longest.length ? current : longest
      )
    },

    extractQuotedText (text) {
      // 从文本中提取引号内的内容
      if (!text) return ''

      const patterns = [
        /"([^"]+)"/g, // 中文双引号
        /'([^']+)'/g, // 中文单引号
        /"([^"]+)"/g, // 英文双引号
        /'([^']+)'/g // 英文单引号
      ]

      for (const pattern of patterns) {
        const matches = text.match(pattern)
        if (matches && matches.length > 0) {
          const longest = matches.reduce((a, b) => a.length > b.length ? a : b)
          return longest.replace(/^["'"]|["'"]$/g, '')
        }
      }

      return ''
    },

    findBestMatchInHtmlContent (queryText, htmlTextContent, documentHtmlContent) {
      // 在HTML内容中找到最佳匹配
      if (!queryText || !htmlTextContent) return null

      let bestMatch = null
      let bestSimilarity = 0

      // 按句子分割HTML文本内容
      const sentences = htmlTextContent.split(/[。！？；：\n]/).filter(s => s.trim().length > 5)

      for (const sentence of sentences) {
        const trimmedSentence = sentence.trim()
        const similarity = this.calculateTextSimilarity(queryText, trimmedSentence)
        if (similarity > bestSimilarity && similarity > 0.2) {
          bestSimilarity = similarity
          // 在DOM中找到包含这个句子的元素
          const element = this.findElementContainingText(documentHtmlContent, trimmedSentence)
          if (element) {
            // 找到实际可以高亮的文本片段
            const actualMatchedText = this.findActualMatchableText(element, queryText, trimmedSentence)
            bestMatch = {
              element,
              matchedText: trimmedSentence,
              actualMatchedText: actualMatchedText || trimmedSentence,
              similarity: bestSimilarity
            }
          }
        }
      }

      // 如果没有找到好的匹配，尝试关键词匹配
      if (!bestMatch || bestSimilarity < 0.3) {
        const words = queryText.split(/\s+/).filter(word => word.length > 2)
        for (const sentence of sentences) {
          const trimmedSentence = sentence.trim()
          const matchedWords = words.filter(word => trimmedSentence.includes(word))
          const wordMatchRatio = matchedWords.length / words.length
          if (wordMatchRatio > 0.5 && wordMatchRatio > bestSimilarity) {
            const element = this.findElementContainingText(documentHtmlContent, trimmedSentence)
            if (element) {
              // 对于关键词匹配，尝试找到包含最多关键词的片段
              const actualMatchedText = this.findKeywordMatchText(element, words, trimmedSentence)
              bestMatch = {
                element,
                matchedText: trimmedSentence,
                actualMatchedText: actualMatchedText || trimmedSentence,
                similarity: wordMatchRatio
              }
              bestSimilarity = wordMatchRatio
            }
          }
        }
      }

      return bestMatch
    },

    findActualMatchableText (element, queryText, sentenceText) {
      // 在元素中找到实际可以匹配的文本片段
      const elementText = element.textContent || element.innerText || ''

      // 如果查询文本直接存在于元素中，返回查询文本
      if (elementText.includes(queryText)) {
        return queryText
      }

      // 如果句子文本存在于元素中，返回句子文本
      if (elementText.includes(sentenceText)) {
        return sentenceText
      }

      // 尝试找到最长的公共子串
      const commonSubstring = this.findLongestCommonSubstring(queryText, elementText)
      if (commonSubstring && commonSubstring.length > 5) {
        return commonSubstring
      }

      // 返回元素中的一个合理长度的文本片段
      const words = elementText.split(/\s+/)
      if (words.length > 10) {
        return words.slice(0, 10).join(' ')
      }

      return elementText.substring(0, Math.min(50, elementText.length))
    },

    findKeywordMatchText (element, keywords, sentenceText) {
      // 找到包含最多关键词的文本片段
      const elementText = element.textContent || element.innerText || ''

      // 按句子分割元素文本
      const elementSentences = elementText.split(/[。！？；：]/).filter(s => s.trim().length > 5)

      let bestMatch = null
      let maxKeywordCount = 0

      for (const sentence of elementSentences) {
        const matchedKeywords = keywords.filter(keyword => sentence.includes(keyword))
        if (matchedKeywords.length > maxKeywordCount) {
          maxKeywordCount = matchedKeywords.length
          bestMatch = sentence.trim()
        }
      }

      return bestMatch || sentenceText
    },

    findLongestCommonSubstring (str1, str2) {
      // 找到两个字符串的最长公共子串
      if (!str1 || !str2) return ''

      let longest = ''
      for (let i = 0; i < str1.length; i++) {
        for (let j = i + 1; j <= str1.length; j++) {
          const substring = str1.substring(i, j)
          if (str2.includes(substring) && substring.length > longest.length) {
            longest = substring
          }
        }
      }
      return longest
    },

    findElementContainingText (container, searchText) {
      // 在DOM中找到包含指定文本的元素
      if (!searchText || searchText.length < 5) return null

      const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null,
        false
      )

      let node
      // eslint-disable-next-line no-cond-assign
      while ((node = walker.nextNode())) {
        if (node.textContent.includes(searchText)) {
          return node.parentElement
        }
      }

      // 如果精确匹配失败，尝试部分匹配
      const walker2 = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null,
        false
      )

      let bestMatch = null
      let bestScore = 0

      // eslint-disable-next-line no-cond-assign
      while ((node = walker2.nextNode())) {
        const nodeText = node.textContent.trim()
        if (nodeText.length < 5) continue

        const similarity = this.calculateTextSimilarity(searchText, nodeText)
        if (similarity > bestScore && similarity > 0.3) {
          bestScore = similarity
          bestMatch = node.parentElement
        }
      }

      return bestMatch
    },

    highlightText (element, searchText, issueId) {
      // 使用缓存机制进行高亮，避免破坏HTML结构
      console.log('高亮文本:', { element, searchText, issueId })

      // 如果当前已有高亮且是同一个issue，不需要重复高亮
      if (this.currentHighlightId === issueId) {
        console.log('相同issue已高亮，跳过')
        return
      }

      // 清除之前的高亮（如果有）
      if (this.currentHighlightId) {
        this.restoreOriginalHtml()
      }

      // 缓存当前元素的原始HTML
      const cacheId = this.cacheElementHtml(element)
      if (!cacheId) {
        console.warn('无法缓存元素HTML')
        return
      }

      // 设置当前高亮ID
      this.currentHighlightId = issueId

      // 使用innerHTML替换的方式进行高亮，避免复杂的DOM操作
      const originalHtml = element.innerHTML
      const highlightedHtml = this.createHighlightedHtml(originalHtml, searchText, issueId)

      if (highlightedHtml !== originalHtml) {
        element.innerHTML = highlightedHtml
        console.log('成功应用高亮HTML')
      } else {
        console.warn('未找到可高亮的文本内容')
        // 如果没有找到匹配的文本，尝试高亮整个元素
        this.highlightEntireElement(element, issueId)
      }
    },

    /**
     * 创建高亮后的HTML内容
     * @param {string} originalHtml 原始HTML内容
     * @param {string} searchText 要高亮的文本
     * @param {string} issueId issue ID
     * @returns {string} 高亮后的HTML内容
     */
    createHighlightedHtml (originalHtml, searchText, issueId) {
      // 创建高亮样式
      const highlightStyle = `
        background: #fbbf24 !important;
        color: #92400e !important;
        padding: 2px 4px !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(251, 191, 36, 0.3) !important;
        display: inline !important;
        position: relative !important;
        z-index: 10 !important;
      `.replace(/\s+/g, ' ').trim()

      // 创建高亮标签
      const highlightTag = `<span class="issue-highlight" data-issue-id="${issueId}" style="${highlightStyle}">$&</span>`

      // 首先尝试精确匹配
      const escapedSearchText = this.escapeRegExp(searchText)
      let highlightedHtml = originalHtml.replace(new RegExp(escapedSearchText, 'gi'), highlightTag)

      // 如果精确匹配失败，尝试部分匹配
      if (highlightedHtml === originalHtml && searchText.length > 10) {
        console.log('精确匹配失败，尝试关键词匹配')
        const words = searchText.split(/\s+/).filter(word => word.length > 2)

        // 对每个关键词进行高亮
        for (const word of words) {
          const escapedWord = this.escapeRegExp(word)
          const wordRegex = new RegExp(`\\b${escapedWord}\\b`, 'gi')
          highlightedHtml = highlightedHtml.replace(wordRegex, highlightTag)
        }
      }

      return highlightedHtml
    },

    /**
     * 高亮整个元素
     * @param {Element} element 要高亮的元素
     * @param {string} issueId issue ID
     */
    highlightEntireElement (element, issueId) {
      element.classList.add('issue-highlight')
      element.setAttribute('data-issue-id', issueId)
      element.style.cssText = `
        background: #fbbf24 !important;
        color: #92400e !important;
        padding: 2px 4px !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(251, 191, 36, 0.3) !important;
        display: inline !important;
        position: relative !important;
        z-index: 10 !important;
      `
      console.log('高亮整个元素')
    },

    escapeRegExp (string) {
      // 转义正则表达式特殊字符
      return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    },

    scrollToTarget (element) {
      // 滚动到目标元素，使其在视野中央
      const preview = this.$refs.htmlPreview
      if (!preview || !element) return

      console.log('开始滚动到目标元素:', element.className || element.tagName)

      // 清除之前的滚动超时，避免冲突
      if (this.scrollTimeout) {
        clearTimeout(this.scrollTimeout)
      }

      // 设置滚动状态
      this.isScrolling = true
      this.lastScrollTime = Date.now()

      // 获取元素的准确位置信息
      const elementRect = element.getBoundingClientRect()
      const previewRect = preview.getBoundingClientRect()

      // 计算元素相对于预览容器的位置
      const elementRelativeTop = elementRect.top - previewRect.top + preview.scrollTop
      const previewHeight = preview.clientHeight
      const elementHeight = elementRect.height

      // 计算目标滚动位置，使元素在视野中央
      const targetScrollTop = elementRelativeTop - (previewHeight / 2) + (elementHeight / 2)

      console.log('滚动计算:', {
        elementRelativeTop,
        previewHeight,
        elementHeight,
        targetScrollTop: Math.max(0, targetScrollTop)
      })

      // 执行滚动，确保不会滚动到负值
      const finalScrollTop = Math.max(0, targetScrollTop)
      preview.scrollTo({
        top: finalScrollTop,
        behavior: 'smooth'
      })

      // 设置超时来重置滚动状态
      this.scrollTimeout = setTimeout(() => {
        this.isScrolling = false
        console.log('滚动完成')
      }, 800)
    },

    createConnectionLine (issueId, targetElement) {
      // 创建连接线连接问题和原文
      const issueElement = document.querySelector(`.issue-item[data-issue-id="${issueId}"]`)
      if (!issueElement || !targetElement) return

      // 等待滚动完成后创建连接线
      setTimeout(() => {
        this.drawConnectionLine(issueElement, targetElement, issueId)
      }, 500)
    },

    drawConnectionLine (issueElement, targetElement, issueId) {
      // 绘制连接线
      const line = document.createElement('div')
      line.className = 'connection-line'
      line.setAttribute('data-issue-id', issueId)

      // 获取两个元素的位置
      const issueRect = issueElement.getBoundingClientRect()
      const targetRect = targetElement.getBoundingClientRect()

      // 计算连接线的位置和角度
      const startX = issueRect.left + issueRect.width / 2
      const startY = issueRect.top + issueRect.height / 2

      // 优化端点计算：更精确地指向高亮元素的最后位置
      // 如果目标元素是高亮元素，使用更精确的定位
      const highlightElement = targetElement.querySelector('.issue-highlight') ||
                              (targetElement.classList.contains('issue-highlight') ? targetElement : null)

      let endX, endY
      if (highlightElement) {
        // 计算高亮元素的最后位置（如果跨多行，指向最后一行的末尾）
        const endPosition = this.calculateHighlightEndPosition(highlightElement)
        endX = endPosition.x
        endY = endPosition.y
      } else {
        // 回退到原来的计算方式
        endX = targetRect.right
        endY = targetRect.top + targetRect.height / 2
      }

      const length = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2))
      const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI

      // 设置连接线样式
      line.style.position = 'fixed'
      line.style.left = startX + 'px'
      line.style.top = startY + 'px'
      line.style.width = length + 'px'
      line.style.height = '2px'
      line.style.backgroundColor = '#fbbf24'
      line.style.transformOrigin = '0 50%'
      line.style.transform = `rotate(${angle}deg)`
      line.style.zIndex = '1000'
      line.style.pointerEvents = 'none'
      line.style.opacity = '0.8'

      document.body.appendChild(line)

      // 监听滚动事件，动态更新连接线
      this.updateConnectionLineOnScroll(issueId)
    },

    updateConnectionLineOnScroll (issueId) {
      // 注册连接线到全局更新列表中
      if (!this.activeConnectionLines) {
        this.activeConnectionLines = new Set()
      }
      this.activeConnectionLines.add(issueId)

      // 立即更新一次连接线位置
      this.updateSingleConnectionLine(issueId)
    },

    // 处理右侧issue面板滚动事件
    handleIssueScroll () {
      // 当右侧面板滚动时，更新所有连接线
      this.updateAllConnectionLines()
    },

    // 处理预览区域滚动事件
    handlePreviewScroll () {
      // 当预览区域滚动时，更新所有连接线
      this.updateAllConnectionLines()
    },

    // 更新所有连接线
    updateAllConnectionLines () {
      // 使用requestAnimationFrame来优化性能
      if (this.updateLinesTimeout) {
        cancelAnimationFrame(this.updateLinesTimeout)
      }

      this.updateLinesTimeout = requestAnimationFrame(() => {
        const lines = document.querySelectorAll('.connection-line')
        lines.forEach(line => {
          const issueId = line.getAttribute('data-issue-id')
          if (issueId) {
            this.updateSingleConnectionLine(issueId)
          }
        })
      })
    },

    // 更新单个连接线
    updateSingleConnectionLine (issueId) {
      const line = document.querySelector(`.connection-line[data-issue-id="${issueId}"]`)
      const issueElement = document.querySelector(`.issue-item[data-issue-id="${issueId}"]`)
      const targetElement = document.querySelector(`.issue-highlight[data-issue-id="${issueId}"]`)

      if (!line) {
        console.warn(`连接线不存在: ${issueId}`)
        return
      }

      if (!issueElement) {
        console.warn(`问题元素不存在: ${issueId}`)
        return
      }

      if (!targetElement) {
        console.warn(`目标高亮元素不存在: ${issueId}`)
        return
      }

      try {
        const issueRect = issueElement.getBoundingClientRect()
        const targetRect = targetElement.getBoundingClientRect()

        // 检查元素是否在视口中
        const isIssueVisible = issueRect.width > 0 && issueRect.height > 0
        const isTargetVisible = targetRect.width > 0 && targetRect.height > 0

        if (!isIssueVisible || !isTargetVisible) {
          // 如果任一元素不可见，隐藏连接线
          line.style.opacity = '0'
          return
        }

        // 恢复连接线可见性
        line.style.opacity = '0.8'

        const startX = issueRect.left + issueRect.width / 2
        const startY = issueRect.top + issueRect.height / 2

        // 修复端点计算：指向高亮元素的最后位置（如果跨多行，指向最后一行的末尾）
        const endPosition = this.calculateHighlightEndPosition(targetElement)
        const endX = endPosition.x
        const endY = endPosition.y

        const length = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2))
        const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI

        line.style.left = startX + 'px'
        line.style.top = startY + 'px'
        line.style.width = length + 'px'
        line.style.transform = `rotate(${angle}deg)`
      } catch (error) {
        console.error(`更新连接线失败 ${issueId}:`, error)
      }
    },

    // 计算高亮元素的最后位置（如果跨多行，指向最后一行的末尾）
    calculateHighlightEndPosition (highlightElement) {
      try {
        const rect = highlightElement.getBoundingClientRect()

        // 获取高亮元素的文本内容和样式
        const text = highlightElement.textContent || highlightElement.innerText || ''
        const computedStyle = window.getComputedStyle(highlightElement)
        const lineHeight = parseFloat(computedStyle.lineHeight) || parseFloat(computedStyle.fontSize) * 1.2

        // 创建一个临时的测量元素来计算文本布局
        const measureElement = document.createElement('div')
        measureElement.style.cssText = `
          position: absolute;
          visibility: hidden;
          white-space: pre-wrap;
          word-wrap: break-word;
          font-family: ${computedStyle.fontFamily};
          font-size: ${computedStyle.fontSize};
          font-weight: ${computedStyle.fontWeight};
          line-height: ${computedStyle.lineHeight};
          letter-spacing: ${computedStyle.letterSpacing};
          width: ${rect.width}px;
          padding: ${computedStyle.padding};
          margin: ${computedStyle.margin};
          border: ${computedStyle.border};
        `
        measureElement.textContent = text
        document.body.appendChild(measureElement)

        const measureRect = measureElement.getBoundingClientRect()
        const estimatedLines = Math.max(1, Math.round(measureRect.height / lineHeight))

        // 清理临时元素
        document.body.removeChild(measureElement)

        // 如果只有一行，返回右边缘中心
        if (estimatedLines <= 1) {
          return {
            x: rect.right,
            y: rect.top + rect.height / 2
          }
        }

        // 如果有多行，计算最后一行的位置
        // 使用Range API来精确定位最后一个字符
        const range = document.createRange()
        const textNode = this.findLastTextNode(highlightElement)

        if (textNode && textNode.textContent) {
          // 选择最后一个字符
          const lastCharIndex = textNode.textContent.length - 1
          if (lastCharIndex >= 0) {
            range.setStart(textNode, lastCharIndex)
            range.setEnd(textNode, lastCharIndex + 1)

            const rangeRect = range.getBoundingClientRect()
            if (rangeRect.width > 0 && rangeRect.height > 0) {
              return {
                x: rangeRect.right,
                y: rangeRect.top + rangeRect.height / 2
              }
            }
          }
        }

        // 如果Range API失败，使用估算方法
        // 假设最后一行在底部，计算最后一行的大概位置
        const lastLineY = rect.bottom - lineHeight / 2

        // 对于多行文本，假设最后一行可能不是满行，使用一个估算的X位置
        // 这里使用一个简单的启发式：假设最后一行大约占总宽度的70%
        const estimatedLastLineWidth = rect.width * 0.7
        const lastLineX = rect.left + estimatedLastLineWidth

        return {
          x: Math.min(lastLineX, rect.right), // 确保不超过元素边界
          y: lastLineY
        }
      } catch (error) {
        console.error('计算高亮元素最后位置失败:', error)
        // 发生错误时回退到简单的右边缘中心
        const rect = highlightElement.getBoundingClientRect()
        return {
          x: rect.right,
          y: rect.top + rect.height / 2
        }
      }
    },

    // 查找元素中的最后一个文本节点
    findLastTextNode (element) {
      const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
      )

      let lastTextNode = null
      let node
      while ((node = walker.nextNode())) {
        if (node.textContent.trim()) {
          lastTextNode = node
        }
      }

      return lastTextNode
    },

    // 跳转到数据分析页面
    goToDataAnalysis () {
      if (!this.isTaskCompleted) {
        this.$message?.warning('任务处理中，请稍候...')
        return
      }

      const taskId = this.$route.params.taskId || this.$route.query.taskId
      if (taskId) {
        this.$router.push(`/analysis/${taskId}`)
      } else {
        this.$message?.error('缺少任务ID参数')
      }
    },

    // MathJax相关方法
    initializeMathJax () {
      // 检查MathJax是否已经加载
      if (window.MathJax) {
        console.log('MathJax已存在，跳过初始化')
        return
      }

      // 配置MathJax
      window.MathJax = {
        tex: {
          inlineMath: [['\\(', '\\)']],
          displayMath: [['\\[', '\\]']],
          processEscapes: true,
          processEnvironments: true
        },
        options: {
          skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
          ignoreHtmlClass: 'tex2jax_ignore',
          processHtmlClass: 'tex2jax_process'
        },
        startup: {
          ready: () => {
            console.log('MathJax已准备就绪')
            window.MathJax.startup.defaultReady()
          }
        }
      }

      // 动态加载MathJax脚本
      const script = document.createElement('script')
      script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
      script.async = true
      script.id = 'MathJax-script'

      script.onload = () => {
        console.log('MathJax脚本加载完成')
      }

      script.onerror = () => {
        console.error('MathJax脚本加载失败')
      }

      document.head.appendChild(script)
    },

    renderMathJax () {
      // 确保MathJax已加载并且DOM已更新
      this.$nextTick(() => {
        if (window.MathJax && window.MathJax.typesetPromise) {
          console.log('开始重新渲染MathJax公式')

          // 获取文档预览容器
          const container = this.$refs.htmlPreview
          if (container) {
            // 重新渲染指定容器中的数学公式
            window.MathJax.typesetPromise([container]).then(() => {
              console.log('MathJax公式渲染完成')
            }).catch((err) => {
              console.error('MathJax渲染失败:', err)
            })
          }
        } else {
          console.warn('MathJax未准备就绪，延迟重试')
          // 如果MathJax还没准备好，延迟重试
          setTimeout(() => {
            this.renderMathJax()
          }, 500)
        }
      })
    }
  }
}
</script>

<style scoped>
.document-preview-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  padding: 0;
  margin: 0;
  width: 100vw;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  box-sizing: border-box;
  gap: 0; /* 移除间距确保完全靠边 */

  /* 初始状态 - 隐藏且模糊 */
  opacity: 0;
  transform: translateY(40px) scale(0.96);
  filter: blur(12px);
  transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 加载完成状态 - 现代化浮现动效 */
.document-preview-container.loaded {
  opacity: 1;
  transform: translateY(0) scale(1);
  filter: blur(0);
}

/* 左侧目录导航 */
.sidebar-left {
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  transition: all 0.3s ease;
  margin: 0;
  padding: 60px 0 0 0; /* 添加顶部间距避免被导航栏遮挡 */
  position: relative;
  flex-shrink: 0; /* 防止压缩 */

  /* 初始状态 */
  opacity: 0;
  transform: translateX(-30px);
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.1s;
}

.document-preview-container.loaded .sidebar-left {
  opacity: 1;
  transform: translateX(0);
}

/* 统一的顶栏样式 */
.sidebar-header,
.content-header {
  padding: 20px;
  background: linear-gradient(135deg, #e0f2fe 0%, #f3e8ff 100%);
  color: #374151;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  height: 60px; /* 固定高度确保一致 */
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.sidebar-header h3,
.content-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

/* 分析状态指示器样式 */
.analysis-status {
  margin: 10px 0;
  padding: 15px;
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.2);
}

.analysis-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #ff6b6b;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.analysis-text {
  font-size: 14px;
  font-weight: 500;
  color: #856404;
}

.analysis-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #6c757d;
}

.tip-icon {
  margin-right: 5px;
}

.directory-tree {
  padding: 15px;
}

.chapter-item {
  margin-bottom: 8px;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.chapter-item:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: translateX(5px);
}

.chapter-item.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
}

.chapter-item.scrolling {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
  box-shadow: 0 2px 15px rgba(102, 126, 234, 0.4);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
}

.chapter-title {
  padding: 12px 15px;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.chapter-icon {
  font-size: 16px;
}

.sections {
  background: rgba(0, 0, 0, 0.02);
}

.section-item {
  padding: 8px 15px 8px 35px;
  color: #5a6c7d;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-item:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.section-item.active {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
  font-weight: 500;
}

.section-item.scrolling {
  background: rgba(102, 126, 234, 0.3);
  color: #667eea;
  font-weight: 600;
  animation: pulse 1s infinite;
}

.section-icon {
  font-size: 12px;
}

/* 中间内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  margin: 0px 0 0 0;
  border-radius: 0; /* 移除圆角确保完全靠边 */
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.1);
  overflow: hidden;

  /* 初始状态 */
  opacity: 0;
  transform: translateY(20px) scale(0.98);
  transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.2s;
}

.document-preview-container.loaded .main-content {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* 文档预览顶栏特殊布局 */
.content-header {
  padding: 20px 25px;
  justify-content: space-between; /* 覆盖通用样式，保持左右布局 */
  text-align: left; /* 覆盖通用样式 */
}

.header-actions {
  display: flex;
  align-items: center;
}

.analysis-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  backdrop-filter: blur(10px);
}

.analysis-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
}

.analysis-button:disabled {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
  box-shadow: 0 2px 8px rgba(156, 163, 175, 0.2);
}

.analysis-icon {
  font-size: 16px;
}

.html-preview {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.document-content {
  max-width: 100%;
  line-height: 1.6;
}

/* 右侧问题列表 */
.sidebar-right {
  width: 320px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-left: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: -2px 0 20px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  transition: all 0.3s ease;
  margin: 0;
  padding: 60px 0 0 0; /* 添加顶部间距避免被导航栏遮挡 */
  position: relative;
  flex-shrink: 0; /* 防止压缩 */

  /* 初始状态 */
  opacity: 0;
  transform: translateX(30px);
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.3s;
}

.document-preview-container.loaded .sidebar-right {
  opacity: 1;
  transform: translateX(0);
}

.issue-summary {
  margin-top: 8px;
}

.issue-count {
  background: rgba(55, 65, 81, 0.1);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  backdrop-filter: blur(10px);
  color: #374151;
}

.issue-stats {
  padding: 15px 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.05);
  padding: 6px 10px;
  border-radius: 15px;
  font-size: 12px;
}

.severity-badge {
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 600;
}

.severity-badge.total {
  background: #6c5ce7;
  color: white;
}

.severity-badge.高 {
  background: #ff6b6b;
  color: white;
}

.severity-badge.中 {
  background: #feca57;
  color: white;
}

.severity-badge.低 {
  background: #48dbfb;
  color: white;
}

.count {
  font-weight: 600;
  color: #2c3e50;
}

.issues-list {
  padding: 0 20px 20px;
}

.chapter-issues {
  margin-bottom: 20px;
}

.chapter-header {
  margin-bottom: 10px;
}

.chapter-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 14px;
  font-weight: 600;
  padding: 8px 0;
  border-bottom: 2px solid rgba(102, 126, 234, 0.2);
}

.issue-item {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.issue-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.issue-item.高 {
  border-left-color: #ff6b6b;
}

.issue-item.中 {
  border-left-color: #feca57;
}

.issue-item.低 {
  border-left-color: #48dbfb;
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  flex-wrap: wrap;
  gap: 4px;
}

.issue-type {
  font-weight: 600;
  color: #2c3e50;
  font-size: 13px;
}

.severity-tag {
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 600;
}

.severity-tag.高 {
  background: #ff6b6b;
  color: white;
}

.severity-tag.中 {
  background: #feca57;
  color: white;
}

.severity-tag.低 {
  background: #48dbfb;
  color: white;
}

/* 移除模糊匹配相关样式，让模糊匹配和正确匹配看起来一样 */

.issue-location {
  font-size: 11px;
  color: #7f8c8d;
  margin-bottom: 6px;
}

.issue-detail {
  font-size: 12px;
  color: #5a6c7d;
  margin-bottom: 8px;
  line-height: 1.4;
}

.issue-suggestion {
  font-size: 12px;
  color: #27ae60;
  background: rgba(39, 174, 96, 0.1);
  padding: 6px 8px;
  border-radius: 4px;
  line-height: 1.4;
}

/* 滚动条样式 */
.sidebar-left::-webkit-scrollbar,
.sidebar-right::-webkit-scrollbar,
.html-preview::-webkit-scrollbar {
  width: 6px;
}

.sidebar-left::-webkit-scrollbar-track,
.sidebar-right::-webkit-scrollbar-track,
.html-preview::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.sidebar-left::-webkit-scrollbar-thumb,
.sidebar-right::-webkit-scrollbar-thumb,
.html-preview::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.5);
  border-radius: 3px;
}

.sidebar-left::-webkit-scrollbar-thumb:hover,
.sidebar-right::-webkit-scrollbar-thumb:hover,
.html-preview::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.7);
}

/* 确保页面完全靠边的全局样式 */
.document-preview-container {
  box-sizing: border-box;
}

.document-preview-container * {
  box-sizing: border-box;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .sidebar-left {
    width: 240px;
  }
  .sidebar-right {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .document-preview-container {
    flex-direction: column;
  }
  .sidebar-left,
  .sidebar-right {
    width: 100%;
    height: 200px;
  }

  .main-content {
    margin: 0;
  }
}

/* 高亮样式已移至全局样式文件 global.css 中，避免 scoped 样式作用域问题 */
</style>
