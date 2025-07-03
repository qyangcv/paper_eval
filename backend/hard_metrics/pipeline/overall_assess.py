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
from typing import List, Dict, Any
from multiprocessing import Pool
from glob import glob
import warnings
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from config.data_config import FILE_CONFIG
from config.model_config import MODEL_CONFIG
from models.request_model import _request_model
from tools.file_utils import read_pickle
from tools.logger import get_logger
from prompts.overall_assess_prompt import (
    selection_prompt_logic, selection_prompt_innovation, selection_prompt_depth, 
    selection_prompt_replicability, selection_prompt_quality,
    p_overall_content_logic, p_overall_content_innovation, p_overall_content_depth,
    p_overall_content_replicability, p_overall_content_quality
)

logger = get_logger(__name__)

def extract_toc_and_chapters(md_path: str) -> dict:
    """
    从Markdown文件中提取目录、摘要和章节内容
    Args:
        md_path: Markdown文件路径
    Returns:
        包含目录和章节内容的字典
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
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
        "quality": selection_prompt_quality,
    }[metric].format(toc=toc, abstract=abstract)
    return selection_prompt

def parse_selected_chapters(response: str) -> List[str]:
    """
    解析模型返回的章节选择结果
    
    Args:
        response: 模型返回的JSON字符串
        
    Returns:
        List[str]: 选中的章节标题列表
    """
    try:
        # 尝试解析JSON
        api_data = json.loads(response)
        content_str = api_data['choices'][0]['message']['content']
        print(content_str)
        selected_chapters=json.loads(content_str)['selected_chapters']
        
        logger.info(f"成功解析选择的章节: {selected_chapters}")
        return selected_chapters
        
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"解析章节选择结果失败: {e}")
        # 降级处理：从响应中提取可能的章节名称
        chapters = re.findall(r'["\']([^"\']*章[^"\']*)["\']', response)
        if chapters:
            logger.info(f"使用正则表达式提取到章节: {chapters}")
            return chapters[:5]  # 最多返回5个章节
        else:
            logger.warning("无法解析章节选择结果，返回空列表")
            return []

def generate_overall_prompt(full_content: str) -> str:
    """
    生成整体评估提示词
    
    Args:
        full_content: 完整论文内容
        
    Returns:
        str: 格式化后的提示词
    """
    try:
        return p_overall_content_logic.format(
            paper_content=full_content
        )
    except KeyError as e:
        logger.error(f"提示词模板缺少必要参数: {e}")
        raise

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
        "quality": p_overall_content_quality,
    }[metric].format(content=selected_content)
    return final_prompt

def infer(
    md_path: str,
    metrics: List[str] = None,
    num_processes: int = 1,
    model_name: str = 'deepseek-chat',
    save_dir: str = None
) -> dict:
    """
    对论文进行两阶段推理
    
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
        paper_data = extract_toc_and_chapters(md_path)
        
        # 设置默认评估指标
        if metrics is None:
            metrics = [
                'logic',
                'innovation',
                'depth',
                'replicability',
                'quality',
            ]
        
        overall_result = {}
        
        for metric in metrics:
            logger.info(f"开始评估维度: {metric}")
            
            # 第一阶段: 根据评价维度选择需要评估的章节
            selection_prompt = generate_selection_prompt(
                paper_data['toc'], 
                paper_data['abstract'], 
                metric
            )
            selected_chapters_result = _request_model((selection_prompt, model_name))
            
            # 检查API调用是否成功
            if 'error' in selected_chapters_result:
                logger.error(f"章节选择API调用失败: {selected_chapters_result['error']}")
                continue
                
            # 解析模型返回选择的章节
            selected_chapter_titles = parse_selected_chapters(selected_chapters_result['output'])
            
            if not selected_chapter_titles:
                logger.warning(f"未能选择到章节，跳过维度 {metric}")
                continue
            
            # 获取选中章节的内容
            selected_content = ""
            for title in selected_chapter_titles:
                for chapter_title, chapter_data in paper_data['chapters'].items():
                    if title in chapter_title or chapter_title in title:
                        selected_content += f"\n\n## {chapter_title}\n{chapter_data['content']}"
                        break
            
            if not selected_content:
                logger.warning(f"未找到选中章节的内容，跳过维度 {metric}")
                continue
            
            # 第二阶段：将选择好的章节内容和对应的评价提示词，一起输入给模型提问
            final_prompt = generate_final_assessment_prompt(selected_content, metric)
            final_assessment_result = _request_model((final_prompt, model_name))
            
            # 检查API调用是否成功
            if 'error' in final_assessment_result:
                logger.error(f"最终评估API调用失败: {final_assessment_result['error']}")
                continue
            
            # 保存结果
            overall_result[metric] = {
                'selected_chapters': selected_chapter_titles,
                'assessment': final_assessment_result['output'],
                'selection_reasoning': selected_chapters_result.get('output', ''),
                'final_prompt_used': final_prompt
            }
            
            logger.info(f"完成维度 {metric} 的评估")
        
        # 保存结果到文件
        if save_dir:
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = os.path.basename(md_path).replace('.md', '')
            filename = f"{base_filename}_overall_assessment_{timestamp}.json"
            output_file = os.path.join(save_dir, filename)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(overall_result, f, ensure_ascii=False, indent=4)
            
            logger.info(f"整体评估结果已保存到: {output_file}")
        
        return overall_result
        
    except Exception as e:
        logger.error(f"整体评估过程出错: {e}")
        raise

if __name__ == "__main__":
    """
    测试函数，仅当本文件作为脚本执行时调用。
    """
    random.seed(42)
    
    try:
        # 从配置文件获取基础路径
        base_dir = FILE_CONFIG.get('base_dir')
        input_root = FILE_CONFIG.get('processed_data_dir')
        output_root = FILE_CONFIG.get('output_data_dir')
        
        input_dir = os.path.join(input_root, 'docx')
        output_dir = os.path.join(output_root, 'docx')

        # 获取所有md文件（假设处理的是markdown文件）
        md_pattern = str(input_dir) + '/*.md'
        md_lst = glob(md_pattern)
        
        if not md_lst:
            logger.warning(f"在 {input_dir} 中没有找到要处理的MD文件")
            
        # 处理每个文件
        for md_path in md_lst:
            try:
                logger.info(f"开始处理文件: {md_path}")
                infer(md_path, save_dir=str(output_dir))
            except Exception as e:
                logger.error(f"处理文件 {md_path} 时出错: {e}")
                continue
                
    except Exception as e:
        logger.error(f"程序执行出错: {e}")