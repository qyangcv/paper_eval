import os
import sys
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.logger import get_logger
from utils.task_storage import get_task_storage
from utils.redis_client import get_redis_manager # 导入 RedisManager
from utils.async_tasks import get_task_manager # 导入 AsyncTaskManager

logger = get_logger(__name__)
router = APIRouter()

# 响应模型
class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str
    status: str
    progress: float
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 按照API需求修改路由路径
@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    获取任务状态

    Args:
        task_id: 任务ID

    Returns:
        dict: 任务状态，按照API需求格式
    """
    try:
        redis_mgr = await get_redis_manager()
        document_info = await redis_mgr.get_document(task_id)

        if document_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")

        status = document_info['status']
        progress = document_info.get('progress', 0.0)
        message = document_info.get('message', "等待处理")

        if status == 'uploaded':
            if progress == 0.0:
                progress = 0.1
                message = "文档已上传"
        elif status == 'processing':
            if progress == 0.0:
                progress = 0.2
                message = "正在处理文档"
        elif status == 'processed':
            task_manager = await get_task_manager()
            task_status_summary = task_manager.get_task_status_summary(task_id)
            background_task_running = task_status_summary["is_running"]

            if background_task_running:
                status = 'processing'
                cached_progress = task_status_summary["last_known_progress"]
                cached_message = task_status_summary["last_known_message"]
                progress = min(max(progress, cached_progress), 0.9)
                message = cached_message if cached_message else "正在进行后台分析评估，预计需要5-7分钟..."
            else:
                hard_eval_completed = document_info.get('hard_eval_result') is not None
                soft_eval_completed = document_info.get('soft_eval_result') is not None
                img_eval_completed = document_info.get('img_eval_result') is not None
                ref_eval_completed = document_info.get('ref_eval_result') is not None
                basic_info_completed = document_info.get('basic_info_result') is not None
                overall_stats_completed = document_info.get('overall_stats_result') is not None
                chapter_stats_completed = document_info.get('chapter_stats_result') is not None
                ref_stats_completed = document_info.get('ref_stats_result') is not None

                if (hard_eval_completed and soft_eval_completed and img_eval_completed and ref_eval_completed and
                    basic_info_completed and overall_stats_completed and chapter_stats_completed and ref_stats_completed):
                    progress = 1.0
                    message = "所有分析完成！"
                    status = 'completed'
                else:
                    status = 'processing'
                    completed_count = sum([hard_eval_completed, soft_eval_completed, img_eval_completed, ref_eval_completed,
                                           basic_info_completed, overall_stats_completed,
                                           chapter_stats_completed, ref_stats_completed])
                    progress = 0.5 + (completed_count / 8) * 0.5
                    message = f"正在进行后台分析评估... ({completed_count}/8 完成)"

        elif status == 'failed':
            progress = 0.0
            message = "处理失败"
            status = 'error'

        result_data = {
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "message": message,
            "error": document_info.get('error')
        }

        if status == 'completed':
            result_data["result"] = {
                "filename": document_info['filename'],
                "size": document_info['size'],
                "has_markdown": 'md_content' in document_info,
                "has_pkl_data": 'pkl_data' in document_info,
                "image_count": len(document_info.get('images', [])),
                "chapter_count": len(document_info.get('pkl_data', {}).get('chapters', [])),
                "basic_info": document_info.get('basic_info_result'),
                "overall_stats": document_info.get('overall_stats_result'),
                "chapter_stats": document_info.get('chapter_stats_result'),
                "ref_stats": document_info.get('ref_stats_result')
            }

        return TaskStatusResponse(**result_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """
    删除指定任务及其相关数据

    Args:
        task_id: 任务ID

    Returns:
        dict: 删除结果，按照API需求格式
    """
    try:
        redis_mgr = await get_redis_manager()
        document_info = await redis_mgr.get_document(task_id)

        if document_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")

        if document_info['status'] == 'processing':
            raise HTTPException(status_code=409, detail="文档正在处理中，无法删除。请等待处理完成或稍后再试。")

        if not await redis_mgr.delete_document(task_id):
            raise HTTPException(status_code=500, detail="任务删除失败")

        logger.info(f"任务删除成功: {task_id}")

        return {
            "message": "任务已删除",
            "task_id": task_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@router.delete("/cache/{task_id}/evaluation")
async def clear_evaluation_cache(task_id: str):
    """
    清除指定文档的所有评估缓存，保留文档本身
    
    Args:
        task_id: 任务ID
        
    Returns:
        dict: 清理结果
    """
    try:
        redis_mgr = await get_redis_manager()
        
        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if redis_mgr._client:
            # 清除Redis中的评估缓存
            keys_to_delete = [
                f"paper_eval:hard:{task_id}",
                f"paper_eval:soft:{task_id}",
                f"paper_eval:img:{task_id}",
                f"paper_eval:ref:{task_id}"
            ]
            deleted_count = await redis_mgr._client.delete(*keys_to_delete)
            
            # 清除文档信息中的评估结果缓存
            eval_keys = [
                'hard_eval_result', 'soft_eval_result', 
                'img_eval_result', 'ref_eval_result'
            ]
            cache_cleared = False
            for key in eval_keys:
                if key in document_info:
                    document_info.pop(key)
                    cache_cleared = True
            
            if cache_cleared:
                await redis_mgr.store_document(task_id, document_info)
        
        logger.info(f"清除评估缓存: {task_id}, 删除Redis键数量: {deleted_count}")
        
        return {
            "task_id": task_id,
            "status": "cache_cleared",
            "message": f"评估缓存已清除，删除了{deleted_count}个Redis键",
            "deleted_redis_keys": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除评估缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除评估缓存失败: {str(e)}")

@router.delete("/cache/all")
async def clear_all_evaluation_cache():
    """
    清除所有文档的评估缓存（开发用）
    
    Returns:
        dict: 清理结果
    """
    try:
        redis_mgr = await get_redis_manager()
        
        if redis_mgr._client:
            total_deleted = 0
            patterns = ["paper_eval:hard:*", "paper_eval:soft:*", "paper_eval:img:*", "paper_eval:ref:*"]
            
            for pattern in patterns:
                keys = []
                cursor = 0
                while True:
                    cursor, batch_keys = await redis_mgr._client.scan(cursor=cursor, match=pattern, count=1000)
                    keys.extend(batch_keys)
                    if cursor == 0:
                        break
                
                if keys:
                    deleted_count = await redis_mgr._client.delete(*keys)
                    total_deleted += deleted_count
                    logger.info(f"删除缓存键 {pattern}: {deleted_count} 个")
        
        logger.info(f"清除所有评估缓存，总共删除: {total_deleted} 个键")
        
        return {
            "status": "all_cache_cleared",
            "message": f"所有评估缓存已清除，删除了{total_deleted}个Redis键",
            "deleted_redis_keys": total_deleted
        }
        
    except Exception as e:
        logger.error(f"清除所有评估缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除所有评估缓存失败: {str(e)}")