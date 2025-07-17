"""
日志配置模块
提供统一的日志记录配置
"""

import os
import logging
from .data_config import LOGS_DIR


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m',       # 重置颜色
        'BOLD': '\033[1m',        # 粗体
        'DIM': '\033[2m',         # 暗淡
    }

    # 模块名颜色
    MODULE_COLORS = {
        'backend_fastapi.main': '\033[94m',      # 亮蓝色
        'uvicorn.error': '\033[96m',             # 亮青色
        'uvicorn.access': '\033[96m',            # 亮青色
        'uvicorn': '\033[96m',                   # 亮青色
        'utils.redis_init': '\033[95m',          # 亮紫色
        'utils.redis_client': '\033[93m',        # 亮黄色
        'models': '\033[92m',                    # 亮绿色
        'pipeline': '\033[91m',                  # 亮红色
        'pipeline.hard_eval': '\033[91m',        # 亮红色
        'api': '\033[97m',                       # 白色
        'httpx': '\033[90m',                     # 灰色
        'httpcore': '\033[90m',                  # 灰色
    }

    def __init__(self, fmt=None, datefmt=None, use_colors=None):
        super().__init__(fmt, datefmt)
        # 自动检测是否支持颜色
        if use_colors is None:
            self.use_colors = self._supports_color()
        else:
            self.use_colors = use_colors

    def _supports_color(self):
        """检测终端是否支持颜色"""
        import sys
        import os

        # Windows系统检查
        if os.name == 'nt':
            # Windows 10 及以上版本支持ANSI颜色
            try:
                import platform
                version = platform.version()
                major_version = int(version.split('.')[0])
                if major_version >= 10:
                    return True
            except:
                pass

            # 检查是否在支持颜色的终端中运行
            return (
                hasattr(sys.stderr, "isatty") and sys.stderr.isatty() and
                (os.environ.get('TERM') != 'dumb') and
                (os.environ.get('COLORTERM') is not None or
                 os.environ.get('TERM_PROGRAM') in ['vscode', 'hyper', 'iterm'])
            )

        # Unix系统检查
        return (
            hasattr(sys.stderr, "isatty") and sys.stderr.isatty() and
            os.environ.get('TERM') != 'dumb'
        )

    def format(self, record):
        if not self.use_colors:
            # 使用标准格式，不带颜色
            return super().format(record)

        # 获取日志级别颜色
        level_color = self.COLORS.get(record.levelname, '')

        # 获取模块名颜色
        module_color = ''
        for module, color in self.MODULE_COLORS.items():
            if record.name.startswith(module):
                module_color = color
                break
        if not module_color:
            module_color = '\033[37m'  # 默认白色

        # 格式化时间（灰色）
        formatted_time = f"\033[90m{self.formatTime(record, self.datefmt)}\033[0m"

        # 格式化日志级别（带颜色和粗体）
        formatted_level = f"{level_color}{self.COLORS['BOLD']}[{record.levelname}]{self.COLORS['RESET']}"

        # 格式化模块名（带颜色）
        formatted_name = f"{module_color}{record.name}{self.COLORS['RESET']}"

        # 格式化消息（白色）
        formatted_message = f"\033[97m{record.getMessage()}\033[0m"

        # 组合最终格式
        return f"{formatted_time} {formatted_level} {formatted_name}: {formatted_message}"

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
        'colored': {
            # 彩色格式化器 - 用于控制台输出
            '()': ColoredFormatter,
            'fmt': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'use_colors': True
        },
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
        # 控制台处理器 - 输出到终端（使用彩色格式）
        'console': {
            'level': 'INFO',
            'formatter': 'colored',
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
            'handlers': ['console', 'file'],  # 也输出到控制台以显示颜色
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
        # HTTP客户端日志
        'httpx': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'httpcore': {
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
            'formatter': 'colored'  # 开发环境使用彩色格式
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
            'level': 'WARNING',
            'formatter': 'standard'  # 生产环境使用标准格式（无颜色）
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
