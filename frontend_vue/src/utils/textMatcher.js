/**
 * 前端文本模糊匹配工具
 * 用于在问题分析中查找原文
 */

/**
 * 计算两个字符串的编辑距离相似度
 * @param {string} str1 第一个字符串
 * @param {string} str2 第二个字符串
 * @returns {number} 相似度分数 [0, 1]
 */
function calculateLevenshteinSimilarity (str1, str2) {
  if (!str1 || !str2) return 0.0

  const len1 = str1.length
  const len2 = str2.length

  if (len1 === 0) return len2 === 0 ? 1.0 : 0.0
  if (len2 === 0) return 0.0

  // 创建距离矩阵
  const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0))

  // 初始化第一行和第一列
  for (let i = 0; i <= len1; i++) matrix[i][0] = i
  for (let j = 0; j <= len2; j++) matrix[0][j] = j

  // 计算编辑距离
  for (let i = 1; i <= len1; i++) {
    for (let j = 1; j <= len2; j++) {
      const cost = str1[i - 1] === str2[j - 1] ? 0 : 1
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1, // 删除
        matrix[i][j - 1] + 1, // 插入
        matrix[i - 1][j - 1] + cost // 替换
      )
    }
  }

  const maxLen = Math.max(len1, len2)
  return (maxLen - matrix[len1][len2]) / maxLen
}

/**
 * 计算Jaccard相似度
 * @param {string} str1 第一个字符串
 * @param {string} str2 第二个字符串
 * @returns {number} 相似度分数 [0, 1]
 */
function calculateJaccardSimilarity (str1, str2) {
  if (!str1 || !str2) return 0.0

  const set1 = new Set(str1)
  const set2 = new Set(str2)

  const intersection = new Set([...set1].filter(x => set2.has(x)))
  const union = new Set([...set1, ...set2])

  return union.size > 0 ? intersection.size / union.size : 0.0
}

/**
 * 计算余弦相似度（基于字符频率）
 * @param {string} str1 第一个字符串
 * @param {string} str2 第二个字符串
 * @returns {number} 相似度分数 [0, 1]
 */
function calculateCosineSimilarity (str1, str2) {
  if (!str1 || !str2) return 0.0

  // 计算字符频率
  const freq1 = {}
  const freq2 = {}

  for (const char of str1) {
    freq1[char] = (freq1[char] || 0) + 1
  }

  for (const char of str2) {
    freq2[char] = (freq2[char] || 0) + 1
  }

  // 获取所有字符
  const allChars = new Set([...Object.keys(freq1), ...Object.keys(freq2)])

  // 构建向量
  const vector1 = []
  const vector2 = []

  for (const char of allChars) {
    vector1.push(freq1[char] || 0)
    vector2.push(freq2[char] || 0)
  }

  // 计算余弦相似度
  const dotProduct = vector1.reduce((sum, val, i) => sum + val * vector2[i], 0)
  const magnitude1 = Math.sqrt(vector1.reduce((sum, val) => sum + val * val, 0))
  const magnitude2 = Math.sqrt(vector2.reduce((sum, val) => sum + val * val, 0))

  if (magnitude1 === 0 || magnitude2 === 0) return 0.0

  return dotProduct / (magnitude1 * magnitude2)
}

/**
 * 计算模糊字符串相似度
 * @param {string} str1 第一个字符串
 * @param {string} str2 第二个字符串
 * @returns {number} 相似度分数 [0, 1]
 */
function calculateFuzzySimilarity (str1, str2) {
  if (!str1 || !str2) return 0.0

  // 预处理：去除标点符号和空格，转换为小写
  const clean1 = str1.replace(/[^\w\u4e00-\u9fff]/g, '').toLowerCase()
  const clean2 = str2.replace(/[^\w\u4e00-\u9fff]/g, '').toLowerCase()

  return calculateLevenshteinSimilarity(clean1, clean2)
}

/**
 * 计算综合相似度分数
 * @param {string} str1 第一个字符串
 * @param {string} str2 第二个字符串
 * @param {Object} weights 各算法权重
 * @returns {number} 综合相似度分数 [0, 1]
 */
function calculateCombinedSimilarity (str1, str2, weights = null) {
  if (!weights) {
    weights = {
      levenshtein: 0.3,
      jaccard: 0.2,
      cosine: 0.3,
      fuzzy: 0.2
    }
  }

  const similarities = {
    levenshtein: calculateLevenshteinSimilarity(str1, str2),
    jaccard: calculateJaccardSimilarity(str1, str2),
    cosine: calculateCosineSimilarity(str1, str2),
    fuzzy: calculateFuzzySimilarity(str1, str2)
  }

  const totalWeight = Object.values(weights).reduce((sum, weight) => sum + weight, 0)
  if (totalWeight === 0) return 0.0

  const weightedSum = Object.entries(similarities).reduce((sum, [method, similarity]) => {
    return sum + (similarities[method] * (weights[method] || 0))
  }, 0)

  return weightedSum / totalWeight
}

/**
 * 应用长度惩罚机制
 * @param {number} similarity 原始相似度
 * @param {string} str1 第一个字符串
 * @param {string} str2 第二个字符串
 * @param {number} penaltyFactor 惩罚因子
 * @returns {number} 调整后的相似度
 */
