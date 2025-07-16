"""
论文评估API路由
提供论文质量评估相关功能
"""

import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.logger import get_logger
from pipeline.paper_evaluation import full_paper_evaluation
from utils.task_storage import get_task_storage
from utils.redis_client import get_redis_manager

logger = get_logger(__name__)
router = APIRouter()

# 请求模型
class EvaluationRequest(BaseModel):
    """评估请求模型"""
    document_id: str
    model_name: str = "deepseek-chat"
    evaluation_type: str = "full"  # full, chapter, overall

    model_config = {'protected_namespaces': ()}

class ChapterEvaluationRequest(BaseModel):
    """章节评估请求模型"""
    document_id: str
    chapter_index: int
    model_name: str = "deepseek-chat"

    model_config = {'protected_namespaces': ()}

# 响应模型
class EvaluationResponse(BaseModel):
    """评估响应模型"""
    success: bool
    message: str
    task_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

async def run_evaluation_task_async(task_id: str, document_id: str, model_name: str):
    """
    运行评估任务的异步版本

    Args:
        task_id: 任务ID
        document_id: 文档ID
        model_name: 模型名称
    """
    try:
        storage = await get_task_storage()
        
        # 更新任务状态
        await storage.set_task(task_id, {
            'status': 'running',
            'progress': 0.0,
            'message': '开始评估...',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 获取文档数据
        document_info = await redis_mgr.get_document(document_id)
        if document_info is None:
            raise Exception("文档不存在")

        if document_info.get('status') != 'processed':
            raise Exception("文档尚未处理完成")

        # 进度回调函数
        def progress_callback(progress: float, message: str):
            # 创建异步任务来更新进度
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，创建任务
                    loop.create_task(storage.update_task(task_id, {
                        'progress': progress,
                        'message': message,
                        'updated_at': datetime.now().isoformat()
                    }))
                else:
                    # 如果没有运行中的事件循环，同步运行
                    loop.run_until_complete(storage.update_task(task_id, {
                        'progress': progress,
                        'message': message,
                        'updated_at': datetime.now().isoformat()
                    }))
            except Exception as e:
                logger.warning(f"更新任务进度失败: {e}")

        # 获取文档内容
        file_content = document_info['content']

        # 调用评估流程
        result = full_paper_evaluation(
            file_content,
            model_name,
            progress_callback
        )

        if result.get('status') == 'error':
            raise Exception(result.get('error', '评估失败'))

        # 更新任务状态为完成
        await storage.update_task(task_id, {
            'status': 'completed',
            'progress': 1.0,
            'message': '评估完成',
            'result': result,
            'updated_at': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"评估任务失败: {e}")
        try:
            storage = await get_task_storage()
            await storage.update_task(task_id, {
                'status': 'failed',
                'progress': 0.0,
                'message': '评估失败',
                'error': str(e),
                'updated_at': datetime.now().isoformat()
            })
        except Exception as update_error:
            logger.error(f"更新失败状态时出错: {update_error}")

def run_evaluation_task_sync(task_id: str, document_id: str, model_name: str):
    """
    运行评估任务的同步包装器

    Args:
        task_id: 任务ID
        document_id: 文档ID
        model_name: 模型名称
    """
    # 使用新的事件循环运行异步函数
    try:
        asyncio.run(run_evaluation_task_async(task_id, document_id, model_name))
    except Exception as e:
        logger.error(f"同步包装器执行失败: {e}")

@router.post("/start", response_model=EvaluationResponse)
async def start_evaluation(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """
    开始论文评估

    Args:
        request: 评估请求
        background_tasks: 后台任务管理器

    Returns:
        EvaluationResponse: 评估结果
    """
    try:
        logger.info(f"开始评估文档: {request.document_id}, 模型: {request.model_name}")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(request.document_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        if document_info.get('status') != 'processed':
            raise HTTPException(status_code=400, detail="文档尚未处理完成")

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 添加后台任务
        background_tasks.add_task(
            run_evaluation_task_sync,
            task_id,
            request.document_id,
            request.model_name
        )

        return EvaluationResponse(
            success=True,
            message="评估任务已启动",
            task_id=task_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始评估失败: {e}")
        raise HTTPException(status_code=500, detail=f"开始评估失败: {str(e)}")

@router.post("/chapter", response_model=EvaluationResponse)
async def evaluate_chapter(request: ChapterEvaluationRequest):
    """
    评估单个章节

    Args:
        request: 章节评估请求

    Returns:
        EvaluationResponse: 评估结果
    """
    try:
        logger.info(f"开始评估章节: 文档{request.document_id}, 章节{request.chapter_index}")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(request.document_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        if document_info.get('status') != 'processed':
            raise HTTPException(status_code=400, detail="文档尚未处理完成")

        # 获取章节数据
        pkl_data = document_info.get('pkl_data', {})
        chapters = pkl_data.get('chapters', [])

        if request.chapter_index < 0 or request.chapter_index >= len(chapters):
            raise HTTPException(status_code=400, detail="章节索引无效")

        chapter = chapters[request.chapter_index]

        # 导入章节评估功能
        from ..pipeline.chapter_inference import process_chapter_evaluation

        # 进行章节评估
        result = process_chapter_evaluation(
            chapter.get('content', ''),
            request.model_name
        )

        return EvaluationResponse(
            success=True,
            message="章节评估完成",
            result=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"章节评估失败: {e}")
        raise HTTPException(status_code=500, detail=f"章节评估失败: {str(e)}")

@router.get("/models")
async def get_available_models():
    """
    获取可用的评估模型
    
    Returns:
        dict: 可用模型列表
    """
    try:
        from ..models.model_manager import model_manager
        
        available_models = model_manager.get_available_models()
        model_status = model_manager.get_model_status()
        
        return {
            'success': True,
            'models': available_models,
            'status': model_status
        }

    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.get("/result/{task_id}", response_model=EvaluationResponse)
async def get_evaluation_result(task_id: str):
    """
    获取评估结果

    Args:
        task_id: 任务ID

    Returns:
        EvaluationResponse: 评估结果
    """
    try:
        storage = await get_task_storage()
        task_info = await storage.get_task(task_id)
        
        if task_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task_info['status'] == 'completed':
            return EvaluationResponse(
                success=True,
                message="评估已完成",
                task_id=task_id,
                result=task_info.get('result')
            )
        elif task_info['status'] == 'failed':
            return EvaluationResponse(
                success=False,
                message=f"评估失败: {task_info.get('error', '未知错误')}",
                task_id=task_id
            )
        else:
            return EvaluationResponse(
                success=True,
                message=f"评估进行中: {task_info.get('message', '')}",
                task_id=task_id
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评估结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评估结果失败: {str(e)}")

@router.get("/progress/{task_id}")
async def get_evaluation_progress(task_id: str):
    """
    获取评估进度

    Args:
        task_id: 任务ID

    Returns:
        dict: 进度信息
    """
    try:
        storage = await get_task_storage()
        task_info = await storage.get_task(task_id)
        
        if task_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {
            'success': True,
            'task_id': task_id,
            'status': task_info.get('status', 'unknown'),
            'progress': task_info.get('progress', 0.0),
            'message': task_info.get('message', ''),
            'created_at': task_info.get('created_at'),
            'updated_at': task_info.get('updated_at')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评估进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评估进度失败: {str(e)}")

