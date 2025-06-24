# 论文评价系统 

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
- `pip install -r requirements.txt`
- 安装 pandoc: https://pandoc.org/installing.html

## 使用方法

### 1. 添加API Key
在 `~/.bashrc` 或 `~/.zshrc` 中添加：
```bash
export DEEPSEEK_API_KEY=...
```


### 2. 处理docx文件
文件转换过程：docx -> md -> pkl
- 将 docx 文件复制到 `data/raw/docx` 目录
- 执行 `pandoc data/raw/docx/<xxx>.docx -o data/raw/docx/<xxx>.md --extract-media=data/raw/docx/images`，将`<xxx>`修改为文件名，得到md文件
- 执行 `utils/docx_tools/md2pkl.py`，将 `md2pkl.py`的`MD_PATH`和`PKL_PATH` 修改为源路径和目标路径，得到pkl文件
- （可选）调试 `utils/docx_tools/pkl_analyse.py` 查看pkl内容


### 3. 开始评估

```bash
python infer.py
```


## 支持的模型

- `deepseek-chat`: deepseek-v3


## 文件格式
- 输出文件格式：pkl
- 输出文件格式：json
- 格式转换工具（存在少量格式问题，待完善）：使用 `utils/json2md.py` 将 josn 转换为易读的 markdown

## 日志

日志文件保存在 `logs/` 目录下