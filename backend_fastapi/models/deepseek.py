"""
DeepSeek模型接口
提供与DeepSeek API的交互功能
"""

import os
from openai import OpenAI
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def request_deepseek(prompt: str, model: str = "deepseek-chat") -> str:
    """
    向DeepSeek模型发送请求
    
    Args:
        prompt (str): 提示词
        model (str): 使用的DeepSeek模型名称，默认 deepseek-chat
            可选： deepseek-chat, deepseek-reasoner 等
        
    Returns:
        str: 模型响应的内容字符串
        
    Raises:
        ValueError: 当API密钥缺失或无效时
        Exception: 当API调用失败时
    """
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("缺少API密钥: 请设置DEEPSEEK_API_KEY或OPENAI_API_KEY环境变量")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        logger.info(f"正在调用DeepSeek模型: {model}")
        logger.debug(f"提示词长度: {len(prompt)} 字符")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        
        # 提取响应内容
        content = response.choices[0].message.content
        logger.info(f"DeepSeek模型响应成功，响应长度: {len(content)} 字符")
        
        return content
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"DeepSeek API调用失败: {error_msg}")
        
        # 更明确地区分API密钥错误
        if any(keyword in error_msg.lower() for keyword in ["api_key", "apikey", "unauthorized", "authentication"]):
            raise ValueError(f"API密钥错误或无效: {error_msg}")
        
        # 其他错误
        raise Exception(f"DeepSeek API调用失败: {error_msg}")

def request_deepseek_json(prompt: str, model: str = "deepseek-chat") -> Dict[str, Any]:
    """
    向DeepSeek模型发送请求并返回完整的响应信息
    
    Args:
        prompt (str): 提示词
        model (str): 使用的DeepSeek模型名称
        
    Returns:
        Dict[str, Any]: 包含输入、输出和元数据的字典
    """
    try:
        content = request_deepseek(prompt, model)
        return {
            'input': prompt,
            'output': content,
            'model': model,
            'status': 'success'
        }
    except Exception as e:
        return {
            'input': prompt,
            'error': str(e),
            'model': model,
            'status': 'error'
        }

def validate_deepseek_config() -> bool:
    """
    验证DeepSeek配置是否正确
    
    Returns:
        bool: 配置是否有效
    """
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    return api_key is not None and len(api_key.strip()) > 0

def get_available_models() -> List[str]:
    """
    获取可用的DeepSeek模型列表
    
    Returns:
        List[str]: 可用模型列表
    """
    return ["deepseek-chat", "deepseek-reasoner"]
