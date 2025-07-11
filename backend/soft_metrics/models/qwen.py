"""
Qwen模型相关的代码
包含与Qwen模型交互的函数
"""

import os
from openai import OpenAI

def request_qwen(prompt: str):
    """
    向Qwen模型发送请求
    
    Args:
        prompt (str): 提示词
        
    Returns:
        str: 模型响应的JSON字符串
    """
    try:
        client = OpenAI(
            api_key=os.getenv("QWEN_API_KEY"),
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
        return completion.model_dump_json()
    except Exception as e:
        print(f"Error requesting Qwen: {e}")
        return '{"error": "Request failed"}' 