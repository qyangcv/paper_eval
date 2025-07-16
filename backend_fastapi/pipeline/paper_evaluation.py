"""
完整论文评估流程
整合文档处理、章节分析、质量评估等功能
"""

from typing import Dict, Any, Optional, Callable, Union, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.docx_tools.docx2md import convert_docx_bytes_to_md
from tools.docx_tools.md2pkl import convert_md_content_to_pkl_data
from pipeline.quality_assessment import evaluate_paper_quality
from tools.logger import get_logger

logger = get_logger(__name__)

def process_docx_file(file_path_or_bytes: Union[str, bytes]) -> Optional[Dict[str, Any]]:
    """
    处理DOCX文件，转换为结构化数据
    
    Args:
        file_path_or_bytes: DOCX文件路径或字节数据
        
    Returns:
        Optional[Dict[str, Any]]: 结构化的论文数据，如果处理失败则返回None
    """
    try:
        # 转换为Markdown
        if isinstance(file_path_or_bytes, bytes):
            md_content = convert_docx_bytes_to_md(file_path_or_bytes)
        else:
            from ..tools.docx_tools.docx2md import convert_docx_to_md
            md_content = convert_docx_to_md(file_path_or_bytes)
        
        # 转换为结构化数据
        pkl_data = convert_md_content_to_pkl_data(md_content)
        
        return pkl_data
        
    except Exception as e:
        logger.error(f"DOCX文件处理失败: {e}")
        return None

def load_chapters(pkl_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从PKL数据中加载章节
    
    Args:
        pkl_data: 结构化的论文数据
        
    Returns:
        List[Dict[str, Any]]: 章节列表
    """
    try:
        chapters = pkl_data.get('chapters', [])
        
        # 确保每个章节都有必要的字段
        processed_chapters = []
        for i, chapter in enumerate(chapters):
            processed_chapter = {
                'index': i,
                'chapter_name': chapter.get('chapter_name', f'第{i+1}章'),
                'content': chapter.get('content', ''),
                'images': chapter.get('images', [])
            }
            processed_chapters.append(processed_chapter)
        
        return processed_chapters
        
    except Exception as e:
        logger.error(f"章节加载失败: {e}")
        return []

def process_chapter(chapter: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    """
    处理单个章节的评估
    
    Args:
        chapter: 章节数据
        model_name: 使用的模型名称
        
    Returns:
        Dict[str, Any]: 章节评估结果
    """
    from .chapter_inference import process_chapter_evaluation
    
    chapter_content = chapter.get('content', '')
    if not chapter_content:
        return {
            "chapter": chapter.get('chapter_name', '未知章节'),
            "index": chapter.get('index', 0),
            "error": "章节内容为空",
            "status": "error"
        }
    
    result = process_chapter_evaluation(chapter_content, model_name)
    
    # 添加章节信息
    result['index'] = chapter.get('index', 0)
    result['chapter_name'] = chapter.get('chapter_name', '未知章节')
    
    return result

def evaluate_overall(chapter_evaluations: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
    """
    基于所有章节的评估结果进行整体评估
    
    Args:
        chapter_evaluations: 所有章节的评估结果
        model_name: 使用的模型
        
    Returns:
        Dict[str, Any]: 整体评估结果
    """
    from .quality_assessment import evaluate_overall_quality
    
    return evaluate_overall_quality(chapter_evaluations, model_name)

def score_paper(all_evaluations: List[Dict[str, Any]], model_name: str) -> List[Dict[str, Any]]:
    """
    对论文进行打分
    
    Args:
        all_evaluations: 所有评估结果
        model_name: 使用的模型
        
    Returns:
        List[Dict[str, Any]]: 评分结果
    """
    from .quality_assessment import score_paper as score_paper_impl
    
    return score_paper_impl(all_evaluations, model_name)

def full_paper_evaluation(
    file_path_or_bytes: Union[str, bytes],
    model_name: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Dict[str, Any]:
    """
    完整的论文评估流程
    
    Args:
        file_path_or_bytes: DOCX文件路径或字节数据
        model_name: 使用的模型名称
        progress_callback: 进度回调函数
        
    Returns:
        Dict[str, Any]: 完整的评估结果
    """
    try:
        if progress_callback:
            progress_callback(0.1, "开始处理文档...")
        
        # 第一步：处理DOCX文件
        pkl_data = process_docx_file(file_path_or_bytes)
        if not pkl_data:
            raise Exception("文档转换失败")
        
        if progress_callback:
            progress_callback(0.2, "加载章节内容...")
        
        # 第二步：加载章节
        chapters = load_chapters(pkl_data)
        if not chapters:
            raise Exception("章节加载失败")
        
        if progress_callback:
            progress_callback(0.3, f"使用{model_name}开始评估...")
        
        # 第三步：进行质量评估 (30%-100%)
        def quality_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(0.3 + progress * 0.7, message)
        
        quality_result = evaluate_paper_quality(chapters, model_name, quality_progress)
        
        if quality_result.get('status') == 'error':
            raise Exception(quality_result.get('error', '质量评估失败'))
        
        # 提取结果
        chapter_evaluations = quality_result.get('chapter_evaluations', [])
        overall_evaluation = quality_result.get('overall_evaluation', {})
        paper_scores = quality_result.get('paper_scores', [])
        
        # 计算总分
        total_score = sum(item.get('score', 0) for item in paper_scores if 'score' in item)
        
        if progress_callback:
            progress_callback(1.0, "评估完成")
        
        # 格式化结果
        return {
            "overall_score": total_score,
            "dimensions": {
                "创新性": next((item.get('score', 0) for item in paper_scores if item.get('dimension') == '创新性'), 0),
                "技术深度": next((item.get('score', 0) for item in paper_scores if item.get('dimension') == '技术深度'), 0),
                "实验设计": next((item.get('score', 0) for item in paper_scores if item.get('dimension') == '实验设计'), 0),
                "写作质量": next((item.get('score', 0) for item in paper_scores if item.get('dimension') == '写作质量'), 0),
                "学术规范": next((item.get('score', 0) for item in paper_scores if item.get('dimension') == '学术规范'), 0)
            },
            "summary": overall_evaluation.get('summary', '评估完成'),
            "detailed_analysis": {
                "strengths": overall_evaluation.get('strengths', []),
                "weaknesses": overall_evaluation.get('weaknesses', []),
                "suggestions": overall_evaluation.get('suggestions', [])
            },
            "chapter_scores": [
                {
                    "chapter": eval_item.get('chapter', '未知章节'),
                    "score": 85  # 默认章节分数，可以根据实际评估结果计算
                }
                for eval_item in chapter_evaluations
            ],
            "raw_evaluations": [overall_evaluation] + chapter_evaluations,
            "raw_scores": paper_scores,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"完整论文评估失败: {e}")
        return {
            "error": str(e),
            "status": "error"
        }
