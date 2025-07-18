/**
 * 模糊搜索定位优化测试工具
 * 用于测试修复后的模糊搜索定位功能
 */

export class ScrollOptimizationTest {
  constructor(documentPreviewComponent) {
    this.component = documentPreviewComponent
    this.testResults = []
  }

  /**
   * 测试多次点击同一问题的定位准确性
   */
  async testMultipleClicks(issue, clickCount = 5) {
    console.log(`开始测试问题 ${issue.id} 的多次点击定位...`)
    
    const results = []
    
    for (let i = 0; i < clickCount; i++) {
      console.log(`第 ${i + 1} 次点击测试`)
      
      // 记录点击前的滚动位置
      const beforeScrollTop = this.component.$refs.htmlPreview?.scrollTop || 0
      
      // 执行点击
      await this.component.highlightIssue(issue)
      
      // 等待滚动完成
      await this.waitForScrollComplete()
      
      // 记录点击后的滚动位置
      const afterScrollTop = this.component.$refs.htmlPreview?.scrollTop || 0
      
      // 检查是否有高亮元素
      const highlightElements = this.component.$refs.htmlPreview?.querySelectorAll('.issue-highlight') || []
      
      results.push({
        clickIndex: i + 1,
        beforeScrollTop,
        afterScrollTop,
        scrollDifference: Math.abs(afterScrollTop - beforeScrollTop),
        highlightCount: highlightElements.length,
        hasHighlight: highlightElements.length > 0,
        timestamp: Date.now()
      })
      
      // 等待一段时间再进行下次点击
      await this.delay(500)
    }
    
    // 分析结果
    const analysis = this.analyzeResults(results)
    
    this.testResults.push({
      issueId: issue.id,
      issueType: issue.type,
      clickResults: results,
      analysis
    })
    
    console.log('测试结果:', analysis)
    return analysis
  }

  /**
   * 等待滚动完成
   */
  async waitForScrollComplete() {
    return new Promise(resolve => {
      let lastScrollTop = -1
      let stableCount = 0
      
      const checkScroll = () => {
        const currentScrollTop = this.component.$refs.htmlPreview?.scrollTop || 0
        
        if (Math.abs(currentScrollTop - lastScrollTop) < 1) {
          stableCount++
          if (stableCount >= 3) {
            resolve()
            return
          }
        } else {
          stableCount = 0
        }
        
        lastScrollTop = currentScrollTop
        setTimeout(checkScroll, 100)
      }
      
      checkScroll()
    })
  }

  /**
   * 延迟函数
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 分析测试结果
   */
  analyzeResults(results) {
    if (results.length === 0) {
      return { success: false, message: '没有测试结果' }
    }

    // 检查是否所有点击都成功高亮
    const allHighlighted = results.every(r => r.hasHighlight)
    
    // 检查滚动位置的一致性
    const scrollPositions = results.map(r => r.afterScrollTop)
    const uniquePositions = [...new Set(scrollPositions)]
    const positionConsistent = uniquePositions.length === 1
    
    // 计算滚动位置的标准差
    const avgScrollTop = scrollPositions.reduce((a, b) => a + b, 0) / scrollPositions.length
    const variance = scrollPositions.reduce((sum, pos) => sum + Math.pow(pos - avgScrollTop, 2), 0) / scrollPositions.length
    const standardDeviation = Math.sqrt(variance)
    
    const analysis = {
      success: allHighlighted && standardDeviation < 50, // 标准差小于50像素认为是成功的
      allHighlighted,
      positionConsistent,
      scrollPositions,
      averageScrollPosition: avgScrollTop,
      standardDeviation,
      maxScrollDifference: Math.max(...results.map(r => r.scrollDifference)),
      message: ''
    }
    
    if (analysis.success) {
      analysis.message = '✅ 多次点击定位测试通过'
    } else {
      const issues = []
      if (!allHighlighted) issues.push('部分点击未能正确高亮')
      if (standardDeviation >= 50) issues.push(`滚动位置不稳定(标准差: ${standardDeviation.toFixed(1)}px)`)
      analysis.message = `❌ 测试失败: ${issues.join(', ')}`
    }
    
    return analysis
  }

  /**
   * 测试所有问题的定位功能
   */
  async testAllIssues(issues, clicksPerIssue = 3) {
    console.log(`开始测试 ${issues.length} 个问题的定位功能...`)
    
    for (const issue of issues) {
      await this.testMultipleClicks(issue, clicksPerIssue)
    }
    
    return this.generateReport()
  }

  /**
   * 生成测试报告
   */
  generateReport() {
    const totalTests = this.testResults.length
    const successfulTests = this.testResults.filter(r => r.analysis.success).length
    const successRate = totalTests > 0 ? (successfulTests / totalTests * 100).toFixed(1) : 0
    
    const report = {
      totalTests,
      successfulTests,
      failedTests: totalTests - successfulTests,
      successRate: `${successRate}%`,
      details: this.testResults,
      summary: {
        avgStandardDeviation: this.testResults.reduce((sum, r) => sum + r.analysis.standardDeviation, 0) / totalTests,
        maxStandardDeviation: Math.max(...this.testResults.map(r => r.analysis.standardDeviation)),
        allHighlightedRate: this.testResults.filter(r => r.analysis.allHighlighted).length / totalTests * 100
      }
    }
    
    console.log('=== 模糊搜索定位优化测试报告 ===')
    console.log(`总测试数: ${report.totalTests}`)
    console.log(`成功率: ${report.successRate}`)
    console.log(`平均滚动位置标准差: ${report.summary.avgStandardDeviation.toFixed(1)}px`)
    console.log(`高亮成功率: ${report.summary.allHighlightedRate.toFixed(1)}%`)
    
    return report
  }

  /**
   * 清理测试数据
   */
  reset() {
    this.testResults = []
  }
}

// 使用示例：
// const tester = new ScrollOptimizationTest(this) // 在DocumentPreview组件中使用
// const report = await tester.testAllIssues(this.issues, 3)
