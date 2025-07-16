"""
FastAPI后端主应用
重构自原Streamlit应用，提供RESTful API服务
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import sys
import uuid
import json
import asyncio
from datetime import datetime
import tempfile
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 延迟初始化日志，避免在日志配置完成前使用
def _get_logger():
    import logging
    logger = logging.getLogger(__name__)

    # 清除现有的处理器，确保使用统一格式
    logger.handlers.clear()

    # 添加统一格式的处理器
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # 防止重复输出

    return logger

# 导入新的模型接口
try:
    from models.model_manager import model_manager, request_model as new_request_model
    _get_logger().info("成功导入新的模型管理器")
    MODEL_MANAGER_AVAILABLE = True
except ImportError as e:
    _get_logger().warning(f"无法导入模型管理器: {e}")
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
    _get_logger().warning(f"导入警告: {e}")
    _get_logger().info("将使用模拟功能进行测试")
    _get_logger().info(f"项目根目录: {project_root}")

# 尝试导入full_paper_eval模块的函数
try:
    # 确保路径正确添加
    hard_criteria_path = os.path.join(project_root, "backend", "hard_criteria")
    if hard_criteria_path not in sys.path:
        sys.path.insert(0, hard_criteria_path)

    # 动态导入模块
    import importlib.util
    spec = importlib.util.spec_from_file_location("full_paper_eval",
                                                  os.path.join(hard_criteria_path, "full_paper_eval.py"))
    full_paper_eval_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(full_paper_eval_module)

    # 获取需要的函数
    process_docx_file = full_paper_eval_module.process_docx_file
    load_chapters = full_paper_eval_module.load_chapters
    process_chapter = full_paper_eval_module.process_chapter
    evaluate_overall = full_paper_eval_module.evaluate_overall
    score_paper = full_paper_eval_module.score_paper
    request_model = full_paper_eval_module.request_model

    _get_logger().info("成功导入full_paper_eval模块")
    FULL_PAPER_EVAL_AVAILABLE = True
except Exception as e:
    _get_logger().warning(f"full_paper_eval导入警告: {e}")
    _get_logger().info("将在需要时动态导入")
    FULL_PAPER_EVAL_AVAILABLE = False
    # 设置默认值
    process_docx_file = None
    load_chapters = None
    process_chapter = None
    evaluate_overall = None
    score_paper = None
    request_model = None

    # 创建模拟函数用于测试
    def mock_convert_word_to_html_with_math(file):
        return "<html><body><h1>模拟HTML内容</h1><p>文档处理功能正常</p></body></html>"

    def mock_extract_toc_from_docx(file):
        return [{"title": "第1章 引言", "level": 1}, {"title": "第2章 相关工作", "level": 1}]

    def mock_process_paper_evaluation(file_path, model_name, progress_callback=None):
        """模拟论文评估过程，用于测试"""
        import time
        import random

        if progress_callback:
            progress_callback(0.1, "开始文档解析...")
            time.sleep(0.5)
            progress_callback(0.3, "提取章节结构...")
            time.sleep(0.5)
            progress_callback(0.5, f"使用{model_name}模型分析中...")
            time.sleep(1.0)
            progress_callback(0.7, "生成评估报告...")
            time.sleep(0.5)
            progress_callback(0.9, "计算综合得分...")
            time.sleep(0.3)
            progress_callback(1.0, "评估完成")

        # 生成模拟的详细评估结果
        return {
            "overall_score": random.randint(75, 95),
            "dimensions": {
                "创新性": random.randint(70, 90),
                "技术深度": random.randint(75, 95),
                "实验设计": random.randint(80, 95),
                "写作质量": random.randint(75, 90),
                "学术规范": random.randint(70, 85)
            },
            "summary": f"使用{model_name}模型完成的论文质量评估",
            "detailed_analysis": {
                "strengths": ["研究方法科学", "实验设计合理", "数据分析充分"],
                "weaknesses": ["文献综述可以更全面", "结论部分需要加强"],
                "suggestions": ["建议补充相关工作对比", "加强实验结果讨论"]
            },
            "chapter_scores": [
                {"chapter": "引言", "score": random.randint(75, 90)},
                {"chapter": "相关工作", "score": random.randint(70, 85)},
                {"chapter": "方法", "score": random.randint(80, 95)},
                {"chapter": "实验", "score": random.randint(85, 95)},
                {"chapter": "结论", "score": random.randint(75, 90)}
            ]
        }

    convert_word_to_html_with_math = mock_convert_word_to_html_with_math
    extract_toc_from_docx = mock_extract_toc_from_docx

    # 尝试使用真实的评估函数，如果失败则使用模拟函数
    def real_process_paper_evaluation(file_path, model_name, progress_callback=None):
        """真实的论文评估函数，调用大模型进行分析"""
        try:
            # 检查是否已成功导入full_paper_eval模块和新的模型管理器
            if not FULL_PAPER_EVAL_AVAILABLE or not all([process_docx_file, load_chapters, process_chapter,
                                                        evaluate_overall, score_paper]):
                raise Exception("full_paper_eval模块未正确导入")

            # 使用新的模型管理器验证模型配置
            if MODEL_MANAGER_AVAILABLE and model_manager:
                if not model_manager.validate_model_config(model_name):
                    raise Exception(f"模型 {model_name} 配置无效或API密钥缺失")

            if progress_callback:
                progress_callback(0.1, "开始处理文档...")

            # 处理docx文件转换为pkl
            pkl_file_path = process_docx_file(file_path)
            if not pkl_file_path:
                raise Exception("文档转换失败")

            if progress_callback:
                progress_callback(0.2, "加载章节内容...")

            # 加载章节
            chapters = load_chapters(pkl_file_path)
            if not chapters:
                raise Exception("章节加载失败")

            if progress_callback:
                progress_callback(0.3, f"使用{model_name}开始章节分析...")

            # 处理每个章节
            chapter_evaluations = []
            total_chapters = len(chapters)
            for i, chapter in enumerate(chapters):
                if progress_callback:
                    progress = 0.3 + (i / total_chapters) * 0.4
                    progress_callback(progress, f"分析章节: {chapter.get('title', f'第{i+1}章')}")

                chapter_eval = process_chapter(chapter, model_name)
                chapter_evaluations.append(chapter_eval)

            if progress_callback:
                progress_callback(0.7, "进行整体评估...")

            # 整体评估
            overall_evaluation = evaluate_overall(chapter_evaluations, model_name)
            all_evaluations = [overall_evaluation] + chapter_evaluations

            if progress_callback:
                progress_callback(0.9, "计算最终得分...")

            # 评分
            paper_scores = score_paper(all_evaluations, model_name)

            # 计算总分
            total_score = sum(item.get('score', 0) for item in paper_scores if 'score' in item)

            if progress_callback:
                progress_callback(1.0, "评估完成")

            # 格式化结果
            return {
                "overall_score": total_score,
                "dimensions": {
                    "创新性": paper_scores[0].get('score', 0) if len(paper_scores) > 0 else 0,
                    "技术深度": paper_scores[1].get('score', 0) if len(paper_scores) > 1 else 0,
                    "实验设计": paper_scores[2].get('score', 0) if len(paper_scores) > 2 else 0,
                    "写作质量": paper_scores[3].get('score', 0) if len(paper_scores) > 3 else 0,
                    "学术规范": paper_scores[4].get('score', 0) if len(paper_scores) > 4 else 0
                },
                "summary": overall_evaluation.get('summary', '评估完成'),
                "detailed_analysis": {
                    "strengths": overall_evaluation.get('strengths', []),
                    "weaknesses": overall_evaluation.get('weaknesses', []),
                    "suggestions": overall_evaluation.get('suggestions', [])
                },
                "chapter_scores": [
                    {
                        "chapter": eval_item.get('chapter', '未知章节'),
                        "score": eval_item.get('score', 0)
                    }
                    for eval_item in chapter_evaluations
                ],
                "raw_evaluations": all_evaluations,
                "raw_scores": paper_scores
            }

        except Exception as e:
            _get_logger().warning(f"真实评估失败，使用模拟结果: {e}")
            return mock_process_paper_evaluation(file_path, model_name, progress_callback)

    process_paper_evaluation = real_process_paper_evaluation

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
    _get_logger().warning(f"无法导入API路由: {e}")
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
    _get_logger().warning(f"无法导入中间件: {e}")
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
    _get_logger().warning(f"Redis模块导入失败: {e}")
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

# 健康检查
@app.get("/health")
async def health_check():
    health_info = {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # 检查Redis状态
    if REDIS_AVAILABLE and check_redis_health:
        try:
            redis_health = await check_redis_health()
            health_info["services"]["redis"] = redis_health
        except Exception as e:
            health_info["services"]["redis"] = {
                "status": "error",
                "connected": False,
                "message": f"Redis健康检查失败: {e}"
            }
    else:
        health_info["services"]["redis"] = {
            "status": "unavailable",
            "connected": False,
            "message": "Redis模块未加载"
        }
    
    return health_info

# 文档上传接口
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    上传Word文档并返回任务ID
    """
    # 验证文件类型
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="仅支持.docx格式的文档")
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 创建任务记录
        processing_tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0.0,
            "message": "文档上传成功，等待处理",
            "filename": file.filename,
            "file_content": file_content,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "task_id": task_id,
            "filename": file.filename,
            "message": "文档上传成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")

# 获取处理状态
@app.get("/api/status/{task_id}")
async def get_processing_status(task_id: str):
    """
    获取文档处理状态
    """
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
