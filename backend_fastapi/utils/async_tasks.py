"""
异步任务处理模块
用于处理耗时的后台任务，避免API请求超时
"""

import asyncio
import json
import time
import tempfile
import os
from typing import Dict, Any
from tools.logger import get_logger
from utils.redis_client import get_redis_manager
from tools.docx_tools.docx_analysis_functions import (
    get_basic_info as extract_basic_info,
    get_overall_stats as extract_overall_stats,
    get_chapter_stats as extract_chapter_stats,
    get_ref_stats as extract_ref_stats
)

logger = get_logger(__name__)

class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self):
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._task_status_cache: Dict[str, Dict[str, Any]] = {}  # 任务状态缓存
    
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
        task.add_done_callback(lambda _: self._cleanup_task(task_id))
        
        logger.info(f"已启动任务 {task_id} 的后台评估")

    def _cleanup_task(self, task_id: str):
        """清理任务资源"""
        self._running_tasks.pop(task_id, None)
        # 标记任务已完成，更新状态缓存
        self._task_status_cache[task_id] = {
            "progress": 1.0,
            "message": "所有分析评估已完成",
            "timestamp": time.time(),
            "completed": True  # 添加完成标记
        }
        logger.info(f"后台评估任务完成: {task_id}")

    def get_task_status_summary(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态摘要，使用缓存减少Redis查询

        Args:
            task_id: 任务ID

        Returns:
            Dict[str, Any]: 任务状态摘要
        """
        is_running = task_id in self._running_tasks
        cached_status = self._task_status_cache.get(task_id, {})

        # 如果任务已完成，直接返回完成状态
        if cached_status.get("completed", False):
            is_running = False

        return {
            "is_running": is_running,
            "completed": cached_status.get("completed", False),
            "last_known_progress": cached_status.get("progress", 0.0),
            "last_known_message": cached_status.get("message", ""),
            "cache_timestamp": cached_status.get("timestamp", 0)
        }

    def _update_status_cache(self, task_id: str, progress: float, message: str):
        """更新状态缓存"""
        import time
        self._task_status_cache[task_id] = {
            "progress": progress,
            "message": message,
            "timestamp": time.time()
        }

    async def _run_evaluation(self, task_id: str, document_info: Dict[str, Any]):
        """
        执行评估任务 - 优化版本，使用并行处理并统一状态更新

        Args:
            task_id: 任务ID
            document_info: 文档信息
        """
        try:
            logger.info(f"开始后台评估任务: {task_id}")

            # 获取Redis管理器
            redis_mgr = await get_redis_manager()

            # 准备同步执行的评估任务列表
            evaluation_tasks = []

            # 检查需要执行的评估任务
            if document_info.get('hard_eval_result') is None:
                evaluation_tasks.append(('硬指标评估', self._run_hard_eval))

            if document_info.get('soft_eval_result') is None:
                evaluation_tasks.append(('软指标评估', self._run_soft_eval))

            if document_info.get('img_eval_result') is None:
                evaluation_tasks.append(('图片评估', self._run_img_eval))

            if document_info.get('ref_eval_result') is None:
                evaluation_tasks.append(('参考文献评估', self._run_ref_eval))
            
            # 新增：文档分析任务
            if document_info.get('basic_info_result') is None:
                evaluation_tasks.append(('基础信息提取', self._run_basic_info_extraction))
            if document_info.get('overall_stats_result') is None:
                evaluation_tasks.append(('整体统计提取', self._run_overall_stats_extraction))
            if document_info.get('chapter_stats_result') is None:
                evaluation_tasks.append(('章节统计提取', self._run_chapter_stats_extraction))
            if document_info.get('ref_stats_result') is None:
                evaluation_tasks.append(('参考文献统计提取', self._run_ref_stats_extraction))

            if not evaluation_tasks:
                logger.info(f"所有评估任务已完成: {task_id}")
                return

            logger.info(f"开始同步执行 {len(evaluation_tasks)} 个评估任务: { ', '.join([name for name, _ in evaluation_tasks])}")

            # 收集所有结果
            evaluation_results = {}
            evaluation_errors = {}

            # 同步执行每个评估任务（外层同步，内层多线程）
            total_tasks = len(evaluation_tasks)
            for i, (task_name, task_func) in enumerate(evaluation_tasks):
                try:
                    # 更新进度状态
                    # 总共有8个任务：hard, soft, img, ref, basic, overall, chapter, ref_stats
                    progress = 0.6 + (i / 8) * 0.4  # 60%-100%的进度用于评估
                    self._update_status_cache(task_id, progress, f"正在执行{task_name}...")

                    logger.info(f"开始执行{task_name}: {task_id}")

                    # 执行单个评估任务（内部可能包含多线程处理）
                    if task_name in ['硬指标评估', '软指标评估', '图片评估', '参考文献评估']:
                        result = await task_func(task_id)
                    elif task_name in ['基础信息提取', '整体统计提取', '章节统计提取', '参考文献统计提取']:
                        result = await task_func(task_id, document_info['content']) # 传递docx_data
                    else:
                        result = None # Should not happen

                    logger.info(f"{task_name}完成: {task_id}")

                    # 存储结果
                    if task_name == '硬指标评估':
                        evaluation_results['hard_eval_result'] = result
                    elif task_name == '软指标评估':
                        evaluation_results['soft_eval_result'] = result
                    elif task_name == '图片评估':
                        evaluation_results['img_eval_result'] = result
                    elif task_name == '参考文献评估':
                        evaluation_results['ref_eval_result'] = result
                    elif task_name == '基础信息提取':
                        evaluation_results['basic_info_result'] = result
                    elif task_name == '整体统计提取':
                        evaluation_results['overall_stats_result'] = result
                    elif task_name == '章节统计提取':
                        evaluation_results['chapter_stats_result'] = result
                    elif task_name == '参考文献统计提取':
                        evaluation_results['ref_stats_result'] = result

                except Exception as e:
                    logger.error(f"{task_name}失败: {task_id}, 错误: {e}")
                    if task_name == '硬指标评估':
                        evaluation_errors['hard_eval_error'] = str(e)
                    elif task_name == '软指标评估':
                        evaluation_errors['soft_eval_error'] = str(e)
                    elif task_name == '图片评估':
                        evaluation_errors['img_eval_error'] = str(e)
                    elif task_name == '参考文献评估':
                        evaluation_errors['ref_eval_error'] = str(e)
                    elif task_name == '基础信息提取':
                        evaluation_errors['basic_info_error'] = str(e)
                    elif task_name == '整体统计提取':
                        evaluation_errors['overall_stats_error'] = str(e)
                    elif task_name == '章节统计提取':
                        evaluation_errors['chapter_stats_error'] = str(e)
                    elif task_name == '参考文献统计提取':
                        evaluation_errors['ref_stats_error'] = str(e)

            # 统一更新文档状态 - 只进行一次Redis写入
            try:
                current_doc_info = await redis_mgr.get_document(task_id)
                if current_doc_info:
                    # 更新评估结果
                    current_doc_info.update(evaluation_results)
                    current_doc_info.update(evaluation_errors)

                    # 检查是否所有评估都完成
                    hard_completed = current_doc_info.get('hard_eval_result') is not None
                    soft_completed = current_doc_info.get('soft_eval_result') is not None
                    img_completed = current_doc_info.get('img_eval_result') is not None
                    ref_completed = current_doc_info.get('ref_eval_result') is not None
                    basic_info_completed = current_doc_info.get('basic_info_result') is not None
                    overall_stats_completed = current_doc_info.get('overall_stats_result') is not None
                    chapter_stats_completed = current_doc_info.get('chapter_stats_result') is not None
                    ref_stats_completed = current_doc_info.get('ref_stats_result') is not None

                    if (hard_completed and soft_completed and img_completed and ref_completed and
                        basic_info_completed and overall_stats_completed and chapter_stats_completed and ref_stats_completed):
                        current_doc_info['progress'] = 1.0
                        current_doc_info['message'] = '所有分析评估已完成'
                        current_doc_info['status'] = 'completed'
                        self._update_status_cache(task_id, 1.0, '所有分析评估已完成')



                        # 记录评估完成的特殊日志
                        logger.info(f"=== 评估任务完成 === {task_id} - 硬指标、软指标、图片、参考文献、基础信息、整体统计、章节统计、参考文献统计评估全部完成")
                    else:
                        # 计算进度（总共8个任务）
                        completed_count = sum([hard_completed, soft_completed, img_completed, ref_completed,
                                               basic_info_completed, overall_stats_completed,
                                               chapter_stats_completed, ref_stats_completed])
                        progress = 0.6 + (completed_count / 8) * 0.4  # 从60%开始到100%
                        message = f'评估进行中... ({completed_count}/8 完成)'
                        current_doc_info['progress'] = progress
                        current_doc_info['message'] = message
                        self._update_status_cache(task_id, progress, message)

                    # 一次性写入所有更新
                    await redis_mgr.store_document(task_id, current_doc_info)
                    logger.info(f"评估状态已统一更新: {task_id}, 进度: {current_doc_info.get('progress', 0):.1%}")

            except Exception as e:
                logger.error(f"更新文档状态失败: {task_id}, 错误: {e}")

            logger.info(f"后台评估任务完成: {task_id}")

        except Exception as e:
            logger.error(f"后台评估任务失败: {task_id}, 错误: {e}")
            # 更新错误状态
            try:
                redis_mgr = await get_redis_manager()
                current_doc_info = await redis_mgr.get_document(task_id)
                if current_doc_info:
                    current_doc_info['status'] = 'failed'  # 将文档状态设置为失败
                    current_doc_info['message'] = f'评估任务失败: {str(e)}'
                    current_doc_info['evaluation_error'] = str(e)
                    await redis_mgr.store_document(task_id, current_doc_info)
            except Exception as update_error:
                logger.error(f"更新错误状态失败: {task_id}, 错误: {update_error}")

    async def _run_hard_eval(self, task_id: str):
        """执行硬指标评估 - 不更新Redis状态"""
        logger.info(f"开始硬指标评估: {task_id}")

        # 调用评估函数，但跳过Redis缓存存储（由AsyncTaskManager统一管理）
        from api.eval_module import hard_eval
        result = await hard_eval(task_id, store_to_redis=False)

        logger.info(f"硬指标评估完成: {task_id}")
        return result

    async def _run_soft_eval(self, task_id: str):
        """执行软指标评估 - 不更新Redis状态"""
        logger.info(f"开始软指标评估: {task_id}")

        from api.eval_module import soft_eval
        result = await soft_eval(task_id, store_to_redis=False)

        logger.info(f"软指标评估完成: {task_id}")
        return result

    async def _run_img_eval(self, task_id: str):
        """执行图片评估 - 不更新Redis状态"""
        logger.info(f"开始图片评估: {task_id}")

        from api.eval_module import img_eval
        result = await img_eval(task_id, store_to_redis=False)

        logger.info(f"图片评估完成: {task_id}")
        return result

    async def _run_ref_eval(self, task_id: str):
        """执行参考文献评估 - 不更新Redis状态"""
        logger.info(f"开始参考文献评估: {task_id}")

        from api.eval_module import ref_eval
        result = await ref_eval(task_id, store_to_redis=False)

        logger.info(f"参考文献评估完成: {task_id}")
        return result

    async def _run_basic_info_extraction(self, task_id: str, docx_data: bytes):
        """执行基础信息提取 - 不更新Redis状态"""
        logger.info(f"开始提取基础信息: {task_id}")
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                await asyncio.to_thread(temp_file.write, docx_data)
                temp_file_path = temp_file.name
            
            basic_info = await asyncio.to_thread(extract_basic_info, temp_file_path)
            logger.info(f"基础信息提取完成: {task_id}")
            return basic_info
        finally:
            if temp_file_path and await asyncio.to_thread(os.path.exists, temp_file_path):
                await asyncio.to_thread(os.unlink, temp_file_path)

    async def _run_overall_stats_extraction(self, task_id: str, docx_data: bytes):
        """执行整体统计提取 - 不更新Redis状态"""
        logger.info(f"开始提取整体统计: {task_id}")
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                await asyncio.to_thread(temp_file.write, docx_data)
                temp_file_path = temp_file.name
            
            overall_stats = await asyncio.to_thread(extract_overall_stats, temp_file_path)
            logger.info(f"整体统计提取完成: {task_id}")
            return overall_stats
        finally:
            if temp_file_path and await asyncio.to_thread(os.path.exists, temp_file_path):
                await asyncio.to_thread(os.unlink, temp_file_path)

    async def _run_chapter_stats_extraction(self, task_id: str, docx_data: bytes):
        """执行章节统计提取 - 不更新Redis状态"""
        logger.info(f"开始提取章节统计: {task_id}")
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                await asyncio.to_thread(temp_file.write, docx_data)
                temp_file_path = temp_file.name
            
            chapter_stats = await asyncio.to_thread(extract_chapter_stats, temp_file_path)
            logger.info(f"章节统计提取完成: {task_id}")
            return chapter_stats
        finally:
            if temp_file_path and await asyncio.to_thread(os.path.exists, temp_file_path):
                await asyncio.to_thread(os.unlink, temp_file_path)

    async def _run_ref_stats_extraction(self, task_id: str, docx_data: bytes):
        """执行参考文献统计提取 - 不更新Redis状态"""
        logger.info(f"开始提取参考文献统计: {task_id}")
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                await asyncio.to_thread(temp_file.write, docx_data)
                temp_file_path = temp_file.name
            
            ref_stats = await asyncio.to_thread(extract_ref_stats, temp_file_path)
            logger.info(f"参考文献统计提取完成: {task_id}")
            return ref_stats
        finally:
            if temp_file_path and await asyncio.to_thread(os.path.exists, temp_file_path):
                await asyncio.to_thread(os.unlink, temp_file_path)

    
    def is_task_running(self, task_id: str) -> bool:
        """
        检查任务是否正在运行

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否正在运行
        """
        # 检查任务是否在运行队列中
        is_running = task_id in self._running_tasks

        # 如果任务已标记为完成，则返回False
        cached_status = self._task_status_cache.get(task_id, {})
        if cached_status.get("completed", False):
            return False

        return is_running
    
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
