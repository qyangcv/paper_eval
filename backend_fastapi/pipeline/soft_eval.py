"""
论文整体评估模块
将整篇论文内容作为整体进行评估
"""
import os
import sys
import json
import re
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, as_completed
from glob import glob
import warnings
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from config.data_config import FILE_CONFIG
from models.deepseek import request_deepseek
from tools.file_utils import read_pickle
from tools.logger import get_logger
from prompts.soft_criteria import (
    selection_prompt_logic, selection_prompt_innovation, selection_prompt_depth, 
    selection_prompt_replicability,
    p_overall_content_logic, p_overall_content_innovation, p_overall_content_depth,
    p_overall_content_replicability, p_overall_hallucination_detection
)

logger = get_logger(__name__)

def extract_toc_and_chapters(md_content: str) -> dict:
    """
    从Markdown文件中提取目录、摘要和章节内容
    Args:
        md_content: Markdown文档内容
    Returns:
        包含目录和章节内容的字典
    """
    content = md_content
    
    # 提取目录部分
    toc_start = content.find('目录')
    toc_end = content.find('#', toc_start)
    toc_content = content[toc_start:toc_end].strip() if toc_start != -1 and toc_end != -1 else ""
    
    # 清理目录内容：去除换行符，合并多个空格
    if toc_content:
        toc_content = re.sub(r'\n+', ' ', toc_content)  # 将一个或多个换行符替换为一个空格
        toc_content = re.sub(r'\s+', ' ', toc_content)  # 将多个连续空格合并为一个空格
        toc_content = toc_content.strip()
    
    # 提取摘要部分
    abstract_start = content.find('摘要')
    if abstract_start == -1:
        abstract_start = content.find('abstract')
    abstract_end = content.find('目录')
    abstract_content = content[abstract_start:abstract_end].strip() if abstract_start != -1 and abstract_end != -1 else ""
    
    # 清理摘要内容：去除换行符，合并多个空格
    if abstract_content:
        abstract_content = re.sub(r'\n+', ' ', abstract_content)  # 将一个或多个换行符替换为一个空格
        abstract_content = re.sub(r'\s+', ' ', abstract_content)  # 将多个连续空格合并为一个空格
        abstract_content = abstract_content.strip()

    # 提取各章节内容
    chapters = {}
    sections = re.findall(r'#+ (.+?)\n', content)
    for section in sections:
        if '目录' in section or '参考文献' in section or '致谢' in section or '附录' in section:
            continue
            
        # 提取章节内容
        section_start = content.find(f'# {section}')
        next_section = content.find('#', section_start + 1)
        section_content = content[section_start:next_section].strip() if next_section != -1 else content[section_start:].strip()
        
        # 提取子章节
        subsections = re.findall(r'## (.+?)\n', section_content)
        subchapter_contents = {}
        for sub in subsections:
            sub_start = section_content.find(f'## {sub}')
            next_sub = section_content.find('##', sub_start + 1)
            sub_content = section_content[sub_start:next_sub].strip() if next_sub != -1 else section_content[sub_start:].strip()
            subchapter_contents[sub] = sub_content
        
        chapters[section] = {
            'content': section_content,
            'subchapters': subchapter_contents
        }
    
    return {
        'toc': toc_content,
        'abstract': abstract_content,
        'chapters': chapters
    }

def generate_selection_prompt(toc: str, abstract: str, metric: str) -> str:
    """
    生成章节选择提示词（第一阶段）
    
    Args:
        toc: 论文目录
        abstract: 论文摘要
        metric: 评估维度
        
    Returns:
        str: 章节选择提示词
    """
    selection_prompt = {
        "logic": selection_prompt_logic,
        "innovation": selection_prompt_innovation,
        "depth": selection_prompt_depth,
        "replicability": selection_prompt_replicability,
    }[metric].format(toc=toc, abstract=abstract)
    return selection_prompt

