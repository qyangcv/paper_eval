"""
项目日志配置文件
提供统一的日志记录配置，支持控制台和文件双重输出
"""
import os
from .data_config import PROJECT_ROOT

# 日志配置字典 - 使用Python logging.config.dictConfig格式
LOG_CONFIG = {
    # 配置版本，必须为1
    'version': 1,
    # 是否禁用已存在的日志记录器，False表示不禁用
    'disable_existing_loggers': False,
    
    # 格式化器配置 - 定义日志消息的显示格式
    'formatters': {
        'standard': {
            # 日志格式：时间 [级别] 记录器名称: 消息内容
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            # 时间格式：年-月-日 时:分:秒（精确到秒）
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    
    # 处理器配置 - 定义日志输出的目标和方式
    'handlers': {
        # 控制台处理器 - 输出到终端
        'default': {
            'level': 'INFO',                    # 最低日志级别
            'formatter': 'standard',            # 使用standard格式化器
            'class': 'logging.StreamHandler',   # 输出到标准输出流（终端）
        },
        # 文件处理器 - 输出到日志文件
        'file': {
            'level': 'INFO',                    # 最低日志级别
            'formatter': 'standard',            # 使用standard格式化器
            'class': 'logging.FileHandler',     # 输出到文件
            'filename': os.path.join(PROJECT_ROOT, 'logs', 'app.log'),  # 日志文件路径
            'mode': 'a',                        # 追加模式写入文件
        },
    },
    
    # 日志记录器配置 - 定义具体的日志记录器行为
    'loggers': {
        # 根日志记录器配置（空字符串表示根记录器）
        '': {
            'handlers': ['default', 'file'],    # 同时使用控制台和文件处理器
            'level': 'INFO',                    # 记录器的最低日志级别
            'propagate': True                   # 是否向父记录器传播日志消息
        }
    }
} 