"""
提示词模块
包含所有用于评估论文质量的提示词模板
"""

from .assess_detail_prompt import (
    p_wq_zh,
    p_wq_en,
    p_wq_col,
    p_wq_for,
    p_wq_ref,
    p_writing_quality,
)
from .review_detail_prompt import (
    review_prompt,
)
from .overall_prompt import (
    p_overall_assessment,
)
from .chapter_prompt import (
    p_chapter_assessment,
)

__all__ = [
    # 批量推理提示词模板
    'p_wq_zh',
    'p_wq_en',
    'p_wq_col',
    'p_wq_for',
    'p_wq_ref',
    
    # 章节评估提示词模板
    'p_writing_quality',  
    'review_prompt',       # 论文复查提示词模板
    
    # 论文整体评估提示词
    'p_overall_assessment',
    
    # 章节专项评估提示词
    'p_chapter_assessment',
]
