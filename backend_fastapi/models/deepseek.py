"""
DeepSeek模型接口
提供与DeepSeek API的交互功能
"""

import os
from openai import OpenAI, AsyncOpenAI
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

def request_deepseek_md(prompt: str, system_prompt: str = "You are a helpful assistant", model: str = "deepseek-chat", format: str = "json") -> str:
    """
    向Deepseek模型发送请求
    
    Args:
        prompt (str): 用户提示词
        system_prompt (str): 系统提示词，默认为通用助手
        model (str): 使用的Deepseek模型名称，默认 deepseek-chat
            可选： deepseek-chat, deepseek-reasoner 等
        
    Returns:
        str: 模型响应的JSON字符串
    """
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("缺少API密钥: 请设置DEEPSEEK_API_KEY或OPENAI_API_KEY环境变量")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        response = client.chat.completions.create(
            # model = "deepseek-chat" or "deepseek-reasoner"
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        if format == "json":
            return response.model_dump_json()
        elif format == "md":
            content = response.choices[0].message.content
            if content is not None:
                return content
            else:
                raise ValueError("模型响应内容为空")
        else:
            raise TypeError('format must be "json" or "md"')
    except Exception as e:
        error_msg = str(e)
        # 更明确地区分API密钥错误
        if "api_key" in error_msg.lower() or "apikey" in error_msg.lower() or "unauthorized" in error_msg.lower():
            raise ValueError(f"API密钥错误或无效: {error_msg}")
        print(f"Error requesting deepseek ({model}): {e}")
        return '{"error": "Request failed"}'

async def request_deepseek_md_async(system_prompt: str, prompt: str, model: str = "deepseek-chat", format: str = "md") -> str:
    """
    向Deepseek模型发送异步请求
    
    Args:
        system_prompt (str): 系统提示词
        prompt (str): 用户提示词
        model (str): 使用的Deepseek模型名称
        format (str): 返回格式，"json"或"md"
        
    Returns:
        str: 模型响应的JSON字符串或Markdown内容
    """
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("缺少API密钥: 请设置DEEPSEEK_API_KEY或OPENAI_API_KEY环境变量")
    
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        if format == "json":
            return response.model_dump_json()
        elif format == "md":
            content = response.choices[0].message.content
            if content is not None:
                return content
            else:
                raise ValueError("模型响应内容为空")
        else:
            raise TypeError('format must be "json" or "md"')
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "apikey" in error_msg.lower() or "unauthorized" in error_msg.lower():
            raise ValueError(f"API密钥错误或无效: {error_msg}")
        logger.error(f"Error requesting deepseek ({model}) asynchronously: {e}")
        return '{"error": "Request failed"}'