def parse_selected_chapters(response: str) -> List[str]:
    """
    解析模型返回的章节选择结果
    
    Args:
        response: 模型返回的JSON字符串（直接包含章节选择结果）
        
    Returns:
        List[str]: 选中的章节标题列表
    """
    try:
        # 直接解析响应字符串为JSON
        result = json.loads(response)
        selected_chapters = result['selected_chapters']
        
        logger.info(f"成功解析选择的章节: {selected_chapters}")
        return selected_chapters
        
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"解析章节选择结果失败: {e}")
        # 处理异常：回复里可能带json代码块格式
        match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            logger.info(f"使用正则表达式再次尝试提取JSON")
            try:
                cleaned_content = match.group(1)
                result = json.loads(cleaned_content)
                selected_chapters = result['selected_chapters']
                logger.info(f"成功解析选择的章节: {selected_chapters}")
                return selected_chapters
            except (json.JSONDecodeError, KeyError) as e2:
                logger.error(f"正则提取后仍解析失败: {e2}")
        
        # 最后尝试：查找任何JSON对象
        json_match = re.search(r'\{[^{}]*"selected_chapters"[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                selected_chapters = result['selected_chapters']
                logger.info(f"通过模式匹配成功解析选择的章节: {selected_chapters}")
                return selected_chapters
            except (json.JSONDecodeError, KeyError) as e3:
                logger.error(f"模式匹配后仍解析失败: {e3}")
        
        logger.warning("无法解析章节选择结果，返回空列表")
        logger.debug(f"原始响应内容: {response[:500]}...")  # 只显示前500字符用于调试
        return []

def generate_final_assessment_prompt(selected_content: str, metric: str) -> str:
    """
    生成最终评估提示词（第二阶段）
    
    Args:
        selected_content: 选中章节的内容
        metric: 评估维度
        
    Returns:
        str: 最终评估提示词
    """
    final_prompt = {
        "logic": p_overall_content_logic,
        "innovation": p_overall_content_innovation,
        "depth": p_overall_content_depth,
        "replicability": p_overall_content_replicability,
    }[metric].format(content=selected_content)
    return final_prompt

def generate_hallucination_detection_prompt(
    dimension: str, abstract: str, eval_result: str, eval_requirement: str
) -> str:
    return p_overall_hallucination_detection.format(
        dimension=dimension,
        abstract=abstract,
        eval_requirement=eval_requirement,
        eval_result=eval_result
    )

def parse_hallucination_detection_result(response: str) -> dict:
    try:
        # 直接解析响应字符串为JSON
        result = json.loads(response)
        return result
        
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"解析幻觉检测结果失败: {e}")
        # 处理异常：回复里可能带json代码块格式
        match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            logger.info(f"使用正则表达式再次尝试提取JSON")
            try:
                cleaned_content = match.group(1)
                result = json.loads(cleaned_content)
                logger.info(f"成功解析幻觉检测结果")
                return result
            except (json.JSONDecodeError, KeyError) as e2:
                logger.error(f"正则提取后仍解析失败: {e2}")
        
        logger.warning("无法解析幻觉检测结果，返回空字典")
        logger.debug(f"原始响应内容: {response[:500]}...")  # 只显示前500字符用于调试
        return {}
        
def get_message(json_str: str):
    try:
        api_data = json.loads(json_str)
        content_str = api_data['choices'][0]['message']['content']
        return content_str
    except Exception as e:
        logger.error(f"解析JSON字符串失败: {e}")
        return json_str

def format_evaluation_result(result: dict) -> dict:
    """
    将评估结果转换为标准格式
    
    Args:
        result: 原始评估结果字典
        
    Returns:
        dict: 标准格式的评估结果
    """
    dimensions = []
    total_weighted_score = 0.0
    total_weight = 0.0
    
    for metric_key, metric_data in result.items():
        # 处理章节名称，将空格替换为下划线
        focus_chapter = [chapter.replace(" ", "_") for chapter in metric_data.get("focus_chapter", [])]
        
        dimension = {
            "name": metric_data.get("name", ""),
            "score": metric_data.get("score", 0),
            "full_score": metric_data.get("full_score", 10),
            "weight": metric_data.get("weight", 1.0),
            "focus_chapter": focus_chapter,
            "comment": metric_data.get("comment", ""),
            "advantages": metric_data.get("advantages", []),
            "weaknesses": metric_data.get("weaknesses", []),
            "suggestions": metric_data.get("suggestions", [])
        }
        
        dimensions.append(dimension)
        
        # 计算加权分数
        score = metric_data.get("score", 0)
        weight = metric_data.get("weight", 1.0)
        total_weighted_score += score * weight
        total_weight += weight
    
    # 计算总体分数（加权平均）
    overall_score = round(total_weighted_score / total_weight, 2) if total_weight > 0 else 0.0
    
    return {
        "overall_score": overall_score,
        "dimensions": dimensions
    }

