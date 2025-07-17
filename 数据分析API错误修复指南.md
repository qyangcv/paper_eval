# 数据分析API错误修复指南

## 问题概述

当前数据分析页面的以下数据显示错误：
1. **论文基础信息** - 标题、作者、学院、导师、关键词
2. **整体统计概览** - 总字数、总公式数、总段落数、总图片数、总表格数
3. **章节内容统计折线图** - 各章节的字数、公式数、表格数、图片数、段落数
4. **文献分析** - 参考文献类型分布、语言分布、时效性分析

## 数据流程分析

### 前端数据获取流程

1. **前端组件**: `frontend_vue/src/views/DataAnalysis.vue`
2. **API服务**: `frontend_vue/src/services/api.js`
3. **数据加载函数**: `loadAllAnalysisData(taskId)`

前端通过以下API接口获取数据：
```javascript
// 并行调用所有分析API
const results = await Promise.allSettled([
    this.getBasicInfo(taskId),        // 基础信息
    this.getOverallStats(taskId),     // 统计概览
    this.getChapterStats(taskId),     // 章节统计
    this.getReferenceStats(taskId),   // 文献分析
    this.getEvaluation(taskId),       // 评价维度
    this.getIssues(taskId)           // 问题分析
])
```

### 后端API路由

所有数据分析API都在 `backend_fastapi/api/analysis.py` 中定义：

- `GET /api/analysis/{task_id}/basic-info` → `get_basic_info()`
- `GET /api/analysis/{task_id}/overall-stats` → `get_overall_stats()`
- `GET /api/analysis/{task_id}/chapter-stats` → `get_chapter_stats()`
- `GET /api/analysis/{task_id}/reference-stats` → `get_ref_stats()`

## 需要修复的具体问题

### 1. 基础信息接口错误

**文件**: `backend_fastapi/api/analysis.py`
**函数**: `get_basic_info()` (第85-129行)

**问题分析**:
- 当前从 `pkl_data` 中提取基础信息
- 但 `pkl_data` 结构中可能缺少这些字段或字段名不匹配

**需要检查的数据源**:
```python
# 当前代码从这里获取数据
pkl_data = document_info.get('pkl_data', {})
title = pkl_data.get('title', '未知标题')
author = pkl_data.get('author', '未知作者')
school = pkl_data.get('school', '未知学院')
advisor = pkl_data.get('advisor', '未知导师')
keywords = pkl_data.get('keywords', [])
```

**修复方向**:
1. 检查 `tools/docx_tools/md2pkl.py` 中的 `extract_basic_info()` 函数
2. 确认基础信息提取逻辑是否正确
3. 验证字段名是否与API期望的一致

### 2. 统计概览接口错误

**文件**: `backend_fastapi/api/analysis.py`
**函数**: `get_overall_stats()` (第132-177行)

**问题分析**:
- 统计计算逻辑可能有误
- 字数统计使用 `len(content.split())` 可能不准确
- 图片、表格、公式统计可能从错误的数据源获取

**当前统计逻辑**:
```python
# 计算统计数据
total_words = sum(len(chapter.get('content', '').split()) for chapter in chapters)
total_paragraphs = sum(len(chapter.get('content', '').split('\n\n')) for chapter in chapters)
total_images = len(document_info.get('images', []))
total_tables = sum(chapter.get('table_count', 0) for chapter in chapters)
total_equations = sum(chapter.get('equation_count', 0) for chapter in chapters)
```

**修复方向**:
1. 检查章节数据结构中是否包含 `table_count` 和 `equation_count` 字段
2. 验证字数统计算法的准确性
3. 确认图片统计是否应该从章节级别聚合

### 3. 章节统计接口错误

**文件**: `backend_fastapi/api/analysis.py`
**函数**: `get_chapter_stats()` (第180-236行)

**问题分析**:
- 章节级别的统计数据可能缺失或计算错误
- 图片统计从 `chapter.get('images', [])` 获取，但可能字段不存在

