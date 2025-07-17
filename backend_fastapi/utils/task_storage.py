"""
任务存储管理器 - 基于Redis
提供任务状态的持久化存储功能
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis.asyncio as aioredis

from pathlib import Path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.redis_config import REDIS_CONFIG, REDIS_POOL_CONFIG
from tools.logger import get_logger

logger = get_logger(__name__)

class TaskStorage:
    """基于Redis的任务存储管理器"""
    
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._connected = False
        self._key_prefix = "paper_eval:task:"
        self._task_list_key = "paper_eval:task_list"
    
    async def connect(self) -> bool:
        """连接到Redis服务器"""
        try:
            self._client = aioredis.Redis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'],
                password=REDIS_CONFIG['password'],
                socket_timeout=REDIS_CONFIG['socket_timeout'],
                socket_connect_timeout=REDIS_CONFIG['socket_connect_timeout'],
                retry_on_timeout=REDIS_CONFIG['retry_on_timeout'],
                health_check_interval=REDIS_CONFIG['health_check_interval'],
                max_connections=REDIS_POOL_CONFIG['max_connections'],
                encoding=REDIS_POOL_CONFIG['encoding'],
                decode_responses=True,
            )
            
            await self._client.ping()
            self._connected = True
            logger.info("任务存储Redis连接成功")
            return True
            
        except Exception as e:
            logger.warning(f"任务存储Redis连接失败: {e}")
            logger.info("系统将在没有Redis任务缓存的情况下运行")
            self._connected = False
            self._client = None
            return False
    
    async def disconnect(self):
        """断开Redis连接"""
        if self._client:
            await self._client.close()
        self._connected = False
        logger.info("任务存储Redis连接已断开")
    
    def is_connected(self) -> bool:
        """检查Redis连接状态"""
        return self._connected
    
    def _get_task_key(self, task_id: str) -> str:
        """获取任务在Redis中的键名"""
        return f"{self._key_prefix}{task_id}"
    
    async def _ensure_connected(self):
        """确保Redis连接可用"""
        if not self._connected or self._client is None:
            await self.connect()
        if not self._connected:
            logger.warning("Redis不可用，任务信息将不会被缓存")
            return False
        return True
    
    async def set_task(self, task_id: str, task_info: Dict[str, Any]) -> bool:
        """
        设置任务信息
        
        Args:
            task_id: 任务ID
            task_info: 任务信息字典
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if not await self._ensure_connected():
                logger.warning(f"Redis不可用，无法缓存任务信息: {task_id}")
                return False

            # 序列化任务信息
            task_data = json.dumps(task_info, ensure_ascii=False, default=str)

            # 存储任务数据
            task_key = self._get_task_key(task_id)
            await self._client.set(task_key, task_data)  # type: ignore

            # 添加到任务列表
            await self._client.sadd(self._task_list_key, task_id)  # type: ignore

            logger.debug(f"任务信息设置成功: {task_id}")
            return True

        except Exception as e:
            logger.warning(f"设置任务信息失败: {task_id}, 错误: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务信息，不存在返回None
        """
        try:
            await self._ensure_connected()
            
            task_key = self._get_task_key(task_id)
            task_data = await self._client.get(task_key)  # type: ignore
            
            if task_data is None:
                return None
            
            return json.loads(task_data)
            
        except Exception as e:
            logger.error(f"获取任务信息失败: {task_id}, 错误: {e}")
            return None
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新任务信息
        
        Args:
            task_id: 任务ID
            updates: 要更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            await self._ensure_connected()
            
            # 获取现有任务信息
            task_info = await self.get_task(task_id)
            if task_info is None:
                logger.warning(f"任务不存在，无法更新: {task_id}")
                return False
            
            # 更新字段
            task_info.update(updates)
            
            # 保存更新后的任务信息
            return await self.set_task(task_id, task_info)
            
        except Exception as e:
            logger.error(f"更新任务信息失败: {task_id}, 错误: {e}")
            return False
    
    async def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            await self._ensure_connected()
            
            task_key = self._get_task_key(task_id)
            
            # 删除任务数据
            result = await self._client.delete(task_key)  # type: ignore
            
            # 从任务列表中移除
            await self._client.srem(self._task_list_key, task_id)  # type: ignore
            
            if result > 0:
                logger.info(f"任务删除成功: {task_id}")
                return True
            else:
                logger.warning(f"任务不存在: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"删除任务失败: {task_id}, 错误: {e}")
            return False
    
    async def task_exists(self, task_id: str) -> bool:
        """
        检查任务是否存在
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 任务是否存在
        """
        try:
            await self._ensure_connected()
            
            task_key = self._get_task_key(task_id)
            result = await self._client.exists(task_key)  # type: ignore
            return bool(result)
            
        except Exception as e:
            logger.error(f"检查任务存在性失败: {task_id}, 错误: {e}")
            return False
    
    async def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有任务
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有任务的字典
        """
        try:
            await self._ensure_connected()
            
            # 获取所有任务ID
            task_ids = await self._client.smembers(self._task_list_key)  # type: ignore
            
            tasks = {}
            for task_id in task_ids:
                task_info = await self.get_task(task_id)
                if task_info is not None:
                    tasks[task_id] = task_info
                else:
                    # 清理无效的任务ID
                    await self._client.srem(self._task_list_key, task_id)  # type: ignore
            
            return tasks
            
        except Exception as e:
            logger.error(f"获取所有任务失败: {e}")
            return {}
    
    async def get_task_count(self) -> int:
        """
        获取任务总数
        
        Returns:
            int: 任务总数
        """
        try:
            await self._ensure_connected()
            return await self._client.scard(self._task_list_key)  # type: ignore
        except Exception as e:
            logger.error(f"获取任务总数失败: {e}")
            return 0
    
    async def clear_completed_tasks(self) -> int:
        """
        清理已完成的任务
        
        Returns:
            int: 清理的任务数量
        """
        try:
            await self._ensure_connected()
            
            completed_statuses = ['completed', 'failed', 'cancelled']
            tasks = await self.get_all_tasks()
            
            cleared_count = 0
            for task_id, task_info in tasks.items():
                if task_info.get('status') in completed_statuses:
                    if await self.delete_task(task_id):
                        cleared_count += 1
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"清理已完成任务失败: {e}")
            return 0
    
    async def clear_old_tasks(self, days: int) -> int:
        """
        清理旧任务
        
        Args:
            days: 清理多少天前的任务
            
        Returns:
            int: 清理的任务数量
        """
        try:
            from datetime import timedelta
            
            await self._ensure_connected()
            
            cutoff_time = datetime.now() - timedelta(days=days)
            tasks = await self.get_all_tasks()
            
            cleared_count = 0
            for task_id, task_info in tasks.items():
                created_at = task_info.get('created_at')
                if created_at:
                    try:
                        created_time = datetime.fromisoformat(created_at)
                        if created_time < cutoff_time:
                            if await self.delete_task(task_id):
                                cleared_count += 1
                    except ValueError:
                        # 时间格式有问题，也删除
                        if await self.delete_task(task_id):
                            cleared_count += 1
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"清理旧任务失败: {e}")
            return 0

