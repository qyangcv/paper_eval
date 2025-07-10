"""
Gemini模型接口
提供与Google Gemini API的交互功能
"""

import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def request_gemini(prompt: str) -> str:
    """
    向Gemini模型发送请求
    
    Args:
        prompt (str): 提示词
        
    Returns:
        str: 模型响应的内容字符串
        
    Raises:
        ValueError: 当API密钥缺失时
        ImportError: 当google-generativeai库未安装时
        Exception: 当API调用失败时
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("缺少API密钥: 请设置GEMINI_API_KEY环境变量")
    
    try:
        # 动态导入google.genai，避免在未安装时导致整个模块无法加载
        from google import genai
        
        logger.info("正在调用Gemini模型")
        logger.debug(f"提示词长度: {len(prompt)} 字符")
        
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=prompt,
        )
        
        content = response.text
        logger.info(f"Gemini模型响应成功，响应长度: {len(content)} 字符")
        
        return content
        
    except ImportError as e:
        error_msg = "google-generativeai库未安装，请运行: pip install google-generativeai"
        logger.error(error_msg)
        raise ImportError(error_msg)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Gemini API调用失败: {error_msg}")
        
        if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
            raise ValueError(f"API密钥错误或无效: {error_msg}")
        
        raise Exception(f"Gemini API调用失败: {error_msg}")

def request_gemini_json(prompt: str) -> Dict[str, Any]:
    """
    向Gemini模型发送请求并返回完整的响应信息
    
    Args:
        prompt (str): 提示词
        
    Returns:
        Dict[str, Any]: 包含输入、输出和元数据的字典
    """
    try:
        content = request_gemini(prompt)
        return {
            'input': prompt,
            'output': content,
            'model': 'gemini-2.5-flash-preview-05-20',
            'status': 'success'
        }
    except Exception as e:
        return {
            'input': prompt,
            'error': str(e),
            'model': 'gemini-2.5-flash-preview-05-20',
            'status': 'error'
        }

def validate_gemini_config() -> bool:
    """
    验证Gemini配置是否正确
    
    Returns:
        bool: 配置是否有效
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or len(api_key.strip()) == 0:
        return False
    
    try:
        from google import genai
        return True
    except ImportError:
        return False

def get_available_models() -> List[str]:
    """
    获取可用的Gemini模型列表
    
    Returns:
        List[str]: 可用模型列表
    """
    return ["gemini-2.5-flash-preview-05-20"]
