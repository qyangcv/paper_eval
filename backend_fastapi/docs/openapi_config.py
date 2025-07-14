"""
OpenAPI配置模块
自定义FastAPI的OpenAPI文档配置
"""

from typing import Dict, Any
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def get_openapi_config() -> Dict[str, Any]:
    """
    获取OpenAPI配置
    
    Returns:
        Dict[str, Any]: OpenAPI配置字典
    """
    return {
        "title": "论文评价分析系统API",
        "version": "1.0.0",
        "description": """
# 北邮本科论文质量评价分析系统API

这是一个基于FastAPI构建的论文质量评价分析系统后端API。

## 主要功能

### 📄 文档处理
- 文档上传和格式验证
- Word文档转换和预处理
- 文档结构分析和目录提取

### 🤖 AI评估
- 支持多种大语言模型（DeepSeek、Gemini、Qwen）
- 章节级别的质量评估
- 整体论文质量分析和打分

### 📊 数据分析
- 评估结果可视化
- 雷达图和柱状图数据生成
- 统计信息和报告导出

### ⚙️ 任务管理
- 异步任务状态跟踪
- 进度监控和结果获取
- 任务历史管理

## 使用流程

1. **上传文档**: 使用 `/api/document/upload` 上传Word文档
2. **处理文档**: 调用 `/api/document/process/{document_id}` 处理文档
3. **开始评估**: 使用 `/api/evaluation/start` 启动评估任务
4. **监控进度**: 通过 `/api/task/{task_id}` 查看任务状态
5. **获取结果**: 使用 `/api/evaluation/result/{task_id}` 获取评估结果
6. **数据分析**: 通过 `/api/analysis/` 相关接口获取可视化数据

## 认证

当前版本不需要认证，但建议在生产环境中添加适当的认证机制。

## 错误处理

所有API响应都遵循统一的格式：
```json
{
    "success": true/false,
    "message": "描述信息",
    "data": {...},  // 成功时的数据
    "error": "...", // 失败时的错误信息
    "error_type": "ErrorType"  // 错误类型
}
```

## 限制

- 文档大小限制：50MB
- 支持格式：.docx, .doc
- 并发任务限制：10个
- 任务超时时间：30分钟

## 联系信息

- 开发团队：北邮论文评价系统开发组
- 版本：v1.0.0
        """,
        "contact": {
            "name": "北邮论文评价系统开发组",
            "email": "support@paper-eval.com"
        },
        "license_info": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "开发环境"
            },
            {
                "url": "https://api.paper-eval.com",
                "description": "生产环境"
            }
        ]
    }

def customize_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    自定义OpenAPI文档
    
    Args:
        app: FastAPI应用实例
        
    Returns:
        Dict[str, Any]: 自定义的OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    config = get_openapi_config()
    
    openapi_schema = get_openapi(
        title=config["title"],
        version=config["version"],
        description=config["description"],
        routes=app.routes,
        servers=config["servers"]
    )
    
    # 添加自定义信息
    openapi_schema["info"]["contact"] = config["contact"]
    openapi_schema["info"]["license"] = config["license_info"]
    
    # 添加标签描述
    openapi_schema["tags"] = [
        {
            "name": "文档处理",
            "description": "文档上传、转换和预处理相关接口"
        },
        {
            "name": "论文评估",
            "description": "AI模型论文质量评估相关接口"
        },
        {
            "name": "任务管理",
            "description": "异步任务状态管理相关接口"
        },
        {
            "name": "数据分析",
            "description": "评估结果分析和可视化相关接口"
        },
        {
            "name": "健康检查",
            "description": "系统健康状态检查相关接口"
        }
    ]
    
    # 添加通用响应模型
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "error": {"type": "string", "example": "错误信息"},
            "detail": {"type": "string", "example": "详细错误描述"},
            "error_type": {"type": "string", "example": "ErrorType"}
        },
        "required": ["success", "error"]
    }
    
    openapi_schema["components"]["schemas"]["SuccessResponse"] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "message": {"type": "string", "example": "操作成功"},
            "data": {"type": "object", "example": {}}
        },
        "required": ["success", "message"]
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
