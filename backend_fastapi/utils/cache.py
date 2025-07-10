"""
缓存管理工具
提供内存缓存功能，提高系统性能
"""

import time
import threading
from typing import Any, Optional, Dict, Callable
from collections import OrderedDict
from datetime import datetime, timedelta

from ..tools.logger import get_logger

logger = get_logger(__name__)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            max_size: 最大缓存项数量
            default_ttl: 默认过期时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
        
        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，如果不存在或已过期则返回None
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            item = self._cache[key]
            
            # 检查是否过期
            if item['expires_at'] and datetime.now() > item['expires_at']:
                del self._cache[key]
                self._stats['misses'] += 1
                return None
            
            # 移动到末尾（LRU）
            self._cache.move_to_end(key)
            self._stats['hits'] += 1
            
            return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认TTL
        """
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
            
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            
            # 如果键已存在，更新值
            if key in self._cache:
                self._cache[key] = {
                    'value': value,
                    'created_at': datetime.now(),
                    'expires_at': expires_at
                }
                self._cache.move_to_end(key)
            else:
                # 检查是否需要清理空间
                if len(self._cache) >= self.max_size:
                    self._evict_lru()
                
                self._cache[key] = {
                    'value': value,
                    'created_at': datetime.now(),
                    'expires_at': expires_at
                }
            
            self._stats['sets'] += 1
    
    def delete(self, key: str) -> bool:
        """
        删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats['deletes'] += 1
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("缓存已清空")
    
    def _evict_lru(self) -> None:
        """清理最近最少使用的缓存项"""
        if self._cache:
            key, _ = self._cache.popitem(last=False)
            self._stats['evictions'] += 1
            logger.debug(f"清理LRU缓存项: {key}")
    
    def _cleanup_expired(self) -> None:
        """清理过期的缓存项"""
        while True:
            try:
                time.sleep(300)  # 每5分钟清理一次
                
                with self._lock:
                    current_time = datetime.now()
                    expired_keys = []
                    
                    for key, item in self._cache.items():
                        if item['expires_at'] and current_time > item['expires_at']:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        del self._cache[key]
                    
                    if expired_keys:
                        logger.debug(f"清理了{len(expired_keys)}个过期缓存项")
                        
            except Exception as e:
                logger.error(f"缓存清理异常: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'sets': self._stats['sets'],
                'deletes': self._stats['deletes'],
                'evictions': self._stats['evictions']
            }
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取缓存详细信息
        
        Returns:
            Dict[str, Any]: 详细信息
        """
        with self._lock:
            items_info = []
            current_time = datetime.now()
            
            for key, item in self._cache.items():
                age = (current_time - item['created_at']).total_seconds()
                ttl = (item['expires_at'] - current_time).total_seconds() if item['expires_at'] else None
                
                items_info.append({
                    'key': key,
                    'age_seconds': round(age, 2),
                    'ttl_seconds': round(ttl, 2) if ttl else None,
                    'size_bytes': len(str(item['value']))  # 简单的大小估算
                })
            
            return {
                'stats': self.get_stats(),
                'items': items_info
            }

class CacheDecorator:
    """缓存装饰器"""
    
    def __init__(self, cache_manager: CacheManager, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
        """
        初始化缓存装饰器
        
        Args:
            cache_manager: 缓存管理器实例
            ttl: 缓存过期时间
            key_func: 自定义键生成函数
        """
        self.cache_manager = cache_manager
        self.ttl = ttl
        self.key_func = key_func
    
    def __call__(self, func: Callable) -> Callable:
        """装饰器实现"""
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if self.key_func:
                cache_key = self.key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 尝试从缓存获取
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            self.cache_manager.set(cache_key, result, self.ttl)
            
            return result
        
        return wrapper

# 全局缓存管理器实例
cache_manager = CacheManager()

def cached(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        key_func: 自定义键生成函数
        
    Returns:
        装饰器函数
    """
    return CacheDecorator(cache_manager, ttl, key_func)

def cache_key_for_document(document_id: str, operation: str) -> str:
    """
    为文档操作生成缓存键
    
    Args:
        document_id: 文档ID
        operation: 操作类型
        
    Returns:
        str: 缓存键
    """
    return f"doc:{document_id}:{operation}"

def cache_key_for_evaluation(document_id: str, model_name: str) -> str:
    """
    为评估结果生成缓存键
    
    Args:
        document_id: 文档ID
        model_name: 模型名称
        
    Returns:
        str: 缓存键
    """
    return f"eval:{document_id}:{model_name}"
