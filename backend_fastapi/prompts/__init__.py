"""
提示词模块
包含所有用于评估论文质量的提示词模板

包含以下模块：
- assess_detail_prompt: 详细评估提示词（包含中文、英文、格式、参考文献等评估）
- overall_prompt: 整体评估提示词
- chapter_prompt: 章节专项评估提示词
- templates: 通用提示词模板
"""

from .assess_detail_prompt import (
    p_writing_quality, p_wq_zh, p_wq_en, p_wq_col, p_wq_for, p_wq_ref
)
from .overall_prompt import p_overall_assessment
from .chapter_prompt import p_chapter_assessment
from .templates import (
    prompt_tempelate_minus_abstract, prompt_tempelate_minus_chapters,
    paper_writing_quality_prompt
)

__all__ = [
    'p_writing_quality', 'p_wq_zh', 'p_wq_en', 'p_wq_col', 'p_wq_for', 'p_wq_ref',
    'p_overall_assessment', 'p_chapter_assessment',
    'prompt_tempelate_minus_abstract', 'prompt_tempelate_minus_chapters', 'paper_writing_quality_prompt'
]
