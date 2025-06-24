"""
Pipeline 包
用于论文质量评估的推理流水线

包含以下模块：
- batch_inference: 批量推理模块
- chapter_inference: 章节推理模块  
- quality_assessment: 质量评估模块
"""


# 优化导入，避免不必要的依赖
try:
    from .batch_inference import batch_inference
except ImportError:
    print("Warning: batch_inference模块导入失败，可能缺少transformers依赖")
    batch_inference = None


# 导入重命名后的主函数
from .batch_inference import infer as batch_infer
from .chapter_inference import infer as chapter_infer
from .quality_assessment import infer as quality_infer

# 导入辅助函数
from .batch_inference import load_context as batch_load_context
from .batch_inference import load_prompts as batch_load_prompts
from .chapter_inference import load_context as chapter_load_context
from .chapter_inference import load_prompts as chapter_load_prompts
from .quality_assessment import load_prompts as quality_load_prompts
from .quality_assessment import load_paper_writing_quality_prompts

__all__ = [
    # 主函数
    'batch_inference',
    'chapter_inference', 
    'quality_assessment',
    # 推理函数
    'batch_infer',
    'chapter_infer',
    'quality_infer',
    # 辅助函数
    'batch_load_context',
    'batch_load_prompts',
    'chapter_load_context',
    'chapter_load_prompts',
    'quality_load_prompts',
    'load_paper_writing_quality_prompts',
    'load_data',
    'extract_chapter_sentences',
    'analyze_chapter_quality',
    'get_inference_config',
    'BackendChapterExtractor',
    'extract_chapters_from_docx_file',
    'convert_docx_to_pickle_format'
]

__version__ = '1.0.0'
__author__ = 'PaperEval Team' 