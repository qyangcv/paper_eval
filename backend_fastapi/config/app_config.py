"""
应用配置模块
包含FastAPI应用的配置信息
"""

import os
from typing import List
from pathlib import Path

# 静默加载.env文件，避免在日志系统初始化前输出
_ENV_LOADED = False
_ENV_PATH = None
_ENV_ERROR = None

try:
    from dotenv import load_dotenv
    # 查找.env文件
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        _ENV_LOADED = True
        _ENV_PATH = env_path
    else:
        _ENV_ERROR = "未找到.env文件，使用系统环境变量"
except ImportError:
    _ENV_ERROR = "未安装python-dotenv，请运行: pip install python-dotenv"
except Exception as e:
    _ENV_ERROR = f"加载.env文件失败: {e}"

def get_env_status():
    """获取环境配置加载状态，供日志系统使用"""
    return {
        'loaded': _ENV_LOADED,
        'path': _ENV_PATH,
        'error': _ENV_ERROR
    }

# 应用基本配置
APP_CONFIG = {
    'title': '论文评价分析系统API',
    'description': '北邮本科论文质量评价分析系统后端API',
    'version': '1.0.0',
    'debug': os.getenv('DEBUG', 'False').lower() == 'true',
    'environment': os.getenv('ENVIRONMENT', 'development'),
}

# 服务器配置
SERVER_CONFIG = {
    'host': os.getenv('HOST', '0.0.0.0'),
    'port': int(os.getenv('PORT', 8000)),
    'reload': os.getenv('RELOAD', 'True').lower() == 'true',
    'workers': int(os.getenv('WORKERS', 1)),
}

# CORS配置
CORS_CONFIG = {
    'allow_origins': [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:8080',
        'http://127.0.0.1:8080',
    ],
    'allow_credentials': True,
    'allow_methods': ['*'],
    'allow_headers': ['*'],
}

# 如果有环境变量指定的允许源，添加到列表中
if os.getenv('ALLOWED_ORIGINS'):
    additional_origins = os.getenv('ALLOWED_ORIGINS').split(',')
    CORS_CONFIG['allow_origins'].extend([origin.strip() for origin in additional_origins])

# 安全配置
SECURITY_CONFIG = {
    'secret_key': os.getenv('SECRET_KEY', 'your-secret-key-change-in-production'),
    'algorithm': 'HS256',
    'access_token_expire_minutes': 30,
    'max_upload_size': 50 * 1024 * 1024,  # 50MB
    'rate_limit': {
        'requests_per_minute': 60,
        'requests_per_hour': 1000,
    }
}

# 任务配置
TASK_CONFIG = {
    'max_concurrent_tasks': 10,
    'task_timeout': 1800,  # 30分钟
    'cleanup_interval': 3600,  # 1小时清理一次过期任务
    'max_task_history': 1000,  # 最多保留1000个任务记录
}

# 缓存配置
CACHE_CONFIG = {
    'enabled': os.getenv('CACHE_ENABLED', 'True').lower() == 'true',
    'ttl': 3600,  # 1小时
    'max_size': 1000,  # 最多缓存1000个项目
}

# API配置
API_CONFIG = {
    'prefix': '/api',
    'docs_url': '/docs' if APP_CONFIG['debug'] else None,
    'redoc_url': '/redoc' if APP_CONFIG['debug'] else None,
    'openapi_url': '/openapi.json' if APP_CONFIG['debug'] else None,
}

# 监控配置
MONITORING_CONFIG = {
    'enabled': os.getenv('MONITORING_ENABLED', 'True').lower() == 'true',
    'metrics_endpoint': '/metrics',
    'health_endpoint': '/health',
    'status_endpoint': '/status',
}

# 文档处理配置
DOCUMENT_CONFIG = {
    'supported_formats': ['.docx', '.doc'],
    'max_pages': 500,
    'max_chapters': 50,
    'processing_timeout': 1800,  # 30分钟
    'temp_file_cleanup': True,
}

# 模型评估配置
EVALUATION_CONFIG = {
    'default_model': 'deepseek-chat',
    'fallback_models': ['qwen', 'gemini'],
    'max_retries': 3,
    'retry_delay': 1,  # 秒
    'batch_size': 5,
    'parallel_processing': True,
}

# 数据库配置（如果需要）
DATABASE_CONFIG = {
    'enabled': False,  # 当前不使用数据库
    'url': os.getenv('DATABASE_URL', 'sqlite:///./app.db'),
    'echo': APP_CONFIG['debug'],
    'pool_size': 10,
    'max_overflow': 20,
}

# 获取完整配置
def get_app_config() -> dict:
    """
    获取完整的应用配置
    
    Returns:
        dict: 完整配置字典
    """
    return {
        'app': APP_CONFIG,
        'server': SERVER_CONFIG,
        'cors': CORS_CONFIG,
        'security': SECURITY_CONFIG,
        'task': TASK_CONFIG,
        'cache': CACHE_CONFIG,
        'api': API_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'document': DOCUMENT_CONFIG,
        'evaluation': EVALUATION_CONFIG,
        'database': DATABASE_CONFIG,
    }

# 根据环境调整配置
def adjust_config_for_environment():
    """根据环境调整配置"""
    if APP_CONFIG['environment'] == 'production':
        # 生产环境配置调整
        APP_CONFIG['debug'] = False
        SERVER_CONFIG['reload'] = False
        API_CONFIG['docs_url'] = None
        API_CONFIG['redoc_url'] = None
        API_CONFIG['openapi_url'] = None
        SECURITY_CONFIG['rate_limit']['requests_per_minute'] = 30
        
    elif APP_CONFIG['environment'] == 'testing':
        # 测试环境配置调整
        TASK_CONFIG['task_timeout'] = 60
        CACHE_CONFIG['enabled'] = False
        
# 在模块导入时调整配置
adjust_config_for_environment()
