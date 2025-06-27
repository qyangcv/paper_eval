# 硬指标评价

本模块主要对论文撰写质量这一硬指标进行评价，包括五个维度：
- **中文写作质量**: 语言表达、逻辑结构
- **英文写作质量**: 英文摘要和术语使用
- **用词客观性**: 客观用词
- **公式格式**: 数学公式的规范性
- **参考文献**: 引用格式和完整性

## 模块结构

```
hard_metrics/
├── config/                   # 配置文件
│   ├── data_config.py        # 数据配置
│   ├── log_config.py         # 日志配置
│   └── model_config.py       # 模型配置
├── data/                     # 数据目录
│   ├── raw/                  # 原始论文数据
│   ├── processed/            # 处理后的数据
│   └── output/               # 评估结果
├── examples/                 # 示例代码
│   ├── logger_example.py     # 日志使用示例
│   └── pkl_analyse.ipynb     # 数据分析示例
├── logs/                     # 日志文件
├── models/                   # AI模型接口
│   ├── deepseek.py          # DeepSeek模型
│   ├── gemini.py            # Gemini模型
│   └── qwen.py              # Qwen模型
├── pipeline/                 # 推理流水线
│   ├── chapter_inference.py # 按章节推理
│   ├── finegrained_inference.py # 细粒度推理
│   └── quality_assessment.py # 质量评估
├── prompts/                  # 评估提示词
│   ├── assess_detail_prompt.py # 详细评估提示
│   ├── chapter_prompt.py     # 章节提示
│   ├── overall_prompt.py     # 总体提示
│   ├── review_detail_prompt.py # 详细审查提示
│   └── templates.py          # 提示模板
├── tools/                    # 工具函数
│   ├── docx_tools/          # 文档处理工具
│   │   ├── docx2md.py       # DOCX转Markdown
│   │   ├── json2md.py       # JSON转Markdown
│   │   ├── md2pkl.py        # Markdown转PKL
│   │   ├── omml_to_latex.py # OMML转LaTeX
│   │   └── pkl_analyse.py   # PKL分析
│   ├── token_count/         # 分词计数工具
│   │   ├── deepseek_tokenizer.py # DeepSeek分词器
│   │   ├── tokenizer.json   # 分词器配置
│   │   └── tokenizer_config.json # 分词器配置
│   ├── clean_utils.py       # 清理工具
│   ├── file_utils.py        # 文件工具
│   ├── fix_utils.py         # 修复工具
│   ├── helper_utils.py      # 辅助工具
│   ├── json2txt.py          # JSON转文本
│   ├── logger.py            # 日志工具
│   ├── parse_utils.py       # 解析工具
│   └── torch_helper.py      # PyTorch辅助工具
├── full_paper_eval.py       # 完整论文评估 (前端调用)
├── infer.py                 # 主入口文件
├── install_torch_gpu.py     # GPU安装脚本
├── requirements.txt         # 依赖列表
└── test_paper_eval.py       # 测试文件
```

⚠️ 注意：full_paper_eval.py 为前端所用，其余模块尚未接入前端

## 安装依赖
```bash
cd backend/hard_metrics
pip install -r requirements.txt
```


## 使用方法

### 1. 添加API Key
```bash
# Linux/macOS
export DEEPSEEK_API_KEY=your_api_key_here

# Windows (CMD)
set DEEPSEEK_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="your_api_key_here"
```


### 2. 文件处理
文件转换过程：
docx -> md -> pkl -> LLMs -> json -> md/html

输入格式处理：
- 将 docx 论文移动到 `./data/raw/docx` 目录下
- docx2md：执行 `./tools/docx_tools/docx2md.py`
- md2pkl：执行 `./tools/docx_tools/md2pkl.py`
- 查看pkl结构： 调试 `./tools/docx_tools/pkl_analyse.py` 
  
输出格式处理：
- json2md：执行 `./tools/docx_tools/json2md.py`


### 3. 开始评价

```bash
cd backend/hard_metircs
python infer.py
```


## 支持模型

- `deepseek-chat`: deepseek-v3
- `qwen`、`gemini`：coming soon...