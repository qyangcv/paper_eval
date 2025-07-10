"""
JSON转Markdown工具模块
用于将 OpenAI SDK 的 response.model_dump_json() 格式的 JSON 文件转换为 Markdown
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from glob import glob

from config import FILE_CONFIG
from logger import get_logger

logger = get_logger(__name__)

# 配置参数
JSON_INPUT_DIR = "data/output/docx/gemini-flash"  # JSON 文件输入目录

class JSONConversionError(Exception):
    """JSON转换错误"""
    pass

def validate_file(file_path: str) -> None:
    """
    验证文件是否有效
    
    Args:
        file_path: 文件路径
        
    Raises:
        JSONConversionError: 当文件无效时抛出
    """
    if not os.path.exists(file_path):
        raise JSONConversionError(f"文件不存在: {file_path}")
        
    if not file_path.lower().endswith('.json'):
        raise JSONConversionError(f"文件必须是JSON格式: {file_path}")
        
    file_size = os.path.getsize(file_path)
    if file_size > FILE_CONFIG['max_file_size']:
        raise JSONConversionError(f"文件大小超过限制: {file_path}")

def parse_openai_response(response_data: Dict) -> Optional[str]:
    """
    解析 OpenAI SDK response.model_dump_json() 格式的内容
    
    Args:
        response_data: OpenAI 响应数据字典
        
    Returns:
        Optional[str]: 提取的内容文本，失败时返回None
    """
    try:
        # 处理错误响应
        if 'error' in response_data:
            logger.warning(f"响应包含错误: {response_data['error']}")
            return None
            
        # OpenAI SDK 的标准格式：response.choices[0].message.content
        if 'choices' in response_data and len(response_data['choices']) > 0:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
        
        # 备用格式：直接在 content 字段
        if 'content' in response_data:
            return response_data['content']
            
        # 备用格式：在 output 字段中
        if 'output' in response_data:
            return response_data['output']
            
        logger.warning(f"无法从响应数据中提取内容: {list(response_data.keys())}")
        return None
        
    except Exception as e:
        logger.error(f"解析 OpenAI 响应时出错: {e}")
        return None

def parse_json_content(content: str) -> Optional[Dict]:
    """
    解析JSON内容
    
    Args:
        content: JSON字符串
        
    Returns:
        Optional[Dict]: 解析后的字典，解析失败时返回None
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {e}")
        return None

def extract_content_from_json_file(json_file: str) -> List[str]:
    """
    从JSON文件中提取所有内容
    
    Args:
        json_file: JSON文件路径
        
    Returns:
        List[str]: 提取的内容列表
    """
    contents = []
    
    try:
        with open(json_file, 'r', encoding=FILE_CONFIG['encoding']) as f:
            json_data = json.load(f)
        
        # 如果是列表格式（多个推理结果）
        if isinstance(json_data, list):
            for item in json_data:
                if not isinstance(item, dict):
                    continue
                
                # 只处理 output 字段
                if 'output' in item:
                    output = item['output']
                    if isinstance(output, str):
                        try:
                            # 解析 output 字符串为 JSON
                            output_data = json.loads(output)
                            # 提取 content 内容
                            if 'choices' in output_data and len(output_data['choices']) > 0:
                                choice = output_data['choices'][0]
                                if 'message' in choice and 'content' in choice['message']:
                                    content_str = choice['message']['content'].strip()
                                    # 清理 markdown code-fence
                                    if content_str.startswith("```json"):
                                        content_str = content_str[7:]
                                    if content_str.endswith("```"):
                                        content_str = content_str[:-3]
                                    contents.append(content_str.strip())
                        except (json.JSONDecodeError, IndexError) as e:
                            logger.warning(f"解析 output JSON 失败或格式不正确: {e}")
                            continue
                                
    except Exception as e:
        logger.error(f"处理文件 {json_file} 时出错: {e}")
    
    return contents

