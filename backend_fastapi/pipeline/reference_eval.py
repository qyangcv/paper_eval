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
    prompt_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    prompt_path = os.path.join(prompt_dir, 'reference_criteria.txt')
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
            print(f"输入目录已自动创建，请将参考文献文件保存到: {input_path}")
        
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
        print(f"检查完成，原始结果已保存到：{output_path}")
        
        # 保存格式化结果（只包含不正确的项）
        save_formatted_results(results, output_path)
        
        return results
    except Exception as e:
        print(f"处理过程中出错：{str(e)}")
        raise

def format_incorrect_references(results):
    """格式化输出，只保留判定为不正确的项
    
    Args:
        results (list): 原始检查结果列表
    
    Returns:
        dict: 格式化后的结果
    """
    incorrect_items = []
    issue_id = 1
    
    for result in results:
        if result.get("status") == "success":
            check_result = result.get("check_result", "")
            # 检查是否判定为不正确
            if "判定结果：[不正确]" in check_result or "判定结果：[错误]" in check_result:
                # 提取错误详情
                suggestions = []
                if "错误详情：" in check_result:
                    # 分割错误详情部分
                    error_details = check_result.split("错误详情：", 1)[1].strip()
                    if error_details and error_details != "无":
                        # 按行分割并处理编号
                        lines = error_details.split("\n")
                        for line in lines:
                            line = line.strip()
                            if line:
                                # 去除行首的数字编号（如"1. "、"2. "等）
                                import re
                                cleaned_line = re.sub(r'^\d+\.\s*', '', line)
                                if cleaned_line:
                                    suggestions.append(cleaned_line)
                
                incorrect_items.append({
                    "id": issue_id,
                    "original_text": result.get("reference_text", ""),
                    "suggestions": suggestions
                })
                issue_id += 1
    
    return {
        "total_issues": len(incorrect_items),
        "detail": incorrect_items
    }

def save_formatted_results(results, output_path):
    """保存格式化后的结果
    
    Args:
        results (list): 原始检查结果列表
        output_path (str): 输出文件路径
    """
    import json
    
    # 生成格式化结果
    formatted_result = format_incorrect_references(results)
    
    # 生成格式化结果的输出路径
    output_dir = os.path.dirname(output_path)
    filename = os.path.basename(output_path)
    name, ext = os.path.splitext(filename)
    formatted_output_path = os.path.join(output_dir, f"{name}_formatted{ext}")
    
    # 保存格式化结果
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(formatted_output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_result, f, ensure_ascii=False, indent=2)
    
    print(f"格式化结果已保存到：{formatted_output_path}")
    print(f"发现 {formatted_result['total_issues']} 个格式问题")
    
    return formatted_output_path

def eval(references_list):
    """
    评估参考文献格式
    
    Args:
        references_list (list): 参考文献列表
        
    Returns:
        dict: 评估结果，包含格式化的问题详情
    """
    if not references_list:
        return {
            "status": "success",
            "total_issues": 0,
            "detail": [],
            "message": "没有参考文献需要检查"
        }
    
    print(f"开始检查 {len(references_list)} 条参考文献...")
    results = []
    
    for idx, ref in enumerate(references_list, 1):
        print(f"正在检查第 {idx}/{len(references_list)} 条参考文献...")
        result = check_reference_format(ref)
        results.append(result)
    
    # 格式化结果，只保留有问题的参考文献
    formatted_result = format_incorrect_references(results)
    
    # 添加状态信息
    formatted_result["status"] = "success"
    if formatted_result["total_issues"] == 0:
        formatted_result["message"] = "所有参考文献格式正确"
    else:
        formatted_result["message"] = f"发现 {formatted_result['total_issues']} 个格式问题"
    
    print(f"参考文献检查完成：{formatted_result['message']}")
    return formatted_result

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
        results = process_references(args.input, args.output)
    except Exception as e:
        exit(1)
    # 测试示例
    # test_reference = "Wan Y, Zou G, Zhang B. Composed image retrieval: a survey on recent research and development[J]. Applied Intelligence, 2025, 55(6): 482."
    # result = check_reference_format(test_reference)
    # print(result)