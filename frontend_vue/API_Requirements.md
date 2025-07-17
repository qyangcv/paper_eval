# 北邮本科论文质量评价分析系统 - API需求配置

## API接口详细规范

### 1. 健康检查接口

**接口**: `GET /health`
**描述**: 检查服务器状态
**响应**:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. 文档上传接口

**接口**: `POST /api/upload`
**描述**: 上传Word文档进行分析
**请求头**: `Content-Type: multipart/form-data`
**请求体**:
```
file: [Word文档文件] (.docx格式，最大10MB)
```
**响应**:
```json
{
  "task_id": "uuid-string",
  "filename": "document.docx",
  "file_size": 1024000,
  "upload_time": "2024-01-01T00:00:00Z",
  "status": "uploaded"
}
```

### 3. 开始处理接口

**接口**: `POST /api/process`
**描述**: 开始分析已上传的文档
**请求体**:
```json
{
  "task_id": "uuid-string",
  "model_config": {
    "model_name": "deepseek|qwen|gemini|gpt|none",
    "api_key": "api-key-string"
  }
}
```
**响应**:
```json
{
  "task_id": "uuid-string",
  "status": "processing",
  "message": "开始处理文档"
}
```

### 4. 状态查询接口

**接口**: `GET /api/status/{task_id}`
**描述**: 查询文档处理状态
**响应**:
```json
{
  "task_id": "uuid-string",
  "status": "pending|processing|completed|error",
  "progress": 0.75,
  "message": "正在分析章节结构...",
  "error": "错误信息（仅在status为error时）",
  "result": "处理结果（仅在status为completed时）"
}
```

### 5. 任务删除接口

**接口**: `DELETE /api/task/{task_id}`
**描述**: 删除指定任务及其相关数据
**响应**:
```json
{
  "message": "任务已删除",
  "task_id": "uuid-string"
}
```

## 数据分析专用API接口

### 6. 基础信息接口

**接口**: `GET /api/analysis/{task_id}/basic-info`
**描述**: 获取论文基础信息
**响应**:
```json
{
  "title": "论文标题",
  "author": "作者姓名",
  "school": "学院名称",
  "advisor": "指导教师",
  "keywords": ["关键词1", "关键词2", "关键词3"]
}
```

### 7. 统计概览接口

**接口**: `GET /api/analysis/{task_id}/overall-stats`
**描述**: 获取整体统计数据
**响应**:
```json
{
  "total_words": 16840,
  "total_equations": 35,
  "total_paragraphs": 108,
  "total_images": 16,
  "total_tables": 9
}
```

### 8. 章节统计接口

**接口**: `GET /api/analysis/{task_id}/chapter-stats`
**描述**: 获取章节详细统计（用于折线图）
**响应**:
```json
{
  "chapters": ["中文摘要", "英文摘要", "第一章_绪论"],
  "word_counts": [380, 1550, 2600],
  "equation_counts": [0, 0, 3],
  "table_counts": [0, 0, 1],
  "image_counts": [0, 1, 2],
  "paragraph_counts": [5, 10, 20]
}
```

### 9. 参考文献分析接口

**接口**: `GET /api/analysis/{task_id}/reference-stats`
**描述**: 获取参考文献统计（用于饼图）
**响应**:
```json
{
  "total_references": 50,
  "by_indicator": {
    "期刊论文[J]": 35,
    "会议论文[C]": 5,
    "学位论文[D]": 3,
    "技术报告[R]": 2,
    "其他": 5
  },
  "by_lang": {
    "中文文献": 20,
    "英文文献": 30
  },
  "recent_3y": 5
}
```

### 10. 评价维度接口

**接口**: `GET /api/analysis/{task_id}/evaluation`
**描述**: 获取评价维度数据（用于雷达图和详细评价）
**响应**:
```json
{
  "overall_score": 4.32,
  "dimensions": [
    {
      "name": "选题创新性",
      "score": 4.6,
      "full_score": 5,
      "weight": 1.0,
      "focus_chapter": ["1.2_国内外研究现状", "1.3_研究内容与创新点"],
      "comment": "评价总结",
      "advantages": ["优势1", "优势2"],
      "weaknesses": ["不足1", "不足2"],
      "suggestions": ["建议1", "建议2"]
    }
  ]
}
```

### 11. 问题分析接口

**接口**: `GET /api/analysis/{task_id}/issues`
**描述**: 获取问题分析数据（用于环形图和问题列表）
**响应**:
```json
{
  "summary": {
    "total_issues": 15,
    "issue_types": ["格式错误", "语法问题", "逻辑不清"],
    "severity_distribution": {
      "高": 2,
      "中": 8,
      "低": 5
    }
  },
  "by_chapter": {
    "第一章_绪论": [
      {
        "id": "issue-1",
        "type": "格式错误",
        "severity": "中",
        "sub_chapter": "1.1_研究背景",
        "original_text": "原文内容",
        "detail": "问题描述",
        "suggestion": "改进建议"
      }
    ]
  }
}
```

### 12. 文档预览接口

**接口**: `GET /api/preview/{task_id}/html`
**描述**: 获取文档预览数据
**响应**:
```json
{
  "filename": "document.docx",
  "html_file": "path/to/converted/document.html",
  "toc_items": [
    {
      "text": "第一章 绪论",
      "level": 1
    }
  ]
}
```

### 13. 文档图片接口

**接口**: `GET /api/preview/{task_id}/image`
**描述**: 获取文档中的图片资源
**参数**:
- `path`: 图片路径参数，如 `images/image_1.png`
**响应**: 直接返回图片文件内容


## 错误处理规范

### HTTP状态码
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `413`: 文件过大
- `422`: 文件格式不支持
- `500`: 服务器内部错误

### 错误响应格式
```json
{
  "detail": "错误描述信息",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```
