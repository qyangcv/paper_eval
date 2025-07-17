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
# from .evaluation import router as evaluation_router  # 不在API需求中，暂时注释
from .task import router as task_router
from .analysis import router as analysis_router
from .health import router as health_router
from .preview import router as preview_router

# 创建主路由
api_router = APIRouter()

# 注册子路由
# 根据前端API需求调整路由前缀
api_router.include_router(document_router, prefix="", tags=["文档处理"])  # 直接挂载到/api下
# api_router.include_router(evaluation_router, prefix="/evaluation", tags=["论文评估"])  # 不在API需求中
api_router.include_router(task_router, prefix="", tags=["任务管理"])  # 直接挂载到/api下
api_router.include_router(analysis_router, prefix="/analysis", tags=["数据分析"])  # 挂载到/api/analysis下
api_router.include_router(preview_router, prefix="/preview", tags=["文档预览"])  # 挂载到/api/preview下
api_router.include_router(health_router, prefix="", tags=["健康检查"])  # 直接挂载到/api下

__all__ = ['api_router']
