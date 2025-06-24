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
    try:
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
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
        print(f"Error requesting deepseek ({model}): {e}")
        return '{"error": "Request failed"}' 