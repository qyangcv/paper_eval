"""
提示词模板
包含所有用于评估论文质量的提示词模板
"""

# 用于评估论文摘要的提示词模板
prompt_tempelate_minus_abstract = """
请评估以下论文摘要的写作质量，从以下几个方面进行分析：
1. 语言表达：是否清晰、准确、专业
2. 结构组织：是否逻辑清晰、层次分明
3. 内容完整性：是否涵盖了论文的主要内容和贡献
4. 学术规范性：是否符合学术写作规范

论文摘要：
{content}

请给出详细的评估意见和改进建议。
"""

# 用于评估论文章节的提示词模板
prompt_tempelate_minus_chapters = """
请评估以下论文章节的写作质量，从以下几个方面进行分析：
1. 语言表达：是否清晰、准确、专业
2. 结构组织：是否逻辑清晰、层次分明
3. 内容完整性：是否充分阐述了该章节的主要内容
4. 学术规范性：是否符合学术写作规范

章节内容：
{content}

请给出详细的评估意见和改进建议。
"""

# 用于评估论文整体写作质量的提示词模板
paper_writing_quality_prompt = """
请评估以下论文内容的写作质量，从以下几个方面进行分析：
1. 语言表达：是否清晰、准确、专业
2. 结构组织：是否逻辑清晰、层次分明
3. 内容完整性：是否充分阐述了相关内容
4. 学术规范性：是否符合学术写作规范

内容：
{content}

请给出详细的评估意见和改进建议。
"""

# 批量推理使用的提示词模板
p_wq_zh = """
请用中文评估以下论文内容的写作质量，从以下几个方面进行分析：
1. 语言表达：是否清晰、准确、专业
2. 结构组织：是否逻辑清晰、层次分明
3. 内容完整性：是否充分阐述了相关内容
4. 学术规范性：是否符合学术写作规范

内容：
{content}

请给出详细的评估意见和改进建议。
"""

p_wq_en = """
Please evaluate the writing quality of the following paper content in English, analyzing from the following aspects:
1. Language expression: Is it clear, accurate, and professional?
2. Structure organization: Is it logical and well-organized?
3. Content completeness: Does it fully elaborate on the relevant content?
4. Academic standards: Does it comply with academic writing standards?

Content:
{content}

Please provide detailed evaluation comments and improvement suggestions.
"""

p_wq_col = """
请从以下方面评估论文内容的学术规范性：
1. 引用格式：是否符合学术引用规范
2. 参考文献：是否完整、准确
3. 学术用语：是否专业、准确
4. 图表使用：是否规范、清晰

内容：
{content}

请给出详细的评估意见和改进建议。
"""

p_wq_for = """
请从以下方面评估论文内容的格式规范性：
1. 标题层级：是否层次分明、格式统一
2. 段落结构：是否段落清晰、过渡自然
3. 图表编号：是否编号规范、引用准确
4. 页面布局：是否整洁、美观

内容：
{content}

请给出详细的评估意见和改进建议。
"""

p_wq_ref = """
请从以下方面评估论文内容的参考文献规范性：
1. 引用格式：是否符合学术引用规范
2. 参考文献列表：是否完整、准确
3. 引用标注：是否规范、统一
4. 文献时效性：是否引用最新研究成果

内容：
{content}

请给出详细的评估意见和改进建议。
"""

# 章节评估的提示词模板
p_writing_quality = """
请评估以下论文章节的写作质量，从以下几个方面进行分析：
1. 语言表达：是否清晰、准确、专业
2. 结构组织：是否逻辑清晰、层次分明
3. 内容完整性：是否充分阐述了该章节的主要内容
4. 学术规范性：是否符合学术写作规范
5. 与整体论文的关联性：是否与论文主题紧密相关
6. 创新性：是否包含创新性的观点或方法

章节内容：
{content}

请给出详细的评估意见和改进建议。
""" 