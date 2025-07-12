import os
from openai import OpenAI  # 修改导入方式
from dotenv import load_dotenv
import argparse
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
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # 使用DeepSeek模型
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        return {
            "status": "success",
            "reference_text": reference_text,
            "check_result": response.choices[0].message.content
        }
    except Exception as e:
        return {
            "status": "failed",
            "reference_text": reference_text,
            "error": str(e)
        }

def read_references_from_file(file_path):
    """从文件中读取参考文献列表，每行一个参考文献"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"输入文件不存在: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        references = [line.strip() for line in f if line.strip()]
    return references

def save_results_to_json(results, output_path):
    """将检查结果保存为JSON文件"""
    import json
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return output_path

def process_references(input_path, output_path):
    """处理参考文献批量检查并保存结果
    
    Args:
        input_path (str): 参考文献输入文件路径
        output_path (str): 结果输出JSON文件路径
    
    Returns:
        list: 检查结果列表
    """
    try:
        # 检查并创建输入目录
        input_dir = os.path.dirname(input_path)
        if not os.path.exists(input_dir):
            os.makedirs(input_dir, exist_ok=True)
            raise FileNotFoundError(f"输入目录已自动创建，请将参考文献文件保存到: {input_path}")
        
        references = read_references_from_file(input_path)
        if not references:
            raise ValueError("输入文件中未找到参考文献内容")
        
        print(f"开始检查 {len(references)} 篇参考文献...")
        results = []
        for idx, ref in enumerate(references, 1):
            print(f"正在检查第 {idx}/{len(references)} 篇...")
            result = check_reference_format(ref)
            results.append(result)
        
        save_results_to_json(results, output_path)
        print(f"检查完成，结果已保存到：{output_path}")
        return results
    except Exception as e:
        print(f"处理过程中出错：{str(e)}")
        raise


if __name__ == "__main__":
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(__file__)
    # 构建默认输入输出路径
    default_input = os.path.join(current_dir, 'input', 'references.txt')
    default_output = os.path.join(current_dir, 'output', 'results.json')
    
    parser = argparse.ArgumentParser(description='批量检查参考文献格式并保存结果到JSON文件')
    parser.add_argument('-i', '--input', default=default_input, help=f'输入文件路径，每行一个参考文献 (默认: {default_input})')
    parser.add_argument('-o', '--output', default=default_output, help=f'输出JSON文件路径 (默认: {default_output})')
    args = parser.parse_args()
    
    try:
        process_references(args.input, args.output)
    except Exception as e:
        exit(1)
    # 测试示例
    test_reference = "Wan Y, Zou G, Zhang B. Composed image retrieval: a survey on recent research and development[J]. Applied Intelligence, 2025, 55(6): 482."
    result = check_reference_format(test_reference)
    print(result)