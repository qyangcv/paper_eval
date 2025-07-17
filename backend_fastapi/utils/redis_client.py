"""
Redis客户端管理器
提供文档存储的核心操作：存储、获取、删除文档
"""

import json
import base64
import logging
from typing import Any, Dict, Optional, Union

# 导入Redis异步库
try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis as AsyncRedis
except ImportError:
    # 兼容旧版本的导入方式
    import aioredis
    AsyncRedis = aioredis.Redis

from pathlib import Path
import sys
# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.redis_config import REDIS_CONFIG, REDIS_POOL_CONFIG, DOCUMENT_REDIS_CONFIG

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis文档存储管理器"""
    
    def __init__(self):
        self._client: Optional[AsyncRedis] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """连接到Redis服务器"""
        try:
            # 创建Redis异步客户端
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
                decode_responses=False,  # 处理二进制数据时设为False
            )

            # 测试连接
            await self._client.ping()
            self._connected = True
            logger.info("Redis连接成功")
            return True

        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            logger.info("系统将在没有Redis缓存的情况下运行")
            self._connected = False
            self._client = None
            return False
    
    async def disconnect(self):
        """断开Redis连接"""
        if self._client:
            await self._client.close()
        self._connected = False
        logger.info("Redis连接已断开")
    
    def is_connected(self) -> bool:
        """检查Redis连接状态"""
        return self._connected
    
    def _get_document_key(self, document_id: str) -> str:
        """生成文档在Redis中的键名"""
        return f"{DOCUMENT_REDIS_CONFIG['key_prefix']}{document_id}"
    
    async def store_document(self, document_id: str, document_data: Dict[str, Any]) -> bool:
        """
        存储文档到Redis

        Args:
            document_id: 文档唯一ID
            document_data: 文档数据字典

        Returns:
            bool: 存储是否成功
        """
        # 检查Redis连接状态
        if not self._connected or not self._client:
            logger.warning("Redis未连接，无法缓存文档")
            return False

        try:
            # 再次检查客户端是否有效
            if self._client is None:
                logger.warning("Redis客户端为空，无法缓存文档")
                self._connected = False
                return False

            # 处理二进制数据转换
            processed_data = self._encode_binary_data(document_data)

            # 序列化为JSON
            serialized_data = json.dumps(processed_data, ensure_ascii=False)

            # 检查数据大小限制
            data_size = len(serialized_data.encode('utf-8'))
            if data_size > DOCUMENT_REDIS_CONFIG['max_content_size']:
                logger.error(f"文档过大: {data_size} > {DOCUMENT_REDIS_CONFIG['max_content_size']}")
                return False

            # 存储到Redis并设置过期时间
            key = self._get_document_key(document_id)
            await self._client.setex(
                key,
                DOCUMENT_REDIS_CONFIG['expire_time'],
                serialized_data
            )

            logger.info(f"文档存储成功: {document_id}, 大小: {data_size} bytes")
            return True

        except Exception as e:
            logger.error(f"文档存储失败: {document_id}, 错误: {e}")
            # 如果是连接相关错误，标记为未连接
            if "connection" in str(e).lower() or "_add_writer" in str(e):
                self._connected = False
                self._client = None
            return False
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        从Redis获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            Optional[Dict[str, Any]]: 文档数据，不存在返回None
        """
        if not self._connected or not self._client:
            logger.warning("Redis未连接，无法从缓存获取文档")
            return None
        
        try:
            key = self._get_document_key(document_id)
            data = await self._client.get(key)
            
            if data is None:
                return None
            
            # 反序列化JSON数据
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            document_data = json.loads(data)
            
            # 还原二进制数据
            processed_data = self._decode_binary_data(document_data)
            
            logger.debug(f"文档获取成功: {document_id}")
            return processed_data
            
        except Exception as e:
            logger.error(f"文档获取失败: {document_id}, 错误: {e}")
            return None
    
    async def delete_document(self, document_id: str) -> bool:
        """删除Redis中的文档"""
        if not self._connected or not self._client:
            logger.warning("Redis未连接，无法删除缓存文档")
            return False
        
        try:
            key = self._get_document_key(document_id)
            result = await self._client.delete(key)
            
            if result > 0:
                logger.info(f"文档删除成功: {document_id}")
                return True
            else:
                logger.warning(f"文档不存在: {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"文档删除失败: {document_id}, 错误: {e}")
            return False
    
    async def document_exists(self, document_id: str) -> bool:
        """检查文档是否存在"""
        if not self._connected or not self._client:
            return False
        
        try:
            key = self._get_document_key(document_id)
            result = await self._client.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"检查文档存在性失败: {document_id}, 错误: {e}")
            return False
    
    def _encode_binary_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将二进制数据编码为base64字符串，便于JSON序列化
        
        Args:
            data: 原始数据字典
            
        Returns:
            Dict[str, Any]: 处理后的数据字典
        """
        processed_data = {}
        
        for key, value in data.items():
            if isinstance(value, bytes):
                # bytes转base64字符串
                processed_data[key] = {
                    '_type': 'bytes',
                    '_data': base64.b64encode(value).decode('ascii')
                }
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                processed_data[key] = self._encode_binary_data(value)
            else:
                # 普通数据直接保存
                processed_data[key] = value
        
        return processed_data
    
    def _decode_binary_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将base64字符串还原为二进制数据
        
        Args:
            data: 存储的数据字典
            
        Returns:
            Dict[str, Any]: 还原后的数据字典
        """
        processed_data = {}
        
        for key, value in data.items():
            if isinstance(value, dict) and '_type' in value and '_data' in value:
                if value['_type'] == 'bytes':
                    # base64字符串转回bytes
                    processed_data[key] = base64.b64decode(value['_data'])
                else:
                    processed_data[key] = value
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                processed_data[key] = self._decode_binary_data(value)
            else:
                # 普通数据直接保存
                processed_data[key] = value
        
        return processed_data

# =============================================================================
# 全局实例和获取函数
# =============================================================================

# 全局Redis管理器实例
redis_manager = RedisManager()

async def get_redis_manager() -> RedisManager:
    """
    获取Redis管理器实例
    如果未连接则自动连接
    """
    if not redis_manager.is_connected():
        await redis_manager.connect()
    return redis_manager
