"""
日志工具模块
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional

from config.log_config import LOG_CONFIG

# 标记是否已经初始化
_is_initialized = False

def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    global _is_initialized
    
    # 确保日志目录存在
    log_dir = Path(LOG_CONFIG['handlers']['file']['filename']).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 只在第一次调用时配置
    if not _is_initialized:
        # 清除所有现有处理器
        root = logging.getLogger()
        if root.handlers:
            root.handlers.clear()
        
        # 配置日志
        logging.config.dictConfig(LOG_CONFIG)
        _is_initialized = True
    
    # 获取日志记录器
    logger = logging.getLogger(name)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return setup_logger(name) 