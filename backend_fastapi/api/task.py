"""
任务管理API路由
提供异步任务状态管理功能
"""

import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
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

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态

    Args:
        task_id: 任务ID

    Returns:
        TaskStatusResponse: 任务状态
    """
    try:
        storage = await get_task_storage()
        task_info = await storage.get_task(task_id)
        
        if task_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")

        duration = calculate_task_duration(task_info)

        return TaskStatusResponse(
            success=True,
            task_id=task_id,
            status=task_info.get('status', 'unknown'),
            progress=task_info.get('progress', 0.0),
            message=task_info.get('message', ''),
            result=task_info.get('result'),
            error=task_info.get('error'),
            created_at=task_info.get('created_at'),
            updated_at=task_info.get('updated_at'),
            duration=duration
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="按状态筛选任务"),
    limit: int = Query(100, description="返回任务数量限制"),
    offset: int = Query(0, description="跳过的任务数量")
):
    """
    获取任务列表

    Args:
        status: 按状态筛选任务 (pending, running, completed, failed, cancelled)
        limit: 返回任务数量限制
        offset: 跳过的任务数量

    Returns:
        TaskListResponse: 任务列表
    """
    try:
        storage = await get_task_storage()
        all_tasks_dict = await storage.get_all_tasks()
        
        all_tasks = []
        active_count = 0
        completed_count = 0
        failed_count = 0

        for task_id, task_info in all_tasks_dict.items():
            task_status = task_info.get('status', 'unknown')
            duration = calculate_task_duration(task_info)

            # 统计任务状态
            if task_status in ['pending', 'running']:
                active_count += 1
            elif task_status == 'completed':
                completed_count += 1
            elif task_status == 'failed':
                failed_count += 1

            # 按状态筛选
            if status and task_status != status:
                continue

            all_tasks.append({
                'task_id': task_id,
                'status': task_status,
                'progress': task_info.get('progress', 0.0),
                'message': task_info.get('message', ''),
                'created_at': task_info.get('created_at'),
                'updated_at': task_info.get('updated_at'),
                'duration': duration,
                'has_result': task_info.get('result') is not None,
                'has_error': task_info.get('error') is not None
            })

        # 按创建时间倒序排序
        all_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # 分页
        paginated_tasks = all_tasks[offset:offset + limit]

        return TaskListResponse(
            success=True,
            tasks=paginated_tasks,
            total=len(all_tasks),
            active_count=active_count,
            completed_count=completed_count,
            failed_count=failed_count
        )

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """
    取消任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        dict: 取消结果
    """
    try:
        storage = await get_task_storage()
        task_info = await storage.get_task(task_id)
        
        if task_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 如果任务正在运行，标记为取消
        if task_info.get('status') in ['running', 'pending']:
            await storage.update_task(task_id, {
                'status': 'cancelled',
                'message': '任务已取消',
                'updated_at': datetime.now().isoformat()
            })
        
        return {
            'success': True,
            'message': '任务取消成功',
            'task_id': task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")

@router.delete("/")
async def clear_completed_tasks():
    """
    清理已完成的任务
    
    Returns:
        dict: 清理结果
    """
    try:
        storage = await get_task_storage()
        cleared_count = await storage.clear_completed_tasks()
        
        return {
            'success': True,
            'message': f'清理了{cleared_count}个已完成的任务',
            'cleared_count': cleared_count
        }

    except Exception as e:
        logger.error(f"清理任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理任务失败: {str(e)}")

@router.get("/summary", response_model=TaskSummaryResponse)
async def get_task_summary():
    """
    获取任务摘要统计

    Returns:
        TaskSummaryResponse: 任务摘要
    """
    try:
        storage = await get_task_storage()
        all_tasks_dict = await storage.get_all_tasks()
        
        total_tasks = len(all_tasks_dict)
        status_counts = {
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0
        }

        total_duration = 0
        completed_tasks = 0

        for task_info in all_tasks_dict.values():
            status = task_info.get('status', 'unknown')
            if status in status_counts:
                status_counts[status] += 1

            # 计算平均持续时间
            if status in ['completed', 'failed']:
                duration = calculate_task_duration(task_info)
                if duration:
                    total_duration += duration
                    completed_tasks += 1

        average_duration = total_duration / completed_tasks if completed_tasks > 0 else 0

        # 获取最近的任务
        recent_tasks = []
        sorted_tasks = sorted(
            all_tasks_dict.items(),
            key=lambda x: x[1].get('created_at', ''),
            reverse=True
        )

        for task_id, task_info in sorted_tasks[:5]:  # 最近5个任务
            recent_tasks.append({
                'task_id': task_id,
                'status': task_info.get('status', 'unknown'),
                'created_at': task_info.get('created_at'),
                'message': task_info.get('message', '')
            })

        summary = {
            'total_tasks': total_tasks,
            'status_counts': status_counts,
            'active_tasks': status_counts['pending'] + status_counts['running'],
            'success_rate': (status_counts['completed'] / total_tasks * 100) if total_tasks > 0 else 0,
            'average_duration': average_duration,
            'recent_tasks': recent_tasks
        }

        return TaskSummaryResponse(
            success=True,
            summary=summary
        )

    except Exception as e:
        logger.error(f"获取任务摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务摘要失败: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_tasks(days: int = Query(7, description="清理多少天前的任务")):
    """
    清理旧任务

    Args:
        days: 清理多少天前的任务

    Returns:
        dict: 清理结果
    """
    try:
        storage = await get_task_storage()
        cleared_count = await storage.clear_old_tasks(days)
        
        cutoff_time = datetime.now() - timedelta(days=days)

        return {
            'success': True,
            'message': f'清理了{cleared_count}个{days}天前的任务',
            'cleared_count': cleared_count,
            'cutoff_date': cutoff_time.isoformat()
        }

    except Exception as e:
        logger.error(f"清理旧任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理旧任务失败: {str(e)}")
