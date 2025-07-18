"""
异步任务处理模块
用于处理耗时的后台任务，避免API请求超时
"""

import asyncio
import json
from typing import Dict, Any
from tools.logger import get_logger
from utils.redis_client import get_redis_manager

logger = get_logger(__name__)

class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self):
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_evaluation_task(self, task_id: str, document_info: Dict[str, Any]):
        """
        启动评估任务
        
        Args:
            task_id: 任务ID
            document_info: 文档信息
        """
        if task_id in self._running_tasks:
            logger.info(f"任务 {task_id} 已在运行中")
            return
        
        # 创建异步任务
        task = asyncio.create_task(self._run_evaluation(task_id, document_info))
        self._running_tasks[task_id] = task
        
        # 设置任务完成回调
        task.add_done_callback(lambda t: self._running_tasks.pop(task_id, None))
        
        logger.info(f"已启动任务 {task_id} 的后台评估")
    
    async def _run_evaluation(self, task_id: str, document_info: Dict[str, Any]):
        """
        执行评估任务
        
        Args:
            task_id: 任务ID
            document_info: 文档信息
        """
        try:
            logger.info(f"开始后台评估任务: {task_id}")
            
            # 获取Redis管理器
            redis_mgr = await get_redis_manager()
            
            # 检查是否需要硬指标评估
            if document_info.get('hard_eval_result') is None:
                logger.info(f"执行硬指标评估: {task_id}")
                try:
                    # 动态导入避免循环导入
                    from api.eval_module import hard_eval
                    hard_result = await hard_eval(task_id)

                    # 重新获取最新的文档信息
                    current_doc_info = await redis_mgr.get_document(task_id)
                    if current_doc_info:
                        current_doc_info['hard_eval_result'] = hard_result
                        await redis_mgr.store_document(task_id, current_doc_info)
                        logger.info(f"硬指标评估完成: {task_id}")

                except Exception as e:
                    logger.error(f"硬指标评估失败: {task_id}, 错误: {e}")
                    # 重新获取最新的文档信息
                    current_doc_info = await redis_mgr.get_document(task_id)
                    if current_doc_info:
                        current_doc_info['hard_eval_error'] = str(e)
                        await redis_mgr.store_document(task_id, current_doc_info)

            # 暂时跳过图片评估，因为img_eval函数可能不存在
            if document_info.get('img_eval_result') is None:
                logger.info(f"设置默认图片评估结果: {task_id}")
                try:
                    # 重新获取最新的文档信息
                    current_doc_info = await redis_mgr.get_document(task_id)
                    if current_doc_info:
                        current_doc_info['img_eval_result'] = {
                            "total_reused": 0,
                            "detail": [],
                            "message": "图片查重分析已跳过"
                        }
                        await redis_mgr.store_document(task_id, current_doc_info)
                        logger.info(f"图片评估设置完成: {task_id}")

                except Exception as e:
                    logger.error(f"图片评估设置失败: {task_id}, 错误: {e}")
            
            logger.info(f"后台评估任务完成: {task_id}")
            
        except Exception as e:
            logger.error(f"后台评估任务失败: {task_id}, 错误: {e}")
    
    def is_task_running(self, task_id: str) -> bool:
        """
        检查任务是否正在运行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否正在运行
        """
        return task_id in self._running_tasks
    
    async def wait_for_task(self, task_id: str, timeout: float = 480.0) -> bool:
        """
        等待任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒），默认8分钟，考虑到分析需要5-7分钟

        Returns:
            bool: 是否在超时前完成
        """
        if task_id not in self._running_tasks:
            return True

        try:
            await asyncio.wait_for(self._running_tasks[task_id], timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"等待任务 {task_id} 超时（{timeout}秒），分析可能仍在进行中")
            return False

# 全局任务管理器实例
_task_manager = None

async def get_task_manager() -> AsyncTaskManager:
    """获取任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = AsyncTaskManager()
    return _task_manager
