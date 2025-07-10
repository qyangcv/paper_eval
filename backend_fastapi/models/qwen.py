"""
Qwen模型接口
提供与阿里云Qwen API的交互功能
"""

import os
import json
import logging
from openai import OpenAI
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def request_qwen(prompt: str) -> str:
    """
    向Qwen模型发送请求
    
    Args:
        prompt (str): 提示词
        
    Returns:
        str: 模型响应的内容字符串
        
    Raises:
        ValueError: 当API密钥缺失或无效时
        Exception: 当API调用失败时
    """
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        raise ValueError("缺少API密钥: 请设置QWEN_API_KEY环境变量")
    
    try:
        logger.info("正在调用Qwen模型")
        logger.debug(f"提示词长度: {len(prompt)} 字符")
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        completion = client.chat.completions.create(
            model="qwen-max",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            extra_body={"enable_thinking": False},
        )
        
        content = completion.choices[0].message.content
        logger.info(f"Qwen模型响应成功，响应长度: {len(content)} 字符")
        
        return content
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Qwen API调用失败: {error_msg}")
        
        if any(keyword in error_msg.lower() for keyword in ["api_key", "apikey", "unauthorized", "authentication"]):
            raise ValueError(f"API密钥错误或无效: {error_msg}")
        
        raise Exception(f"Qwen API调用失败: {error_msg}")

def request_qwen_json(prompt: str) -> Dict[str, Any]:
    """
    向Qwen模型发送请求并返回完整的响应信息
    
    Args:
        prompt (str): 提示词
        
    Returns:
        Dict[str, Any]: 包含输入、输出和元数据的字典
    """
    try:
        content = request_qwen(prompt)
        return {
            'input': prompt,
            'output': content,
            'model': 'qwen-max',
            'status': 'success'
        }
    except Exception as e:
        return {
            'input': prompt,
            'error': str(e),
            'model': 'qwen-max',
            'status': 'error'
        }

def validate_qwen_config() -> bool:
    """
    验证Qwen配置是否正确
    
    Returns:
        bool: 配置是否有效
    """
    api_key = os.getenv("QWEN_API_KEY")
    return api_key is not None and len(api_key.strip()) > 0

def get_available_models() -> List[str]:
    """
    获取可用的Qwen模型列表
    
    Returns:
        List[str]: 可用模型列表
    """
    return ["qwen-max"]
