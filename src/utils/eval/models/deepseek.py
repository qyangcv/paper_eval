"""
Deepseek模型相关的代码
包含与Deepseek模型交互的函数
"""

import os
from openai import OpenAI

def request_deepseek(prompt: str, model: str = "deepseek-chat"):
    """
    向Deepseek模型发送请求
    
    Args:
        prompt (str): 提示词
        model (str): 使用的Deepseek模型名称，默认 deepseek-chat
            可选： deepseek-chat, deepseek-reasoner 等
        
    Returns:
        str: 模型响应的JSON字符串
    """
    api_key = "sk-e6068e4723e74a4b8a8e2788cf7ac055"
    # api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
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
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        return response.model_dump_json()
    except Exception as e:
        error_msg = str(e)
        # 更明确地区分API密钥错误
        if "api_key" in error_msg.lower() or "apikey" in error_msg.lower() or "unauthorized" in error_msg.lower():
            raise ValueError(f"API密钥错误或无效: {error_msg}")
        print(f"Error requesting deepseek ({model}): {e}")
        return '{"error": "Request failed"}' 