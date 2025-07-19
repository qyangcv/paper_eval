"""
FastAPI后端主应用
重构自原Streamlit应用，提供RESTful API服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

import json
import asyncio
from datetime import datetime
import tempfile
import logging
import logging.config

# 添加项目根目录到Python路径
# backend_fastapi目录的父目录才是真正的项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 初始化彩色日志配置
def _init_colored_logging():
    """初始化彩色日志配置"""
    try:
        from config.log_config import ColoredFormatter

        # 创建彩色格式化器，强制启用颜色
        colored_formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            use_colors=True  # 强制启用颜色
        )

        # 完全重置日志系统
        _reset_logging_system(colored_formatter)

    except ImportError as e:
        print(f"警告：无法导入日志配置: {e}")
        # 如果无法导入配置，使用简单的彩色格式
        _setup_fallback_colored_logging()

def _reset_logging_system(colored_formatter):
    """完全重置日志系统，确保没有重复的处理器"""
    # 获取根日志记录器
    root_logger = logging.getLogger()

    # 清除所有现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 清除所有子日志记录器的处理器
    logger_dict = logging.Logger.manager.loggerDict
    for logger_name, logger_obj in logger_dict.items():
        if isinstance(logger_obj, logging.Logger):
            for handler in logger_obj.handlers[:]:
                logger_obj.removeHandler(handler)
            # 设置为传播到根日志记录器
            logger_obj.propagate = True

    # 为根日志记录器添加唯一的彩色控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(colored_formatter)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)

    # 禁用basicConfig，防止自动创建处理器
    logging.basicConfig = lambda **kwargs: None

def _setup_fallback_colored_logging():
    """设置备用的彩色日志配置"""
    # 简单的彩色格式化器类
    class SimpleColoredFormatter(logging.Formatter):
        COLORS = {
            'DEBUG': '\033[36m',    # 青色
            'INFO': '\033[32m',     # 绿色
            'WARNING': '\033[33m',  # 黄色
            'ERROR': '\033[31m',    # 红色
            'CRITICAL': '\033[35m', # 紫色
            'RESET': '\033[0m',     # 重置
        }

        def format(self, record):
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            record.levelname = f"{color}[{record.levelname}]{reset}"
            return super().format(record)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 添加彩色控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    colored_formatter = SimpleColoredFormatter(
        '%(asctime)s %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(colored_formatter)
    root_logger.addHandler(console_handler)

# 初始化彩色日志
_init_colored_logging()

# 获取日志记录器
def _get_logger():
    return logging.getLogger(__name__)



# 导入新的模型接口
try:
    from models.model_manager import model_manager, request_model as new_request_model
    _get_logger().info("成功导入新的模型管理器")
    MODEL_MANAGER_AVAILABLE = True
except ImportError as e:
    _get_logger().warning("无法导入模型管理器: %s", str(e))
    model_manager = None
    new_request_model = None
    MODEL_MANAGER_AVAILABLE = False

# Note: Backend module imports removed as they are now handled by the new API system

# 导入API路由
try:
    from api import api_router
    _get_logger().info("成功导入API路由")
    API_ROUTER_AVAILABLE = True
except ImportError as e:
    _get_logger().warning("无法导入API路由: %s", str(e))
    api_router = None
    API_ROUTER_AVAILABLE = False

# 导入中间件和文档配置
try:
    # 尝试绝对导入
    try:
        from backend_fastapi.middleware import ErrorHandlerMiddleware, LoggingMiddleware
        from backend_fastapi.docs.openapi_config import customize_openapi
    except ImportError:
        # 如果绝对导入失败，尝试相对导入
        from middleware import ErrorHandlerMiddleware, LoggingMiddleware
        from docs.openapi_config import customize_openapi
    _get_logger().info("成功导入中间件和文档配置")
    MIDDLEWARE_AVAILABLE = True
except ImportError as e:
    _get_logger().warning("无法导入中间件: %s", str(e))
    ErrorHandlerMiddleware = None
    LoggingMiddleware = None
    customize_openapi = None
    MIDDLEWARE_AVAILABLE = False

# 导入Redis初始化模块
try:
    from utils.redis_init import redis_lifespan, check_redis_health
    REDIS_AVAILABLE = True
    _get_logger().info("Redis模块导入成功")
except ImportError as e:
    _get_logger().warning("Redis模块导入失败: %s", str(e))
    REDIS_AVAILABLE = False
    redis_lifespan = None
    check_redis_health = None

# 创建FastAPI应用
if REDIS_AVAILABLE and redis_lifespan:
    app = FastAPI(
        title="论文评价分析系统API",
        description="北邮本科论文质量评价分析系统后端API",
        version="1.0.0",
        lifespan=redis_lifespan
    )
else:
    app = FastAPI(
        title="论文评价分析系统API",
        description="北邮本科论文质量评价分析系统后端API",
        version="1.0.0"
    )

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Vue.js开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加中间件
if MIDDLEWARE_AVAILABLE:
    if ErrorHandlerMiddleware:
        app.add_middleware(ErrorHandlerMiddleware)
        _get_logger().info("错误处理中间件已添加")

    if LoggingMiddleware:
        app.add_middleware(LoggingMiddleware, log_requests=True, log_responses=True)
        _get_logger().info("日志记录中间件已添加")

# 自定义OpenAPI文档
if MIDDLEWARE_AVAILABLE and customize_openapi:
    app.openapi = lambda: customize_openapi(app)
    _get_logger().info("OpenAPI文档配置已自定义")

# 注册API路由
if API_ROUTER_AVAILABLE and api_router:
    app.include_router(api_router, prefix="/api")
    _get_logger().info("API路由注册成功")
else:
    _get_logger().warning("API路由未注册，使用原有路由")

# 日志系统已在初始化时配置完成
logger = logging.getLogger(__name__)

# Note: The old API routes have been removed to prevent conflicts with the new API system.
# All document processing now uses the new API routes in api/document.py and related modules.

# 根路径
@app.get("/")
async def root():
    return {"message": "论文评价分析系统API", "version": "1.0.0"}

# 健康检查 - 按照API需求返回简化格式
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }

# Note: All API routes have been moved to the api/ module system to prevent conflicts.
# The old routes that were here have been removed.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
