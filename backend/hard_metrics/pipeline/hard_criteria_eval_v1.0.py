"""
对论文的硬指标作评价

- 修改自: chapter_inference.py
- 评价标准: prompts/hard_criteria.py
"""

import os
import sys
from multiprocessing import Pool
from functools import partial

# 添加父路径到python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.deepseek import request_deepseek
# from config.data_config import FILE_CONFIG
from tools.logger import get_logger
from tools.hard_criteria.extract_md import (
    load_md,
    extract_toc,
    extract_abstract,
    extract_chapters,
    extract_references
)
from tools.hard_criteria.scan_colloquial_word import scan_colloquial_words
from prompts.hard_criteria import system_prompt, context_prompt, aggregate_prompt


# 创建日志记录器
logger = get_logger(__name__)

def build_prompts(abs, chapters):
    # context = dict()
    
    # # 提取目录、中英文摘要、参考文献
    # context['toc'] = toc
    # context['abs_zh'] = abs['摘要']
    # context['abs_en'] = abs['Abstract']
    # context['references'] = references

    # # 提取章节内容，按二级标题 ## 提取
    # sub_chapters = dict()
    # for ch_name, ch in chapters.items():
    #     subchapters = ch.get('subchapters', {})
    #     for sub_ch_name, sub_ch in subchapters.items():
    #         sub_chapters[sub_ch_name] = {
    #             'content': sub_ch,
    #             'parent_chapter': ch_name
    #         }
    # context['chapters'] = sub_chapters

    # 构建提示词
    prompt_lst = list()
    prompt_lst.append(context_prompt.format(context=abs['摘要'], section='摘要'))
    prompt_lst.append(context_prompt.format(context=abs['Abstract'], section='Abstract'))
    
    # 提取章节内容，按二级标题'##'提取
    for ch_name, ch in chapters.items():
        subchapters = ch.get('subchapters', {})
        for sub_ch_name, sub_ch in subchapters.items():
            prompt_lst.append(context_prompt.format(context=sub_ch, section=f"章节：{ch_name} - {sub_ch_name}"))
    
    return prompt_lst
        
def _scan_colloquial_words(chapters):
    out = list()
    for ch_name, ch in chapters.items():
        case = scan_colloquial_words(ch.get('content', {}))
        if case:
            out.extend(case)
    return out


def eval(md_path):
    # 加载Markdown文件内容
    md = load_md(md_path)

    # 提取目录、摘要、章节内容、参考文献
    toc = extract_toc(md)
    abs = extract_abstract(md)
    chapters = extract_chapters(md)
    references = extract_references(md)

    # 检查正文中的主观用词：“我们”“我”
    colloquial_cases = _scan_colloquial_words(chapters)

    # 构建提示词
    user_prompts = build_prompts(abs, chapters)
    
    # infer
    request_with_format = partial(request_deepseek, system_prompt, format="md")
    with Pool(processes=16) as pool:
        responses = pool.map(request_with_format, user_prompts)

    # aggregate
    agg_prompt = aggregate_prompt.format(context='\n'.join(colloquial_cases)+'\n'.join(responses))
    responses = request_deepseek(agg_prompt, system_prompt, format='md')

    # 保存结果
    md_name = os.path.basename(md_path)
    o_dir = '/Users/yang/Documents/bupt/code/github/paper_eval/backend/hard_metrics/data/output/hard_criteria_eval_v1.0'
    if not os.path.exists(o_dir):
        os.makedirs(o_dir)
    o_file = os.path.join(o_dir, md_name.replace('.md', '_eval.md'))
    with open(o_file, 'w', encoding='utf-8') as f:
        f.write(responses)


if __name__ == "__main__":
    md_path = "/Users/yang/Documents/bupt/code/github/paper_eval/backend/hard_metrics/data/processed/docx/龚礼盛-本科毕业论文.md"
    eval(md_path)