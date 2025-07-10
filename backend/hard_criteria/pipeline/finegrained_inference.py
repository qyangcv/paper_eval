"""
批量推理模块
用于对多个论文文件进行批量质量评估
"""

# 导入标准库
import os
import sys
import json
from multiprocessing import Pool
import warnings

# 导入项目模块
from models.deepseek import request_deepseek
from models.qwen import request_qwen
from models.gemini import request_gemini
from prompts.assess_detail_prompt import (
    p_wq_zh,
    p_wq_en,
    p_wq_col,
    p_wq_for,
    p_wq_ref
)
from tools.file_utils import read_pickle
from tools.logger import get_logger
from config.data_config import FILE_CONFIG
from config.model_config import MODEL_CONFIG

logger = get_logger(__name__)

def load_context(pkl_path: str, model_name: str) -> list[str]:
    """
    加载论文内容
    
    Args:
        pkl_path (str): pickle文件路径
        model_name (str): 模型名称
        
    Returns:
        list[str]: 论文内容列表
    """
    # Use safe tokenizer import
    # if not model_name.startswith("deepseek"):
    #     _get_tokenizer(model_name)
    
    context_lst = []
    data = read_pickle(pkl_path)
    keys = list(data.keys())
    for i, k in enumerate(keys):
        if k == 'chapters':
            chapters_list = data.get(k, [])
            for chap_idx, chapter_data in enumerate(chapters_list):
                if isinstance(chapter_data, dict) and isinstance(chapter_data.get('content'), str):
                    c = chapter_data['content']
                    context_lst.append(c)
                else:
                    print(f"Skipping chapter {chap_idx} for key '{k}' due to missing or non-string content in {pkl_path}")
        elif isinstance(data[k], str):
            c = data[k]
            context_lst.append(c)
        else:
            print(f"Skipping key '{k}' because its value is not a string in {pkl_path}")

    print(f'Loaded {len(context_lst)} chapters for paper writing quality from {pkl_path}')
    return context_lst

def load_prompts(context: list[str]) -> list[str]:
    """
    根据内容生成提示词列表
    
    Args:
        context (list[str]): 论文内容列表
        
    Returns:
        list[str]: 提示词列表
    """
    instructions = [p_wq_zh, p_wq_en, p_wq_col, p_wq_for, p_wq_ref]
    prompt_lst = []
    for idx_c, c in enumerate(context):
        for idx_i, i in enumerate(instructions):
            prompt = i.format(content=c)
            prompt_lst.append(prompt)
    return prompt_lst

def _request_model(args: tuple[str, str]):
    """根据模型名称调用对应的请求接口。

    Args:
        args: (prompt, model_name)

    Returns:
        str: 模型返回的结果 JSON 字符串
    """
    prompt, model_name = args
    try:
        if model_name.startswith("deepseek"):
            response = request_deepseek(prompt, model_name)
        elif model_name == "gemini":
            response = request_gemini(prompt)
        elif model_name == "qwen":
            response = request_qwen(prompt)
        else:
            raise ValueError(f"Invalid model name: {model_name}")
        return {'input': prompt, 'output': response}
    except Exception as e:
        logger.error(f"不存在该模型: {e}")
        return {'input': prompt, 'error': str(e)}

def infer(pkl_path: str, out_dir: str, num_processes: int = 16, model_name: str = "deepseek-chat"):
    """
    对单个文件进行批量推理
    
    Args:
        pkl_path (str): 输入文件路径
        out_dir (str): 输出目录
        num_processes (int): 并行处理的进程数
        model_name (str): 模型名称
    """
    try:
        # 确保输出目录存在
        os.makedirs(out_dir, exist_ok=True)
        
        # 加载上下文和提示词
        logger.info(f"使用模型: {model_name}")
        
        context = load_context(pkl_path, model_name)
        prompts = load_prompts(context)
        
        # 准备进程池参数
        pool_args = [(prompt, model_name) for prompt in prompts]
        
        # 使用进程池处理章节
        with Pool(processes=num_processes) as pool:
            results = pool.map(_request_model, pool_args)
        
        # 保存结果
        filename = os.path.basename(pkl_path)
        output_file = os.path.join(out_dir, filename.replace('.pkl', '.json'))
        
        with open(output_file, 'w', encoding=FILE_CONFIG['encoding']) as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        logger.info(f"推理完成，结果已保存到: {output_file}")
        
    except Exception as e:
        logger.error(f"推理过程出错: {e}")

def batch_inference():
    """
    批量推理主函数
    """
    from glob import glob
    import random
    random.seed(42)
    
    pkl_path_lst = glob('/Users/yang/Documents/bupt/code/paper_eval/qy_data_pipeline/docx_example/龚礼盛-本科毕业论文.pkl')
    out_dir = '/Users/yang/Documents/bupt/code/paper_eval/qy_data_pipeline/docx_example/api_1d1t'

    num_processes_to_use = 16

    if pkl_path_lst:
        infer(pkl_path_lst[0], out_dir, num_processes=num_processes_to_use)
    else:
        print("No PKL files found to process.")

if __name__ == "__main__":
    batch_inference() 