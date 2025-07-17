"""
健康检查API路由
提供系统健康状态检查功能
"""

import os
import psutil
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.model_manager import model_manager
from config.app_config import APP_CONFIG
from tools.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: str
    version: str
    uptime: float
    system: Dict[str, Any]
    models: Dict[str, Any]

# 应用启动时间
app_start_time = datetime.now()

# 这个路由已经在main.py中定义，这里删除避免重复

@router.get("/models")
async def check_models():
    """
    检查模型状态
    
    Returns:
        dict: 模型状态信息
    """
    try:
        model_status = model_manager.get_model_status()
        available_models = model_manager.get_available_models()
        
        return {
            'success': True,
            'available_models': available_models,
            'model_status': model_status,
            'total_models': len(model_status),
            'available_count': sum(1 for status in model_status.values() if status.get('available', False))
        }
        
    except Exception as e:
        logger.error(f"模型状态检查失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.get("/system")
async def system_info():
    """
    获取系统信息
    
    Returns:
        dict: 系统信息
    """
    try:
        return {
            'success': True,
            'system': {
                'platform': psutil.sys.platform,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_total': psutil.disk_usage('/').total,
                'disk_free': psutil.disk_usage('/').free,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            },
            'app': {
                'version': APP_CONFIG['version'],
                'environment': APP_CONFIG['environment'],
                'debug': APP_CONFIG['debug'],
                'start_time': app_start_time.isoformat(),
                'uptime': (datetime.now() - app_start_time).total_seconds()
            }
        }
        
    except Exception as e:
        logger.error(f"系统信息获取失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }
