"""
模型配置模块
包含所有AI模型的配置信息
"""

# 模型配置
MODEL_CONFIG = {
    'deepseek-chat': {
        'model_name': 'deepseek-chat',
        'provider': 'deepseek',
        'api_base': 'https://api.deepseek.com',
        'max_tokens': 8192,
        'temperature': 0.7,
        'timeout': 0,  # 移除超时限制
        'retry_times': 3,
        'retry_delay': 1,
    },
    'deepseek-reasoner': {
        'model_name': 'deepseek-reasoner',
        'provider': 'deepseek',
        'api_base': 'https://api.deepseek.com',
        'max_tokens': 8192,
        'temperature': 0.7,
        'timeout': 0,  # 移除超时限制
        'retry_times': 3,
        'retry_delay': 1,
    },
    'gemini': {
        'model_name': 'gemini-2.5-flash-preview-05-20',
        'provider': 'google',
        'api_base': 'https://generativelanguage.googleapis.com',
        'max_tokens': 8192,
        'temperature': 0.7,
        'timeout': 0,  # 移除超时限制
        'retry_times': 3,
        'retry_delay': 1,
    },
    'qwen': {
        'model_name': 'qwen-max',
        'provider': 'alibaba',
        'api_base': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'max_tokens': 8192,
        'temperature': 0.7,
        'timeout': 0,  # 移除超时限制
        'retry_times': 3,
        'retry_delay': 1,
    },
}

# 默认模型配置
DEFAULT_MODEL = 'deepseek-chat'

# 模型优先级（用于自动选择）
MODEL_PRIORITY = [
    'deepseek-chat',
    'qwen',
    'gemini',
    'deepseek-reasoner'
]

# API密钥环境变量映射
API_KEY_ENV_MAP = {
    'deepseek-chat': ['DEEPSEEK_API_KEY', 'OPENAI_API_KEY'],
    'deepseek-reasoner': ['DEEPSEEK_API_KEY', 'OPENAI_API_KEY'],
    'gemini': ['GEMINI_API_KEY'],
    'qwen': ['QWEN_API_KEY'],
}

# 模型能力配置
MODEL_CAPABILITIES = {
    'deepseek-chat': {
        'supports_chinese': True,
        'supports_english': True,
        'supports_code': True,
        'supports_math': True,
        'context_window': 32768,
        'good_for': ['general', 'coding', 'analysis']
    },
    'deepseek-reasoner': {
        'supports_chinese': True,
        'supports_english': True,
        'supports_code': True,
        'supports_math': True,
        'context_window': 32768,
        'good_for': ['reasoning', 'complex_analysis', 'problem_solving']
    },
    'gemini': {
        'supports_chinese': True,
        'supports_english': True,
        'supports_code': True,
        'supports_math': True,
        'context_window': 32768,
        'good_for': ['general', 'multimodal', 'creative']
    },
    'qwen': {
        'supports_chinese': True,
        'supports_english': True,
        'supports_code': True,
        'supports_math': True,
        'context_window': 32768,
        'good_for': ['chinese', 'general', 'analysis']
    },
}

def get_model_config(model_name: str) -> dict:
    """
    获取指定模型的配置
    
    Args:
        model_name: 模型名称
        
    Returns:
        dict: 模型配置
    """
    return MODEL_CONFIG.get(model_name, MODEL_CONFIG[DEFAULT_MODEL])

def get_available_models() -> list:
    """
    获取所有可用的模型列表
    
    Returns:
        list: 模型名称列表
    """
    return list(MODEL_CONFIG.keys())

def get_model_by_capability(capability: str) -> list:
    """
    根据能力获取推荐的模型列表
    
    Args:
        capability: 能力类型 ('general', 'coding', 'reasoning', 'chinese', etc.)
        
    Returns:
        list: 推荐的模型列表
    """
    recommended = []
    for model_name, capabilities in MODEL_CAPABILITIES.items():
        if capability in capabilities.get('good_for', []):
            recommended.append(model_name)
    
    return recommended
