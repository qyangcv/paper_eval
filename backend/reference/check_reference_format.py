import os
from openai import OpenAI  # 修改导入方式
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化DeepSeek客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),  # 使用DeepSeek API密钥
    base_url="https://api.deepseek.com"  # DeepSeek API基础地址
)

def load_prompt(prompt_path):
    """加载提示词模板"""
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def check_reference_format(reference_text):
    """检查参考文献格式是否正确"""
    # 加载提示词
    prompt_dir = os.path.join(os.path.dirname(__file__), 'prompt')
    prompt_path = os.path.join(prompt_dir, 'reference_check_prompt.txt')
    system_prompt = load_prompt(prompt_path)

    # 构建消息
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请检查以下参考文献格式：{reference_text}"}
    ]

    # 调用DeepSeek API
    response = client.chat.completions.create(
        model="deepseek-chat",  # 使用DeepSeek模型
        messages=messages,
        temperature=0.3,
        max_tokens=500
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    # 测试示例
    test_reference = "Wan Y, Zou G, Zhang B. Composed image retrieval: a survey on recent research and development[J]. Applied Intelligence, 2025, 55(6): 482."
    result = check_reference_format(test_reference)
    print(result)