def evaluate_single_metric(args):
    """
    评估单个维度的函数，用于多线程处理

    Args:
        args: 包含评估参数的元组 (metric, paper_data, dimension_mapping, model_name)

    Returns:
        tuple: (metric, result_data, overall_result_data)
    """
    metric, paper_data, dimension_mapping, model_name = args

    try:
        logger.info(f"开始评估维度: {metric}")

        # 第一阶段: 根据评价维度选择需要评估的章节
        selection_prompt = generate_selection_prompt(
            paper_data['toc'],
            paper_data['abstract'],
            metric
        )
        selected_chapters_result = request_deepseek(selection_prompt, model_name)
        selected_chapters_result = parse_selected_chapters(selected_chapters_result)

        # 检查API调用是否成功 - 修改为检查解析结果
        if not selected_chapters_result:
            logger.error(f"章节选择失败或解析失败: {metric}")
            return metric, None, None

        # 解析模型返回选择的章节
        selected_chapter_titles = selected_chapters_result

        if not selected_chapter_titles:
            logger.warning(f"未能选择到章节，跳过维度 {metric}")
            return metric, None, None

        # 获取选中章节的内容
        selected_content = ""
        for title in selected_chapter_titles:
            normalized_title = title.strip().lower()
            matched = False

            # 首先尝试精确匹配
            for chapter_title, chapter_data in paper_data['chapters'].items():
                normalized_chapter_title = chapter_title.strip().lower()
                if normalized_title == normalized_chapter_title:
                    selected_content += f"\n\n## {chapter_title}\n{chapter_data['content']}"
                    matched = True
                    break

            # 如果精确匹配失败，尝试模糊匹配（包含关系）
            if not matched:
                for chapter_title, chapter_data in paper_data['chapters'].items():
                    normalized_chapter_title = chapter_title.strip().lower()
                    if normalized_title in normalized_chapter_title or normalized_chapter_title in normalized_title:
                        selected_content += f"\n\n## {chapter_title}\n{chapter_data['content']}"
                        matched = True
                        logger.info(f"使用模糊匹配找到章节: '{title}' -> '{chapter_title}'")
                        break

            # 如果还是没找到，尝试匹配子章节
            if not matched:
                for chapter_title, chapter_data in paper_data['chapters'].items():
                    for sub_title, sub_content in chapter_data.get('subchapters', {}).items():
                        normalized_sub_title = sub_title.strip().lower()
                        if normalized_title in normalized_sub_title or normalized_sub_title in normalized_title:
                            selected_content += f"\n\n## {sub_title}\n{sub_content}"
                            matched = True
                            logger.info(f"在子章节中找到匹配: '{title}' -> '{sub_title}'")
                            break
                    if matched:
                        break

            if not matched:
                logger.warning(f"未找到匹配的章节: '{title}'")

        if not selected_content:
            logger.warning(f"未找到任何选中章节的内容，跳过维度 {metric}")
            return metric, None, None

        # 第二阶段：将选择好的章节内容和对应的评价提示词，一起输入给模型提问
        final_prompt = generate_final_assessment_prompt(selected_content, metric)
        final_assessment_result = request_deepseek(final_prompt, model_name)

        # 检查API调用是否成功
        if not final_assessment_result:
            logger.error(f"最终评估API调用失败或返回空结果: {metric}")
            return metric, None, None

        # 第三阶段：幻觉检测
        logger.info(f"开始对维度 {metric} 进行幻觉检测")

        final_assessment = final_assessment_result  # 默认使用原始结果
        hallucination_info = None

        # 解析幻觉检测结果
        for i in range(3):
            hallucination_prompt = generate_hallucination_detection_prompt(
                dimension=dimension_mapping[metric],
                abstract=paper_data['abstract'],
                eval_requirement=final_prompt,
                eval_result=final_assessment_result
            )
            hallucination_result = request_deepseek(hallucination_prompt, model_name)
            hallucination_data = parse_hallucination_detection_result(hallucination_result)

            if not hallucination_data:
                logger.warning(f"幻觉检测结果解析失败，使用原始评估结果: {metric}")
                hallucination_info = {
                    'detection_status': 'parse_failed',
                    'raw_response': hallucination_result
                }
                break
            elif 'hallucination_points' in hallucination_data and hallucination_data['hallucination_points']:
                # 检测到幻觉，使用修正后的结果
                logger.info(f"检测到 {len(hallucination_data['hallucination_points'])} 个幻觉点，使用修正后的结果: {metric}")
                final_assessment = json.dumps(hallucination_data['fixed_eval_result'], ensure_ascii=False)
                hallucination_info = {
                    'detection_status': 'hallucination_detected',
                    'hallucination_points': hallucination_data['hallucination_points'],
                    'original_assessment': final_assessment_result
                }
                break
            else:
                # 未检测到幻觉，使用原始结果
                logger.info(f"未检测到幻觉，使用原始评估结果: {metric}")
                hallucination_info = {
                    'detection_status': 'no_hallucination',
                    'verification': hallucination_data.get('verification', '所有陈述均有原文支持')
                }
                break

        # 保存结果
        overall_result_data = {
            'selected_chapters': selected_chapter_titles,
            'assessment': final_assessment,
            'selection_reasoning': selected_chapters_result,
            'final_prompt_used': final_prompt,
            'hallucination_detection': hallucination_info
        }

        # 解析最终评估结果用于标准格式输出
        try:
            final_data = json.loads(final_assessment)
        except json.JSONDecodeError as e:
            logger.error(f"解析最终评估结果失败: {e}")
            # 如果解析失败，使用默认值
            final_data = {
                'score': 0,
                'overall_assessment': '评估结果解析失败',
                'strengths': [],
                'weaknesses': [],
                'suggestions': []
            }

        result_data = {
            "name": dimension_mapping[metric],
            "score": final_data.get('score', 0),
            "full_score": 10,
            "weight": 1.0,
            "focus_chapter": selected_chapter_titles,
            "comment": final_data.get('overall_assessment', ''),
            "advantages": final_data.get('strengths', []),
            "weaknesses": final_data.get('weaknesses', []),
            "suggestions": final_data.get('suggestions', []),
        }

        logger.info(f"完成维度 {metric} 的评估")
        return metric, result_data, overall_result_data

    except Exception as e:
        logger.error(f"评估维度 {metric} 时出错: {e}")
        return metric, None, None

