"""
提示词模块
包含所有用于评估论文质量的提示词模板
"""

from .assess_prompt import (
    p_wq_zh,
    p_wq_en,
    p_wq_col,
    p_wq_for,
    p_wq_ref,
    p_writing_quality,
)
from .review_prompt import (
    review_prompt,
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

    # 论文复查提示词模板
    'review_prompt',
]
