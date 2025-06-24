# 论文评估系统 (Paper Evaluation System)

## 项目简介

本项目是一个基于大语言模型的论文质量评价系统，支持对学术论文进行自动化的写作质量评估。

## 主要功能
对论文的撰写质量进行评价，包括五个维度：
- **中文写作质量**: 语言表达、逻辑结构
- **英文写作质量**: 英文摘要和术语使用
- **客观性**: 客观用词
- **公式格式**: 数学公式的规范性
- **参考文献**: 引用格式和完整性

## 项目结构

```
paper_eval/
├── config/          # 配置文件
├── data/           # 数据目录
│   ├── raw/        # 原始论文文件
│   ├── processed/  # 处理后的数据
│   └── output/     # 评估结果
├── models/         # AI模型接口
├── pipeline/       # 推理流水线
├── prompts/        # 评估提示词
├── utils/          # 工具函数
└── infer.py        # 主入口文件
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 添加 API Key
在 `~/.bashrc` 或 `~/.zshrc` 中添加：
```bash
export DEEPSEEK_API_KEY=...
```

### 2. 修改配置

在 `infer.py` 中修改配置参数，默认配置为：

```python
INPUT_ROOT = "data/processed/docx"    # 输入目录
OUTPUT_ROOT = "data/output/docx"      # 输出目录
PROCESSES = 16                        # 并行请求进程数
MODEL_NAME = "deepseek-chat"          # 使用的模型
```


### 3. 开始评估

```bash
python infer.py
```


## 支持的模型

- `deepseek-chat`: deepseek-v3


## 文件格式
- 输出文件格式：DOCX
- 输出文件格式：JSON
- 格式转换工具（存在少量格式问题，待完善）：使用 `utils/json2md.py` 将 JSON 转换为易读的 Markdown

## 日志

日志文件保存在 `logs/` 目录下