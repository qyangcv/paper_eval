/**
 * 原文查找工具
 * 用于在问题分析中查找对应的原文片段
 */

import { findBestMatchInDocument } from './textMatcher.js'

/**
 * 从问题信息中提取查询文本
 * @param {Object} issue 问题信息
 * @returns {string} 提取的查询文本
 */
function extractQueryFromIssue (issue) {
  const queries = []

  // 优先从detail中提取引号内容
  const detail = issue.detail || ''
  if (detail) {
    const quotedText = extractQuotedText(detail)
    if (quotedText && quotedText.length > 3) {
      queries.push(quotedText)
    }

    // 提取detail中的关键短语（去除常见的描述性词汇）
    const cleanDetail = detail.replace(/建议|应该|需要|可以|问题|错误|不当|不合适/g, '')
    const phrases = cleanDetail.split(/[，。；！？\s]+/).filter(phrase => phrase.length > 5)
    queries.push(...phrases.slice(0, 3))
  }

  // 从suggestion中提取
  const suggestion = issue.suggestion || ''
  if (suggestion) {
    const quotedText = extractQuotedText(suggestion)
    if (quotedText && quotedText.length > 3) {
      queries.push(quotedText)
    }

    // 提取建议中的关键短语
    const cleanSuggestion = suggestion.replace(/建议|应该|需要|可以|改为|修改为|替换为/g, '')
    const phrases = cleanSuggestion.split(/[，。；！？\s]+/).filter(phrase => phrase.length > 5)
    queries.push(...phrases.slice(0, 2))
  }

  // 如果已有原文，使用原文
  if (issue.original_text && issue.original_text.trim()) {
    queries.unshift(issue.original_text.trim()) // 原文优先级最高
  }

  // 使用问题类型作为备用查询
  if (issue.type && issue.type.length > 2) {
    queries.push(issue.type)
  }

  // 返回最长的有效查询文本
  const validQueries = queries.filter(q => q && q.length > 3)
  if (validQueries.length === 0) return ''

  // 优先返回最长的查询文本
  return validQueries.reduce((longest, current) =>
    current.length > longest.length ? current : longest
  )
}

/**
 * 从文本中提取引号内的内容
 * @param {string} text 输入文本
 * @returns {string} 提取的引用文本
 */
function extractQuotedText (text) {
  if (!text) return ''

  // 匹配各种引号
  const patterns = [
    /"([^"]+)"/g, // 中文双引号
    /'([^']+)'/g, // 中文单引号
    /"([^"]+)"/g, // 英文双引号
    /'([^']+)'/g // 英文单引号
  ]

  for (const pattern of patterns) {
    const matches = text.match(pattern)
    if (matches && matches.length > 0) {
      // 返回最长的匹配，去除引号
      const longest = matches.reduce((a, b) => a.length > b.length ? a : b)
      return longest.replace(/^["'"]|["'"]$/g, '')
    }
  }

  return ''
}

/**
 * 在文档章节中查找相似片段
 * @param {string} queryText 查询文本
 * @param {Object} documentChapters 章节内容字典
 * @param {Object} options 选项
 * @returns {Array<Object>} 相似片段列表
 */
function findSimilarFragments (queryText, documentChapters, options = {}) {
  const {
    minSimilarity = 0.3,
    maxResults = 10,
    includeChapterInfo = true
  } = options

  if (!queryText || !documentChapters) return []

  const allMatches = []

  Object.entries(documentChapters).forEach(([chapterName, chapterData]) => {
    let chapterContent = ''

    // 处理不同的章节数据格式
    if (typeof chapterData === 'string') {
      chapterContent = chapterData
    } else if (chapterData && typeof chapterData === 'object') {
      chapterContent = chapterData.content || chapterData.text || ''
    }

    if (!chapterContent) return

    const bestMatch = findBestMatchInDocument(queryText, chapterContent, {
      minSimilarity,
      contextWindow: 100
    })

    if (bestMatch) {
      if (includeChapterInfo) {
        bestMatch.chapterName = chapterName
        bestMatch.chapterContentLength = chapterContent.length
      }
      allMatches.push(bestMatch)
    }
  })

  // 按相似度降序排列
  allMatches.sort((a, b) => b.similarity - a.similarity)

  return allMatches.slice(0, maxResults)
}

