"""
性能监控和优化工具
提供系统性能监控、内存管理、并发控制等功能
"""



import time
import psutil
import asyncio
import threading
import os
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from tools.logger import get_logger

logger = get_logger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        """
        初始化性能监控器
        
        Args:
            max_history: 最大历史记录数量
        """
        self.max_history = max_history
        self.request_times = deque(maxlen=max_history)
        self.api_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': 0
        })
        self.system_stats = deque(maxlen=max_history)
        self.start_time = datetime.now()
        self._lock = threading.Lock()
        
        # 启动系统监控
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self._monitor_thread.start()
    
    def record_request(self, endpoint: str, duration: float, success: bool = True):
        """
        记录请求性能数据
        
        Args:
            endpoint: API端点
            duration: 请求持续时间（秒）
            success: 请求是否成功
        """
        with self._lock:
            # 记录总体请求时间
            self.request_times.append({
                'timestamp': datetime.now(),
                'endpoint': endpoint,
                'duration': duration,
                'success': success
            })
            
            # 更新API统计
            stats = self.api_stats[endpoint]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            
            if not success:
                stats['errors'] += 1
    
    def _monitor_system(self):
        """系统资源监控线程"""
        while self._monitoring:
            try:
                # 获取系统资源使用情况
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                # 跨平台磁盘使用情况获取
                try:
                    if os.name == 'nt':  # Windows
                        disk = psutil.disk_usage('C:\\')
                    else:  # Unix/Linux/macOS
                        disk = psutil.disk_usage('/')
                except (OSError, FileNotFoundError):
                    # 如果无法获取磁盘信息，使用默认值
                    disk = type('DiskUsage', (), {
                        'percent': 0,
                        'used': 0,
                        'total': 0
                    })()

                system_info = {
                    'timestamp': datetime.now(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used': memory.used,
                    'memory_total': memory.total,
                    'disk_percent': disk.percent,
                    'disk_used': disk.used,
                    'disk_total': disk.total
                }

                with self._lock:
                    self.system_stats.append(system_info)

                time.sleep(10)  # 每10秒监控一次

            except Exception as e:
                # 屏蔽特定的格式化错误
                error_msg = str(e)
                if "impossible<bad format char>" not in error_msg:
                    logger.error("系统监控错误: %s", error_msg)
                time.sleep(30)  # 出错时等待更长时间
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        with self._lock:
            current_time = datetime.now()
            uptime = (current_time - self.start_time).total_seconds()
            
            # 计算最近的请求统计
            recent_requests = [
                req for req in self.request_times
                if (current_time - req['timestamp']).total_seconds() <= 300  # 最近5分钟
            ]
            
            # 计算请求速率
            request_rate = len(recent_requests) / 300 if recent_requests else 0
            
            # 计算成功率
            successful_requests = sum(1 for req in recent_requests if req['success'])
            success_rate = (successful_requests / len(recent_requests) * 100) if recent_requests else 100
            
            # 获取最新的系统状态
            latest_system = self.system_stats[-1] if self.system_stats else {}
            
            return {
                'uptime_seconds': uptime,
                'total_requests': len(self.request_times),
                'recent_request_rate': round(request_rate, 2),
                'success_rate': round(success_rate, 2),
                'api_stats': dict(self.api_stats),
                'system_stats': {
                    'cpu_percent': latest_system.get('cpu_percent', 0),
                    'memory_percent': latest_system.get('memory_percent', 0),
                    'disk_percent': latest_system.get('disk_percent', 0)
                },
                'timestamp': current_time.isoformat()
            }
    
    def get_slow_endpoints(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """
        获取响应时间较慢的端点
        
        Args:
            threshold: 响应时间阈值（秒）
            
        Returns:
            List[Dict[str, Any]]: 慢端点列表
        """
        slow_endpoints = []
        
        with self._lock:
            for endpoint, stats in self.api_stats.items():
                if stats['avg_time'] > threshold:
                    slow_endpoints.append({
                        'endpoint': endpoint,
                        'avg_time': round(stats['avg_time'], 3),
                        'max_time': round(stats['max_time'], 3),
                        'count': stats['count'],
                        'error_rate': round(stats['errors'] / stats['count'] * 100, 2) if stats['count'] > 0 else 0
                    })
        
        # 按平均响应时间排序
        slow_endpoints.sort(key=lambda x: x['avg_time'], reverse=True)
        return slow_endpoints
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        获取系统健康状态
        
        Returns:
            Dict[str, Any]: 系统健康信息
        """
        with self._lock:
            if not self.system_stats:
                return {'status': 'unknown', 'message': '暂无系统数据'}
            
            latest = self.system_stats[-1]
            
            # 判断系统健康状态
            cpu_healthy = latest['cpu_percent'] < 80
            memory_healthy = latest['memory_percent'] < 85
            disk_healthy = latest['disk_percent'] < 90
            
            if cpu_healthy and memory_healthy and disk_healthy:
                status = 'healthy'
                message = '系统运行正常'
            elif latest['cpu_percent'] > 90 or latest['memory_percent'] > 95:
                status = 'critical'
                message = '系统资源严重不足'
            else:
                status = 'warning'
                message = '系统资源使用率较高'
            
            return {
                'status': status,
                'message': message,
                'cpu_percent': latest['cpu_percent'],
                'memory_percent': latest['memory_percent'],
                'disk_percent': latest['disk_percent'],
                'timestamp': latest['timestamp'].isoformat()
            }
    
    def cleanup_old_data(self, hours: int = 24):
        """
        清理旧的监控数据
        
        Args:
            hours: 保留数据的小时数
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            # 清理请求数据
            self.request_times = deque(
                [req for req in self.request_times if req['timestamp'] > cutoff_time],
                maxlen=self.max_history
            )
            
            # 清理系统数据
            self.system_stats = deque(
                [stat for stat in self.system_stats if stat['timestamp'] > cutoff_time],
                maxlen=self.max_history
            )
        
        logger.info(f"清理了{hours}小时前的监控数据")
    
    def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

class RequestTimer:
    """请求计时器上下文管理器"""
    
    def __init__(self, monitor: PerformanceMonitor, endpoint: str):
        """
        初始化请求计时器
        
        Args:
            monitor: 性能监控器实例
            endpoint: API端点名称
        """
        self.monitor = monitor
        self.endpoint = endpoint
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        """进入上下文"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.start_time:
            duration = time.time() - self.start_time
            self.success = exc_type is None
            self.monitor.record_request(self.endpoint, duration, self.success)
    
    def mark_error(self):
        """标记请求为错误"""
        self.success = False

# 全局性能监控器实例
performance_monitor = PerformanceMonitor()

def monitor_performance(endpoint: str):
    """
    性能监控装饰器
    
    Args:
        endpoint: API端点名称
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                with RequestTimer(performance_monitor, endpoint) as timer:
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        timer.mark_error()
                        raise
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with RequestTimer(performance_monitor, endpoint) as timer:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        timer.mark_error()
                        raise
            return sync_wrapper
    return decorator
