<template>
  <div class="data-analysis-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-loading-directive v-loading="true" element-loading-text="正在加载数据分析报告...">
        <div style="height: 400px;"></div>
      </el-loading-directive>
    </div>

    <!-- 数据分析内容 -->
    <div v-else class="analysis-layout">
        <!-- 左侧导航栏 -->
        <div class="left-navigation">
          <div class="nav-content">
            <div class="nav-section">
              <div class="nav-section-title">基础信息</div>
              <div class="nav-items">
                <div class="nav-item" :class="{ active: activeNavItem === 'basic-info' }" @click="scrollToSection('basic-info')">
                  <div>
                    <el-icon><Document /></el-icon>
                    <span>论文基础信息</span>
                  </div>
                </div>
                <div class="nav-item" :class="{ active: activeNavItem === 'overall-stats' }" @click="scrollToSection('overall-stats')">
                  <div>
                    <el-icon><DataBoard /></el-icon>
                    <span>整体统计概览</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="nav-section">
              <div class="nav-section-title">图表分析</div>
              <div class="nav-items">
                <div class="nav-item" :class="{ active: activeNavItem === 'chapter-content' }" @click="scrollToSection('chapter-content')">
                  <div>
                    <el-icon><TrendCharts /></el-icon>
                    <span>章节内容统计</span>
                  </div>
                </div>
                <div class="nav-item" :class="{ active: activeNavItem === 'literature-analysis' }" @click="scrollToSection('literature-analysis')">
                  <div>
                    <el-icon><Document /></el-icon>
                    <span>文献分析</span>
                  </div>
                </div>
                <div class="nav-item" :class="{ active: activeNavItem === 'evaluation-analysis' }" @click="scrollToSection('evaluation-analysis')">
                  <div>
                    <el-icon><Star /></el-icon>
                    <span>评价分析</span>
                  </div>
                </div>
                <div class="nav-item" :class="{ active: activeNavItem === 'dimension-radar' }" @click="scrollToSection('dimension-radar')">
                  <div>
                    <el-icon><Radar /></el-icon>
                    <span>维度雷达图</span>
                  </div>
                </div>
                <div class="nav-item" :class="{ active: activeNavItem === 'dimension-relation' }" @click="scrollToSection('dimension-relation')">
                  <div>
                    <el-icon><Connection /></el-icon>
                    <span>维度章节关联图</span>
                  </div>
                </div>
                <div class="nav-item" :class="{ active: activeNavItem === 'issues-analysis' }" @click="scrollToSection('issues-analysis')">
                  <div>
                    <el-icon><Warning /></el-icon>
                    <span>问题分析</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="nav-section">
              <div class="nav-section-title">快速统计</div>
              <div class="nav-stats">
                <div class="stat-quick">
                  <span class="stat-label">总字数</span>
                  <span class="stat-value">{{ analysisData.overall_stats?.total_words?.toLocaleString() }}</span>
                </div>
                <div class="stat-quick">
                  <span class="stat-label">维度得分均分</span>
                  <span class="stat-value">{{ dimensionAverageScore }}分</span>
                </div>
                <div class="stat-quick">
                  <span class="stat-label">问题数量</span>
                  <span class="stat-value">{{ analysisData.issue_list?.summary?.total_issues || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 主要内容区域 -->
        <div class="main-content">
          <!-- 基础信息和统计概览区域 -->
          <div class="info-stats-section" id="basic-info">
          <div class="info-stats-row">
            <!-- 基础信息卡片 -->
            <div class="info-card">
              <div class="card-header">
                <div class="card-title">
                  <span class="title-emoji">📄</span>
                  论文基础信息
                </div>
              </div>
              <div class="info-content">
                <div class="info-grid">
                  <div class="info-item">
                    <span class="info-icon">📝</span>
                    <span class="info-label">论文标题</span>
                    <div class="info-divider"></div>
                    <span class="info-value">{{ analysisData.basic_info?.title }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-icon">👤</span>
                    <span class="info-label">作者</span>
                    <div class="info-divider"></div>
                    <span class="info-value">{{ analysisData.basic_info?.author }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-icon">🏫</span>
                    <span class="info-label">学院</span>
                    <div class="info-divider"></div>
                    <span class="info-value">{{ analysisData.basic_info?.school }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-icon">👨‍🏫</span>
                    <span class="info-label">指导教师</span>
                    <div class="info-divider"></div>
                    <span class="info-value">{{ analysisData.basic_info?.advisor }}</span>
                  </div>
                  <div class="info-item keywords-item">
                    <span class="info-icon">🔖</span>
                    <span class="info-label">关键词</span>
                    <div class="info-divider"></div>
                    <div class="keywords-tags">
                      <el-tag
                        v-for="keyword in analysisData.basic_info?.keywords || []"
                        :key="keyword"
                        size="small"
                        type="primary"
                        class="keyword-tag"
                      >
                        {{ keyword }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 整体统计卡片 -->
            <div class="stats-card" id="overall-stats">
              <div class="card-header">
                <div class="card-title">
                  <span class="title-emoji">📊</span>
                  整体统计概览
                </div>
              </div>
              <div class="stats-content">
                <div class="stats-grid-rows">
                  <!-- 第一行：总字数、章节数、段落数 -->
                  <div class="stats-row">
                    <div class="stat-item-new">
                      <span class="stat-icon-new">📝</span>
                      <span class="stat-label-new">总字数</span>
                      <div class="stat-divider"></div>
                      <span class="stat-value-new">{{ analysisData.overall_stats?.total_words?.toLocaleString() }}</span>
                    </div>
                    <div class="stat-item-new">
                      <span class="stat-icon-new">📚</span>
                      <span class="stat-label-new">章节数</span>
                      <div class="stat-divider"></div>
                      <span class="stat-value-new">{{ analysisData.chapter_stats?.chapters?.length || 0 }}</span>
                    </div>
                    <div class="stat-item-new">
                      <span class="stat-icon-new">📄</span>
                      <span class="stat-label-new">段落数</span>
                      <div class="stat-divider"></div>
                      <span class="stat-value-new">{{ analysisData.overall_stats?.total_paragraphs }}</span>
                    </div>
                  </div>

                  <!-- 第二行：图片数量、表格数量、公式数量 -->
                  <div class="stats-row">
                    <div class="stat-item-new">
                      <span class="stat-icon-new">🖼️</span>
                      <span class="stat-label-new">图片数量</span>
                      <div class="stat-divider"></div>
                      <span class="stat-value-new">{{ analysisData.overall_stats?.total_images }}</span>
                    </div>
                    <div class="stat-item-new">
                      <span class="stat-icon-new">📋</span>
                      <span class="stat-label-new">表格数量</span>
                      <div class="stat-divider"></div>
                      <span class="stat-value-new">{{ analysisData.overall_stats?.total_tables }}</span>
                    </div>
                    <div class="stat-item-new">
                      <span class="stat-icon-new">🧮</span>
                      <span class="stat-label-new">公式数量</span>
                      <div class="stat-divider"></div>
                      <span class="stat-value-new">{{ analysisData.overall_stats?.total_equations }}</span>
                    </div>
                  </div>

                  <!-- 第三行：参考文献数、维度均分、问题数量 -->
                  <div class="stats-row">
                    <div class="stat-item-new">
                      <span class="stat-icon-new">📖</span>
                      <span class="stat-label-new">参考文献数</span>
                      <div class="stat-divider"></div>
                      <span class="stat-value-new">{{ analysisData.reference_stats?.total_references }}</span>
                    </div>
                    <div class="stat-item-new">
                      <span class="stat-icon-new">⭐</span>
                      <span class="stat-label-new">维度均分</span>
                      <div class="stat-divider"></div>
                      <span class="stat-value-new">{{ dimensionAverageScore }}分</span>
                    </div>
                    <div class="stat-item-new">
                      <span class="stat-icon-new">⚠️</span>
                      <span class="stat-label-new">问题数量</span>
                      <div class="stat-divider"></div>
                      <span class="stat-value-new">{{ analysisData.issue_list?.summary?.total_issues || 0 }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

          <!-- 图表分析区域 -->
          <div class="charts-section">
            <!-- 章节内容统计折线图 -->
            <div class="chart-card full-width shadow-card" id="chapter-content" v-motion-slide-visible-once-bottom>
            <div class="card-header">
              <div class="card-title">
                <el-icon><TrendCharts /></el-icon>
                章节内容统计折线图
              </div>
            </div>
            <div class="chart-container large">
              <v-chart
                class="chart"
                :option="chapterContentLineOption"
                autoresize
              />
            </div>
          </div>

          <!-- 文献分析板块 -->
          <div class="analysis-block" id="literature-analysis" v-motion-slide-visible-once-bottom>
            <div class="block-header">
              <div class="block-title">
                <el-icon><Document /></el-icon>
                文献分析
              </div>
              <div class="block-subtitle">参考文献类型、语言分布及时效性分析</div>
            </div>
            <div class="block-content">
              <div class="charts-grid">
                <div class="chart-card">
                  <div class="card-header">
                    <div class="card-title">
                      <el-icon><PieChart /></el-icon>
                      文献类型分布
                    </div>
                  </div>
                  <div class="chart-container">
                    <v-chart
                      class="chart"
                      :option="referenceTypePieOption"
                      autoresize
                    />
                  </div>
                </div>

                <div class="chart-card">
                  <div class="card-header">
                    <div class="card-title">
                      <el-icon><DataBoard /></el-icon>
                      语言分布
                    </div>
                  </div>
                  <div class="chart-container">
                    <v-chart
                      class="chart"
                      :option="referenceLangPieOption"
                      autoresize
                    />
                  </div>
                </div>

                <div class="chart-card">
                  <div class="card-header">
                    <div class="card-title">
                      <el-icon><TrendCharts /></el-icon>
                      时效性分析
                    </div>
                  </div>
                  <div class="chart-container">
                    <v-chart
                      class="chart"
                      :option="referenceTimelinessOption"
                      autoresize
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 评价分析板块 -->
          <div class="analysis-block" id="evaluation-analysis" v-motion-slide-visible-once-bottom>
            <div class="block-header">
              <div class="block-title">
                <el-icon><Star /></el-icon>
                评价分析
              </div>
              <div class="block-subtitle">论文质量评价维度及详细分析</div>
            </div>
            <div class="block-content">
              <div class="evaluation-new-layout">
                <!-- 维度导航栏 -->
                <div class="dimension-nav-bar">
                  <div
                    v-for="(dimension, index) in evaluationDimensions"
                    :key="index"
                    class="nav-item"
                    :class="{ active: activeDimension === index }"
                    @click="activeDimension = index"
                  >
                    <div class="nav-content">
                      <span class="nav-name">{{ dimension.name }}</span>
                      <span class="nav-weight">权重: {{ dimension.weight || 1.0 }}</span>
                    </div>
                  </div>
                </div>

                <!-- 维度详细内容 -->
                <div class="dimension-detail-content" v-if="currentDimension" v-motion-slide-visible-once-bottom>
                  <div class="content-header">
                    <div class="dimension-title-section">
                      <div class="dimension-icon">{{ getDimensionEmoji(currentDimension.name) }}</div>
                      <h3>{{ currentDimension.name }}</h3>
                    </div>
                    <div class="score-display-enhanced">
                      <div class="score-main">
                        <span class="score-number" v-motion-pop-visible-once>{{ currentDimension.score }}</span>
                        <span class="score-divider">/</span>
                        <span class="score-total">{{ currentDimension.full_score }}</span>
                      </div>
                      <div class="score-percentage" :class="currentDimension ? getPercentageColorClass(currentDimension.score, currentDimension.full_score) : ''" v-motion-slide-visible-once-right>
                        {{ currentDimension ? Math.round((currentDimension.score / currentDimension.full_score) * 100) : 0 }}%
                      </div>
                    </div>
                  </div>

                  <div class="content-body">
                    <div class="comment-section-enhanced" v-motion-fade-visible-once>
                      <div class="comment-header">
                        <span class="comment-icon">💬</span>
                        <h4>总体评价</h4>
                      </div>
                      <div class="comment-content">
                        <p>{{ currentDimension.comment }}</p>
                      </div>
                    </div>

                    <div class="details-grid-enhanced">
                      <div class="detail-item-enhanced advantages" v-motion-slide-visible-once-left>
                        <div class="detail-header">
                          <span class="detail-emoji">✨</span>
                          <h4>优势亮点</h4>
                          <div class="detail-count">{{ currentDimension.advantages.length }}</div>
                        </div>
                        <div class="detail-content">
                          <div class="advantage-item" v-for="(advantage, index) in currentDimension.advantages" :key="advantage"
                               v-motion-slide-visible-once-bottom :delay="index * 100">
                            <div class="item-icon">🎯</div>
                            <div class="item-text">{{ advantage }}</div>
                          </div>
                        </div>
                      </div>

                      <div class="detail-item-enhanced weaknesses" v-motion-slide-visible-once-bottom>
                        <div class="detail-header">
                          <span class="detail-emoji">⚠️</span>
                          <h4>待改进点</h4>
                          <div class="detail-count">{{ currentDimension.weaknesses.length }}</div>
                        </div>
                        <div class="detail-content">
                          <div class="weakness-item" v-for="(weakness, index) in currentDimension.weaknesses" :key="weakness"
                               v-motion-slide-visible-once-bottom :delay="index * 100">
                            <div class="item-icon">🔍</div>
                            <div class="item-text">{{ weakness }}</div>
                          </div>
                        </div>
                      </div>

                      <div class="detail-item-enhanced suggestions" v-motion-slide-visible-once-right>
                        <div class="detail-header">
                          <span class="detail-emoji">💡</span>
                          <h4>改进建议</h4>
                          <div class="detail-count">{{ currentDimension.suggestions.length }}</div>
                        </div>
                        <div class="detail-content">
                          <div class="suggestion-item" v-for="(suggestion, index) in currentDimension.suggestions" :key="suggestion"
                               v-motion-slide-visible-once-bottom :delay="index * 100">
                            <div class="item-icon">🚀</div>
                            <div class="item-text">{{ suggestion }}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 维度雷达图 - 独立卡片 -->
          <div class="chart-card full-width shadow-card" id="dimension-radar" v-motion-slide-visible-once-bottom>
            <div class="card-header">
              <div class="card-title">
                <el-icon><Radar /></el-icon>
                评价维度雷达图
              </div>
            </div>
            <div class="chart-container radar-enhanced">
              <v-chart
                class="chart"
                :option="evaluationRadarOption"
                autoresize
              />
            </div>
          </div>

          <!-- 维度章节关联图 - 独立卡片 -->
          <div class="chart-card full-width shadow-card" id="dimension-relation" v-motion-slide-visible-once-bottom>
            <div class="card-header">
              <div class="card-title">
                <el-icon><Connection /></el-icon>
                评价维度与章节关联图
              </div>
            </div>
            <div class="chart-container relation-chart-horizontal">
              <v-chart
                class="chart"
                :option="dimensionChapterRelationOption"
                autoresize
              />
            </div>
          </div>

          <!-- 问题分析板块 -->
          <div class="analysis-block issues-analysis-block" id="issues-analysis" v-motion-slide-visible-once-bottom>
            <div class="block-header issues-block-header">
              <div class="block-title">
                <div class="title-icon-wrapper">
                  <el-icon><Warning /></el-icon>
                </div>
                <div class="title-content">
                  <span class="title-text">问题分析</span>
                </div>
              </div>
              <div class="block-subtitle">深度分析论文中的问题类型分布与详细建议</div>
            </div>
            <div class="block-content issues-block-content">
              <div class="issues-layout">
                <!-- 问题统计卡片 -->
                <div class="issues-stats-section">
                  <div class="chart-card issues-stats-card">
                    <div class="card-header stats-card-header">
                      <div class="card-title">
                        <div class="stats-icon-wrapper">
                          <el-icon><PieChart /></el-icon>
                        </div>
                        <div class="stats-title-content">
                          <span class="stats-title">问题类型分布</span>
                          <span class="stats-subtitle">按类型统计问题数量</span>
                        </div>
                      </div>
                      <div class="issues-summary-enhanced">
                        <div class="summary-main">
                          <span class="summary-number">{{ analysisData.issue_list?.summary?.total_issues || 0 }}</span>
                          <span class="summary-label">个问题</span>
                        </div>
                        <div class="summary-status" :class="getSummaryStatusClass(analysisData.issue_list?.summary?.total_issues || 0)">
                          {{ getSummaryStatusText(analysisData.issue_list?.summary?.total_issues || 0) }}
                        </div>
                      </div>
                    </div>
                    <div class="chart-container issues-chart-container">
                      <v-chart
                        ref="issueTypeChart"
                        class="chart"
                        :option="issueTypePieOption"
                        :autoresize="true"
                        :resize-delay="100"
                        @click="onIssueChartClick"
                        @mouseover="onIssueChartMouseover"
                        @mouseout="onIssueChartMouseout"
                      />
                    </div>
                  </div>
                </div>

                <!-- 问题详情区域 -->
                <div class="issues-details-section">
                  <!-- 问题严重程度统计 -->
                  <div class="severity-stats-bar">
                    <div class="severity-summary-text">
                      <span class="severity-stat-item total">
                        <span class="severity-label">总</span>
                        <span class="severity-count">{{ analysisData.issue_list?.summary?.total_issues || 0 }}</span>
                      </span>
                      <span
                        v-for="(count, severity) in analysisData.issue_list?.summary?.severity_distribution"
                        :key="severity"
                        class="severity-stat-item"
                        :class="severity"
                      >
                        <span class="severity-label">{{ severity }}</span>
                        <span class="severity-count">{{ count }}</span>
                      </span>
                    </div>
                  </div>

                  <div class="issues-nav enhanced-issues-nav">
                    <el-tabs
                      v-model="activeIssueTab"
                      type="border-card"
                      class="enhanced-tabs"
                      v-if="analysisData.issue_list && analysisData.issue_list.by_chapter"
                      @tab-change="handleTabChange"
                    >
                      <el-tab-pane
                        v-for="(issues, chapter) in analysisData.issue_list.by_chapter"
                        :key="chapter"
                        :label="chapter"
                        :name="chapter"
                      >
                        <div class="issues-list enhanced-issues-list">
                          <div class="issues-count-info">
                            <el-icon><InfoFilled /></el-icon>
                            本章节共发现 <strong>{{ issues.length }}</strong> 个问题
                          </div>
                          <div
                            v-for="(issue, index) in issues"
                            :key="issue.id"
                            class="issue-item enhanced-issue-item"
                            :style="{ animationDelay: `${index * 0.1}s` }"
                          >
                            <div class="issue-header enhanced-issue-header">
                              <div class="issue-meta">
                                <div class="issue-type-wrapper">
                                  <el-tag
                                    :type="getIssueTagType(issue.type)"
                                    size="small"
                                    class="issue-type-tag"
                                    effect="dark"
                                  >
                                    <el-icon class="tag-icon">
                                      <component :is="getIssueIcon(issue.type)" />
                                    </el-icon>
                                    {{ issue.type }}
                                  </el-tag>
                                </div>
                                <div class="issue-location">
                                  <el-icon><Location /></el-icon>
                                  <span>{{ issue.sub_chapter }}</span>
                                </div>
                              </div>
                              <div class="issue-severity" :class="getIssueSeverityClass(issue.type)">
                                {{ getIssueSeverityText(issue.type) }}
                              </div>
                            </div>
                            <div class="issue-content enhanced-issue-content">
                              <div class="issue-section original-text-section">
                                <div class="section-header">
                                  <el-icon><Document /></el-icon>
                                  <span class="section-title">原文内容</span>
                                </div>
                                <div class="section-content original-text">
                                  {{ issue.original_text }}
                                </div>
                              </div>
                              <div class="issue-section problem-section">
                                <div class="section-header">
                                  <el-icon><Warning /></el-icon>
                                  <span class="section-title">问题描述</span>
                                </div>
                                <div class="section-content problem-text">
                                  {{ issue.detail }}
                                </div>
                              </div>
                              <div class="issue-section suggestion-section">
                                <div class="section-header">
                                  <el-icon><Promotion /></el-icon>
                                  <span class="section-title">改进建议</span>
                                </div>
                                <div class="section-content suggestion-text">
                                  {{ issue.suggestion }}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </el-tab-pane>
                    </el-tabs>
                    <div v-else class="no-data enhanced-no-data">
                      <div class="no-data-icon">
                        <el-icon><DocumentChecked /></el-icon>
                      </div>
                      <div class="no-data-text">
                        <h3>暂无问题数据</h3>
                        <p>论文质量良好，未发现明显问题</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- 主要内容区域结束 -->
        </div>
      </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import {
  RadarChart,
  PieChart,
  BarChart,
  LineChart,
  GraphChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { LabelLayout } from 'echarts/features'
import VChart from 'vue-echarts'
import {
  DataAnalysis as DataAnalysisIcon,
  Document,
  List,
  Picture as PictureIcon,
  Grid,
  Operation,
  Link as LinkIcon,
  TrendCharts,
  PieChart as PieChartIcon,
  Histogram as RadarIcon,
  Warning,
  DataLine as BarChartIcon,
  DataBoard,
  Star,
  Check,
  Close,
  Promotion,
  Connection,
  Location,
  InfoFilled,
  DocumentChecked,
  EditPen,
  ChatLineRound,
  Tools,
  QuestionFilled,
  CircleCheck,
  Menu as ElMenu
} from '@element-plus/icons-vue'
import { useDocumentStore } from '../stores/document'
import { useRoute } from 'vue-router'
import api from '../services/api'

// 注册ECharts组件
use([
  CanvasRenderer,
  RadarChart,
  PieChart,
  BarChart,
  LineChart,
  GraphChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  LabelLayout
])

export default {
  name: 'DataAnalysis',
  components: {
    VChart,
    DataAnalysisIcon,
    Document,
    List,
    PictureIcon,
    Grid,
    Operation,
    LinkIcon,
    TrendCharts,
    PieChart: PieChartIcon,
    Radar: RadarIcon,
    Warning,
    BarChart: BarChartIcon,
    DataBoard,
    Star,
    Check,
    Close,
    Promotion,
    Connection,
    Location,
    InfoFilled,
    DocumentChecked,
    EditPen,
    ChatLineRound,
    Tools,
    QuestionFilled,
    CircleCheck,
    ElMenu
  },
  setup () {
    const documentStore = useDocumentStore()
    const route = useRoute()

    const activeIssueTab = ref('')
    const activeDimension = ref(0)
    const analysisData = ref({})
    const loading = ref(true)
    const hoveredIssueType = ref(null) // 当前悬停的问题类型
    const activeNavItem = ref('basic-info') // 当前激活的导航项
    const isScrolling = ref(false) // 是否正在滚动中
    const scrollTimeout = ref(null) // 滚动超时句柄
    const lastScrollTime = ref(0) // 上次滚动时间
    const scrollDebounceTimeout = ref(null) // 滚动防抖超时句柄

    // 加载分析数据
    const loadAnalysisData = async () => {
      try {
        loading.value = true

        // 获取task_id，优先从路由参数获取，否则使用默认值
        const taskId = route.params.taskId || route.query.taskId || 'demo-task-id'

        console.log('正在加载数据分析数据，task_id:', taskId)

        try {
          // 使用API服务加载所有分析数据
          analysisData.value = await api.loadAllAnalysisData(taskId)
          console.log('API数据加载成功:', analysisData.value)
        } catch (apiError) {
          console.warn('API数据加载失败，降级到静态数据:', apiError)
          // 降级到静态JSON文件
          const response = await fetch('/data_exhibit.json')
          analysisData.value = await response.json()
          console.log('静态数据加载成功')
        }

        // 设置第一个章节为默认选中的问题标签页
        const chapters = Object.keys(analysisData.value.issue_list?.by_chapter || {})
        if (chapters.length > 0) {
          activeIssueTab.value = chapters[0]
        }

        // 延迟一帧来避免ResizeObserver错误
        await new Promise(resolve => requestAnimationFrame(resolve))
      } catch (error) {
        console.error('加载分析数据失败:', error)
        ElMessage.error('加载分析数据失败')
      } finally {
        loading.value = false
      }
    }

    // 参考文献类型分布饼图配置
    const referenceTypePieOption = computed(() => {
      if (!analysisData.value || !analysisData.value.reference_stats) {
        return {}
      }

      const data = Object.entries(analysisData.value.reference_stats?.by_indicator || {})
        .map(([name, value]) => ({ name, value }))

      return {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'horizontal',
          top: 'top',
          padding: [5, 10, 20, 10],
          itemGap: 10,
          formatter: name => name,
          textStyle: {
            fontSize: 12
          },
          wrap: true
        },
        series: [{
          name: '文献类型',
          type: 'pie',
          radius: '50%',
          top: 40,
          data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }
    })

    // 评价维度雷达图配置
    const evaluationRadarOption = computed(() => {
      if (!analysisData.value || !analysisData.value.evaluation) {
        return {}
      }

      const dimensions = analysisData.value.evaluation?.dimensions || []
      const indicator = dimensions.map(dim => ({
        name: dim.name,
        max: dim.full_score,
        min: 0
      }))
      const actualData = dimensions.map(dim => dim.score)
      const fullData = dimensions.map(dim => dim.full_score)

      return {
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e2e8f0',
          borderWidth: 1,
          textStyle: {
            color: '#2d3748',
            fontSize: 13
          },
          extraCssText: 'box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); border-radius: 8px;',
          formatter: (params) => {
            const dim = dimensions[params.dataIndex]
            const percentage = Math.round((dim.score / dim.full_score) * 100)
            let colorClass = ''
            if (percentage >= 90) colorClass = 'color: #059669;'
            else if (percentage >= 80) colorClass = 'color: #1e40af;'
            else colorClass = 'color: #d97706;'

            return `
              <div style="padding: 4px;">
                <div style="font-weight: 600; margin-bottom: 4px;">${dim.name}</div>
                <div>得分: <span style="font-weight: 600;">${dim.score}</span>/${dim.full_score}</div>
                <div>百分比: <span style="font-weight: 600; ${colorClass}">${percentage}%</span></div>
              </div>
            `
          }
        },
        legend: {
          data: ['实际得分', '满分标准'],
          top: 20,
          left: 'center',
          itemGap: 30,
          textStyle: {
            fontSize: 14,
            color: '#4a5568',
            fontWeight: '500'
          },
          itemStyle: {
            borderWidth: 0
          },
          icon: 'circle',
          itemWidth: 14,
          itemHeight: 14
        },
        grid: {
          top: 80,
          bottom: 60,
          left: 60,
          right: 60
        },
        radar: {
          indicator,
          radius: '65%',
          center: ['50%', '55%'],
          splitNumber: 4,
          shape: 'polygon',
          startAngle: 90,
          axisName: {
            color: '#2c3e50',
            fontSize: 13,
            fontWeight: '600',
            padding: [8, 12],
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderRadius: 8,
            shadowBlur: 4,
            shadowColor: 'rgba(0, 0, 0, 0.1)',
            borderColor: '#e2e8f0',
            borderWidth: 1
          },
          splitLine: {
            lineStyle: {
              color: ['#f7fafc', '#edf2f7', '#e2e8f0', '#cbd5e0'],
              width: 1.5,
              type: 'solid'
            }
          },
          splitArea: {
            show: true,
            areaStyle: {
              color: [
                'rgba(99, 179, 237, 0.02)',
                'rgba(99, 179, 237, 0.04)',
                'rgba(99, 179, 237, 0.06)',
                'rgba(99, 179, 237, 0.08)'
              ]
            }
          },
          axisLine: {
            lineStyle: {
              color: '#a0aec0',
              width: 2
            }
          }
        },
        series: [{
          type: 'radar',
          data: [
            {
              value: actualData,
              name: '实际得分',
              areaStyle: {
                color: {
                  type: 'radial',
                  x: 0.5,
                  y: 0.5,
                  r: 0.6,
                  colorStops: [
                    { offset: 0, color: 'rgba(59, 130, 246, 0.35)' },
                    { offset: 0.7, color: 'rgba(59, 130, 246, 0.15)' },
                    { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
                  ]
                },
                shadowBlur: 20,
                shadowColor: 'rgba(59, 130, 246, 0.25)',
                shadowOffsetX: 0,
                shadowOffsetY: 3
              },
              lineStyle: {
                color: '#3b82f6',
                width: 4,
                shadowBlur: 10,
                shadowColor: 'rgba(59, 130, 246, 0.4)',
                cap: 'round'
              },
              itemStyle: {
                color: '#3b82f6',
                borderColor: '#ffffff',
                borderWidth: 4,
                shadowBlur: 12,
                shadowColor: 'rgba(59, 130, 246, 0.4)',
                shadowOffsetX: 0,
                shadowOffsetY: 3
              },
              symbol: 'circle',
              symbolSize: 14,
              emphasis: {
                itemStyle: {
                  shadowBlur: 20,
                  shadowColor: 'rgba(59, 130, 246, 0.6)'
                }
              }
            },
            {
              value: fullData,
              name: '满分标准',
              lineStyle: {
                color: '#f59e0b',
                width: 3,
                type: [10, 6],
                shadowBlur: 8,
                shadowColor: 'rgba(245, 158, 11, 0.3)',
                cap: 'round'
              },
              itemStyle: {
                color: '#f59e0b',
                borderColor: '#ffffff',
                borderWidth: 3,
                shadowBlur: 8,
                shadowColor: 'rgba(245, 158, 11, 0.3)',
                shadowOffsetX: 0,
                shadowOffsetY: 2
              },
              symbol: 'diamond',
              symbolSize: 12,
              areaStyle: {
                color: 'rgba(245, 158, 11, 0.06)'
              },
              emphasis: {
                itemStyle: {
                  shadowBlur: 15,
                  shadowColor: 'rgba(245, 158, 11, 0.5)'
                }
              }
            }
          ]
        }]
      }
    })

    // 评价维度与章节关联图配置
    const dimensionChapterRelationOption = computed(() => {
      if (!analysisData.value || !analysisData.value.evaluation) {
        return {}
      }

      const dimensions = analysisData.value.evaluation?.dimensions || []

      // 获取主章节列表
      const chaptersList = analysisData.value.chapter_stats?.chapters || []

      // 收集子章节并进行分类
      const subChapters = new Set()

      // 子章节与主章节的映射
      const subToMainChapterMap = {}

      // 提取子章节
      dimensions.forEach(dim => {
        if (dim.focus_chapter && Array.isArray(dim.focus_chapter)) {
          dim.focus_chapter.forEach(subChapter => {
            subChapters.add(subChapter)

            // 通过子章节编号确定其所属的主章节
            // 例如 "3.1_实验设计" 中的 "3" 表示它属于第三章
            const chapterNumberMatch = subChapter.match(/^(\d+)\./)
            if (chapterNumberMatch) {
              const chapterNumber = parseInt(chapterNumberMatch[1])
              // 章节序号是从1开始的，但数组索引从0开始
              if (chapterNumber > 0 && chapterNumber <= chaptersList.length - 2) { // 减去摘要和参考文献
                const mainChapter = chaptersList[chapterNumber + 1] // +2 (摘要) - 1 (索引从0开始)
                subToMainChapterMap[subChapter] = mainChapter
              }
            }
          })
        }
      })

      // 格式化章节名称
      const formatChapterName = (chapter) => {
        return chapter.replace('_', ' ')
      }

      // 整理数据
      const nodes = []
      const links = []
      const categoryMap = {
        dimension: 0, // 评价维度
        mainChapter: 1, // 主章节
        subChapter: 2 // 子章节
      }

      // 添加维度节点
      dimensions.forEach((dim) => {
        nodes.push({
          id: `dim-${dim.name}`,
          name: dim.name,
          symbolSize: 70,
          symbol: 'circle',
          category: categoryMap.dimension,
          label: {
            show: true,
            fontSize: 12,
            formatter: (params) => {
              return dim.name + '\n(' + dim.score + '分)'
            }
          },
          value: dim.score
        })
      })

      // 添加主章节节点（只添加与子章节有关联的主章节）
      const usedMainChapters = [...new Set(Object.values(subToMainChapterMap))]
      usedMainChapters.forEach((chapter) => {
        nodes.push({
          id: `main-${chapter}`,
          name: chapter,
          symbolSize: 55,
          symbol: 'rect',
          category: categoryMap.mainChapter,
          label: {
            show: true
          }
        })
      })

      // 添加子章节节点
      Array.from(subChapters).forEach((chapter) => {
        const mainChapter = subToMainChapterMap[chapter]

        nodes.push({
          id: `sub-${chapter}`,
          name: formatChapterName(chapter),
          symbolSize: 40,
          symbol: 'roundRect',
          category: categoryMap.subChapter,
          label: {
            show: true,
            fontSize: 10
          }
        })

        // 子章节与对应主章节的连接
        if (mainChapter) {
          links.push({
            source: `main-${mainChapter}`,
            target: `sub-${chapter}`,
            lineStyle: {
              width: 1,
              opacity: 0.6,
              curveness: 0.1
            }
          })
        }
      })

      // 维度与子章节的连接
      dimensions.forEach((dim) => {
        if (dim.focus_chapter && Array.isArray(dim.focus_chapter)) {
          dim.focus_chapter.forEach(chapter => {
            links.push({
              source: `dim-${dim.name}`,
              target: `sub-${chapter}`,
              lineStyle: {
                width: 2.5,
                opacity: 0.7,
                curveness: 0.3,
                color: '#1e90ff'
              }
            })
          })
        }
      })

      console.log('Graph data:', { nodes, links, chaptersList, subToMainChapterMap })
      return {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e2e8f0',
          borderWidth: 1,
          textStyle: {
            color: '#334155',
            fontSize: 12
          },
          formatter: (params) => {
            if (params.dataType === 'edge') {
              return `<div style="padding: 4px 8px;">
                        <strong>${params.data.source}</strong>
                        <span style="color: #64748b;">关联</span>
                        <strong>${params.data.target}</strong>
                      </div>`
            }
            return `<div style="padding: 4px 8px;">
                      <strong>${params.name}</strong>
                    </div>`
          }
        },
        legend: [{
          data: ['评价维度', '主章节', '子章节'],
          selectedMode: 'multiple',
          textStyle: {
            fontSize: 14,
            color: '#475569',
            fontWeight: '500'
          },
          left: 'center',
          top: 20,
          orient: 'horizontal',
          itemGap: 40,
          itemWidth: 14,
          itemHeight: 14
        }],
        animationDuration: 2500,
        animationEasingUpdate: 'cubicOut',
        series: [{
          name: '评价维度与章节关系',
          type: 'graph',
          layout: 'force',
          data: nodes,
          links,
          categories: [
            {
              name: '评价维度',
              itemStyle: {
                color: '#8b5cf6',
                borderColor: '#ffffff',
                borderWidth: 3,
                shadowBlur: 12,
                shadowColor: 'rgba(139, 92, 246, 0.4)'
              }
            },
            {
              name: '主章节',
              itemStyle: {
                color: '#06b6d4',
                borderColor: '#ffffff',
                borderWidth: 3,
                shadowBlur: 12,
                shadowColor: 'rgba(6, 182, 212, 0.4)'
              }
            },
            {
              name: '子章节',
              itemStyle: {
                color: '#f59e0b',
                borderColor: '#ffffff',
                borderWidth: 3,
                shadowBlur: 12,
                shadowColor: 'rgba(245, 158, 11, 0.4)'
              }
            }
          ],
          roam: true,
          draggable: true,
          label: {
            show: true,
            position: 'bottom',
            formatter: '{b}',
            fontSize: 12,
            color: '#1e293b',
            fontWeight: '600',
            distance: 8,
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            borderRadius: 4,
            padding: [2, 6]
          },
          force: {
            repulsion: 500,
            gravity: 0.05,
            edgeLength: [150, 300],
            layoutAnimation: true,
            friction: 0.7
          },
          lineStyle: {
            color: '#94a3b8',
            curveness: 0.2,
            width: 2.5,
            opacity: 0.7,
            shadowBlur: 3,
            shadowColor: 'rgba(148, 163, 184, 0.3)'
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4,
              color: '#6366f1',
              opacity: 1,
              shadowBlur: 8,
              shadowColor: 'rgba(99, 102, 241, 0.5)'
            },
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 0, 0, 0.3)',
              borderWidth: 4,
              scale: 1.1
            },
            label: {
              fontSize: 13,
              fontWeight: 'bold',
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              shadowBlur: 5,
              shadowColor: 'rgba(0, 0, 0, 0.1)'
            }
          },
          symbolSize: (value, params) => {
            // 根据节点类型调整大小
            if (params.category === 0) return 55 // 评价维度
            if (params.category === 1) return 45 // 主章节
            return 38 // 子章节
          }
        }]
      }
    })

    // 问题类型统计环形图配置 - ECharts圆角环形图
    const issueTypePieOption = computed(() => {
      if (!analysisData.value || !analysisData.value.issue_list) {
        return {}
      }

      // 定义问题类型对应的颜色，与右侧详细内容标签颜色保持一致
      const getIssueTypeColor = (type) => {
        const colorMap = {
          格式错误: '#e6a23c', // warning - 橙色
          语法问题: '#f56c6c', // danger - 红色
          逻辑不清: '#909399', // info - 灰色
          图表问题: '#409eff', // primary - 蓝色
          公式问题: '#67c23a', // success - 绿色
          引用错误: '#f56c6c' // danger - 红色
        }
        return colorMap[type] || '#909399' // 默认灰色
      }

      const issueTypes = analysisData.value.issue_list?.summary?.issue_types || []
      const data = issueTypes.map(type => {
        // 统计每种类型的问题数量
        let count = 0
        const byChapter = analysisData.value.issue_list?.by_chapter || {}
        Object.values(byChapter).forEach(issues => {
          count += issues.filter(issue => issue.type === type).length
        })
        return {
          name: type,
          value: count,
          itemStyle: {
            color: getIssueTypeColor(type),
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          }
        }
      })

      return {
        tooltip: {
          trigger: 'item'
        },
        legend: {
          top: '5%',
          left: 'center'
        },
        series: [
          {
            name: '问题类型',
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 16,
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data
          }
        ]
      }
    })

    // 章节内容统计折线图配置
    const chapterContentLineOption = computed(() => {
      if (!analysisData.value || !analysisData.value.chapter_stats) {
        return {}
      }

      const chapters = analysisData.value.chapter_stats?.chapters || []
      const wordCounts = analysisData.value.chapter_stats?.word_counts || []
      const imageCounts = analysisData.value.chapter_stats?.image_counts || []
      const tableCounts = analysisData.value.chapter_stats?.table_counts || []
      const equationCounts = analysisData.value.chapter_stats?.equation_counts || []

      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' }
        },
        legend: {
          data: ['字数', '图片', '表格', '公式'],
          top: 60,
          itemGap: 20
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '8%', // 减小折线图与卡片底边的间距
          top: '30%', // 增大图例与折线图之间的间距
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: chapters,
          axisLabel: {
            rotate: 45,
            fontSize: 10
          }
        },
        yAxis: [
          {
            type: 'value',
            name: '字数',
            position: 'left',
            nameGap: 40,
            axisLabel: {
              formatter: '{value}',
              margin: 16
            }
          },
          {
            type: 'value',
            name: '数量',
            position: 'right',
            nameGap: 40,
            axisLabel: {
              formatter: '{value}',
              margin: 16
            }
          }
        ],
        series: [
          {
            name: '字数',
            type: 'line',
            yAxisIndex: 0,
            data: wordCounts,
            smooth: true,
            lineStyle: {
              width: 3,
              color: '#5470c6'
            },
            itemStyle: {
              color: '#5470c6'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [{
                  offset: 0, color: 'rgba(84, 112, 198, 0.3)'
                }, {
                  offset: 1, color: 'rgba(84, 112, 198, 0.1)'
                }]
              }
            }
          },
          {
            name: '图片',
            type: 'line',
            yAxisIndex: 1,
            data: imageCounts,
            smooth: true,
            lineStyle: {
              width: 2,
              color: '#91cc75'
            },
            itemStyle: {
              color: '#91cc75'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [{
                  offset: 0, color: 'rgba(145, 204, 117, 0.3)'
                }, {
                  offset: 1, color: 'rgba(145, 204, 117, 0.1)'
                }]
              }
            }
          },
          {
            name: '表格',
            type: 'line',
            yAxisIndex: 1,
            data: tableCounts,
            smooth: true,
            lineStyle: {
              width: 2,
              color: '#fac858'
            },
            itemStyle: {
              color: '#fac858'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [{
                  offset: 0, color: 'rgba(250, 200, 88, 0.3)'
                }, {
                  offset: 1, color: 'rgba(250, 200, 88, 0.1)'
                }]
              }
            }
          },
          {
            name: '公式',
            type: 'line',
            yAxisIndex: 1,
            data: equationCounts,
            smooth: true,
            lineStyle: {
              width: 2,
              color: '#ee6666'
            },
            itemStyle: {
              color: '#ee6666'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [{
                  offset: 0, color: 'rgba(238, 102, 102, 0.3)'
                }, {
                  offset: 1, color: 'rgba(238, 102, 102, 0.1)'
                }]
              }
            }
          }
        ]
      }
    })

    // 文献语言分布饼图配置
    const referenceLangPieOption = computed(() => {
      if (!analysisData.value || !analysisData.value.reference_stats) {
        return {}
      }

      const data = Object.entries(analysisData.value.reference_stats?.by_lang || {})
        .map(([name, value]) => ({ name, value }))

      return {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'horizontal',
          top: 'top',
          padding: [5, 10, 20, 10],
          itemGap: 10,
          formatter: name => name,
          textStyle: {
            fontSize: 12
          },
          wrap: true
        },
        series: [{
          name: '文献语言',
          type: 'pie',
          radius: ['40%', '70%'],
          top: 40,
          avoidLabelOverlap: false,
          data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }
    })

    // 文献时效性分析图表配置
    const referenceTimelinessOption = computed(() => {
      if (!analysisData.value || !analysisData.value.reference_stats) {
        return {}
      }

      const totalRefs = analysisData.value.reference_stats?.total_references || 0
      const recentRefs = analysisData.value.reference_stats?.recent_3y || 0
      const olderRefs = totalRefs - recentRefs

      const data = [
        { name: '近三年文献', value: recentRefs },
        { name: '三年前文献', value: olderRefs }
      ]

      return {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'horizontal',
          top: 'top',
          padding: [5, 10, 20, 10],
          itemGap: 10,
          formatter: name => name,
          textStyle: {
            fontSize: 12
          },
          wrap: true
        },
        series: [{
          name: '文献时效性',
          type: 'pie',
          radius: ['40%', '70%'],
          top: 40,
          avoidLabelOverlap: false,
          data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }
    })

    // 评价维度数据
    const evaluationDimensions = computed(() => {
      return analysisData.value.evaluation?.dimensions || []
    })

    // 当前选中的维度
    const currentDimension = computed(() => {
      return evaluationDimensions.value[activeDimension.value] || null
    })

    // 维度得分均分（使用权重计算）
    const dimensionAverageScore = computed(() => {
      if (!analysisData.value || !analysisData.value.evaluation) {
        return '0.0'
      }

      const dimensions = analysisData.value.evaluation?.dimensions || []
      if (dimensions.length === 0) {
        return '0.0'
      }

      // 使用权重计算加权平均分
      const totalWeightedScore = dimensions.reduce((sum, dim) => {
        const weight = dim.weight || 1.0
        const score = dim.score || 0
        return sum + (score * weight)
      }, 0)

      const totalWeight = dimensions.reduce((sum, dim) => sum + (dim.weight || 1.0), 0)

      if (totalWeight === 0) {
        return '0.0'
      }

      const weightedAverage = totalWeightedScore / totalWeight
      return weightedAverage.toFixed(1)
    })

    // 问题图表点击事件
    const onIssueChartClick = (params) => {
      // 可以根据点击的问题类型切换到对应的章节
      console.log('点击了问题类型:', params.name)
    }

    // 问题图表鼠标悬停事件 - 简化版本
    const onIssueChartMouseover = (params) => {
      // ECharts圆角环形图的悬停效果由内置样式处理
      console.log('悬停问题类型:', params.name)
    }

    // 问题图表鼠标离开事件 - 简化版本
    const onIssueChartMouseout = () => {
      // ECharts圆角环形图的悬停效果由内置样式处理
    }

    // 辅助函数
    const getScoreTagType = (score) => {
      if (score >= 4.5) return 'success'
      if (score >= 4.0) return 'primary'
      if (score >= 3.5) return 'warning'
      return 'danger'
    }

    const getIssueTagType = (type) => {
      const typeMap = {
        格式错误: 'warning',
        语法问题: 'danger',
        逻辑不清: 'info',
        图表问题: 'primary',
        公式问题: 'success',
        引用错误: 'danger'
      }
      return typeMap[type] || 'info'
    }

    // 根据百分数返回颜色类名
    const getPercentageColorClass = (score, fullScore) => {
      const percentage = Math.round((score / fullScore) * 100)
      if (percentage >= 90) return 'percentage-excellent' // 绿色
      if (percentage >= 80) return 'percentage-good' // 蓝色
      return 'percentage-warning' // 黄色
    }

    // 获取维度对应的emoji
    const getDimensionEmoji = (dimensionName) => {
      const emojiMap = {
        研究内容: '🔬',
        研究方法: '⚙️',
        实验设计: '🧪',
        数据分析: '📊',
        结果讨论: '💭',
        文献综述: '📚',
        创新性: '💡',
        逻辑性: '🧠',
        规范性: '📋',
        完整性: '✅'
      }
      return emojiMap[dimensionName] || '📝'
    }

    // 获取问题类型对应的图标
    const getIssueIcon = (type) => {
      const iconMap = {
        格式错误: 'EditPen',
        语法问题: 'ChatLineRound',
        逻辑不清: 'QuestionFilled',
        图表问题: 'PictureIcon',
        公式问题: 'Operation',
        引用错误: 'LinkIcon'
      }
      return iconMap[type] || 'Warning'
    }

    // 获取问题严重程度类名
    const getIssueSeverityClass = (type) => {
      const severityMap = {
        格式错误: 'severity-low',
        语法问题: 'severity-high',
        逻辑不清: 'severity-medium',
        图表问题: 'severity-medium',
        公式问题: 'severity-medium',
        引用错误: 'severity-high'
      }
      return severityMap[type] || 'severity-medium'
    }

    // 获取问题严重程度文本
    const getIssueSeverityText = (type) => {
      const severityMap = {
        格式错误: '轻微',
        语法问题: '严重',
        逻辑不清: '中等',
        图表问题: '中等',
        公式问题: '中等',
        引用错误: '严重'
      }
      return severityMap[type] || '中等'
    }

    // 获取问题总数状态类名
    const getSummaryStatusClass = (total) => {
      if (total === 0) return 'status-excellent'
      if (total <= 5) return 'status-good'
      if (total <= 15) return 'status-warning'
      return 'status-danger'
    }

    // 获取问题总数状态文本
    const getSummaryStatusText = (total) => {
      if (total === 0) return '优秀'
      if (total <= 5) return '良好'
      if (total <= 15) return '需改进'
      return '需重点关注'
    }

    // 处理标签页切换
    const handleTabChange = async (tabName) => {
      // 由于固定了高度，不再需要触发resize事件
      // 这样可以避免ResizeObserver错误
      console.log('Tab changed to:', tabName)
    }

    // 组件挂载时加载数据
    // 处理ResizeObserver错误
    let resizeObserverErrorHandler = null

    onMounted(() => {
      resizeObserverErrorHandler = (e) => {
        if (e.message === 'ResizeObserver loop completed with undelivered notifications.' ||
            e.message.includes('ResizeObserver loop')) {
          e.stopImmediatePropagation()
          e.preventDefault()
          return false
        }
      }
      window.addEventListener('error', resizeObserverErrorHandler, true)
      loadAnalysisData()
    })

    onUnmounted(() => {
      if (resizeObserverErrorHandler) {
        window.removeEventListener('error', resizeObserverErrorHandler, true)
      }
    })

    // 滚动到指定部分
    const scrollToSection = (sectionId) => {
      const element = document.getElementById(sectionId)
      if (element) {
        // 如果已经是当前激活的项，则不需要滚动
        if (activeNavItem.value === sectionId && !isScrolling.value) {
          return
        }

        // 清除之前的超时
        if (scrollTimeout.value) {
          clearTimeout(scrollTimeout.value)
        }
        if (scrollDebounceTimeout.value) {
          clearTimeout(scrollDebounceTimeout.value)
        }

        // 设置滚动状态，暂时禁用滚动监听
        isScrolling.value = true
        lastScrollTime.value = Date.now()

        // 使用nextTick确保DOM更新后再更新导航状态
        nextTick(() => {
          activeNavItem.value = sectionId
        })

        // 获取顶部导航栏高度，动态获取以确保准确性
        const navbar = document.querySelector('.navbar')
        const navbarHeight = navbar ? navbar.offsetHeight : 60

        // 减小额外偏移量，减小卡片与顶部导航栏之间间隔
        const extraOffset = 8

        const elementPosition = element.offsetTop - navbarHeight - extraOffset

        window.scrollTo({
          top: Math.max(0, elementPosition), // 确保不会滚动到负值
          behavior: 'smooth'
        })

        // 滚动完成后重新启用滚动监听
        scrollTimeout.value = setTimeout(() => {
          isScrolling.value = false
          scrollTimeout.value = null
        }, 800) // 稍微增加延迟确保滚动完成
      }
    }

    // 防抖的滚动处理函数
    const debouncedHandleScroll = () => {
      const now = Date.now()

      // 如果正在程序化滚动，或者距离上次程序化滚动时间太近，则不更新导航状态
      if (isScrolling.value || (now - lastScrollTime.value < 1000)) {
        return
      }

      const navbar = document.querySelector('.navbar')
      const navbarHeight = navbar ? navbar.offsetHeight : 60
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop

      const sections = [
        'basic-info',
        'overall-stats',
        'chapter-content',
        'literature-analysis',
        'evaluation-analysis',
        'dimension-radar',
        'dimension-relation',
        'issues-analysis'
      ]

      let currentSection = 'basic-info'

      for (const sectionId of sections) {
        const element = document.getElementById(sectionId)
        if (element) {
          const elementTop = element.offsetTop - navbarHeight - 80
          if (scrollTop >= elementTop) {
            currentSection = sectionId
          }
        }
      }

      // 只有当检测到的section与当前激活的不同时才更新
      if (currentSection !== activeNavItem.value) {
        activeNavItem.value = currentSection
      }
    }

    // 滚动监听，自动更新导航栏激活状态
    const handleScroll = () => {
      // 清除之前的防抖超时
      if (scrollDebounceTimeout.value) {
        clearTimeout(scrollDebounceTimeout.value)
      }

      // 设置新的防抖超时
      scrollDebounceTimeout.value = setTimeout(() => {
        debouncedHandleScroll()
      }, 50) // 50ms防抖延迟
    }

    // 添加滚动监听
    onMounted(() => {
      window.addEventListener('scroll', handleScroll)
      // 初始化时检查一次
      handleScroll()
    })

    onUnmounted(() => {
      window.removeEventListener('scroll', handleScroll)
      // 清理所有超时句柄
      if (scrollTimeout.value) {
        clearTimeout(scrollTimeout.value)
      }
      if (scrollDebounceTimeout.value) {
        clearTimeout(scrollDebounceTimeout.value)
      }
    })

    return {
      documentStore,
      analysisData,
      activeIssueTab,
      activeDimension,
      activeNavItem,
      isScrolling,
      loading,
      referenceTypePieOption,
      evaluationRadarOption,
      dimensionChapterRelationOption, // Added this line
      issueTypePieOption,
      chapterContentLineOption,
      referenceLangPieOption,
      referenceTimelinessOption,
      evaluationDimensions,
      currentDimension,
      dimensionAverageScore,
      onIssueChartClick,
      onIssueChartMouseover,
      onIssueChartMouseout,
      hoveredIssueType,
      getScoreTagType,
      getIssueTagType,
      getPercentageColorClass,
      getDimensionEmoji,
      getIssueIcon,
      getIssueSeverityClass,
      getIssueSeverityText,
      getSummaryStatusClass,
      getSummaryStatusText,
      handleTabChange,
      scrollToSection
    }
  }
}
</script>

<style scoped>
/* 数据分析页面容器 */
.data-analysis-page {
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
  width: 100%;
}

.data-analysis-page .loading-container {
  width: 100%;
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.analysis-layout {
  display: flex;
  width: 100%;
  min-height: calc(100vh - 60px);
  /* Remove top padding; spacing handled within main-content */
  padding: 0 20px 20px;
  gap: 20px;
  box-sizing: border-box;
}

/* 左侧导航栏样式 */
.left-navigation {
  width: 280px;
  min-width: 280px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  /* Fix navigation bar to viewport */
  position: fixed;
  /* Align just below fixed top navbar (~60px height) */
  top: 60px;
  /* Align with page padding */
  left: 20px;
  z-index: 1000;
  /* Stretch navigation full height */
  height: calc(100vh - 60px);
  /* Disable internal scrolling */
  overflow: visible;
  border: 1px solid #e2e8f0;
}

.nav-content {
  padding: 20px;
}

.nav-section {
  margin-bottom: 24px;
}

.nav-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #4a5568;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #6366f1;
}

.nav-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease, border-left 0.15s ease;
  color: #475569;
  font-size: 14px;
  position: relative;
  border: 1px solid transparent;
  background: transparent;
  transform: translateX(0);
  will-change: transform, background-color;
}

