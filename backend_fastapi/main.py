"""
FastAPI后端主应用
重构自原Streamlit应用，提供RESTful API服务
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
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

# 导入现有的后端模块
process_paper_evaluation = None
convert_word_to_html_with_math = None
extract_toc_from_docx = None

try:
    # 添加backend/hard_criteria到路径以便导入其模块
    backend_metrics_path = os.path.join(project_root, "backend", "hard_criteria")
    if backend_metrics_path not in sys.path:
        sys.path.insert(0, backend_metrics_path)

    from frontend.services.document_processor import process_paper_evaluation, convert_word_to_html_with_math, extract_toc_from_docx
    _get_logger().info("成功导入后端模块")
except ImportError as e:
    _get_logger().warning("导入警告: %s", str(e))
    _get_logger().info("将使用模拟功能进行测试")
    _get_logger().info(f"项目根目录: {project_root}")

# 导入API路由
try:
    # 尝试绝对导入
    try:
        from backend_fastapi.api import api_router
    except ImportError:
        # 如果绝对导入失败，尝试相对导入
        from api import api_router
    _get_logger().info("成功导入API路由")
    API_ROUTER_AVAILABLE = True
except ImportError as e:
    _get_logger().warning("无法导入API路由: %s", str(e))
    api_router = None
    API_ROUTER_AVAILABLE = False

from api import api_router
_get_logger().info("成功导入API路由")
API_ROUTER_AVAILABLE = True

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

# 全局存储处理任务状态
processing_tasks: Dict[str, Dict[str, Any]] = {}

# Pydantic模型定义
class ProcessingStatus(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "error"
    progress: float
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ModelConfig(BaseModel):
    name: str  # 改名避免与pydantic的model_命名空间冲突
    api_key: Optional[str] = None

    # 确保可以正确序列化和反序列化
    model_config = {
        'populate_by_name': True,  # 允许使用别名填充
        'protected_namespaces': ()  # 防止与pydantic内部命名冲突
    }

class EvaluationRequest(BaseModel):
    task_id: str
    model_settings: dict  # 修改为dict类型，以便更灵活地处理请求

    model_config = {
        'populate_by_name': True,
        'protected_namespaces': (),
        'arbitrary_types_allowed': True
    }

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

# 文档上传接口已移至 api/document.py，避免重复路由

# 获取处理状态
@app.get("/api/status/{task_id}")
async def get_processing_status(task_id: str):
    """
    获取文档处理状态
    """
    try:
        # 优先从Redis获取状态（新系统）
        from utils.redis_client import get_redis_manager
        redis_mgr = await get_redis_manager()
        document_info = await redis_mgr.get_document(task_id)

        if document_info is not None:
            # 使用Redis中的状态
            status = document_info['status']
            progress = document_info.get('progress', 0.0)
            message = document_info.get('message', "等待处理")

            # 状态映射：将Redis状态映射为前端期望的状态
            if status == 'uploaded':
                if progress == 0.0:
                    progress = 0.1
                    message = "文档已上传"
            elif status == 'processing':
                if progress == 0.0:
                    progress = 0.2
                    message = "正在处理文档"
                # 使用存储的进度和消息
            elif status == 'processed':
                # 检查后台评估任务是否完成
                from utils.async_tasks import get_task_manager
                task_manager = await get_task_manager()

                # 使用优化的状态检查
                task_status_summary = task_manager.get_task_status_summary(task_id)
                background_task_running = task_manager.is_task_running(task_id)

                if background_task_running:
                    # 后台任务仍在运行，使用缓存的进度信息
                    status = 'processing'
                    cached_progress = task_status_summary["last_known_progress"]
                    cached_message = task_status_summary["last_known_message"]

                    # 使用缓存的进度，但确保不超过90%
                    progress = min(max(progress, cached_progress), 0.9)
                    message = cached_message if cached_message else "正在进行后台分析评估，预计需要5-7分钟..."
                else:
                    # 检查是否所有评估都完成（图片评估已禁用，视为已完成）
                    hard_eval_completed = document_info.get('hard_eval_result') is not None
                    soft_eval_completed = document_info.get('soft_eval_result') is not None
                    img_eval_completed = True  # 图片评估已禁用，视为已完成
                    ref_eval_completed = document_info.get('ref_eval_result') is not None

                    if hard_eval_completed and soft_eval_completed and img_eval_completed and ref_eval_completed:
                        # 所有评估完成
                        progress = 1.0
                        message = "所有分析完成！"
                        status = 'completed'  # 前端期望的状态名

                        # 检查是否是第一次完成，如果是则记录特殊日志
                        if document_info.get('first_completion_logged') != True:
                            from tools.logger import get_logger
                            status_logger = get_logger("backend_fastapi.middleware.logging_middleware")
                            status_logger.info(f"[COMPLETED] GET /api/status/{task_id} - 127.0.0.1 - 评估任务完成")

                            # 标记已记录完成日志，避免重复记录
                            document_info['first_completion_logged'] = True
                            await redis_mgr.store_document(task_id, document_info)
                    else:
                        # 评估未完成，保持processing状态
                        status = 'processing'
                        progress = min(progress, 0.9)
                        message = "正在进行后台分析评估..."

            elif status == 'failed':
                progress = 0.0
                message = "处理失败"
                status = 'error'  # 前端期望的状态名

            result_data = {
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "message": message,
                "error": document_info.get('error')
            }

            # 如果处理完成，添加结果信息
            if status == 'completed':
                result_data["result"] = {
                    "filename": document_info['filename'],
                    "size": document_info['size'],
                    "has_markdown": 'md_content' in document_info,
                    "has_pkl_data": 'pkl_data' in document_info,
                    "image_count": len(document_info.get('images', [])),
                    "chapter_count": len(document_info.get('pkl_data', {}).get('chapters', []))
                }

            return ProcessingStatus(**result_data)

        # 如果Redis中没有，回退到旧系统
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")

        task = processing_tasks[task_id]
        return ProcessingStatus(
            task_id=task["task_id"],
            status=task["status"],
            progress=task["progress"],
            message=task["message"],
            result=task.get("result"),
            error=task.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

# 开始文档处理
@app.post("/api/process")
async def start_processing(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks
):
    """
    开始文档处理和评估
    """
    try:
        # 直接记录请求对象
        print(f"🔍 接收到的原始请求: task_id='{request.task_id}'")
        print(f"🔍 请求JSON: {request.model_dump()}")
        
        task_id = request.task_id

        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")

        task = processing_tasks[task_id]
        if task["status"] != "pending":
            raise HTTPException(status_code=400, detail="任务已在处理中或已完成")

        model_settings = request.model_settings
        print(f"🔍 模型配置对象: {model_settings}")
        print(f"🔍 模型配置类型: {type(model_settings)}")

        if isinstance(model_settings, dict):
            print(f"🔍 模型配置字典内容: {model_settings}")
        else:
            print(f"🔍 模型配置属性: {dir(model_settings)}")

        # 增强模型配置解析
        model_name = 'none'
        api_key = None

        # 直接解析字典类型的model_settings
        if isinstance(model_settings, dict):
            model_name = model_settings.get('model_name', 'none')
            api_key = model_settings.get('api_key')
            print(f"从字典直接解析: model_name={model_name}, api_key={'已设置' if api_key else 'None'}")
        # 尝试标准的Pydantic对象属性访问
        elif hasattr(model_settings, 'model_name'):
            model_name = model_settings.model_name
            if hasattr(model_settings, 'api_key'):
                api_key = model_settings.api_key

        print(f"🔍 解析后的模型名称: {model_name}")
        print(f"🔍 解析后的API密钥: {api_key[:10] + '...' if api_key else 'None'}")

        # 如果没有提供API密钥但选择了需要API的模型，使用预设的DeepSeek密钥
        if not api_key and model_name.startswith("deepseek"):
            api_key = "sk-e6068e4723e74a4b8a8e2788cf7ac055"
            print(f"🔧 使用预设的DeepSeek API密钥: {api_key[:10]}...")

        if api_key:
            if model_name.startswith("deepseek"):
                os.environ["DEEPSEEK_API_KEY"] = api_key
                print(f"✓ 设置DeepSeek API密钥: {api_key[:10]}...")
            elif model_name == "gemini":
                os.environ["GEMINI_API_KEY"] = api_key
                print(f"✓ 设置Gemini API密钥: {api_key[:10]}...")
            elif model_name == "gpt":
                os.environ["OPENAI_API_KEY"] = api_key
                print(f"✓ 设置OpenAI API密钥: {api_key[:10]}...")
        else:
            print(f"⚠️ 未提供API密钥，模型: {model_name}")

        # 启动后台处理任务
        background_tasks.add_task(
            process_document_background,
            task_id,
            model_name
        )

        # 更新任务状态
        processing_tasks[task_id]["status"] = "processing"
        processing_tasks[task_id]["message"] = "开始处理文档"

        return {"message": "文档处理已开始", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"处理启动错误: {e}")
        raise HTTPException(status_code=500, detail=f"处理启动失败: {str(e)}")

async def process_document_background(task_id: str, model_name: str):
    """
    后台处理文档的异步任务
    """
    try:
        task = processing_tasks[task_id]
        file_content = task["file_content"]
        filename = task["filename"]
        
        # 更新进度回调函数
        def update_progress(progress: float, message: str):
            processing_tasks[task_id]["progress"] = progress
            processing_tasks[task_id]["message"] = message
        
        # 模拟文件对象
        class MockUploadedFile:
            def __init__(self, content, name):
                self.content = content
                self.name = name
            
            def getvalue(self):
                return self.content
            
            def read(self):
                return self.content
        
        mock_file = MockUploadedFile(file_content, filename)
        
        # 第一步：生成HTML预览
        update_progress(0.1, "正在生成文档预览...")
        try:
            html_content = convert_word_to_html_with_math(mock_file)
        except Exception as e:
            print(f"HTML转换错误: {e}")
            html_content = "<html><body><h1>文档预览</h1><p>文档处理完成，但预览生成失败</p></body></html>"

        # 第二步：提取目录结构
        update_progress(0.2, "正在提取文档结构...")
        try:
            toc_items = extract_toc_from_docx(mock_file)
        except Exception as e:
            print(f"目录提取错误: {e}")
            toc_items = [{"title": "文档内容", "level": 1}]
        
        # 第三步：进行论文评估（如果不是'none'模型）
        evaluation_result = None
        if model_name != 'none':
            update_progress(0.3, "开始论文质量评估...")
            
            # 这里需要适配原有的评估函数
            # 由于原函数需要文件路径，我们需要创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            try:
                # 调用原有的评估函数
                evaluation_result = process_paper_evaluation(
                    temp_path,
                    model_name=model_name,
                    progress_callback=lambda prog, msg: update_progress(0.3 + prog * 0.6, msg)
                )
            finally:
                # 清理临时文件
                os.unlink(temp_path)
        else:
            update_progress(0.9, "跳过模型评估...")
        
        # 完成处理
        update_progress(1.0, "处理完成")
        
        # 保存结果
        processing_tasks[task_id].update({
            "status": "completed",
            "result": {
                "html_content": html_content,
                "toc_items": toc_items,
                "evaluation": evaluation_result,
                "filename": filename
            }
        })
        
    except Exception as e:
        # 处理错误
        processing_tasks[task_id].update({
            "status": "error",
            "error": str(e),
            "message": f"处理失败: {str(e)}"
        })

# 获取处理结果
@app.get("/api/result/{task_id}")
async def get_result(task_id: str):
    """
    获取文档处理结果
    """
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = processing_tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    return task["result"]

# 清理任务
@app.delete("/api/task/{task_id}")
async def delete_task(task_id: str):
    """
    删除任务记录
    """
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    del processing_tasks[task_id]
    return {"message": "任务已删除"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
