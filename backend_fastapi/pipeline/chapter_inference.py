"""
章节推理模块
用于对论文的各个章节进行硬指标质量评估
"""

import json
import logging
from typing import List, Dict, Any, Optional, Callable
from ..models.model_manager import request_model
from ..prompts.chapter_prompt import p_chapter_assessment
from ..tools.logger import get_logger

logger = get_logger(__name__)

def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """
    从模型响应中提取JSON数据
    
    Args:
        response: 模型原始响应
        
    Returns:
        Optional[Dict[str, Any]]: 提取的JSON数据，如果提取失败则返回None
    """
    try:
        # 尝试直接解析JSON
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # 尝试从代码块中提取JSON
    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 尝试从其他格式中提取JSON
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    logger.warning(f"无法从响应中提取有效的JSON: {response[:200]}...")
    return None

def process_chapter_evaluation(
    chapter_content: str, 
    model_name: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Dict[str, Any]:
    """
    处理单个章节的评估
    
    Args:
        chapter_content: 章节内容
        model_name: 使用的模型名称
        progress_callback: 进度回调函数
        
    Returns:
        Dict[str, Any]: 章节评估结果
    """
    try:
        if progress_callback:
            progress_callback(0.1, "准备章节评估...")
        
        # 生成评估提示词
        prompt = p_chapter_assessment.format(content=chapter_content)
        
        if progress_callback:
            progress_callback(0.3, f"使用{model_name}进行章节分析...")
        
        # 调用模型
        result = request_model(prompt, model_name)
        
        if progress_callback:
            progress_callback(0.7, "处理评估结果...")
        
        # 检查是否有错误
        if result.get('status') == 'error':
            logger.error(f"章节评估失败: {result.get('error')}")
            return {
                "chapter": "未知章节",
                "error": result.get('error', '评估失败'),
                "status": "error"
            }
        
        # 提取评估结果
        eval_data = extract_json_from_response(result.get('output', '{}'))
        
        if not eval_data:
            logger.warning("无法提取有效的章节评估结果")
            return {
                "chapter": "未知章节",
                "error": "无法提取有效的评估结果",
                "status": "error"
            }
        
        if progress_callback:
            progress_callback(1.0, "章节评估完成")
        
        # 构造标准格式结果
        evaluation = {
            "chapter": eval_data.get('章节类型', '未知章节'),
            "summary": eval_data.get('summary', ''),
            "strengths": eval_data.get('strengths', []),
            "weaknesses": eval_data.get('weaknesses', []),
            "suggestions": eval_data.get('suggestions', []),
            "status": "success"
        }
        
        return evaluation
        
    except Exception as e:
        logger.error(f"章节评估过程中发生错误: {e}")
        return {
            "chapter": "未知章节",
            "error": str(e),
            "status": "error"
        }

def process_multiple_chapters(
    chapters: List[Dict[str, Any]], 
    model_name: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> List[Dict[str, Any]]:
    """
    处理多个章节的评估
    
    Args:
        chapters: 章节列表，每个章节包含content字段
        model_name: 使用的模型名称
        progress_callback: 进度回调函数
        
    Returns:
        List[Dict[str, Any]]: 所有章节的评估结果
    """
    results = []
    total_chapters = len(chapters)
    
    for i, chapter in enumerate(chapters):
        if progress_callback:
            base_progress = i / total_chapters
            progress_callback(base_progress, f"评估第{i+1}/{total_chapters}个章节...")
        
        # 定义章节级别的进度回调
        def chapter_progress(sub_progress: float, message: str):
            if progress_callback:
                overall_progress = base_progress + (sub_progress / total_chapters)
                progress_callback(overall_progress, message)
        
        # 处理章节评估
        chapter_content = chapter.get('content', '')
        if not chapter_content:
            logger.warning(f"第{i+1}个章节内容为空，跳过评估")
            continue
        
        result = process_chapter_evaluation(
            chapter_content, 
            model_name, 
            chapter_progress
        )
        
        # 添加章节索引信息
        result['index'] = i
        result['chapter_name'] = chapter.get('chapter_name', f'第{i+1}章')
        
        results.append(result)
    
    if progress_callback:
        progress_callback(1.0, f"完成所有{len(results)}个章节的评估")
    
    return results