# 全局任务存储实例
_task_storage_instance: Optional[TaskStorage] = None

async def get_task_storage() -> TaskStorage:
    """
    获取任务存储实例
    如果未连接则自动连接
    """
    global _task_storage_instance
    
    if _task_storage_instance is None:
        _task_storage_instance = TaskStorage()
    
    if not _task_storage_instance.is_connected():
        await _task_storage_instance.connect()
    
    return _task_storage_instance

# 兼容性接口 - 模拟字典操作
class TaskStorageDict:
    """
    任务存储字典接口
    提供类似字典的同步操作接口，内部使用Redis异步存储
    """
    
    def __init__(self):
        self._storage: Optional[TaskStorage] = None
    
    async def _get_storage(self) -> TaskStorage:
        """获取存储实例"""
        if self._storage is None:
            self._storage = await get_task_storage()
        return self._storage
    
    def __getitem__(self, task_id: str) -> Dict[str, Any]:
        """同步获取任务（不推荐使用）"""
        try:
            loop = asyncio.get_event_loop()
            storage = loop.run_until_complete(self._get_storage())
            result = loop.run_until_complete(storage.get_task(task_id))
            if result is None:
                raise KeyError(f"任务不存在: {task_id}")
            return result
        except Exception as e:
            logger.error(f"同步获取任务失败: {task_id}, 错误: {e}")
            raise KeyError(f"任务不存在: {task_id}")
    
    def __setitem__(self, task_id: str, task_info: Dict[str, Any]):
        """同步设置任务（不推荐使用）"""
        try:
            loop = asyncio.get_event_loop()
            storage = loop.run_until_complete(self._get_storage())
            loop.run_until_complete(storage.set_task(task_id, task_info))
        except Exception as e:
            logger.error(f"同步设置任务失败: {task_id}, 错误: {e}")
            raise
    
    def __contains__(self, task_id: str) -> bool:
        """检查任务是否存在"""
        try:
            loop = asyncio.get_event_loop()
            storage = loop.run_until_complete(self._get_storage())
            return loop.run_until_complete(storage.task_exists(task_id))
        except Exception as e:
            logger.error(f"检查任务存在性失败: {task_id}, 错误: {e}")
            return False
    
    def __delitem__(self, task_id: str):
        """删除任务"""
        try:
            loop = asyncio.get_event_loop()
            storage = loop.run_until_complete(self._get_storage())
            success = loop.run_until_complete(storage.delete_task(task_id))
            if not success:
                raise KeyError(f"任务不存在: {task_id}")
        except Exception as e:
            logger.error(f"删除任务失败: {task_id}, 错误: {e}")
            raise
    
    def get(self, task_id: str, default: Any = None) -> Any:
        """获取任务，如果不存在返回默认值"""
        try:
            return self[task_id]
        except KeyError:
            return default
    
    def items(self):
        """获取所有任务项（不推荐大量数据使用）"""
        try:
            loop = asyncio.get_event_loop()
            storage = loop.run_until_complete(self._get_storage())
            tasks = loop.run_until_complete(storage.get_all_tasks())
            return tasks.items()
        except Exception as e:
            logger.error(f"获取所有任务项失败: {e}")
            return []
    
    def values(self):
        """获取所有任务值（不推荐大量数据使用）"""
        try:
            loop = asyncio.get_event_loop()
            storage = loop.run_until_complete(self._get_storage())
            tasks = loop.run_until_complete(storage.get_all_tasks())
            return tasks.values()
        except Exception as e:
            logger.error(f"获取所有任务值失败: {e}")
            return []
    
    def keys(self):
        """获取所有任务键（不推荐大量数据使用）"""
        try:
            loop = asyncio.get_event_loop()
            storage = loop.run_until_complete(self._get_storage())
            tasks = loop.run_until_complete(storage.get_all_tasks())
            return tasks.keys()
        except Exception as e:
            logger.error(f"获取所有任务键失败: {e}")
            return []
    
    def __len__(self) -> int:
        """获取任务总数"""
        try:
            loop = asyncio.get_event_loop()
            storage = loop.run_until_complete(self._get_storage())
            return loop.run_until_complete(storage.get_task_count())
        except Exception as e:
            logger.error(f"获取任务总数失败: {e}")
            return 0

# 创建全局兼容性实例
task_storage = TaskStorageDict()
