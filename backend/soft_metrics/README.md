# 硬指标评价

本模块主要对论文撰写软指标进行评价，包括四个维度：
- 逻辑连贯性与结构严谨性
- 学术贡献与创新性的实质性
- 论证深度与批判性思维
- 研究的严谨性与可复现性

## 模块结构

```
soft_metrics/
├── config/                    # 配置文件
│   ├── data_config.py         # 数据配置
│   ├── log_config.py          # 日志配置
│   └── model_config.py        # 模型配置
├── data/                      # 数据目录
│   ├── output/                # 输出结果
│   ├── processed/             # 处理后的数据
│   └── raw/                   # 原始数据
├── logs/                      # 日志文件
│   └── app.log
├── models/                    # 模型封装
│   ├── deepseek.py            # DeepSeek模型
│   ├── gemini.py              # Gemini模型
│   ├── qwen.py                # Qwen模型
│   └── request_model.py       # 请求模型基类
├── pipeline/                  # 评估流水线
│   ├── overall_assess.py           # 整体评估
├── prompts/                   # 提示词模板
│   ├── overall_assess_prompt.py # 整体评估提示词
├── tools/                    # 工具函数
│   ├── clean_utils.py         # 清理工具
│   ├── file_utils.py          # 文件工具
│   ├── fix_utils.py           # 修复工具
│   ├── get_pkl_files.py       # PKL文件处理
│   ├── helper_utils.py        # 辅助工具
│   ├── json2txt.py            # JSON转文本
│   ├── logger.py              # 日志工具
│   ├── parse_utils.py         # 解析工具
│   ├── torch_helper.py        # PyTorch辅助
│   ├── docx_tools/            # DOCX处理工具
│   │   ├── docx2md.py         # DOCX转Markdown
│   │   ├── json2md.py         # JSON转Markdown
│   │   ├── md2pkl.py          # Markdown转PKL
│   │   ├── omml_to_latex.py   # OMML转LaTeX
│   │   └── pkl_analyse.py     # PKL分析
│   ├── hard_criteria/         # 硬指标工具
│   │   ├── extract_content.py # 内容提取
│   │   ├── extract_md.py      # Markdown提取
│   │   └── scan_colloquial_word.py # 口语词扫描
│   └── token_count/           # Token计数工具
│       ├── deepseek_tokenizer.py # DeepSeek分词器
│       ├── tokenizer.json
│       └── tokenizer_config.json
└── infer.py                   # 推理入口文件
```

## 安装依赖(和硬指标评价一致)
```bash
cd backend/hard_criteria
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
文件转换过程：（使用md作为LLMs的输入）
docx -> md -> LLMs -> json -> md/html

输入格式处理：
- 将 docx 论文移动到 `./data/raw/docx` 目录下
- docx2md：执行 `./tools/docx_tools/docx2md.py`
  
输出格式处理：
- json2md：执行 `./tools/docx_tools/json2md.py`


### 3. 分析论文

```bash
cd backend/soft_metrics
python infer.py
```


## 支持模型

- `deepseek-chat`: deepseek-v3
- `qwen`、`gemini`：coming soon...