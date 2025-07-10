"""
论文质量评估模块。
用于评估论文的写作质量，包括摘要和各个章节。

6月26日新增，为前端调用的推理模块。
"""

import os
import sys
import json
import re
import time
import warnings
from pathlib import Path

# 修改导入语句，使用torch_helper.py中的安全导入方法
try:
    from tools.torch_helper import get_transformers
except ImportError as e:
    print(f"Warning: 无法导入torch_helper模块，将使用备用导入方法: {e}")
    # 仅在torch_helper导入失败时使用原有的延迟导入方法
    _transformers = None
    _tokenizer = None

    def _safe_import_transformers():
        """Safely import transformers module without triggering Streamlit file watcher issues."""
        global _transformers
        if _transformers is None:
            try:
                import transformers
                _transformers = transformers
                return transformers
            except ImportError:
                warnings.warn("Failed to import transformers library. Tokenization functionality will be unavailable.")
                return None
        return _transformers
else:
    # 如果torch_helper导入成功，直接使用其方法
    def _safe_import_transformers():
        return get_transformers()

def _get_tokenizer():
    """Safely get a tokenizer with deferred import."""
    transformers = _safe_import_transformers()
    if not transformers:
        return None
        
    try:
        return transformers.AutoTokenizer.from_pretrained('Qwen/Qwen3-0.6B')
    except Exception as e:
        warnings.warn(f"Failed to initialize tokenizer: {e}")
        return None

# 确保能够导入项目模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 移除直接导入，改用安全导入方式
# try:
#     from transformers import AutoTokenizer
# except ImportError:
#     print("Warning: transformers 库未安装，tokenizer 功能将不可用")

# 修改导入路径
try:
    from models.deepseek import request_deepseek
    from models.qwen import request_qwen
    from models.gemini import request_gemini
    from prompts.assess_detail_prompt import (
        p_wq_zh,
        p_wq_en,
        p_wq_col,
        p_wq_for,
        p_wq_ref,
        p_writing_quality
    )
    from prompts.overall_prompt import p_overall_assessment
    from tools.file_utils import read_pickle
except ImportError as e:
    print(f"Warning: 模块导入错误，某些功能可能不可用: {e}")
    
    # 提供空的替代函数，确保即使导入失败也不会导致整个模块崩溃
    def read_pickle(path):
        print(f"Warning: 无法读取 pickle 文件 {path}，未找到 read_pickle 函数")
        return {"chapters": []}
    
    def request_deepseek(prompt, model_name="deepseek-chat"):
        print("Warning: 无法调用 DeepSeek API，未找到 request_deepseek 函数")
        return "API 调用失败，请检查依赖和环境配置"
    
    def request_qwen(prompt):
        print("Warning: 无法调用 Qwen API，未找到 request_qwen 函数")
        return "API 调用失败，请检查依赖和环境配置"
    
    def request_gemini(prompt):
        print("Warning: 无法调用 Gemini API，未找到 request_gemini 函数")
        return "API 调用失败，请检查依赖和环境配置"
    
    # 如果模板导入失败，定义一个简单的模板
    p_overall_assessment = p_overall_assessment_lite = """
    你是一位学术论文评审专家，需要基于论文各章节的评价生成一份整体评价报告。
    
    # 任务
    分析所有章节评价，识别整体优势、共同问题，并提出改进建议。
    
    # 输出格式
    你必须生成一个包含以下四个字段的JSON对象：
    1. `summary`: 论文整体质量概括(150-250字)
    2. `strengths`: 3-5条主要优势(数组)
    3. `weaknesses`: 3-5条主要不足(数组)
    4. `suggestions`: 3-5条改进建议(数组)
    
    {chapter_evaluations}
    """
    
    # 如果写作质量评估提示词导入失败，定义一个简单的模板
    p_writing_quality = """
    请分析以下论文章节内容，提供写作质量评估：
    
    {content}
    """

def get_tokenizer():
    """获取tokenizer，失败则返回None"""
    return _get_tokenizer()

