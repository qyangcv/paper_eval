"""
API路由模块
包含所有的API端点定义

包含以下路由：
- document: 文档处理相关API
- evaluation: 论文评估相关API
- task: 任务管理相关API
- analysis: 数据分析相关API
- health: 健康检查相关API
"""

from fastapi import APIRouter
from .document import router as document_router
from .evaluation import router as evaluation_router
from .task import router as task_router
from .analysis import router as analysis_router
from .health import router as health_router

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(document_router, prefix="/document", tags=["文档处理"])
api_router.include_router(evaluation_router, prefix="/evaluation", tags=["论文评估"])
api_router.include_router(task_router, prefix="/task", tags=["任务管理"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["数据分析"])
api_router.include_router(health_router, prefix="/health", tags=["健康检查"])

__all__ = ['api_router']
