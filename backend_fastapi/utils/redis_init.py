"""
Redis连接生命周期管理
负责应用启动时连接Redis，关闭时断开连接
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from utils.redis_client import redis_manager
from config.redis_config import validate_redis_config

logger = logging.getLogger(__name__)

@asynccontextmanager
async def redis_lifespan(app: FastAPI):
    """
    FastAPI应用生命周期管理
    自动处理Redis连接的启动和关闭
    """
    # 应用启动时
    logger.info("正在初始化Redis连接...")
    
    # 验证配置
    is_valid, error_msg = validate_redis_config()
    if not is_valid:
        logger.error(f"Redis配置无效: {error_msg}")
        logger.warning("将在没有Redis的情况下运行")
    else:
        # 尝试连接
        if await redis_manager.connect():
            logger.info("Redis连接初始化成功")
        else:
            logger.warning("Redis连接失败，功能受限")
    
    try:
        yield  # 应用运行期间
    finally:
        # 应用关闭时
        logger.info("正在关闭Redis连接...")
        await redis_manager.disconnect()
        logger.info("Redis连接已关闭")

async def check_redis_health() -> dict:
    """
    检查Redis健康状态
    用于健康检查接口
    
    Returns:
        dict: Redis状态信息
    """
    try:
        if redis_manager.is_connected():
            return {
                'status': 'healthy',
                'connected': True,
                'message': 'Redis连接正常'
            }
        else:
            return {
                'status': 'disconnected',
                'connected': False,
                'message': 'Redis未连接'
            }
    except Exception as e:
        return {
            'status': 'error',
            'connected': False,
            'message': f'Redis检查失败: {e}'
        }