def load_prompts(pkl_path: str, model_name: str) -> list[str]:
    """
    加载论文内容的提示词
    
    Args:
        pkl_path (str): pickle文件路径
        model_name (str): 模型名称
        
    Returns:
        list[str]: 提示词列表
    """
    tokenizer = None
    if not model_name.startswith("deepseek"):
        tokenizer = get_tokenizer()
    
    prompt_lst = []
    try:
        data = read_pickle(pkl_path)
        prompt = p_writing_quality.format(content=data.get('cn_abs', ''))
        prompt_lst.append(prompt)
        chapters = data.get('chapters', [])
        for i, ch in enumerate(chapters):
            if isinstance(ch, dict) and 'text_content' in ch:
                prompt = p_writing_quality.format(content=ch['text_content'])
                prompt_lst.append(prompt)
    except Exception as e:
        print(f"Error loading prompts: {e}")
        return []
        
    print(f'Loaded {len(prompt_lst)} prompts from {pkl_path}')
    for i, prompt in enumerate(prompt_lst):
        if tokenizer:
            try:
                token_len = tokenizer(prompt)['input_ids']
                print(f'Prompt {i} len: {len(prompt)}, token len: {len(token_len)}')
            except:
                print(f'Prompt {i} len: {len(prompt)}, token len: unknown')
        else:
            print(f'Prompt {i} len: {len(prompt)}')
    return prompt_lst

def load_paper_writing_quality_prompts(pkl_path: str, model_name: str) -> list[str]:
    """
    加载论文写作质量评估的提示词
    
    Args:
        pkl_path (str): pickle文件路径
        model_name (str): 模型名称
        
    Returns:
        list[str]: 提示词列表
    """
    prompt_lst = []
    try:
        data = read_pickle(pkl_path)
        keys = list(data.keys())
        for i, k in enumerate(keys):
            if k == 'chapters':
                chapters_list = data.get(k, [])
                for chap_idx, chapter_data in enumerate(chapters_list):
                    if isinstance(chapter_data, dict) and isinstance(chapter_data.get('text_content'), str):
                        prompt = p_writing_quality.format(content=chapter_data['text_content'])
                        prompt_lst.append(prompt)
                    else:
                        print(f"Skipping chapter {chap_idx} for key '{k}' due to missing or non-string text_content in {pkl_path}")
            elif isinstance(data[k], str):
                prompt = p_writing_quality.format(content=data[k])
                prompt_lst.append(prompt)
            else:
                print(f"Skipping key '{k}' because its value is not a string in {pkl_path}")
    except Exception as e:
        print(f"Error loading writing quality prompts: {e}")
        return []

    print(f'Loaded {len(prompt_lst)} prompts for paper writing quality from {pkl_path}')
    return prompt_lst

def _request_model(args: tuple[str, str]):
    """请求模型返回结果，自动处理错误"""
    prompt, model_name = args
    try:
        if model_name.startswith("deepseek"):
            return request_deepseek(prompt, model_name)
        if model_name == "gemini":
            return request_gemini(prompt)
        return request_qwen(prompt)
    except Exception as e:
        print(f"Error calling model: {e}")
        return f"模型调用失败: {str(e)}"

