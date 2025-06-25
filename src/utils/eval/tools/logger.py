"""
日志工具模块
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional

from utils.eval.config import LOG_CONFIG

def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    log_dir = Path(LOG_CONFIG['handlers']['file']['filename']).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志
    logging.config.dictConfig(LOG_CONFIG)
    
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