/**
 * 模糊查找原文的主函数
 * @param {string} queryText 要查找的文本
 * @param {Object} documentData 文档数据
 * @param {Object} options 选项
 * @returns {Object|null} 找到的最佳匹配
 */
function findOriginalTextFuzzy (queryText, documentData, options = {}) {
  const { minSimilarity = 0.4 } = options

  if (!queryText || !documentData) return null

  try {
    // 提取章节内容
    const chapters = {}

    if (documentData.chapters) {
      Object.entries(documentData.chapters).forEach(([chapterName, chapterInfo]) => {
        if (typeof chapterInfo === 'object' && chapterInfo.content) {
          chapters[chapterName] = chapterInfo.content
        } else if (typeof chapterInfo === 'string') {
          chapters[chapterName] = chapterInfo
        }
      })
    } else if (documentData.content) {
      chapters['全文'] = documentData.content
    } else if (typeof documentData === 'object') {
      // 尝试直接使用对象的属性作为章节
      Object.entries(documentData).forEach(([key, value]) => {
        if (typeof value === 'string' && value.length > 50) {
          chapters[key] = value
        }
      })
    } else if (typeof documentData === 'string') {
      chapters['全文'] = documentData
    }

    // 如果有摘要，也加入搜索范围
    if (documentData.abstract) {
      if (typeof documentData.abstract === 'object') {
        Object.entries(documentData.abstract).forEach(([key, value]) => {
          if (typeof value === 'string') {
            chapters[key] = value
          }
        })
      } else if (typeof documentData.abstract === 'string') {
        chapters['摘要'] = documentData.abstract
      }
    }

    console.log('处理的章节数量:', Object.keys(chapters).length)
    console.log('查询文本:', queryText)
    console.log('最小相似度:', minSimilarity)

    if (Object.keys(chapters).length === 0) {
      console.warn('未找到章节内容')
      return null
    }

    // 查找相似片段
    const matches = findSimilarFragments(queryText, chapters, {
      minSimilarity,
      maxResults: 10, // 增加结果数量
      includeChapterInfo: true
    })

    console.log('找到的匹配数量:', matches.length)
    if (matches.length > 0) {
      console.log('最佳匹配:', matches[0])
    }

    if (matches.length > 0) {
      const bestMatch = matches[0]
      return {
        originalText: bestMatch.text,
        similarity: bestMatch.similarity,
        chapterName: bestMatch.chapterName || '未知章节',
        contextBefore: bestMatch.contextBefore || '',
        contextAfter: bestMatch.contextAfter || '',
        fullContext: bestMatch.fullContext || '',
        position: bestMatch.positionInDocument || -1,
        segmentType: bestMatch.segmentTypeUsed || 'unknown',
        allMatches: matches.slice(0, 3) // 返回前3个匹配结果供参考
      }
    }

    // 如果没有找到匹配，尝试更宽松的匹配策略
    console.log('标准匹配失败，尝试宽松匹配...')
    const relaxedMatches = findSimilarFragments(queryText, chapters, {
      minSimilarity: Math.max(0.1, minSimilarity - 0.2),
      maxResults: 5,
      includeChapterInfo: true
    })

    if (relaxedMatches.length > 0) {
      console.log('宽松匹配成功:', relaxedMatches[0])
      const bestMatch = relaxedMatches[0]
      return {
        originalText: bestMatch.text,
        similarity: bestMatch.similarity,
        chapterName: bestMatch.chapterName || '未知章节',
        contextBefore: bestMatch.contextBefore || '',
        contextAfter: bestMatch.contextAfter || '',
        fullContext: bestMatch.fullContext || '',
        position: bestMatch.positionInDocument || -1,
        segmentType: bestMatch.segmentTypeUsed || 'unknown',
        allMatches: relaxedMatches.slice(0, 3),
        isRelaxedMatch: true
      }
    }

    return null
  } catch (error) {
    console.error('模糊查找原文时发生错误:', error)
    return null
  }
}

