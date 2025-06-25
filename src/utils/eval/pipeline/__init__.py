"""
Pipeline 包
用于论文质量评估的推理流水线

包含以下模块：
- batch_inference: 批量推理模块
- chapter_inference: 章节推理模块  
- quality_assessment: 质量评估模块
"""

__all__ = [
    # 主函数
    'batch_inference',
    'chapter_inference', 
    'quality_assessment',
    # 推理函数
    'batch_infer',
    'chapter_infer',
    'quality_infer',
    'generate_overall_assessment',
    # 辅助函数
    'batch_load_context',
    'batch_load_prompts',
    'chapter_load_context',
    'chapter_load_prompts',
    'quality_load_prompts',
    'load_paper_writing_quality_prompts',
]

__version__ = '1.0.0'
__author__ = 'PaperEval Team' 