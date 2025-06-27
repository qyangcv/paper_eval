# 前端界面
本模块为基于Streamlit前端可视化界面

## 环境要求
- Python>=3.10
 
## 模块结构

```
frontend/                     # 前端界面模块
├── components/               # 页面组件
│   ├── upload_page.py        # 文件上传页面
│   ├── processing_page.py    # 处理中页面
│   └── results_page.py       # 结果展示页面
├── services/                 # 业务逻辑服务
│   ├── document_processor.py # 文档处理主逻辑
│   ├── docx2html.py          # Word转HTML转换器
│   └── omml_to_latex.py      # Office Math ML转LaTeX
├── styles/                   # 样式定义
│   └── custom_styles.py      # 自定义样式
└── utils/                    # 工具函数
    └── session_state.py      # 会话状态管理
```

## 安装依赖

```bash
cd frontend/
pip install -r requirements.txt
```


## 使用方法

启动Word文档分析器前端
```bash
# ⚠️ 在项目根目录 paper_eval/ 下执行
streamlit run app.py
```

### Word文档分析器使用流程

1. 启动应用后，在上传页面选择要分析的Word文档（.docx格式）
2. 点击"开始分析"按钮，等待处理完成
3. 在结果页面查看文档分析结果和优化建议
4. 使用左侧内容优化建议面板导航不同章节
5. 点击章节标题可展开查看详细分析和建议
6. 点击"全屏查看"按钮进入全屏阅读模式

## 功能特性

- **多格式支持**: 支持.docx格式的Word文档上传和分析
- **实时处理**: 文档上传后实时进行结构提取和内容分析
- **可视化展示**: 提供清晰的HTML文档预览和章节导航
- **优化建议**: 智能分析文档内容并提供针对性的优化建议
- **全屏阅读**: 支持全屏模式下的文档阅读和分析查看
- **响应式设计**: 适配不同屏幕尺寸的设备

## 注意事项

- 仅支持.docx格式的Word文档
- 建议文档大小不超过10MB
- 确保文档包含清晰的章节结构以获得更好的分析效果
- 数学公式渲染需要网络连接以加载MathJax库
- 建议在稳定的网络环境下使用以确保最佳体验
