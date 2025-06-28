"""
Logger setup for frontend components
"""

import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 获取项目根目录
project_root = Path(__file__).parent.parent.parent
logs_dir = project_root / "logs"

# 确保logs目录存在
logs_dir.mkdir(parents=True, exist_ok=True)
log_file = logs_dir / "frontend.log"

# 配置日志格式
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', 
                                 datefmt='%Y-%m-%d %H:%M:%S')

# 创建文件处理器
file_handler = RotatingFileHandler(
    filename=str(log_file),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# 创建frontend日志记录器
logger = logging.getLogger('frontend')

def get_module_logger(name):
    """
    为指定模块获取一个日志记录器
    
    Args:
        name: 模块名称，通常使用__name__
        
    Returns:
        一个配置好的日志记录器
    """
    if name.startswith('__'):
        # 如果是直接执行的脚本
        return logging.getLogger(f'frontend.{Path(name).stem}')
    return logging.getLogger(name) 