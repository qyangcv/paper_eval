"""
日志配置模块
提供统一的日志记录配置
"""

import os
from .data_config import LOGS_DIR

# 从环境变量获取日志级别
def get_env_log_level(env_var: str, default: str = 'INFO') -> str:
    """从环境变量获取日志级别"""
    return os.getenv(env_var, default).upper()

# 日志配置字典 - 使用Python logging.config.dictConfig格式
LOG_CONFIG = {
    # 配置版本，必须为1
    'version': 1,
    # 是否禁用已存在的日志记录器，False表示不禁用
    'disable_existing_loggers': False,
    
    # 格式化器配置 - 定义日志消息的显示格式
    'formatters': {
        'standard': {
            # 统一日志格式：时间 [级别] 记录器名称: 消息内容
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            # 时间格式：年-月-日 时:分:秒（精确到秒，不显示毫秒）
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            # 详细格式：使用相同的时间格式，但包含函数名和行号
            'format': '%(asctime)s [%(levelname)s] %(name)s - %(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            # 简单格式：只有级别和消息
            'format': '[%(levelname)s] %(message)s'
        }
    },
    
    # 处理器配置 - 定义日志输出的目标和方式
    'handlers': {
        # 控制台处理器 - 输出到终端
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        # 文件处理器 - 输出到日志文件
        'file': {
            'level': 'INFO',
            'formatter': 'standard',  # 改为使用标准格式
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'app.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8',
        },
        # 错误文件处理器 - 只记录错误日志
        'error_file': {
            'level': 'ERROR',
            'formatter': 'standard',  # 改为使用标准格式
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'error.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8',
        },
        # API调用日志处理器
        'api_file': {
            'level': 'INFO',
            'formatter': 'standard',  # 改为使用标准格式
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'api.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8',
        },
    },
    
    # 日志记录器配置 - 定义具体的日志记录器行为
    'loggers': {
        # 根日志记录器配置（空字符串表示根记录器）
        '': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False
        },
        # FastAPI相关日志
        'uvicorn': {
            'handlers': ['console', 'file'],
            'level': get_env_log_level('UVICORN_LOG_LEVEL', 'INFO'),
            'propagate': False
        },
        'uvicorn.access': {
            'handlers': ['file'],
            'level': get_env_log_level('UVICORN_LOG_LEVEL', 'INFO'),
            'propagate': False
        },
        'uvicorn.error': {
            'handlers': ['console', 'file'],
            'level': get_env_log_level('UVICORN_LOG_LEVEL', 'INFO'),
            'propagate': False
        },
        # 模型API调用日志
        'models': {
            'handlers': ['console', 'api_file'],
            'level': 'INFO',
            'propagate': False
        },
        # 文档处理日志
        'pipeline': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        # 禁用watchfiles的调试日志
        'watchfiles': {
            'handlers': [],
            'level': get_env_log_level('WATCHFILES_LOG_LEVEL', 'WARNING'),
            'propagate': False
        },
        'watchfiles.main': {
            'handlers': [],
            'level': get_env_log_level('WATCHFILES_LOG_LEVEL', 'WARNING'),
            'propagate': False
        },
    }
}

# 日志级别配置
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# 开发环境日志配置
DEV_LOG_CONFIG = {
    **LOG_CONFIG,
    'handlers': {
        **LOG_CONFIG['handlers'],
        'console': {
            **LOG_CONFIG['handlers']['console'],
            'level': 'DEBUG',
            'formatter': 'standard'  # 改为使用标准格式，保持一致性
        }
    },
    'loggers': {
        **LOG_CONFIG['loggers'],
        '': {
            **LOG_CONFIG['loggers'][''],
            'level': 'DEBUG'
        }
    }
}

# 生产环境日志配置
PROD_LOG_CONFIG = {
    **LOG_CONFIG,
    'handlers': {
        **LOG_CONFIG['handlers'],
        'console': {
            **LOG_CONFIG['handlers']['console'],
            'level': 'WARNING'
        }
    }
}

def get_log_config(environment: str = 'development') -> dict:
    """
    根据环境获取日志配置
    
    Args:
        environment: 环境类型 ('development', 'production')
        
    Returns:
        dict: 日志配置
    """
    if environment == 'production':
        return PROD_LOG_CONFIG
    elif environment == 'development':
        return DEV_LOG_CONFIG
    else:
        return LOG_CONFIG
