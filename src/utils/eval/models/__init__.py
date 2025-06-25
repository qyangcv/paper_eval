"""
模型模块
包含与各种大语言模型交互的函数
"""

from .qwen import request_qwen
from .deepseek import request_deepseek
from .gemini import request_gemini

__all__ = [
    'request_qwen',
    'request_deepseek',
    'request_gemini',
]
