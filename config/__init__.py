"""
项目配置文件
"""

from .log_config import LOG_CONFIG
from .data_config import FILE_CONFIG
from .model_config import MODEL_CONFIG

__all__ = [
    'LOG_CONFIG',
    'FILE_CONFIG',
    'MODEL_CONFIG',
    'DEBUG_CONFIG',
    'DEBUG_MODE',
    'get_mock_analysis_for_chapter',
    'is_debug_mode_enabled',
    'get_debug_config'
] 