/**
 * 为问题查找原文
 * @param {Object} issue 问题信息
 * @param {Object} documentData 文档数据
 * @param {Object} options 选项
 * @returns {Object|null} 查找结果
 */
function findOriginalTextForIssue (issue, documentData, options = {}) {
  if (!issue || !documentData) return null

  // 提取查询文本
  const queryText = extractQueryFromIssue(issue)
  console.log('提取的查询文本:', queryText)

  if (!queryText) {
    console.log('无法提取查询文本')
    return null
  }

  // 如果已经有原文且质量较好，先尝试验证原文是否在文档中存在
  if (issue.original_text && issue.original_text.trim().length > 10) {
    const originalTextResult = findOriginalTextFuzzy(issue.original_text, documentData, {
      ...options,
      minSimilarity: 0.8 // 对原文使用较高的相似度要求
    })

    if (originalTextResult) {
      return {
        originalText: issue.original_text,
        similarity: 1.0,
        chapterName: issue.sub_chapter || originalTextResult.chapterName || '未知章节',
        isExisting: true
      }
    }
  }

  // 进行模糊匹配
  const fuzzyResult = findOriginalTextFuzzy(queryText, documentData, options)

  if (fuzzyResult) {
    console.log('模糊匹配成功:', fuzzyResult)
    return fuzzyResult
  }

  // 如果主查询失败，尝试使用更宽松的条件
  console.log('主查询失败，尝试宽松匹配...')
  const relaxedResult = findOriginalTextFuzzy(queryText, documentData, {
    ...options,
    minSimilarity: Math.max(0.15, (options.minSimilarity || 0.3) - 0.15)
  })

  if (relaxedResult) {
    console.log('宽松匹配成功:', relaxedResult)
    return relaxedResult
  }

  console.log('所有匹配尝试都失败了')
  return null
}

/**
 * 格式化匹配结果为可读字符串
 * @param {Object} matchResult 匹配结果
 * @param {Object} options 选项
 * @returns {string} 格式化后的结果字符串
 */
function formatMatchResult (matchResult, options = {}) {
  const { includeContext = true } = options

  if (!matchResult) return '未找到匹配的原文'

  const { originalText, similarity, chapterName } = matchResult

  let result = `在章节「${chapterName}」中找到相似度为 ${(similarity * 100).toFixed(1)}% 的原文：\n`
  result += `「${originalText}」`

  if (includeContext && matchResult.contextBefore) {
    const contextBefore = matchResult.contextBefore
    const contextAfter = matchResult.contextAfter

    if (contextBefore || contextAfter) {
      result += `\n\n上下文：\n...${contextBefore}【${originalText}】${contextAfter}...`
    }
  }

  return result
}

/**
 * 批量为问题列表查找原文
 * @param {Array<Object>} issues 问题列表
 * @param {Object} documentData 文档数据
 * @param {Object} options 选项
 * @returns {Array<Object>} 增强后的问题列表
 */
function enhanceIssuesWithOriginalText (issues, documentData, options = {}) {
  if (!Array.isArray(issues) || !documentData) return issues

  return issues.map(issue => {
    const matchResult = findOriginalTextForIssue(issue, documentData, options)

    if (matchResult && !matchResult.isExisting) {
      return {
        ...issue,
        original_text: matchResult.originalText,
        fuzzy_match_info: {
          similarity: matchResult.similarity,
          chapterName: matchResult.chapterName,
          context: matchResult.fullContext,
          isFuzzyMatch: true
        }
      }
    }

    return issue
  })
}

export {
  extractQueryFromIssue,
  extractQuotedText,
  findSimilarFragments,
  findOriginalTextFuzzy,
  findOriginalTextForIssue,
  formatMatchResult,
  enhanceIssuesWithOriginalText
}