function applyLengthPenalty (similarity, str1, str2, penaltyFactor = 0.1) {
  const len1 = str1.length
  const len2 = str2.length

  if (len1 === 0 || len2 === 0) return 0.0

  const lengthRatio = Math.min(len1, len2) / Math.max(len1, len2)
  const penalty = (1 - lengthRatio) * penaltyFactor
  const adjustedSimilarity = similarity * (1 - penalty)

  return Math.max(0.0, adjustedSimilarity)
}

/**
 * 将文本分割成片段
 * @param {string} text 输入文本
 * @param {string} segmentType 分割类型 ('sentence', 'paragraph', 'window')
 * @returns {Array<string>} 文本片段列表
 */
function splitTextIntoSegments (text, segmentType = 'sentence') {
  if (!text) return []

  switch (segmentType) {
    case 'sentence': {
      // 按句子分割，支持更多中文标点
      const sentences = text.split(/[。！？；：\n]/).map(s => s.trim()).filter(s => s.length > 3)

      // 如果句子太少，尝试按逗号分割
      if (sentences.length < 3) {
        const clauses = text.split(/[，、]/).map(s => s.trim()).filter(s => s.length > 5)
        return clauses.length > sentences.length ? clauses : sentences
      }

      return sentences
    }
    case 'paragraph': {
      // 按段落分割
      return text.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 10)
    }
    case 'window': {
      // 滑动窗口分割，动态调整窗口大小
      const textLength = text.length
      const windowSize = Math.min(100, Math.max(30, textLength / 10))
      const step = Math.floor(windowSize / 3)
      const segments = []

      for (let i = 0; i <= textLength - windowSize; i += step) {
        segments.push(text.substring(i, i + windowSize))
      }

      // 确保包含文本末尾
      if (textLength > windowSize) {
        segments.push(text.substring(textLength - windowSize))
      }

      return segments.filter(s => s.trim().length > 10)
    }
    default:
      return [text]
  }
}

/**
 * 在候选文本中找到最佳匹配
 * @param {string} queryText 查询文本
 * @param {Array<string>} candidateTexts 候选文本列表
 * @param {Object} options 选项
 * @returns {Array<Object>} 匹配结果列表
 */
function findBestMatches (queryText, candidateTexts, options = {}) {
  const {
    segmentType = 'sentence',
    minSimilarity = 0.3,
    maxResults = 10,
    weights = null
  } = options

  if (!queryText || !candidateTexts || candidateTexts.length === 0) {
    return []
  }

  const allMatches = []

  candidateTexts.forEach((candidateText, sourceIndex) => {
    if (!candidateText) return

    const segments = splitTextIntoSegments(candidateText, segmentType)

    segments.forEach((segment, segmentIndex) => {
      if (!segment.trim()) return

      const similarity = calculateCombinedSimilarity(queryText, segment, weights)
      const adjustedSimilarity = applyLengthPenalty(similarity, queryText, segment, 0.05) // 减少长度惩罚

      // 对于较短的查询文本，降低相似度要求
      const effectiveMinSimilarity = queryText.length < 10 ? minSimilarity * 0.7 : minSimilarity

      if (adjustedSimilarity >= effectiveMinSimilarity) {
        allMatches.push({
          text: segment,
          similarity: adjustedSimilarity,
          rawSimilarity: similarity,
          sourceIndex,
          segmentIndex,
          segmentType,
          lengthRatio: Math.min(queryText.length, segment.length) / Math.max(queryText.length, segment.length)
        })
      }
    })
  })

  // 按相似度降序排列
  allMatches.sort((a, b) => b.similarity - a.similarity)

  return allMatches.slice(0, maxResults)
}

/**
 * 在文档中找到最佳匹配片段
 * @param {string} queryText 查询文本
 * @param {string} documentContent 文档内容
 * @param {Object} options 选项
 * @returns {Object|null} 最佳匹配结果
 */
function findBestMatchInDocument (queryText, documentContent, options = {}) {
  const { contextWindow = 100 } = options

  if (!queryText || !documentContent) return null

  const segmentTypes = ['sentence', 'paragraph', 'window']
  let bestMatch = null
  let bestSimilarity = 0.0

  for (const segmentType of segmentTypes) {
    const matches = findBestMatches(queryText, [documentContent], {
      ...options,
      segmentType
    })

    if (matches.length > 0 && matches[0].similarity > bestSimilarity) {
      bestSimilarity = matches[0].similarity
      bestMatch = { ...matches[0], segmentTypeUsed: segmentType }
    }
  }

  if (bestMatch) {
    // 添加上下文信息
    const matchedText = bestMatch.text
    const matchStart = documentContent.indexOf(matchedText)

    if (matchStart !== -1) {
      const contextStart = Math.max(0, matchStart - contextWindow)
      const contextEnd = Math.min(documentContent.length, matchStart + matchedText.length + contextWindow)

      bestMatch.contextBefore = documentContent.substring(contextStart, matchStart)
      bestMatch.contextAfter = documentContent.substring(matchStart + matchedText.length, contextEnd)
      bestMatch.fullContext = documentContent.substring(contextStart, contextEnd)
      bestMatch.positionInDocument = matchStart
      bestMatch.contextStart = contextStart
      bestMatch.contextEnd = contextEnd
    }
  }

  return bestMatch
}

export {
  calculateLevenshteinSimilarity,
  calculateJaccardSimilarity,
  calculateCosineSimilarity,
  calculateFuzzySimilarity,
  calculateCombinedSimilarity,
  applyLengthPenalty,
  splitTextIntoSegments,
  findBestMatches,
  findBestMatchInDocument
}
