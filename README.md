# Paper Eval - 论文评价与分析系统

## 项目简介

PaperEval 是一个集成的论文与文档分析系统，包含两个核心组件：
1. **Word文档分析器前端** - 基于Streamlit的文档可视化与分析工具
2. **论文评价系统后端** - 基于大语言模型的论文质量自动化评估系统

本项目可用于分析学术论文的写作质量，提供多维度的评估与改进建议，同时提供友好的文档可视化界面。

## 核心功能

### Word文档分析器前端

- 📝 **智能预览**：完整保留文档格式、图片和数学公式
- 🔍 **结构分析**：逐章节分析文档结构，提供清晰导航
- 💡 **内容优化**：智能分析文章内容，提供优化建议
- 📊 **质量评估**：章节质量评分与改进方向指导
- 🔖 **交互式导航**：通过自定义侧边栏实现章节快速跳转
- 📱 **全屏阅读**：支持全屏模式，提供更好的阅读体验
- ➗ **数学公式**：完美支持LaTeX数学公式渲染
- 🖼️ **图片显示**：正确显示文档中的所有图片

### 论文评价系统后端

- **中文写作质量**：评估语言表达、逻辑结构
- **英文写作质量**：评估英文摘要和术语使用
- **客观性**：评估客观用词
- **公式格式**：评估数学公式的规范性
- **参考文献**：评估引用格式和完整性

## 系统要求

- Python 3.10+ 
- Streamlit 1.45.1
- Pandoc (用于文档转换)
- 所有依赖见项目根目录和 `src/utils/eval` 目录下的 requirements.txt

## 项目结构

```
paper_eval/
├── README.md                 # 项目文档
├── requirements.txt          # 主项目依赖
├── src/                      # 源代码目录
│   ├── app.py                # Streamlit主应用入口
│   ├── components/           # 页面组件
│   │   ├── upload_page.py    # 文件上传页面
│   │   ├── processing_page.py # 处理中页面
│   │   └── results_page.py   # 结果展示页面
│   ├── services/             # 业务逻辑服务
│   │   ├── document_processor.py # 文档处理主逻辑
│   │   ├── docx2html.py      # Word转HTML转换器
│   │   └── omml_to_latex.py  # Office Math ML转LaTeX
│   ├── styles/               # 样式定义
│   │   └── custom_styles.py  # 自定义样式
│   └── utils/                # 工具函数
│       ├── eval/             # 论文评价系统
│       │   ├── config/       # 配置文件
│       │   ├── data/         # 数据目录
│       │   ├── models/       # AI模型接口
│       │   ├── pipeline/     # 推理流水线
│       │   ├── prompts/      # 评估提示词
│       │   ├── utils/        # 工具函数
│       │   ├── infer.py      # 评估系统入口
│       │   └── requirements.txt # 评估系统依赖
│       └── session_state.py  # 会话状态管理
```

## 安装步骤

### 1. 安装基础依赖

```bash
# 安装前端依赖
pip install -r requirements.txt

# 安装评估系统依赖
pip install -r src/utils/eval/requirements.txt

# 安装GPU支持（可选）
python src/utils/eval/install_torch_gpu.py
```

### 2. 安装Pandoc

从[Pandoc官网](https://pandoc.org/installing.html)下载并安装Pandoc文档转换工具。

### 3. 配置API密钥（用于评估系统）

在系统环境变量中设置您的API密钥：

```bash
# Linux/macOS
export DEEPSEEK_API_KEY=your_api_key_here

# Windows (CMD)
set DEEPSEEK_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="your_api_key_here"
```

## 使用方法

### 启动Word文档分析器前端

```bash
streamlit run src/app.py
```

### 使用评估系统评价论文

```bash
cd src/utils/eval
python single_paper_eval.py  # 单个文件评估
# 或
python infer.py  # 批量评估
```

### Word文档分析器使用流程

1. 启动应用后，在上传页面选择要分析的Word文档（.docx格式）
2. 点击"开始分析"按钮，等待处理完成
3. 在结果页面查看文档分析结果和优化建议
4. 使用左侧内容优化建议面板导航不同章节
5. 点击章节标题可展开查看详细分析和建议
6. 点击"全屏查看"按钮进入全屏阅读模式

### 论文评价系统使用流程

1. 将待评估论文(.docx格式)复制到 `src/utils/eval/data/raw/docx` 目录
2. 运行 `python single_paper_eval.py` 并按照提示操作
3. 评估结果将保存在 `src/utils/eval/data/output` 目录中

## 支持的模型

- **DeepSeek Chat**: deepseek-v3
- **Gemini**: Google Gemini模型
- **Qwen**: 阿里通义千问模型

## 注意事项

- 仅支持.docx格式的Word文档
- 建议文档大小不超过10MB
- 确保文档包含清晰的章节结构以获得更好的分析效果
- 数学公式渲染需要网络连接以加载MathJax库
- 评估系统需要有效的API密钥
- 批量处理大量文档可能需要更多系统资源
