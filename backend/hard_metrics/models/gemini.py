"""
Gemini 模型相关的代码（占位实现）
如果需要使用 Google Gemini Pro，请安装 `google-generativeai` 并设置环境变量 `GEMINI_API_KEY`。
"""

import os
import json
from google import genai


def request_gemini(prompt: str):
    """向 Gemini Pro 模型发送请求。

    当前为简化实现：当本地未安装 google-generativeai 时返回错误信息。
    如果已安装且设置了环境变量 GEMINI_API_KEY，则会调用 Gemini Pro 模型。

    Args:
        prompt: 提示内容

    Returns:
        str: 模型响应的 JSON 字符串
    """
    try:
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        response = client.models.generate_content(
            model = "gemini-2.5-flash-preview-05-20",
            contents = prompt,
        )
        return json.dumps({"response": response.text}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False) 