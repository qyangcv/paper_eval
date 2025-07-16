"""
Redis配置模块
直接在Python中配置Redis连接参数，便于开发调试
生产环境建议使用环境变量覆盖默认值
"""

import os
from typing import Optional

# =============================================================================
# Redis核心配置
# =============================================================================

# Redis服务器连接配置
REDIS_CONFIG = {
    'host': 'localhost',           # Redis服务器地址
    'port': 6379,                  # Redis服务器端口
    'db': 0,                       # Redis数据库编号 (0-15)
    'password': None,              # Redis密码，生产环境建议设置
    'decode_responses': True,      # 自动解码响应为字符串
    'socket_timeout': 5.0,         # Socket读取超时(秒)
    'socket_connect_timeout': 5.0, # Socket连接超时(秒)
    'retry_on_timeout': True,      # 超时是否重试
    'health_check_interval': 30,   # 健康检查间隔(秒)
}

# Redis连接池配置
REDIS_POOL_CONFIG = {
    'max_connections': 20,         # 连接池最大连接数
    'encoding': 'utf-8',          # 字符编码
    'decode_responses': True,      # 解码响应
}

# 文档存储专用配置
DOCUMENT_REDIS_CONFIG = {
    'key_prefix': 'paper_eval:doc:',        # Redis键名前缀
    'expire_time': 86400,                   # 文档过期时间(24小时)
    'max_content_size': 50 * 1024 * 1024,  # 最大内容大小(50MB)
}

# =============================================================================
# 环境变量覆盖支持
# =============================================================================

def _apply_env_overrides():
    """应用环境变量覆盖默认配置"""
    # 基础连接配置
    redis_host = os.getenv('REDIS_HOST')
    if redis_host:
        REDIS_CONFIG['host'] = redis_host
    
    redis_port = os.getenv('REDIS_PORT')
    if redis_port:
        REDIS_CONFIG['port'] = int(redis_port)
    
    redis_db = os.getenv('REDIS_DB')
    if redis_db:
        REDIS_CONFIG['db'] = int(redis_db)
    
    redis_password = os.getenv('REDIS_PASSWORD')
    if redis_password:
        REDIS_CONFIG['password'] = redis_password

# 启动时自动应用环境变量
_apply_env_overrides()

# =============================================================================
# 配置验证函数
# =============================================================================

def validate_redis_config() -> tuple[bool, Optional[str]]:
    """
    验证Redis配置的有效性
    
    Returns:
        tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    try:
        # 检查主机地址
        if not REDIS_CONFIG['host']:
            return False, "Redis主机地址不能为空"
        
        # 检查端口范围
        port = REDIS_CONFIG['port']
        if port <= 0 or port > 65535:
            return False, f"Redis端口无效: {port}"
        
        # 检查数据库编号
        db = REDIS_CONFIG['db']
        if db < 0 or db > 15:
            return False, f"Redis数据库编号无效: {db}"
        
        return True, None
        
    except Exception as e:
        return False, f"配置验证失败: {e}"

def get_redis_url() -> str:
    """获取Redis连接URL"""
    password_part = f":{REDIS_CONFIG['password']}@" if REDIS_CONFIG['password'] else ""
    return f"redis://{password_part}{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}"
