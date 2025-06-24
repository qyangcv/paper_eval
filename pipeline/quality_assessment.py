"""
论文质量评估模块
用于评估论文的写作质量，包括摘要和各个章节
"""

import os
import sys
import json
from transformers import AutoTokenizer

from models import request_qwen, request_deepseek
from models import request_gemini
from prompts import p_wq_zh, p_wq_en, p_wq_col, p_wq_for, p_wq_ref, p_writing_quality
from utils import read_pickle

def load_prompts(pkl_path: str, model_name: str) -> list[str]:
    """
    加载论文内容的提示词
    
    Args:
        pkl_path (str): pickle文件路径
        model_name (str): 模型名称
        
    Returns:
        list[str]: 提示词列表
    """
    if not model_name.startswith("deepseek"):
        tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-0.6B')
    prompt_lst = []
    data = read_pickle(pkl_path)
    prompt = prompt_tempelate_minus_abstract.format(content=data['cn_abs'])
    prompt_lst.append(prompt)
    chapters = data['chapters']
    for i, ch in enumerate(chapters):
        prompt = prompt_tempelate_minus_chapters.format(content=ch['text_content'])
        prompt_lst.append(prompt)
        
    print(f'Loaded {len(prompt_lst)} prompts from {pkl_path}')
    for i, prompt in enumerate(prompt_lst):
        if not model_name.startswith("deepseek"):
            token_len = tokenizer(prompt)['input_ids']
            print(f'Prompt {i} len: {len(prompt)}, token len: {len(token_len)}')
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
    if not model_name.startswith("deepseek"):
        tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-0.6B')
    prompt_lst = []
    data = read_pickle(pkl_path)
    keys = list(data.keys())
    for i, k in enumerate(keys):
        if k == 'chapters':
            chapters_list = data.get(k, [])
            for chap_idx, chapter_data in enumerate(chapters_list):
                if isinstance(chapter_data, dict) and isinstance(chapter_data.get('text_content'), str):
                    prompt = paper_writing_quality_prompt.format(content=chapter_data['text_content'])
                    prompt_lst.append(prompt)
                else:
                    print(f"Skipping chapter {chap_idx} for key '{k}' due to missing or non-string text_content in {pkl_path}")
        elif isinstance(data[k], str):
            prompt = paper_writing_quality_prompt.format(content=data[k])
            prompt_lst.append(prompt)
        else:
            print(f"Skipping key '{k}' because its value is not a string in {pkl_path}")

    print(f'Loaded {len(prompt_lst)} prompts for paper writing quality from {pkl_path}')
    return prompt_lst

def _request_model(args: tuple[str, str]):
    prompt, model_name = args
    if model_name.startswith("deepseek"):
        return request_deepseek(prompt, model_name)
    if model_name == "gemini":
        return request_gemini(prompt)
    return request_qwen(prompt)

def infer(pkl_path: str, out_dir: str, model_name: str = "deepseek-chat"):
    """
    对单个文件进行推理
    
    Args:
        pkl_path (str): 输入文件路径
        out_dir (str): 输出目录
    """
    os.makedirs(out_dir, exist_ok=True)
    prompts = load_paper_writing_quality_prompts(pkl_path, model_name=model_name)
    filename = os.path.basename(pkl_path)
    out = []
    print('Starting inference for:', filename)
    for i, prompt in enumerate(prompts):
        print(f'Processing prompt {i+1}/{len(prompts)}, {filename}')
        response = _request_model((prompt, model_name))
        out.append({'input': prompt, 'output': response})

    with open(os.path.join(out_dir, filename.replace('.pkl', '.json')), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=4)

def quality_assessment():
    """
    质量评估主函数
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