**当前统计逻辑**:
```python
for chapter in chapters:
    chapter_names.append(chapter.get('chapter_name', '未知章节'))
    content = chapter.get('content', '')
    word_counts.append(len(content.split()))
    equation_counts.append(chapter.get('equation_count', 0))
    table_counts.append(chapter.get('table_count', 0))
    image_counts.append(len(chapter.get('images', [])))
    paragraph_counts.append(len(content.split('\n\n')))
```

**修复方向**:
1. 检查 `pkl_data` 中章节数据的实际结构
2. 验证每个章节是否包含所需的统计字段
3. 确认章节名称提取是否正确

### 4. 文献分析接口错误

**文件**: `backend_fastapi/api/analysis.py`
**函数**: `get_ref_stats()` (第238-319行)

**问题分析**:
- 参考文献数据源可能错误
- 文献类型识别逻辑可能有问题
- 语言识别和年份提取可能不准确

**当前分析逻辑**:
```python
# 获取参考文献
references = document_info.get('references', [])

# 文献类型分析
if '[J]' in ref:
    by_indicator["期刊论文[J]"] += 1
elif '[C]' in ref:
    by_indicator["会议论文[C]"] += 1
# ...

# 语言分析
if any('\u4e00' <= char <= '\u9fff' for char in ref):
    by_lang["中文文献"] += 1
else:
    by_lang["英文文献"] += 1
```

**修复方向**:
1. 检查参考文献提取是否正确存储在 `document_info['references']`
2. 验证文献类型标识符匹配逻辑
3. 改进语言识别算法
4. 优化年份提取的正则表达式

## 数据结构分析

### PKL数据结构

根据代码分析，`pkl_data` 的标准结构应该是：
```python
{
    'zh_abs': str,      # 中文摘要
    'en_abs': str,      # 英文摘要
    'ref': str,         # 参考文献
    'chapters': [       # 章节列表
        {
            'chapter_name': str,    # 章节名称
            'content': str,         # 章节内容
            'images': list,         # 章节图片
            'table_count': int,     # 表格数量（可能缺失）
            'equation_count': int   # 公式数量（可能缺失）
        }
    ],
    # 基础信息字段（可能缺失）
    'title': str,
    'author': str,
    'school': str,
    'advisor': str,
    'keywords': list
}
```

### Redis存储结构

文档数据在Redis中的存储结构：
```python
document_info = {
    'task_id': str,
    'filename': str,
    'content': bytes,           # 原始文档内容
    'status': str,              # 处理状态
    'md_content': str,          # Markdown内容
    'images': list,             # 提取的图片
    'references': list,         # 提取的参考文献
    'pkl_data': dict,           # 结构化数据
    'progress': float,
    'message': str
}
```

## 修复任务清单

### 任务1: 检查基础信息提取
- **文件**: `backend_fastapi/tools/docx_tools/md2pkl.py`
- **函数**: `extract_basic_info()`
- **检查**: 确认是否正确提取标题、作者等信息并添加到pkl_data中

### 任务2: 修复统计计算逻辑
- **文件**: `backend_fastapi/api/analysis.py`
- **函数**: `get_overall_stats()`, `get_chapter_stats()`
- **检查**: 
  - 验证章节数据中是否包含table_count、equation_count字段
  - 改进字数统计算法
  - 确认图片统计数据源

### 任务3: 完善章节数据结构
- **文件**: `backend_fastapi/tools/docx_tools/md2pkl.py`
- **函数**: `extract_chapters()`
- **检查**: 确认章节提取时是否计算并存储表格数、公式数等统计信息

### 任务4: 修复参考文献分析
- **文件**: `backend_fastapi/api/analysis.py`
- **函数**: `get_ref_stats()`
- **检查**:
  - 验证references数据源
  - 改进文献类型识别
  - 优化语言和年份识别算法

### 任务5: 数据一致性检查
- **检查**: 确认文档处理流程中数据的完整性
- **文件**: `backend_fastapi/api/document.py`
- **验证**: 处理过程中是否正确提取和存储所有必要的统计信息