def eval(
    md_content: str,
    metrics: Optional[List[str]] = None,
    num_processes: int = 1,
    model_name: str = 'deepseek-chat',
    save_dir: Optional[str] = None
) -> dict:
    """
    对论文进行三阶段推理：章节选择 -> 内容评估 -> 幻觉检测
    
    Args:
        md_path: markdown文件路径
        metrics: 评估指标列表
        num_processes: 进程数
        model_name: 使用的模型名称
        save_dir: 结果保存目录
        
    Returns:
        dict: 包含评估结果的字典
    """
    try:
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        
        # 提取论文目录和章节内容
        paper_data = extract_toc_and_chapters(md_content)
        
        # 设置默认评估指标
        if metrics is None:
            metrics = [
                'logic',
                'innovation',
                'depth',
                'replicability',
            ]
        
        # 评估维度中英文映射
        dimension_mapping = {
            'logic': '逻辑连贯性与结构严谨性',
            'innovation': '学术贡献与创新性的实质性',
            'depth': '论证深度与批判性思维',
            'replicability': '研究的严谨性与可复现性'
        }
        
        overall_result = {}
        result = {}

        # 过滤支持的维度
        valid_metrics = [metric for metric in metrics if metric in dimension_mapping]
        if not valid_metrics:
            logger.warning("没有有效的评估维度")
            return format_evaluation_result({})

        # 使用多线程并行处理各个维度
        logger.info(f"开始并行评估 {len(valid_metrics)} 个维度: {valid_metrics}")

        # 准备参数
        eval_args = [
            (metric, paper_data, dimension_mapping, model_name)
            for metric in valid_metrics
        ]

        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=min(4, len(valid_metrics))) as executor:
            # 提交所有任务
            future_to_metric = {
                executor.submit(evaluate_single_metric, args): args[0]
                for args in eval_args
            }

            # 收集结果
            for future in as_completed(future_to_metric):
                metric = future_to_metric[future]
                try:
                    metric_name, result_data, overall_result_data = future.result()
                    if result_data is not None and overall_result_data is not None:
                        result[metric_name] = result_data
                        overall_result[metric_name] = overall_result_data
                        logger.info(f"维度 {metric_name} 评估完成")
                    else:
                        logger.warning(f"维度 {metric_name} 评估失败")
                except Exception as exc:
                    logger.error(f"维度 {metric} 评估时发生异常: {exc}")

        logger.info(f"一共完成 {len(result)} 个维度的评估")
        
        # 转换为标准格式
        standard_result = format_evaluation_result(result)
        
        # 保存结果到文件（保存标准格式）
        # if save_dir:
        #     # 生成带时间戳的文件名
        #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        #     base_filename = os.path.basename(md_path).replace('.md', '')
        #     filename = f"{base_filename}_softeval.json"
        #     output_file = os.path.join(save_dir, filename)
            
        #     with open(output_file, 'w', encoding='utf-8') as f:
        #         json.dump(standard_result, f, ensure_ascii=False, indent=4)
            
        #     logger.info(f"整体评估结果已保存到: {output_file}")
        
        return standard_result
        
    except Exception as e:
        logger.error(f"整体评估过程出错: {e}")
        raise

if __name__ == "__main__":
    """
    测试函数，仅当本文件作为脚本执行时调用。
    """
    random.seed(42)
    
    md_path = "/Users/yang/Documents/bupt/code/github/paper_eval/backend_fastapi/data/processed/龚礼盛-本科毕业论文.md"
    output_dir = "/Users/yang/Documents/bupt/code/github/paper_eval/backend_fastapi/data/output"
    logger.info(f"开始处理文件: {md_path}")
    eval(md_path, save_dir=str(output_dir))

