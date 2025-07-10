"""
推理流水线模块
包含论文评估的各种推理流水线

包含以下模块：
- chapter_inference: 按章节推理
- quality_assessment: 质量评估
- paper_evaluation: 完整论文评估流程
"""

from .chapter_inference import process_chapter_evaluation
from .quality_assessment import evaluate_paper_quality
from .paper_evaluation import full_paper_evaluation

__all__ = [
    'process_chapter_evaluation',
    'evaluate_paper_quality', 
    'full_paper_evaluation'
]