def generate_overall_assessment(chapter_evaluations, model_name="deepseek-chat"):
    """
    根据所有章节的评价生成整体评价
    
    Args:
        chapter_evaluations (list): 所有章节的评价列表
        model_name (str): 使用的模型名称
    
    Returns:
        dict: 包含summary, strengths, weaknesses, suggestions的整体评价
    """
    print("生成论文整体评价...")
    
    # 将所有章节评价拼接成一个字符串
    evaluations_text = "\n\n===== 章节分隔符 =====\n\n".join(
        [f"章节 {i+1} 评价:\n{eval_data}" for i, eval_data in enumerate(chapter_evaluations)]
    )
    
    # 根据评价数量选择使用完整版还是精简版提示词
    if len(evaluations_text) > 30000:  # 如果评价文本过长，使用精简版提示词
        prompt = p_overall_assessment_lite.format(chapter_evaluations=evaluations_text)
        print("使用精简版整体评价提示词")
    else:
        prompt = p_overall_assessment.format(chapter_evaluations=evaluations_text)
        print("使用完整版整体评价提示词")
    
    try:
        # 调用模型生成整体评价
        response = _request_model((prompt, model_name))
        
        # 尝试解析JSON响应
        try:
            # 查找JSON部分 - 有时模型会在JSON前后添加额外文本
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response
            
            result = json.loads(json_str)
            
            # 确保包含所有必需的字段
            required_fields = ["summary", "strengths", "weaknesses", "suggestions"]
            for field in required_fields:
                if field not in result:
                    result[field] = [] if field != "summary" else "未能生成有效的论文总结评价"
                    print(f"警告: 生成的整体评价缺少 '{field}' 字段，已添加默认值")
            
            return result
        except json.JSONDecodeError as e:
            print(f"错误: 无法解析整体评价响应为JSON: {e}")
            print(f"原始响应: {response}")
    except Exception as e:
        print(f"生成整体评价时发生错误: {e}")
    
    # 返回默认结果
    return {
        "summary": "系统无法生成有效的论文总结评价。请检查评价流程是否正确。",
        "strengths": ["论文结构基本完整", "研究方向有一定意义", "基本遵循了学术写作规范"],
        "weaknesses": ["评价系统未能正确提取论文优缺点", "需要手动进行详细评估", "可能存在格式或内容问题"],
        "suggestions": ["建议进行人工审阅论文质量", "检查系统评价流程是否存在问题", "重新运行评价流程尝试获取更准确的结果"]
    }

def infer(pkl_path: str, out_dir: str, processes: int = 8, model_name: str = "deepseek-chat"):
    """
    对单个文件进行推理，包括章节评价和整体评价
    
    Args:
        pkl_path (str): 输入文件路径
        out_dir (str): 输出目录
        processes (int): 处理线程数
        model_name (str): 模型名称
    """
    os.makedirs(out_dir, exist_ok=True)
    prompts = load_paper_writing_quality_prompts(pkl_path, model_name=model_name)
    filename = os.path.basename(pkl_path)
    chapter_results = []
    
    print('Starting inference for:', filename)
    
    # 检查是否有足够的提示词
    if not prompts:
        print(f"错误: 无法从 {pkl_path} 加载有效的提示词")
        return None
    
    # 使用多进程并行处理各章节
    try:
        from multiprocessing import Pool
        with Pool(processes=min(processes, len(prompts))) as pool:
            args = [(prompt, model_name) for prompt in prompts]
            responses = pool.map(_request_model, args)
    except Exception as e:
        print(f"多进程处理失败: {e}, 使用单进程处理")
        responses = [_request_model((prompt, model_name)) for prompt in prompts]
    
    # 保存章节评价结果
    for i, (prompt, response) in enumerate(zip(prompts, responses)):
        print(f'Processed prompt {i+1}/{len(prompts)}, {filename}')
        chapter_results.append({'input': prompt, 'output': response})
    
    # 提取所有章节的评价结果用于生成整体评价
    chapter_evaluations = [result['output'] for result in chapter_results]
    
    # 生成整体评价
    overall_assessment = generate_overall_assessment(chapter_evaluations, model_name)
    
    # 将整体评价添加到结果中
    final_results = {
        'chapter_evaluations': chapter_results,
        'overall_assessment': overall_assessment
    }
    
    # 保存结果
    output_path = os.path.join(out_dir, filename.replace('.pkl', '.json'))
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    
    print(f"评价结果已保存至: {output_path}")
    
    return overall_assessment

def quality_assessment():
    """
    测试函数，仅当本文件作为脚本执行时调用。
    """
    from glob import glob
    import random
    random.seed(42)
    
    pkl_path_lst = glob('/Users/yang/Documents/bupt/code/paper_eval/qy_data_pipeline/md2pkl/pkl/23.黄加宇-市优.pkl')
    print(f"Found {len(pkl_path_lst)} PKL files: {pkl_path_lst}")
    random.shuffle(pkl_path_lst)
    out_dir = '/Users/yang/Documents/bupt/code/paper_eval/qy_data_pipeline/paper_w_quality_ds_r1_i1'

    from multiprocessing import Pool
    with Pool(processes=8) as pool:
        pool.starmap(infer, [(pkl_path, out_dir) for pkl_path in pkl_path_lst])

if __name__ == "__main__":
    quality_assessment() 