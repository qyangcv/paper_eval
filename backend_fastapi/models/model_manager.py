"""
模型管理器
提供统一的模型调用接口和配置管理
"""

import logging
from typing import Dict, Any, List, Optional
from .deepseek import request_deepseek, validate_deepseek_config, get_available_models as get_deepseek_models
from .gemini import request_gemini, validate_gemini_config, get_available_models as get_gemini_models
from .qwen import request_qwen, validate_qwen_config, get_available_models as get_qwen_models

logger = logging.getLogger(__name__)

class ModelManager:
    """模型管理器，提供统一的模型调用接口"""
    
    def __init__(self):
        self.supported_models = {
            'deepseek-chat': request_deepseek,
            'deepseek-reasoner': request_deepseek,
            'gemini': request_gemini,
            'qwen': request_qwen,
        }
    
    def request_model(self, prompt: str, model_name: str) -> Dict[str, Any]:
        """
        统一的模型请求接口
        
        Args:
            prompt: 提示词
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 推理结果
        """
        logger.info(f"正在使用模型 {model_name} 进行推理...")
        logger.debug(f"提示词长度: {len(prompt)} 字符")

        try:
            if model_name.startswith("deepseek"):
                response = request_deepseek(prompt, model_name)
                return {'input': prompt, 'output': response, 'model': model_name, 'status': 'success'}
            elif model_name == "gemini":
                response = request_gemini(prompt)
                return {'input': prompt, 'output': response, 'model': model_name, 'status': 'success'}
            elif model_name == "qwen":
                response = request_qwen(prompt)
                return {'input': prompt, 'output': response, 'model': model_name, 'status': 'success'}
            else:
                raise ValueError(f"不支持的模型: {model_name}")
                
        except Exception as e:
            logger.error(f"模型推理失败: {e}")
            return {'input': prompt, 'error': str(e), 'model': model_name, 'status': 'error'}
    
    def validate_model_config(self, model_name: str) -> bool:
        """
        验证模型配置是否正确
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 配置是否有效
        """
        try:
            if model_name.startswith("deepseek"):
                return validate_deepseek_config()
            elif model_name == "gemini":
                return validate_gemini_config()
            elif model_name == "qwen":
                return validate_qwen_config()
            else:
                return False
        except Exception as e:
            logger.error(f"验证模型配置失败: {e}")
            return False
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """
        获取所有可用的模型列表
        
        Returns:
            Dict[str, List[str]]: 按提供商分组的模型列表
        """
        return {
            'deepseek': get_deepseek_models(),
            'gemini': get_gemini_models(),
            'qwen': get_qwen_models(),
        }
    
    def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有模型的状态信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 模型状态信息
        """
        status = {}
        
        for provider, models in self.get_available_models().items():
            for model in models:
                status[model] = {
                    'provider': provider,
                    'available': self.validate_model_config(model),
                    'name': model
                }
        
        return status

# 创建全局模型管理器实例
model_manager = ModelManager()

def request_model(prompt: str, model_name: str) -> Dict[str, Any]:
    """
    全局模型请求函数
    
    Args:
        prompt: 提示词
        model_name: 模型名称
        
    Returns:
        Dict[str, Any]: 推理结果
    """
    return model_manager.request_model(prompt, model_name)
