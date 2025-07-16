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

from models.deepseek import request_deepseek_md
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
    将响应格式从原始JSON列表转换为新的格式
    
    Args:
        responses (str): 原始响应字符串，包含JSON格式的问题列表
        ch_names (tuple): 章节名称候选集
        sub_ch_names (tuple): 小节名称候选集
        
    Returns:
        str: 转换后的格式化JSON字符串
    """
    try:
        # 解析JSON响应
        if isinstance(responses, str):
            json_match = re.search(r'\[.*\]', responses, re.DOTALL)
            issues_list = json.loads(json_match.group()) if json_match else []
        else:
            issues_list = responses
    except (json.JSONDecodeError, ValueError):
        issues_list = []
    
    # 初始化统计
    severity_distribution = {"高": 0, "中": 0, "低": 0}
    issue_types_set = set()
    by_chapter = {}
    
    # 处理每个问题
    for issue in issues_list:
        # 获取基本信息
        issue_type = issue.get("type", "未知")
        severity = issue.get("severity", "中")
        chapter = issue.get("chapter", "未知章节").replace(" ", "_")
        sub_chapter = issue.get("sub_chapter", "未知小节").replace(" ", "_")
        
        # 统计
        issue_types_set.add(issue_type)
        severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # 构造问题项（暂时不分配ID）
        formatted_issue = {
            "type": issue_type,
            "severity": severity,
            "sub_chapter": sub_chapter,
            "original_text": issue.get("original_text", ""),
            "detail": issue.get("detail", ""),
            "suggestion": issue.get("suggestion", "")
        }
        
        # 按章节分组
        by_chapter.setdefault(chapter, []).append(formatted_issue)
    
    # 定义章节排序函数
    def get_chapter_order(chapter_name):
        """定义章节排序优先级"""
        if chapter_name == "摘要":
            return (0, 0)
        elif chapter_name == "Abstract":
            return (0, 1)
        elif "第" in chapter_name and "章" in chapter_name:
            # 提取章节编号
            try:
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
            return (1, 999)
        else:
            return (2, 999)
    
    # 按章节顺序排序并重新分配ID
    ordered_chapters = sorted(by_chapter.keys(), key=get_chapter_order)
    ordered_by_chapter = {}
    current_id = 1
    
    # 定义小节排序函数
    def get_subsection_order(issue):
        """定义小节排序优先级"""
        sub_chapter = issue.get("sub_chapter", "")
        try:
            # 提取小节编号，如 "1.1", "1.2", "2.3" 等
            import re
            match = re.search(r'(\d+)\.(\d+)', sub_chapter)
            if match:
                major_num = int(match.group(1))
                minor_num = int(match.group(2))
                return (major_num, minor_num)
            else:
                # 如果没有找到数字编号，按字符串排序
                return (999, 999)
        except:
            return (999, 999)
    
    for chapter in ordered_chapters:
        ordered_by_chapter[chapter] = []
        
        # 对当前章节内的问题按小节顺序排序
        chapter_issues = sorted(by_chapter[chapter], key=get_subsection_order)
        
        for issue in chapter_issues:
            # 为每个问题重新分配ID
            issue_with_id = {
                "id": current_id,
                **issue
            }
            ordered_by_chapter[chapter].append(issue_with_id)
            current_id += 1
    
    # 构造结果
    result = {
        "summary": {
            "total_issues": len(issues_list),
            "issue_types": list(issue_types_set),
            "severity_distribution": severity_distribution
        },
        "by_chapter": ordered_by_chapter
    }
    
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


def eval(md_content):
    # 提取目录、摘要、章节内容、参考文献
    toc = extract_toc(md_content)
    abs = extract_abstract(md_content)
    chapters = extract_chapters(md_content)
    references = extract_references(md_content)
    
    if not toc or not abs or not chapters:
        logger.error("Markdown格式不符合要求，无法提取目录、摘要或正文内容")
        return []

    # 检查正文中的主观用词：“我们”“我”
    colloquial_cases = _scan_colloquial_words(chapters)

    # 构建提示词
    prompts = build_prompts(abs, chapters)
    user_prompts, ch_names, sub_ch_names = zip(*prompts)

    # infer
    logger.info("INFER | 开始并行调用API进行写作质量问题分析...")
    start_time_infer = time.time()
    request_with_format = partial(request_deepseek_md, system_prompt, format="md")
    with Pool(processes=16) as pool:
        responses = pool.map(request_with_format, user_prompts)
    end_time_infer = time.time()
    infer_duration = end_time_infer - start_time_infer
    logger.info(f"INFER | Infer阶段完成，耗时: {infer_duration:.2f} 秒")

    # aggregate
    logger.info("AGGREGATE | 开始调用API对结果进行优化...")
    start_time_aggregate = time.time()
    agg_prompt = aggregate_prompt.format(context_1='\n'.join(responses), context_2='\n'.join(colloquial_cases), ch_names=ch_names, sub_ch_names=sub_ch_names)
    responses = request_deepseek_md(agg_prompt, system_prompt, format='md')
    end_time_aggregate = time.time()
    aggregate_duration = end_time_aggregate - start_time_aggregate
    logger.info(f"AGGREGATE | Aggregate阶段完成，耗时: {aggregate_duration:.2f} 秒")

    # formatting
    responses = formatting_js(responses, ch_names, sub_ch_names)

    return responses


if __name__ == "__main__":
    md_path = "/Users/yang/Documents/bupt/code/github/paper_eval/backend_fastapi/data/processed/龚礼盛-本科毕业论文.md"
    md_content = load_md(md_path)
    responses = eval(md_content)
    
    out_path = "/Users/yang/Documents/bupt/code/github/paper_eval/backend_fastapi/data/output/龚礼盛-本科毕业论文.json"
    if isinstance(responses, str):
        # 如果是JSON字符串，先解析为字典
        responses_dict = json.loads(responses)
    else:
        # 如果已经是字典，直接使用
        responses_dict = responses
    # 保存为格式化的JSON
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(responses_dict, f, ensure_ascii=False, indent=2)
    print(f'✅ 结果已保存到: {out_path}')