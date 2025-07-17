"""
任务管理API路由
提供异步任务状态管理功能
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.logger import get_logger
from utils.task_storage import get_task_storage

logger = get_logger(__name__)
router = APIRouter()

# 响应模型
class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    success: bool
    task_id: str
    status: str
    progress: float
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    duration: Optional[float] = None

class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    success: bool
    tasks: List[Dict[str, Any]]
    total: int
    active_count: int
    completed_count: int
    failed_count: int

class TaskSummaryResponse(BaseModel):
    """任务摘要响应模型"""
    success: bool
    summary: Dict[str, Any]

# Redis任务存储（替代内存存储）

def calculate_task_duration(task_info: Dict[str, Any]) -> Optional[float]:
    """
    计算任务持续时间

    Args:
        task_info: 任务信息

    Returns:
        Optional[float]: 持续时间（秒），如果无法计算则返回None
    """
    try:
        created_at = task_info.get('created_at')
        updated_at = task_info.get('updated_at')

        if not created_at:
            return None

        created_time = datetime.fromisoformat(created_at)

        if task_info.get('status') in ['completed', 'failed', 'cancelled'] and updated_at:
            end_time = datetime.fromisoformat(updated_at)
        else:
            end_time = datetime.now()

        return (end_time - created_time).total_seconds()

    except Exception:
        return None

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
        storage = await get_task_storage()
        task_info = await storage.get_task(task_id)

        if task_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 按照API需求返回格式
        return {
            "task_id": task_id,
            "status": task_info.get('status', 'pending'),
            "progress": task_info.get('progress', 0.0),
            "message": task_info.get('message', ''),
            "error": task_info.get('error'),
            "result": task_info.get('result')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

# 删除不在API需求中的list_tasks路由

# 按照API需求修改路由路径
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
        storage = await get_task_storage()
        task_info = await storage.get_task(task_id)

        if task_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 删除任务数据
        await storage.delete_task(task_id)

        # 按照API需求返回格式
        return {
            "message": "任务已删除",
            "task_id": task_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

# 删除不在API需求中的clear_completed_tasks路由

# 删除不在API需求中的summary和cleanup路由