def generate_markdown(contents: List[str], filename: str) -> str:
    """
    生成Markdown内容
    
    Args:
        contents: 内容列表
        filename: 文件名（用作标题）
        
    Returns:
        str: Markdown格式的文本
    """
    markdown = []
    
    # 添加文件标题
    title = os.path.splitext(filename)[0]
    markdown.append(f"# {title}\n\n")
    
    # 添加内容
    for content in contents:
        try:
            # 解析 JSON 内容
            json_data = json.loads(content)
            
            # 添加章节类型和内容概括
            if '章节类型' in json_data:
                markdown.append(f"# {json_data['章节类型']}\n\n")
            if '内容概括' in json_data:
                markdown.append(f"{json_data['内容概括']}\n\n")
            
            # 处理评价部分
            if '评价' in json_data:
                evaluation = json_data['评价']
                
                categories = [('zh', 'zh'), ('en', 'en'), ('col', 'col'), ('for', 'for'), ('ref', 'ref')]
                
                for key, name in categories:
                    if key in evaluation:
                        category_data = evaluation[key]
                        markdown.append(f"## {name}\n\n")
                        markdown.append(f"{category_data.get('概览', '')}\n\n")
                        details = category_data.get('详情', [])
                        if details:
                            for idx, detail in enumerate(details, 1):
                                markdown.append(f"{idx}. \n\n")
                                if '原文片段' in detail:
                                    markdown.append(f"- 原文：{detail['原文片段']}\n\n")
                                if '问题分析' in detail:
                                    markdown.append(f"- 问题分析：{detail['问题分析']}\n\n")
                                if '修改建议' in detail:
                                    markdown.append(f"- 修改建议：{detail['修改建议']}\n\n")
                        else:
                            markdown.append("未发现问题\n\n")
            
        except json.JSONDecodeError as e:
            logger.warning(f"无法解析内容为JSON，当成普通文本处理: {e}")
            # 如果不是 JSON 格式，直接添加内容
            markdown.append(f"{content}\n\n")
    
    return "".join(markdown)

def find_json_files(directory: str) -> List[str]:
    """
    查找指定目录下的所有JSON文件
    
    Args:
        directory: 目录路径
        
    Returns:
        List[str]: JSON文件路径列表
    """
    if not os.path.exists(directory):
        logger.warning(f"目录不存在: {directory}")
        return []
    
    # 递归查找所有JSON文件
    json_pattern = os.path.join(directory, "**", "*.json")
    json_files = glob(json_pattern, recursive=True)
    
    return sorted(json_files)

def json2md(input_file: str, output_file: str) -> None:
    """
    将JSON文件转换为Markdown文件
    
    Args:
        input_file: 输入JSON文件路径
        output_file: 输出Markdown文件路径
        
    Raises:
        JSONConversionError: 当转换过程出错时抛出
    """
    try:
        # 验证输入文件
        validate_file(input_file)
        
        # 提取内容
        contents = extract_content_from_json_file(input_file)
        
        if not contents:
            raise JSONConversionError(f"没有找到有效的内容: {input_file}")
        
        # 生成Markdown内容
        filename = os.path.basename(input_file)
        markdown_content = generate_markdown(contents, filename)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 写入Markdown文件
        with open(output_file, 'w', encoding=FILE_CONFIG['encoding']) as f:
            f.write(markdown_content)
            
        logger.info(f"✓ 成功转换: {input_file} -> {output_file}")
        
    except Exception as e:
        logger.error(f"转换 {input_file} 时出错: {e}")
        raise JSONConversionError(f"转换失败: {str(e)}")

def batch_convert() -> None:
    """
    批量转换指定目录下的所有JSON文件
    """
    print("=" * 60)
    print("开始批量转换 JSON 文件为 Markdown...")
    print(f"扫描目录: {JSON_INPUT_DIR}")
    print("=" * 60)
    
    # 查找所有JSON文件
    json_files = find_json_files(JSON_INPUT_DIR)
    
    if not json_files:
        print(f"在目录 {JSON_INPUT_DIR} 中没有找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个JSON文件:")
    for json_file in json_files:
        print(f"  - {json_file}")
    print()
    
    # 批量转换
    success_count = 0
    failed_count = 0
    
    for json_file in json_files:
        try:
            # 生成输出文件路径（同目录下，扩展名改为.md）
            output_file = os.path.splitext(json_file)[0] + '.md'
            
            # 转换文件
            json2md(json_file, output_file)
            success_count += 1
            
        except Exception as e:
            print(f"✗ 转换失败: {json_file}, 错误: {e}")
            failed_count += 1
    
    print("\n" + "=" * 60)
    print("批量转换完成!")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {failed_count} 个文件")
    print("=" * 60)

if __name__ == "__main__":
    batch_convert() 