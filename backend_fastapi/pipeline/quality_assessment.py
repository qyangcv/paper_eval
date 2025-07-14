"""
质量评估模块
提供论文质量评估的核心功能
"""

import json
import logging
from typing import List, Dict, Any, Optional, Callable
from ..models.model_manager import request_model
from ..prompts.overall_prompt import p_overall_assessment
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

def evaluate_overall_quality(
    chapter_evaluations: List[Dict[str, Any]], 
    model_name: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Dict[str, Any]:
    """
    基于所有章节的评估结果进行整体评估
    
    Args:
        chapter_evaluations: 所有章节的评估结果
        model_name: 使用的模型
        progress_callback: 进度回调函数
        
    Returns:
        Dict[str, Any]: 整体评估结果
    """
    try:
        if progress_callback:
            progress_callback(0.1, "准备整体评估...")
        
        logger.info("开始进行整体评估...")
        
        # 准备章节评估结果作为输入
        chapter_eval_str = json.dumps(chapter_evaluations, ensure_ascii=False, indent=2)
        
        # 生成整体评估提示词
        prompt = p_overall_assessment.format(chapter_evaluations=chapter_eval_str)
        
        if progress_callback:
            progress_callback(0.5, f"使用{model_name}进行整体分析...")
        
        # 调用模型
        result = request_model(prompt, model_name)
        
        if progress_callback:
            progress_callback(0.8, "处理整体评估结果...")
        
        # 提取评估结果
        if result.get('status') == 'error':
            logger.error(f"整体评估失败: {result.get('error')}")
            return {
                "chapter": "全篇",
                "index": 0,
                "error": result.get('error', '整体评估失败'),
                "status": "error"
            }
        
        # 提取JSON评估结果
        eval_data = extract_json_from_response(result.get('output', '{}'))
        
        if not eval_data:
            logger.warning("无法提取有效的整体评估结果")
            return {
                "chapter": "全篇",
                "index": 0,
                "error": "无法提取有效的整体评估结果",
                "status": "error"
            }
        
        if progress_callback:
            progress_callback(1.0, "整体评估完成")
        
        # 构造标准格式结果
        evaluation = {
            "chapter": "全篇",
            "index": 0,
            "summary": eval_data.get('summary', ''),
            "strengths": eval_data.get('strengths', []),
            "weaknesses": eval_data.get('weaknesses', []),
            "suggestions": eval_data.get('suggestions', []),
            "status": "success"
        }
        
        return evaluation
        
    except Exception as e:
        logger.error(f"整体评估过程中发生错误: {e}")
        return {
            "chapter": "全篇",
            "index": 0,
            "error": str(e),
            "status": "error"
        }

def generate_score_prompt(all_evaluations: List[Dict[str, Any]]) -> str:
    """
    生成评分提示词
    
    Args:
        all_evaluations: 所有评估结果
        
    Returns:
        str: 评分提示词
    """
    evaluations_str = json.dumps(all_evaluations, ensure_ascii=False, indent=2)
    
    return f"""
你是一位经验丰富的学术论文评审专家，你的任务是基于详细的评估结果对论文进行打分。

请根据以下评估结果，对论文的五个维度进行打分（满分100分）：

1. 创新性（Innovation）：研究问题的新颖性、方法的创新性、结果的原创性
2. 技术深度（Technical Depth）：技术方法的深度、实现的复杂性、理论分析的严谨性
3. 实验设计（Experimental Design）：实验设计的合理性、数据的充分性、结果的可信度
4. 写作质量（Writing Quality）：语言表达、逻辑结构、学术规范性
5. 学术规范（Academic Standards）：引用规范、格式统一、学术诚信

请严格按照以下JSON格式输出评分结果：

```json
[
    {{"dimension": "创新性", "score": <0-100的整数分数>, "reasoning": "<评分理由，50-100字>"}},
    {{"dimension": "技术深度", "score": <0-100的整数分数>, "reasoning": "<评分理由，50-100字>"}},
    {{"dimension": "实验设计", "score": <0-100的整数分数>, "reasoning": "<评分理由，50-100字>"}},
    {{"dimension": "写作质量", "score": <0-100的整数分数>, "reasoning": "<评分理由，50-100字>"}},
    {{"dimension": "学术规范", "score": <0-100的整数分数>, "reasoning": "<评分理由，50-100字>"}}
]
```

# 评估结果
{evaluations_str}
"""

def score_paper(
    all_evaluations: List[Dict[str, Any]], 
    model_name: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> List[Dict[str, Any]]:
    """
    对论文进行打分
    
    Args:
        all_evaluations: 所有评估结果
        model_name: 使用的模型
        progress_callback: 进度回调函数
        
    Returns:
        List[Dict[str, Any]]: 评分结果
    """
    try:
        if progress_callback:
            progress_callback(0.1, "准备论文打分...")
        
        logger.info("开始对论文进行评分...")
        
        # 生成评分提示词
        prompt = generate_score_prompt(all_evaluations)
        
        if progress_callback:
            progress_callback(0.5, f"使用{model_name}进行评分...")
        
        # 调用模型
        result = request_model(prompt, model_name)
        
        if progress_callback:
            progress_callback(0.8, "处理评分结果...")
        
        # 检查是否有错误
        if result.get('status') == 'error':
            logger.error(f"论文评分失败: {result.get('error')}")
            # 返回默认评分
            return [
                {"dimension": "创新性", "score": 70, "reasoning": "评分失败，使用默认分数"},
                {"dimension": "技术深度", "score": 70, "reasoning": "评分失败，使用默认分数"},
                {"dimension": "实验设计", "score": 70, "reasoning": "评分失败，使用默认分数"},
                {"dimension": "写作质量", "score": 70, "reasoning": "评分失败，使用默认分数"},
                {"dimension": "学术规范", "score": 70, "reasoning": "评分失败，使用默认分数"}
            ]
        
        # 提取评分结果
        scores_data = extract_json_from_response(result.get('output', '[]'))
        
        if not scores_data or not isinstance(scores_data, list):
            logger.warning("无法提取有效的评分结果，使用默认评分")
            return [
                {"dimension": "创新性", "score": 75, "reasoning": "无法获取详细评分，使用默认分数"},
                {"dimension": "技术深度", "score": 75, "reasoning": "无法获取详细评分，使用默认分数"},
                {"dimension": "实验设计", "score": 75, "reasoning": "无法获取详细评分，使用默认分数"},
                {"dimension": "写作质量", "score": 75, "reasoning": "无法获取详细评分，使用默认分数"},
                {"dimension": "学术规范", "score": 75, "reasoning": "无法获取详细评分，使用默认分数"}
            ]
        
        if progress_callback:
            progress_callback(1.0, "论文评分完成")
        
        return scores_data
        
    except Exception as e:
        logger.error(f"论文评分过程中发生错误: {e}")
        return [
            {"dimension": "创新性", "score": 70, "reasoning": f"评分过程出错: {str(e)}"},
            {"dimension": "技术深度", "score": 70, "reasoning": f"评分过程出错: {str(e)}"},
            {"dimension": "实验设计", "score": 70, "reasoning": f"评分过程出错: {str(e)}"},
            {"dimension": "写作质量", "score": 70, "reasoning": f"评分过程出错: {str(e)}"},
            {"dimension": "学术规范", "score": 70, "reasoning": f"评分过程出错: {str(e)}"}
        ]

def evaluate_paper_quality(
    chapters: List[Dict[str, Any]], 
    model_name: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Dict[str, Any]:
    """
    完整的论文质量评估流程
    
    Args:
        chapters: 章节列表
        model_name: 使用的模型名称
        progress_callback: 进度回调函数
        
    Returns:
        Dict[str, Any]: 完整的评估结果
    """
    try:
        # 导入章节推理模块
        from .chapter_inference import process_multiple_chapters
        
        # 第一步：章节评估 (0-60%)
        def chapter_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress * 0.6, message)
        
        chapter_evaluations = process_multiple_chapters(chapters, model_name, chapter_progress)
        
        # 第二步：整体评估 (60-80%)
        def overall_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(0.6 + progress * 0.2, message)
        
        overall_evaluation = evaluate_overall_quality(chapter_evaluations, model_name, overall_progress)
        
        # 第三步：评分 (80-100%)
        def score_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(0.8 + progress * 0.2, message)
        
        all_evaluations = [overall_evaluation] + chapter_evaluations
        paper_scores = score_paper(all_evaluations, model_name, score_progress)
        
        if progress_callback:
            progress_callback(1.0, "论文质量评估完成")
        
        return {
            "chapter_evaluations": chapter_evaluations,
            "overall_evaluation": overall_evaluation,
            "paper_scores": paper_scores,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"论文质量评估过程中发生错误: {e}")
        return {
            "error": str(e),
            "status": "error"
        }
