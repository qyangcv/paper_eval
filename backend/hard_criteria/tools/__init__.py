"""
工具函数模块
包含项目所需的所有工具函数，包括文件操作、日志记录、数据处理等通用工具函数

包含以下子模块：
- file_utils: 文件读写操作工具（支持txt、pickle、md等格式）
- logger: 日志记录工具
- clean_utils: 数据清理工具
- fix_utils: 数据修复工具  
- parse_utils: 数据解析工具
- helper_utils: 辅助工具函数
- json2txt: JSON数据转换工具
- get_pkl_files: pickle文件获取工具
- torch_helper: PyTorch相关辅助工具
- docx_tools/: Word文档处理工具包
  - docx2md: Word转Markdown
  - md2pkl: Markdown转pickle
  - omml_to_latex: OMML数学公式转LaTeX
  - pkl_analyse: pickle文件分析
- token_count: deepseek官方token计数工具

备注：
某些模块未被项目使用且存在问题，但保留在项目中，以备后续使用，一切参考README.md。
"""