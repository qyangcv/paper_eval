"""
模型配置
"""

MODEL_CONFIG = {
    'qwen': {
        'model_name': 'Qwen/Qwen3-0.6B',
        'max_length': 2048,
        'temperature': 0.7
    },
    'deepseek-chat': {
        'model_name': 'deepseek-ai/deepseek-chat',
        'max_length': 8192,
        'temperature': 0.7
    },
    'deepseek-reasoner': {
        'model_name': 'deepseek-ai/deepseek-reasoner',
        'max_length': 8192,
        'temperature': 0.7
    },
    'gemini': {
        'model_name': 'google/generative-ai/gemini-pro',
        'max_length': 8192,
        'temperature': 0.7
    },
} 