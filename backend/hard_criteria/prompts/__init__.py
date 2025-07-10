"""
提示词模块
包含所有用于评估论文质量的提示词模板

包含以下模块：
- assess_detail_prompt: 详细评估提示词（包含中文、英文、格式、参考文献等评估）
- overall_prompt: 整体评估提示词
- review_detail_prompt: 论文复查提示词
- chapter_prompt: 章节专项评估提示词
- templates: 通用提示词模板

使用方法：
    from backend.prompts.assess_detail_prompt import p_wq_zh, p_writing_quality
    from backend.prompts.overall_prompt import p_overall_assessment
    from backend.prompts.chapter_prompt import p_chapter_assessment
"""