.nav-item:hover {
  background: #f8fafc;
  color: #4f46e5;
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

.nav-item.active {
  background: linear-gradient(135deg, #f0f9ff 0%, #ede9fe 100%);
  color: #4f46e5;
  border-left: 3px solid #6366f1;
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}

.nav-item.active:hover {
  background: linear-gradient(135deg, #e0f2fe 0%, #e4e7ff 100%);
  transform: translateX(2px);
}

.nav-item > div {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.nav-item .el-icon {
  font-size: 16px;
  flex-shrink: 0;
  color: #64748b;
  transition: color 0.3s ease;
}

.nav-item:hover .el-icon,
.nav-item.active .el-icon {
  color: #6366f1;
}

.nav-sub-item.active:hover {
  background: rgba(99, 102, 241, 0.2);
}

.nav-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-quick {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stat-quick .stat-label {
  font-size: 13px;
  color: #64748b;
}

.stat-quick .stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

/* 主要内容区域样式 */
.main-content {
  flex: 1;
  min-width: 0;
  /* Shift content to the right of fixed navigation (280px width + 20px gap) */
  margin-left: 300px;
  width: calc(100% - 300px);
  /* Add small top padding to create 8px gap below fixed navbar */
  padding-top: 8px;
  max-width: none;
}

.page-header {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
  padding: 32px;
  color: white;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: right;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.info-label {
  font-weight: 500;
  opacity: 0.9;
}

.info-value {
  font-weight: 600;
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 8px;
  border-radius: 4px;
}

/* 基础信息和统计概览区域 */
.info-stats-section {
  margin-bottom: 40px;
}

.info-stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.info-card,
.stats-card {
  background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.info-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #4361ee, #7209b7, #f72585);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.info-card:hover::before {
  opacity: 1;
}

.info-card:hover,
.stats-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.info-content {
  padding: 20px;
}

.stats-content {
  padding: 24px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  position: relative;
  transition: all 0.3s ease;
  border-radius: 8px;
}

.info-item:hover {
  background: rgba(67, 97, 238, 0.02);
  padding-left: 8px;
  padding-right: 8px;
}

.info-item.keywords-item {
  flex-direction: row;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}

.info-icon {
  font-size: 18px;
  min-width: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.info-item:hover .info-icon {
  transform: scale(1.1) rotate(5deg);
}

.info-label {
  font-weight: 600;
  color: #606266;
  min-width: 80px;
  flex-shrink: 0;
  font-size: 14px;
}

.info-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(to right, #e4e7ed, transparent);
  margin: 0 8px;
}

.info-value {
  color: #303133;
  font-weight: 500;
  font-size: 14px;
  max-width: 60%;
  text-align: right;
}

.info-separator {
  height: 1px;
  background: linear-gradient(to right, transparent, #e4e7ed, transparent);
  margin: 8px 0;
  opacity: 0.6;
}

.keywords-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-width: 60%;
  justify-content: flex-end;
}

.title-emoji {
  font-size: 20px;
  margin-right: 8px;
}

.keyword-tag {
  margin: 0;
  background: linear-gradient(135deg, #f0f4ff, #e8f2ff);
  border: 1px solid #d4e6ff;
  color: #4361ee;
  font-weight: 500;
  border-radius: 16px;
  padding: 4px 12px;
  font-size: 12px;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(67, 97, 238, 0.1);
}

.keyword-tag:hover {
  background: linear-gradient(135deg, #e8f2ff, #dae8ff);
  border-color: #b3d4ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(67, 97, 238, 0.15);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stats-grid-rows {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-item-new {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-height: 80px;
}

.stat-item-new:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border-color: rgba(67, 97, 238, 0.2);
}

.stat-icon-new {
  font-size: 20px;
  flex-shrink: 0;
}

.stat-label-new {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
  flex-shrink: 0;
}

.stat-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, #e2e8f0 50%, transparent 100%);
  margin: 0 8px;
}

.stat-value-new {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  flex-shrink: 0;
}

.stat-item:hover {
  background: rgba(64, 158, 255, 0.1);
  transform: translateY(-2px);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.words-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.equations-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.paragraphs-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.images-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.tables-icon {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.references-icon {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
}

.equations-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.overview-section {
  margin-bottom: 32px;
}

.shadow-card {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.shadow-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.overview-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.card-icon.words {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.card-icon.chapters {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.card-icon.images {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.card-icon.tables {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.card-icon.equations {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.card-icon.references {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #333;
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 32px;
  font-weight: 800;
  color: #303133;
  line-height: 1;
  margin-bottom: 6px;
}

.card-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

/* 新的分析板块样式 */
.charts-section {
  margin-bottom: 32px; /* 恢复原来的间距，因为现在通过折线图卡片控制间距 */
}

.analysis-block {
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); /* 中性浅灰蓝背景，去除浅红 */
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05); /* 调整阴影为中性灰 */
  border: 1px solid rgba(0, 0, 0, 0.05); /* 调整边框为中性灰 */
  margin-bottom: 48px; /* 增大板块之间的间距 */
  overflow: hidden;
  transition: all 0.3s ease;
}

.analysis-block:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

/* 基础信息、概览、折线图顶栏样式 - 偏白一些 */
.info-card .card-header,
.stats-card .card-header,
.chart-card .card-header {
  background: linear-gradient(135deg, #f0f9ff 0%, #f8fafc 100%);
  padding: 24px 32px;
  color: #374151;
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid #e2e8f0;
}

.info-card .card-header::before,
.stats-card .card-header::before,
.chart-card .card-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  opacity: 0.3;
}

.info-card .card-header .card-title,
.stats-card .card-header .card-title,
.chart-card .card-header .card-title {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 8px;
}

/* 文献分析板块顶栏样式 - 偏白一些 */
.analysis-block:nth-of-type(2) .block-header {
  background: linear-gradient(135deg, #f0f9ff 0%, #f3e8ff 100%);
  color: #374151;
  padding: 24px 32px;
  position: relative;
  overflow: hidden;
}

.analysis-block:nth-of-type(2) .block-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  opacity: 0.3;
}

/* 评价分析板块顶栏样式 - 基础样式 */
.analysis-block:nth-of-type(3) .block-header {
  background: linear-gradient(135deg, #e0f2fe 0%, #f3e8ff 100%);
  color: #374151;
  padding: 24px 32px;
  position: relative;
  overflow: hidden;
}

.analysis-block:nth-of-type(3) .block-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  opacity: 0.3;
}

/* 默认板块顶栏样式（其他板块） */
.block-header {
  background: linear-gradient(135deg, #e0f2fe 0%, #f3e8ff 100%);
  color: #374151;
  padding: 24px 32px;
  position: relative;
  overflow: hidden;
}

.block-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  opacity: 0.3;
}

.block-title {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: #374151;
}

.block-subtitle {
  position: relative;
  z-index: 1;
  font-size: 0.95rem;
  opacity: 0.9;
  font-weight: 400;
  color: #374151;
}

.block-content {
  padding: 32px;
}

/* 问题分析区域特殊样式 */
.issues-block-content {
  padding: 16px 32px 32px 32px; /* 进一步减少顶部padding */
}

/* 图表网格布局 */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s ease;
}

.chart-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.chart-card.full-width {
  grid-column: 1 / -1;
  margin-bottom: 64px; /* 进一步增大折线图与下方板块之间的间距 */
}

.card-header {
  background: linear-gradient(135deg, #e0f2fe 0%, #f3e8ff 100%);
  padding: 24px 32px;
  color: #374151;
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid #e2e8f0;
}

.card-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  opacity: 0.3;
}

.card-title {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 6px;
  color: #374151;
}

.chart-container {
  padding: 24px;
  height: 400px;
}

.chart-container.large {
  height: 500px;
  padding: 24px 24px 16px; /* 减小底部内边距，使图表靠近卡片底部 */
}

.chart {
  width: 100%;
  height: 100%;
}

/* 评价分析布局 */
.evaluation-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

/* 新的评价分析布局 */
.evaluation-new-layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 维度导航栏 - 完全平面设计，无立体效果 */
.dimension-nav-bar {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 0;
  /* 完全移除阴影效果 */
  box-shadow: none;
  display: flex;
  gap: 0;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  /* 确保导航栏左右靠边 */
  margin: 0 -32px;
  border-radius: 0;
}

.dimension-nav-bar::-webkit-scrollbar {
  display: none;
}

.dimension-nav-bar .nav-item {
  flex: 1;
  min-width: 120px; /* 进一步缩小到120px */
  padding: 14px 16px; /* 进一步缩小内边距 */
  text-align: center;
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  border-bottom: 3px solid transparent;
  /* 完全平面设计，无任何立体效果 */
  box-shadow: none !important;
  transform: none !important;
  border-left: none;
  border-top: none;
  border-right: none;
  border-radius: 0;
}

.dimension-nav-bar .nav-item:first-child {
  padding-left: 20px; /* 进一步缩小到20px */
}

.dimension-nav-bar .nav-item:last-child {
  padding-right: 20px; /* 进一步缩小到20px */
}

.dimension-nav-bar .nav-item:hover {
  background: #f8fafc;
  border-bottom-color: #cbd5e1;
  /* 完全平滑过渡，绝对无立体效果 */
  transform: none !important;
  box-shadow: none !important;
}

.dimension-nav-bar .nav-item.active {
  /* 使用与顶栏相同的渐变背景色，完全平面 */
  background: linear-gradient(135deg, #f0f9ff 0%, #ede9fe 100%);
  color: #4f46e5;
  border-bottom-color: #6366f1;
  /* 边界明显，完全平面 */
  border-bottom-width: 3px;
  border-bottom-style: solid;
  /* 确保完全无立体效果 */
  box-shadow: none !important;
  transform: none !important;
  border-left: none;
  border-top: none;
  border-right: 1px solid #e2e8f0;
}

.dimension-nav-bar .nav-item.active:hover {
  /* 选中状态悬停时使用稍深的渐变，保持平面 */
  background: linear-gradient(135deg, #e0f2fe 0%, #e4e7ff 100%);
  transform: none !important;
  box-shadow: none !important;
}

.dimension-nav-bar .nav-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px; /* 从4px缩小到3px */
}

.dimension-nav-bar .nav-name {
  font-size: 1.1rem; /* 增大字体到1.1rem */
  font-weight: 500;
  color: #1e293b;
  white-space: nowrap;
  transition: color 0.3s ease;
}

.dimension-nav-bar .nav-item.active .nav-name {
  color: #4f46e5;
  font-weight: 600;
}

.dimension-nav-bar .nav-weight {
  font-size: 0.9rem; /* 增大权重字体到0.9rem */
  color: #64748b;
  white-space: nowrap;
  transition: color 0.3s ease;
}

.dimension-nav-bar .nav-item.active .nav-weight {
  color: #6366f1;
}

/* 完全平面的边界分隔线 */
.dimension-nav-bar .nav-item:not(:last-child) {
  border-right: 1px solid #e2e8f0;
}

/* 移除所有伪元素立体效果 */
.dimension-nav-bar .nav-content {
  position: relative;
}

.nav-score {
  font-size: 12px;
  opacity: 0.8;
}

/* 维度详细内容 */
.dimension-detail-content {
  background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
  border-radius: 16px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04);
  padding: 32px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  position: relative;
  overflow: visible;
}

.dimension-detail-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 20%, rgba(139, 92, 246, 0.02) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(6, 182, 212, 0.02) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.dimension-detail-content > * {
  position: relative;
  z-index: 1;
}

/* 维度标题部分 */
.dimension-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.dimension-icon {
  font-size: 32px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}

/* 增强的得分显示 */
.score-display-enhanced {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

/* 关联图横向展示 */
.relation-section-full {
  margin-top: 24px;
}

.relation-chart-horizontal {
  height: 500px !important;
  min-width: 100%;
  background: linear-gradient(135deg, #fefefe 0%, #f8fafc 50%, #f1f5f9 100%);
  border-radius: 16px;
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(226, 232, 240, 0.6);
  position: relative;
  overflow: hidden;
}

.relation-chart-horizontal::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 20%, rgba(139, 92, 246, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(6, 182, 212, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 40% 60%, rgba(245, 158, 11, 0.02) 0%, transparent 50%);
  pointer-events: none;
}

/* 雷达图增强显示 */
.radar-section-enhanced {
  margin-top: 24px;
}

.radar-enhanced {
  height: 520px !important;
  background: linear-gradient(135deg, #fafbfc 0%, #f1f5f9 100%);
  border-radius: 12px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.04);
  padding: 20px;
  position: relative;
  overflow: visible;
}

.radar-section {
  display: flex;
  flex-direction: column;
}

.dimension-details-section {
  display: flex;
  flex-direction: column;
}

.dimension-nav {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.nav-header {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.nav-tabs {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-tab {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  transform: translateX(0);
}

.nav-tab:hover {
  background: #e3f2fd;
  transform: translateX(2px);
}

.nav-tab.active {
  background: #2196f3;
  color: white;
  border-color: #1976d2;
  transform: translateX(2px);
}

.tab-name {
  font-weight: 500;
}

.tab-score {
  font-size: 12px;
  opacity: 0.8;
}

.dimension-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.content-header h3 {
  margin: 0;
  background: linear-gradient(135deg, #374151 0%, #6b7280 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 24px;
  font-weight: 600;
  position: relative;
}

.content-header h3::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 0;
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #8b5cf6 0%, #06b6d4 100%);
  border-radius: 2px;
  animation: underlineGrow 1s ease-out;
}

@keyframes underlineGrow {
  0% { width: 0; }
  100% { width: 60px; }
}

/* 简化的得分显示 */
.score-display-simple {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.score-main {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
}

.score-number {
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.score-divider {
  font-size: 24px;
  color: #94a3b8;
  font-weight: 400;
}

.score-total {
  font-size: 20px;
  color: #64748b;
  font-weight: 500;
}

.score-percentage {
  font-size: 14px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 90%以上 - 绿色 */
.percentage-excellent {
  color: #059669;
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border: 1px solid #6ee7b7;
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.2);
}

/* 80%-90% - 蓝色 */
.percentage-good {
  color: #1e40af;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border: 1px solid #93c5fd;
  box-shadow: 0 2px 8px rgba(30, 64, 175, 0.2);
}

/* 80%以下 - 黄色 */
.percentage-warning {
  color: #d97706;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #fbbf24;
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.2);
}

.content-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 增强的评论部分 */
.comment-section-enhanced {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid rgba(33, 150, 243, 0.2);
  box-shadow: 0 4px 16px rgba(33, 150, 243, 0.08);
  position: relative;
  overflow: hidden;
}

.comment-section-enhanced::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #2196f3 0%, #03a9f4 100%);
  border-radius: 0 2px 2px 0;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.comment-icon {
  font-size: 20px;
}

.comment-header h4 {
  margin: 0;
  color: #1976d2;
  font-size: 16px;
  font-weight: 600;
}

.comment-content {
  position: relative;
  z-index: 1;
}

.comment-content p {
  margin: 0;
  color: #37474f;
  line-height: 1.8;
  font-size: 15px;
  position: relative;
  padding: 16px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  border-left: 3px solid #2196f3;
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.1);
}

.comment-content p::before {
  content: '"';
  position: absolute;
  top: -5px;
  left: 8px;
  font-size: 24px;
  color: #2196f3;
  font-weight: bold;
  opacity: 0.6;
}

.comment-content p::after {
  content: '"';
  position: absolute;
  bottom: -5px;
  right: 8px;
  font-size: 24px;
  color: #2196f3;
  font-weight: bold;
  opacity: 0.6;
}

/* 增强的详细内容网格 */
.details-grid-enhanced {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 24px;
}

.detail-item-enhanced {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: visible;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.detail-item-enhanced:hover {
  transform: translateY(-2px);
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.detail-item-enhanced.advantages {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-left: 4px solid #10b981;
}

.detail-item-enhanced.advantages::before {
  /* 取消伪元素内容及背景 */
  content: none !important;
  background: none !important;
}

.detail-item-enhanced.weaknesses {
  background: linear-gradient(135deg, #fef2f2 0%, #fef7f7 100%);
  border-left: 4px solid #ef4444;
}

.detail-item-enhanced.weaknesses::before {
  /* 取消伪元素内容及背景 */
  content: none !important;
  background: none !important;
}

.detail-item-enhanced.suggestions {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-left: 4px solid #f59e0b;
}

.detail-item-enhanced.suggestions::before {
  /* 取消伪元素内容及背景 */
  content: none !important;
  background: none !important;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  position: relative;
  z-index: 2;
}

.detail-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.detail-emoji {
  font-size: 20px;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.detail-count {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  min-width: 24px;
  text-align: center;
}

.detail-content {
  position: relative;
  z-index: 2;
}

/* 优势项目样式 */
.advantage-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(16, 185, 129, 0.1);
  transition: all 0.3s ease;
}

.advantage-item:last-child {
  border-bottom: none;
}

.advantage-item:hover {
  background: rgba(16, 185, 129, 0.05);
  border-radius: 8px;
  padding: 12px;
  margin: 0 -12px;
}

/* 不足项目样式 */
.weakness-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(239, 68, 68, 0.1);
  transition: all 0.3s ease;
}

.weakness-item:last-child {
  border-bottom: none;
}

.weakness-item:hover {
  background: rgba(239, 68, 68, 0.05);
  border-radius: 8px;
  padding: 12px;
  margin: 0 -12px;
}

/* 建议项目样式 */
.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(245, 158, 11, 0.1);
  transition: all 0.3s ease;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background: rgba(245, 158, 11, 0.05);
  border-radius: 8px;
  padding: 12px;
  margin: 0 -12px;
}

/* 项目图标和文本 */
.item-icon {
  font-size: 16px;
  margin-top: 2px;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}

/* 悬停时放大效果 */
.advantage-item:hover .item-icon,
.weakness-item:hover .item-icon,
.suggestion-item:hover .item-icon {
  transform: scale(1.2);
}

/* 加载动画 */
@keyframes shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}

.dimension-detail-content.loading {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200px 100%;
  animation: shimmer 1.5s infinite;
}

/* 成功状态动画 */
@keyframes checkmark {
  0% { transform: scale(0) rotate(45deg); }
  50% { transform: scale(1.2) rotate(45deg); }
  100% { transform: scale(1) rotate(45deg); }
}

.detail-count.success {
  animation: checkmark 0.6s ease-in-out;
}

.item-text {
  flex: 1;
  line-height: 1.6;
  color: #374151;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .details-grid-enhanced {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .dimension-detail-content {
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .dimension-title-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .dimension-icon {
    font-size: 24px;
  }

  .score-display-enhanced {
    align-items: flex-start;
  }

  .detail-item-enhanced {
    padding: 20px;
  }

  .comment-section-enhanced {
    padding: 20px;
  }
}

/* 问题分析板块增强样式 */
.issues-analysis-block {
  background: #ffffff; /* 改为白色背景 */
  border: 1px solid rgba(239, 68, 68, 0.1);
}

.issues-block-header {
  background: linear-gradient(135deg, #FF9AA2 0%, #FFB6C1 100%); /* 更深的浅红色 */
  color: #ffffff; /* 改为白色文字 */
  position: relative;
  overflow: hidden;
  margin: 0;
  padding: 24px 32px;
}

.issues-analysis-block .block-content {
  padding: 16px 32px 32px 32px;
}

.issues-block-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="warning-pattern" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="1" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23warning-pattern)"/></svg>');
  opacity: 0.3;
}

.issues-block-header .block-title {
  position: relative;
  z-index: 1;
  color: #374151;
}

.title-icon-wrapper {
  width: 28px;
  height: 28px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: #ef4444;
}

.title-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.title-text {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: #374151;
}

.title-badge {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  width: fit-content;
}

/* 问题分析布局 */
.issues-layout {
  display: grid;
  grid-template-columns: 400px 1fr; /* 固定左侧宽度为400px，右侧自适应 */
  gap: 32px;
  align-items: stretch;
  min-height: 600px; /* 设置最小高度 */
}

.issues-stats-section {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 400px; /* 固定宽度 */
  min-width: 400px; /* 最小宽度 */
  max-width: 400px; /* 最大宽度 */
  background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
  border-radius: 16px;
  border: 1px solid rgba(239, 68, 68, 0.1);
}

.issues-details-section {
  display: flex;
  flex-direction: column;
  height: 600px; /* 固定高度 */
  min-height: 600px; /* 最小高度 */
  max-height: 600px; /* 最大高度 */
  min-width: 0; /* 允许收缩 */
  overflow: hidden; /* 防止内容溢出 */
}

/* 严重程度统计栏样式 */
.severity-stats-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.severity-stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
}

.severity-stat-item.total {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.severity-stat-item.高 {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.severity-stat-item.中 {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.severity-stat-item.低 {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.severity-label {
  font-size: 13px;
  font-weight: 600;
}

.severity-count {
  font-size: 16px;
  font-weight: 700;
}

.issues-stats-card, .enhanced-issues-nav {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  height: 100%;
}

.issues-chart-container {
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 统计卡片增强样式 */
.issues-stats-card {
  background: transparent; /* 移除背景，使用父容器的渐变 */
  border: none; /* 移除边框，使用父容器的边框 */
  box-shadow: none; /* 移除阴影，使用父容器的样式 */
  border-radius: 16px;
}

.stats-card-header {
  background: linear-gradient(135deg, #ffdede 0%, #fff9f9 100%) !important; /* 使用更柔和的淡红色样式 */
  border-bottom: 1px solid rgba(239, 68, 68, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-icon-wrapper {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.stats-title-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats-title {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.stats-subtitle {
  font-size: 12px;
  color: #6b7280;
}

.issues-summary-enhanced {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.summary-main {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.summary-number {
  font-size: 28px;
  font-weight: 800;
  color: #ef4444;
}

.summary-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.summary-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.summary-status.status-excellent {
  background: #dcfce7;
  color: #166534;
}

.summary-status.status-good {
  background: #dbeafe;
  color: #1e40af;
}

.summary-status.status-warning {
  background: #fef3c7;
  color: #92400e;
}

.summary-status.status-danger {
  background: #fee2e2;
  color: #dc2626;
}

.issues-chart-container {
  background: linear-gradient(135deg, rgba(254, 242, 242, 0.6) 0%, rgba(255, 255, 255, 0.9) 100%);
  border-radius: 12px;
  padding-top: 10px;
  position: relative;
  overflow: hidden;
}

.issues-chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 25% 30%, rgba(252, 165, 165, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 75% 70%, rgba(239, 68, 68, 0.05) 0%, transparent 50%);
  pointer-events: none;
}

/* 问题详情导航增强样式 */
.enhanced-issues-nav {
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); /* 中性背景 */
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  animation: slideInRight 0.6s ease-out;
  border: 1px solid rgba(0, 0, 0, 0.05);
  height: 100%;
  max-height: 600px; /* 固定最大高度 */
}

.enhanced-nav-header {
  background: #ffffff;
  color: #374151;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.nav-header-content {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.nav-icon {
  width: 44px;
  height: 44px;
  background: #f3f4f6;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.nav-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-main-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.nav-subtitle {
  font-size: 13px;
  color: #6b7280;
  font-weight: 400;
}

/* 增强的标签页样式 */
.enhanced-tabs {
  background: white;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.enhanced-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.enhanced-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: linear-gradient(to right, #f0f9ff, #e8f5ff); /* 中性浅蓝 */
  border-bottom: 1px solid #cfe6ff;
  padding: 8px 8px 0;
  border-radius: 12px 12px 0 0;
  overflow: hidden; /* 防止溢出 */
}

.enhanced-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0 20px;
  overflow: hidden; /* 隐藏溢出内容 */
  position: relative;
}

.enhanced-tabs :deep(.el-tabs__nav-scroll) {
  overflow-x: auto; /* 启用水平滚动 */
  overflow-y: hidden;
  scrollbar-width: thin; /* Firefox 滚动条样式 */
  scrollbar-color: rgba(239, 68, 68, 0.3) transparent;
}

/* Webkit 浏览器滚动条样式 */
.enhanced-tabs :deep(.el-tabs__nav-scroll)::-webkit-scrollbar {
  height: 6px;
}

.enhanced-tabs :deep(.el-tabs__nav-scroll)::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.enhanced-tabs :deep(.el-tabs__nav-scroll)::-webkit-scrollbar-thumb {
  background: rgba(239, 68, 68, 0.3);
  border-radius: 3px;
  transition: background 0.3s ease;
}

.enhanced-tabs :deep(.el-tabs__nav-scroll)::-webkit-scrollbar-thumb:hover {
  background: rgba(239, 68, 68, 0.5);
}

.enhanced-tabs :deep(.el-tabs__nav) {
  white-space: nowrap; /* 防止标签页换行 */
  min-width: max-content; /* 确保有足够宽度显示所有标签 */
}

.enhanced-tabs :deep(.el-tabs__item) {
  color: #64748b;
  font-weight: 500;
  transition: all 0.3s ease;
  border-radius: 8px 8px 0 0;
  margin-right: 4px;
  font-size: 15px;
  padding: 0 20px;
  height: 42px;
  line-height: 42px;
  white-space: nowrap; /* 防止文字换行 */
  flex-shrink: 0; /* 防止标签页被压缩 */
  min-width: max-content; /* 确保标签页有足够宽度 */
}

.enhanced-tabs :deep(.el-tabs__item:hover) {
  color: #1e40af;
  background-color: rgba(219, 234, 254, 0.6);
}

.enhanced-tabs :deep(.el-tabs__item.is-active) {
  color: #1e40af;
  font-weight: 600;
  background-color: #fff;
  box-shadow: 0 0 10px rgba(30, 64, 175, 0.1);
}

.enhanced-tabs :deep(.el-tabs__active-bar) {
  background: #1e40af;
  height: 3px;
}

/* 问题列表增强样式 */
.enhanced-issues-list {
  padding: 16px;
  height: 480px; /* 固定高度 */
  max-height: 480px; /* 最大高度 */
  overflow-y: auto;
  background: linear-gradient(135deg, #ffffff 0%, #fefefe 100%);
}

.issues-count-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 8px;
  margin-bottom: 16px;
  color: #1e40af;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.enhanced-issue-item {
  background: linear-gradient(135deg, #ffffff 0%, #fefefe 100%);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.6s ease-out;
  animation-fill-mode: both;
  position: relative;
  overflow: hidden;
}

.enhanced-issue-item:last-child {
  margin-bottom: 0;
}

.enhanced-issue-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  transition: all 0.3s ease;
  border-radius: 0 2px 2px 0;
}

.enhanced-issue-item:hover {
  background: linear-gradient(135deg, #fefefe 0%, #f9fafb 100%);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  border-color: rgba(239, 68, 68, 0.2);
}

.enhanced-issue-item:hover::before {
  width: 6px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.enhanced-issue-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.issue-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.issue-type-wrapper {
  display: flex;
  align-items: center;
}

.issue-type-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tag-icon {
  font-size: 14px;
}

.issue-location {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 6px;
  width: fit-content;
}

.issue-severity {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.severity-low {
  background: #dcfce7;
  color: #166534;
}

.severity-medium {
  background: #fef3c7;
  color: #92400e;
}

.severity-high {
  background: #fee2e2;
  color: #dc2626;
}

/* 问题内容增强样式 */
.enhanced-issue-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.issue-section {
  background: #fafbfc;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.issue-section:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  font-size: 14px;
}

.section-title {
  color: #374151;
}

.section-content {
  line-height: 1.6;
  font-size: 14px;
}

.original-text-section .section-header {
  color: #6b7280;
}

.original-text {
  color: #4b5563;
  font-weight: 500;
}

.problem-section .section-header {
  color: #ef4444;
}

.problem-text {
  color: #dc2626;
  font-weight: 500;
}

.suggestion-section .section-header {
  color: #059669;
}

.suggestion-text {
  color: #047857;
  font-weight: 500;
}

/* 无数据状态增强样式 */
.enhanced-no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-radius: 16px;
  margin: 20px;
}

.no-data-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: white;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
}

.no-data-text {
  text-align: center;
}

.no-data-text h3 {
  margin: 0 0 8px 0;
  color: #065f46;
  font-size: 20px;
  font-weight: 700;
}

.no-data-text p {
  margin: 0;
  color: #047857;
  font-size: 14px;
  opacity: 0.8;
}

/* 动画关键帧 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 图表卡片动画 */
.chart-card {
  animation: scaleIn 0.5s ease-out;
  animation-fill-mode: both;
}

.charts-grid .chart-card:nth-child(1) { animation-delay: 0.1s; }
.charts-grid .chart-card:nth-child(2) { animation-delay: 0.2s; }
.charts-grid .chart-card:nth-child(3) { animation-delay: 0.3s; }

/* 评价维度导航动画 */
.nav-tab {
  animation: slideInLeft 0.4s ease-out;
  animation-fill-mode: both;
}

.nav-tabs .nav-tab:nth-child(1) { animation-delay: 0.1s; }
.nav-tabs .nav-tab:nth-child(2) { animation-delay: 0.2s; }
.nav-tabs .nav-tab:nth-child(3) { animation-delay: 0.3s; }
.nav-tabs .nav-tab:nth-child(4) { animation-delay: 0.4s; }
.nav-tabs .nav-tab:nth-child(5) { animation-delay: 0.5s; }

/* 维度内容动画 */
.dimension-content {
  animation: fadeInUp 0.6s ease-out;
}

.details-grid .detail-item {
  animation: scaleIn 0.5s ease-out;
  animation-fill-mode: both;
}

.details-grid .detail-item:nth-child(1) { animation-delay: 0.1s; }
.details-grid .detail-item:nth-child(2) { animation-delay: 0.2s; }
.details-grid .detail-item:nth-child(3) { animation-delay: 0.3s; }

.issues-summary {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.dimension-item {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.dimension-item:last-child {
  margin-bottom: 0;
  border-bottom: none;
  padding-bottom: 0;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dimension-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.dimension-score {
  flex-shrink: 0;
}

.dimension-comment {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.dimension-details {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.detail-section h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.detail-section ul {
  margin: 0;
  padding-left: 16px;
}

.detail-section li {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  margin-bottom: 6px;
}

.detail-section li:last-child {
  margin-bottom: 0;
}

.issues-tabs {
  margin-top: 16px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .analysis-layout {
    padding: 16px;
  }

  .info-stats-row {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .charts-row {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .evaluation-cards {
    grid-template-columns: 1fr;
  }
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .evaluation-layout {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .dimension-nav-bar {
    flex-wrap: wrap;
    gap: 12px;
  }

  .nav-item {
    min-width: 100px;
    padding: 12px 16px;
  }

  .issues-layout {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .details-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-title h1 {
    font-size: 24px;
  }

  .info-stats-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .stat-item {
    padding: 12px;
  }

  .stat-value {
    font-size: 20px;
  }

  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .overview-card {
    padding: 20px;
  }

  .card-value {
    font-size: 28px;
  }

  .chart-container {
    height: 300px;
    padding: 16px;
  }

  .card-header {
    padding: 16px 20px;
  }

  .block-header {
    padding: 20px 24px;
  }

  .block-title {
    font-size: 18px;
  }

  .block-content {
    padding: 24px;
  }

  .charts-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .evaluation-layout {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .dimension-nav-bar {
    flex-direction: column;
    gap: 8px;
  }

  .nav-item {
    min-width: auto;
    padding: 12px 16px;
  }

  .dimension-detail-content {
    padding: 20px;
  }

  .issues-layout {
    grid-template-columns: 1fr;
    gap: 20px;
    min-height: auto; /* 移动端不设置最小高度 */
  }

  .issues-details-section {
    height: auto; /* 移动端自适应高度 */
    min-height: auto;
    max-height: none;
  }

  .enhanced-issues-list {
    height: auto; /* 移动端自适应高度 */
    max-height: 400px;
  }

  .details-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .dimension-nav {
    padding: 16px;
  }

  .nav-tabs {
    gap: 6px;
  }

  .nav-tab {
    padding: 10px 12px;
  }

  .dimension-content {
    padding: 20px;
  }

  .issues-list {
    padding: 16px;
    max-height: 400px;
  }

  .issue-item {
    padding: 12px;
    margin-bottom: 10px;
  }
}

@media (max-width: 480px) {
  .analysis-layout {
    padding: 12px;
  }

  .page-header {
    padding: 24px;
    margin-bottom: 20px;
  }

  .header-title h1 {
    font-size: 20px;
  }

  .info-stats-row {
    gap: 12px;
  }

  .info-content,
  .stats-content {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .stat-item {
    padding: 12px;
  }

  .stat-icon {
    width: 32px;
    height: 32px;
    font-size: 16px;
  }

  .stat-value {
    font-size: 18px;
  }

  .overview-cards {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .overview-card {
    padding: 16px;
    gap: 12px;
  }

  .card-icon {
    width: 48px;
    height: 48px;
    font-size: 24px;
  }

  .card-value {
    font-size: 24px;
  }

  .charts-row {
    gap: 16px;
    margin-bottom: 16px;
  }

  .chart-container {
    height: 250px;
    padding: 12px;
  }

  .card-header {
    padding: 12px 16px;
  }

  .card-title {
    font-size: 14px;
  }

  .evaluation-content,
  .issues-content {
    padding: 16px;
  }

  .dimension-item {
    margin-bottom: 24px;
    padding-bottom: 20px;
  }

  .dimension-name {
    font-size: 16px;
  }

  .issue-item {
    padding: 12px;
    margin-bottom: 16px;
  }
}

.relation-chart {
  height: 750px !important;
  min-width: 500px;
  background-color: #f8f9fa;
  border-radius: 12px;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.05);
}

@media (max-width: 1200px) {
  .relation-chart-horizontal {
    height: 450px !important;
  }

  .radar-enhanced {
    height: 480px !important;
  }
}

@media (max-width: 1024px) {
  .analysis-layout {
    flex-direction: column;
  }

  .left-navigation {
    width: 100%;
    min-width: auto;
    position: static;
    max-height: none;
    margin-bottom: 20px;
  }

  .nav-content {
    padding: 15px;
  }

  .nav-section {
    margin-bottom: 16px;
  }

  .nav-items {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 8px;
  }

  .nav-item {
    flex: 1;
    min-width: 120px;
    justify-content: center;
    text-align: center;
  }

  .nav-stats {
    flex-direction: row;
    gap: 8px;
  }

  .stat-quick {
    flex: 1;
    flex-direction: column;
    text-align: center;
    gap: 4px;
  }

  /* Reset main content offset on smaller screens where nav is not fixed on the side */
  .main-content {
    margin-left: 0;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .analysis-layout {
    padding: 10px;
  }

  .left-navigation {
    margin-bottom: 15px;
  }

  .nav-header {
    padding: 15px;
  }

  .nav-content {
    padding: 10px;
  }

  .nav-items {
    flex-direction: column;
  }

  .nav-item {
    min-width: auto;
    justify-content: flex-start;
  }

  .nav-stats {
    flex-direction: column;
  }

  .stat-quick {
    flex-direction: row;
    justify-content: space-between;
  }

  .relation-chart-horizontal {
    height: 400px !important;
  }

  .radar-enhanced {
    height: 420px !important;
    padding: 15px;
  }

  .score-display-simple {
    align-items: center;
  }

  .score-number {
    font-size: 28px;
  }

  .score-total {
    font-size: 18px;
  }
}

/* -----------------------------------------------------------------
   去除关联图与雷达图背景及边缘颜色
-------------------------------------------------------------------*/
.radar-enhanced,
.relation-chart-horizontal,
.chart-container.radar-enhanced,
.chart-container.relation-chart-horizontal {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.relation-chart-horizontal::before {
  content: none !important;
}

/* -----------------------------------------------------------------
   保留原有的内边距和顶栏优化设置
-------------------------------------------------------------------*/
.chart-container.radar-enhanced,
.chart-container.relation-chart-horizontal {
  padding: 0 !important;
}

.radar-section-enhanced .chart-card .card-header,
.relation-section-full .chart-card .card-header {
  padding-bottom: 0 !important;
  border-bottom: none !important;
}

/* -----------------------------------------------------------------
   独立卡片样式优化
-------------------------------------------------------------------*/
/* 维度雷达图独立卡片 */
#dimension-radar.chart-card {
  margin-bottom: 32px;
}

/* 维度章节关联图独立卡片 */
#dimension-relation.chart-card {
  margin-bottom: 32px;
}

/* 确保独立卡片的图表容器有合适的高度 */
#dimension-radar .chart-container {
  height: 520px !important;
}

#dimension-relation .chart-container {
  height: 500px !important;
}
</style>
