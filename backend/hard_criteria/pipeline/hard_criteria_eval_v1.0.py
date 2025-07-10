"""
对论文的硬指标作评价

- 修改自: chapter_inference.py
- 评价标准: prompts/hard_criteria.py
"""

import os
import sys
import json
import re
import time
from collections import defaultdict
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

def formatting_js(responses, ch_names, sub_ch_names):
    """
    将响应格式从原始JSON列表转换为新的JavaScript格式
    
    Args:
        responses (str): 原始响应字符串，包含JSON格式的问题列表
        ch_names (tuple): 章节名称候选集
        sub_ch_names (tuple): 小节名称候选集
        
    Returns:
        str: 转换后的JavaScript格式字符串
    """
    try:
        # 尝试解析JSON响应
        # 如果responses是字符串，需要先解析
        if isinstance(responses, str):
            # 使用正则表达式提取JSON部分
            json_match = re.search(r'\[.*\]', responses, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                issues_list = json.loads(json_str)
            else:
                # 如果没有找到JSON，返回空结果
                issues_list = []
        else:
            issues_list = responses
            
    except (json.JSONDecodeError, ValueError):
        # 如果解析失败，返回空结果
        issues_list = []
    
    # 统计信息
    total_issues = len(issues_list)
    issue_types_set = set()
    by_chapter = {}
    
    # 问题类型映射（从原始类型到目标类型）
    type_mapping = {
        "主观用词": "主观用词",
        "错别字": "错别字", 
        "逻辑混乱": "逻辑混乱",
        "搭配不当": "搭配不当",
        "指代不清": "指代不清",
        "标点混用": "标点混用"
    }
    
    # 处理每个问题
    for i, issue in enumerate(issues_list, 1):
        # 获取问题类型
        original_type = issue.get("type", "未知")
        mapped_type = type_mapping.get(original_type, original_type)
        issue_types_set.add(mapped_type)
        
        # 获取章节名和小节名，并替换空格为下划线
        chapter = issue.get("chapter", "未知章节").replace(" ", "_")
        sub_chapter = issue.get("sub_chapter", "未知小节").replace(" ", "_")
        
        # 构造新格式的问题项（暂时不设置id）
        formatted_issue = {
            "type": mapped_type,
            "sub_chapter": sub_chapter,
            "original_text": issue.get("original_text", ""),
            "detail": issue.get("detail", ""),
            "suggestion": issue.get("suggestion", "")
        }
        
        # 按章节分组
        if chapter not in by_chapter:
            by_chapter[chapter] = []
        by_chapter[chapter].append(formatted_issue)
    
    # 定义章节顺序
    def get_chapter_order(chapter_name):
        """定义章节排序优先级"""
        if chapter_name == "摘要":
            return (0, 0)
        elif chapter_name == "Abstract":
            return (0, 1)
        elif chapter_name.startswith("第") and "章" in chapter_name:
            # 提取章节编号，如"第一章"、"第二章"等
            try:
                # 尝试提取数字或中文数字
                import re
                match = re.search(r'第([一二三四五六七八九十\d]+)章', chapter_name)
                if match:
                    num_str = match.group(1)
                    # 中文数字映射
                    chinese_num_map = {
                        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
                    }
                    if num_str in chinese_num_map:
                        return (1, chinese_num_map[num_str])
                    else:
                        return (1, int(num_str))
            except:
                pass
            return (1, 999)  # 无法解析的章节放到后面
        else:
            return (2, 999)  # 其他章节放到最后
    
    # 按章节顺序排序
    ordered_chapters = sorted(by_chapter.keys(), key=get_chapter_order)
    ordered_by_chapter = {}
    current_id = 1
    
    # 按章节顺序重新分配ID
    for chapter in ordered_chapters:
        ordered_by_chapter[chapter] = []
        for issue in by_chapter[chapter]:
            # 为每个问题重新分配ID
            issue_with_id = {
                "id": current_id,
                **issue  # 展开原有的问题数据
            }
            ordered_by_chapter[chapter].append(issue_with_id)
            current_id += 1
    
    # 构造最终结果
    result = {
        "issue_list": {
            "summary": {
                "total_issues": total_issues,
                "issue_types": list(issue_types_set)
            },
            "by_chapter": ordered_by_chapter
        }
    }
    
    # 转换为格式化的JSON字符串
    return json.dumps(result, ensure_ascii=False, indent=2)


def build_prompts(abs, chapters):
    # 构建提示词
    prompt_lst = list()
    prompt_lst.append((context_prompt.format(context=abs['摘要'], section='摘要', chapter='摘要', sub_chapter='摘要'), '摘要', '摘要'))
    prompt_lst.append((context_prompt.format(context=abs['Abstract'], section='Abstract', chapter='Abstract', sub_chapter='Abstract'), 'Abstract', 'Abstract'))
    
    # 提取章节内容，按二级标题'##'提取
    for ch_name, ch in chapters.items():
        subchapters = ch.get('subchapters', {})
        for sub_ch_name, sub_ch in subchapters.items():
            prompt_lst.append((context_prompt.format(context=sub_ch, section=f"章节：{ch_name} - {sub_ch_name}", chapter=ch_name, sub_chapter=sub_ch_name), ch_name, sub_ch_name))
    
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
    prompts = build_prompts(abs, chapters)
    user_prompts, ch_names, sub_ch_names = zip(*prompts)

    # infer
    logger.info("开始并行调用API进行章节分析...")
    start_time_infer = time.time()
    request_with_format = partial(request_deepseek, system_prompt, format="md")
    with Pool(processes=16) as pool:
        responses = pool.map(request_with_format, user_prompts)
    end_time_infer = time.time()
    infer_duration = end_time_infer - start_time_infer
    logger.info(f"Infer阶段完成，耗时: {infer_duration:.2f} 秒")

    # aggregate
    logger.info("开始调用API进行结果聚合...")
    start_time_aggregate = time.time()
    agg_prompt = aggregate_prompt.format(context_1='\n'.join(responses), context_2='\n'.join(colloquial_cases), ch_names=ch_names, sub_ch_names=sub_ch_names)
    responses = request_deepseek(agg_prompt, system_prompt, format='md')
    end_time_aggregate = time.time()
    aggregate_duration = end_time_aggregate - start_time_aggregate
    logger.info(f"Aggregate阶段完成，耗时: {aggregate_duration:.2f} 秒")

    # formatting
    responses = formatting_js(responses, ch_names, sub_ch_names)

    # 保存结果
    md_name = os.path.basename(md_path)
    o_dir = '/Users/yang/Documents/bupt/code/github/paper_eval/backend/hard_criteria/data/output/hard_criteria_eval_v1.0'
    if not os.path.exists(o_dir):
        os.makedirs(o_dir)
    # 保存为JSON文件
    json_file = os.path.join(o_dir, md_name.replace('.md', '_eval.json'))
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(responses)


if __name__ == "__main__":
    md_path = "/Users/yang/Documents/bupt/code/github/paper_eval/backend/hard_criteria/data/processed/docx/龚礼盛-本科毕业论文.md"
    eval(md_path)