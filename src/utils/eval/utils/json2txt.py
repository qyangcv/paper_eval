import json
import os

def parse_and_format_json_content(file_path):
    """
    解析单个JSON文件，提取并格式化大模型的输出内容。
    特别处理嵌套的JSON字符串和转义字符。
    """
    formatted_outputs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, item in enumerate(data):
            if isinstance(item, dict) and 'output' in item:
                try:
                    output_str = item['output']
                    output_json = json.loads(output_str) # 解析第一层output字符串
                    
                    if output_json.get('choices') and isinstance(output_json['choices'], list) and len(output_json['choices']) > 0:
                        message_obj = output_json['choices'][0].get('message', {})
                        if message_obj: # 确保 message 对象存在
                            message_content_str = message_obj.get('content', '')
                            if message_content_str:
                                # 移除可能存在的Markdown代码块标记
                                if message_content_str.startswith("```json"):
                                    message_content_str = message_content_str[len("```json"):].strip()
                                if message_content_str.endswith("```"):
                                    message_content_str = message_content_str[:-len("```")].strip()
                                
                                try:
                                    # 解析 'content' 字符串（它本身也是一个JSON）
                                    message_json = json.loads(message_content_str)
                                    # 美化JSON输出
                                    formatted_content = json.dumps(message_json, indent=4, ensure_ascii=False)
                                    # 进一步处理换行符，将\n替换为实际换行
                                    formatted_content = formatted_content.replace('\\n', '\n')
                                    formatted_outputs.append(f"章节 {i+1} 的大模型输出:\n{formatted_content}")
                                except json.JSONDecodeError as e_inner:
                                    formatted_outputs.append(f"章节 {i+1} 的 'content' 无法解析为JSON: {e_inner}\n原始 'content': {message_content_str}")
                                except Exception as e_general:
                                    formatted_outputs.append(f"章节 {i+1} 处理 'content' 时发生未知错误: {e_general}\n原始 'content': {message_content_str}")
                            else:
                                formatted_outputs.append(f"章节 {i+1} 的 'content' 为空。")
                        else:
                            formatted_outputs.append(f"章节 {i+1} 的 'choices'[0] 中缺少 'message' 对象。")
                    else:
                        formatted_outputs.append(f"章节 {i+1} 的 'output' JSON结构不符合预期（缺少 'choices' 或其内容不正确）。")
                except json.JSONDecodeError as e_outer:
                    formatted_outputs.append(f"章节 {i+1} 的 'output' 字段无法解析为JSON: {e_outer}\n原始 'output': {item.get('output', 'N/A')}")
                except Exception as e_main:
                     formatted_outputs.append(f"处理章节 {i+1} 的 'output' 时发生未知错误: {e_main}")
            else:
                formatted_outputs.append(f"条目 {i+1} 不是一个有效的章节对象或缺少 'output' 字段。")
                
    except FileNotFoundError:
        return [f"错误：文件 {file_path} 未找到。"]
    except json.JSONDecodeError as e_file:
        return [f"错误：文件 {file_path} 不是有效的JSON格式: {e_file}"]
    except Exception as e:
        return [f"读取或解析文件 {file_path} 时发生未知错误: {e}"]
        
    return formatted_outputs

def main():
    """
    主函数，遍历目录中的JSON文件，解析内容并为每个文件生成单独的txt输出文件。
    """
    workspace_root = "/Users/yang/Documents/bupt/code/paper_eval"
    input_directory = os.path.join(workspace_root, 'qy_data_pipeline/docx_example/api_1c1t')
    output_base_directory = os.path.join(workspace_root, 'qy_data_pipeline/docx_example/api_1c1t')
    
    if not os.path.exists(input_directory):
        print(f"错误：输入目录 {input_directory} 不存在。")
        return
    if not os.path.isdir(input_directory):
        print(f"错误：指定的输入路径 {input_directory} 不是一个目录。")
        return

    # 创建输出目录（如果它不存在）
    os.makedirs(output_base_directory, exist_ok=True)
        
    files_processed_count = 0
    for filename in os.listdir(input_directory):
        if filename.lower().endswith('.json'):
            input_file_path = os.path.join(input_directory, filename)
            
            # 生成输出文件名
            base_filename, _ = os.path.splitext(filename)
            output_filename = f"{base_filename}.txt"
            output_file_path = os.path.join(output_base_directory, output_filename)
            
            parsed_data = parse_and_format_json_content(input_file_path)
            
            try:
                with open(output_file_path, 'w', encoding='utf-8') as f_out:
                    f_out.write(f"=============== 文件: {filename} ===============\n\n")
                    for line in parsed_data:
                        f_out.write(line + '\n')
                    f_out.write('\n\n') # 文件末尾添加空行
                print(f"已处理文件: {filename} -> {output_filename}")
                files_processed_count += 1
            except IOError as e:
                print(f"错误：无法写入输出文件 {output_file_path}: {e}")
            except Exception as e_write:
                print(f"写入文件 {output_file_path} 时发生未知错误: {e_write}")
            
    if files_processed_count == 0:
        print(f"在目录 {input_directory} 中没有找到JSON文件。")
        return

    print(f"\n处理完成。共处理 {files_processed_count} 个JSON文件。")
    print(f"结果已保存到目录: {output_base_directory}")

if __name__ == '__main__':
    main() 