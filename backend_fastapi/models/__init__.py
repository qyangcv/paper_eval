"""
AI模型接口模块
包含与各种大语言模型的接口实现

支持的模型：
- DeepSeek: deepseek-chat, deepseek-reasoner
- Gemini: gemini-2.5-flash-preview-05-20
- Qwen: qwen-max

使用方法：
    from models.deepseek import request_deepseek
    from models.gemini import request_gemini
    from models.qwen import request_qwen
"""

from .deepseek import request_deepseek
from .gemini import request_gemini
from .qwen import request_qwen

__all__ = ['request_deepseek', 'request_gemini', 'request_qwen']
