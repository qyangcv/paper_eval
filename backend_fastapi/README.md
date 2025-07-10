# 论文评价分析系统 - FastAPI后端

基于FastAPI构建的论文质量评价分析系统后端，支持多种大语言模型进行论文质量评估。

## 🚀 功能特性

### 📄 文档处理
- **文档上传**: 支持Word文档(.docx, .doc)上传和验证
- **格式转换**: 自动将Word文档转换为Markdown和结构化数据
- **内容分析**: 提取论文章节、摘要、参考文献等结构信息

### 🤖 AI评估
- **多模型支持**: 集成DeepSeek、Gemini、Qwen等大语言模型
- **章节评估**: 对论文各章节进行详细质量分析
- **整体评分**: 从创新性、技术深度、实验设计、写作质量、学术规范五个维度评分
- **智能建议**: 提供具体的改进建议和优化方向

### 📊 数据分析
- **可视化数据**: 生成雷达图、柱状图等可视化数据
- **统计分析**: 提供详细的文档统计信息
- **报告导出**: 支持JSON、摘要等格式的报告导出

### ⚙️ 系统管理
- **异步任务**: 支持长时间运行的评估任务
- **进度监控**: 实时跟踪任务执行进度
- **性能监控**: 系统资源使用情况监控
- **错误处理**: 完善的错误处理和日志记录

## 📋 系统要求

- Python 3.8+
- 至少4GB内存
- 支持的操作系统: Windows, macOS, Linux

## 🛠️ 快速开始

### 方法1：一键启动（推荐）

**Windows用户：**
```bash
# 双击运行或在PowerShell中执行
.\start.ps1

# 或者使用批处理文件
start.bat
```

**Linux/macOS用户：**
```bash
# 运行安装脚本
python setup.py

# 启动服务器
python run_server.py
```

### 方法2：手动安装

#### 1. 安装依赖

```bash
# 安装基础依赖
pip install fastapi uvicorn python-multipart aiofiles python-docx psutil python-dotenv

# 安装AI模型依赖
pip install openai google-generativeai requests
```

#### 2. 环境配置

系统已为您创建了 `.env` 配置文件，包含以下配置：

- ✅ **DeepSeek API密钥已配置**
- ⚠️ Gemini API密钥（需要您自行配置）
- ⚠️ Qwen API密钥（需要您自行配置）

如需配置其他模型，请编辑 `.env` 文件：

```bash
# 取消注释并填入您的API密钥
GEMINI_API_KEY=your_gemini_api_key_here
QWEN_API_KEY=your_qwen_api_key_here
```

#### 3. 启动服务器

```bash
# 使用启动脚本（推荐）
python run_server.py

# 或者直接使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 生产环境启动
python run_server.py --env production --workers 4 --no-reload
```

## 📖 API文档

启动服务器后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 使用示例

### 1. 文档上传

```python
import requests

# 上传文档
with open('论文.docx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/document/upload',
        files={'file': f}
    )
    
document_id = response.json()['document_id']
```

### 2. 文档处理

```python
# 处理文档
response = requests.post(f'http://localhost:8000/api/document/process/{document_id}')
print(response.json())
```

### 3. 开始评估

```python
# 启动评估任务
response = requests.post(
    'http://localhost:8000/api/evaluation/start',
    json={
        'document_id': document_id,
        'model_name': 'deepseek-chat'
    }
)

task_id = response.json()['task_id']
```

### 4. 查看进度

```python
# 查看任务进度
response = requests.get(f'http://localhost:8000/api/evaluation/progress/{task_id}')
print(response.json())
```

### 5. 获取结果

```python
# 获取评估结果
response = requests.get(f'http://localhost:8000/api/evaluation/result/{task_id}')
result = response.json()
print(f"总分: {result['result']['overall_score']}")
```

## 🧪 测试

### 运行所有测试

```bash
# 运行完整测试套件
python -m tests.run_tests

# 只运行API测试
python -m tests.run_tests --api-only

# 只运行模型测试
python -m tests.run_tests --models-only

# 保存测试报告
python -m tests.run_tests --save-report test_report.json
```

### 健康检查

```bash
# 检查系统状态
curl http://localhost:8000/api/health/

# 检查模型状态
curl http://localhost:8000/api/health/models
```

## 📁 项目结构

```
backend_fastapi/
├── api/                    # API路由
│   ├── document.py        # 文档处理API
│   ├── evaluation.py      # 评估API
│   ├── task.py           # 任务管理API
│   ├── analysis.py       # 数据分析API
│   └── health.py         # 健康检查API
├── models/                # AI模型接口
│   ├── deepseek.py       # DeepSeek模型
│   ├── gemini.py         # Gemini模型
│   ├── qwen.py           # Qwen模型
│   └── model_manager.py  # 模型管理器
├── pipeline/              # 推理流水线
│   ├── chapter_inference.py    # 章节推理
│   ├── quality_assessment.py   # 质量评估
│   └── paper_evaluation.py     # 论文评估
├── tools/                 # 工具函数
│   ├── docx_tools/       # Word文档处理
│   ├── file_utils.py     # 文件操作
│   └── logger.py         # 日志工具
├── config/               # 配置管理
├── middleware/           # 中间件
├── tests/               # 测试模块
├── utils/               # 实用工具
├── main.py              # 主应用
└── run_server.py        # 启动脚本
```

## 🔒 安全注意事项

1. **API密钥安全**: 不要在代码中硬编码API密钥
2. **文件上传**: 系统会验证文件类型和大小
3. **输入验证**: 所有输入都经过严格验证
4. **错误处理**: 敏感信息不会在错误消息中泄露

## 🐛 故障排除

### 常见问题

1. **模型API调用失败**
   - 检查API密钥是否正确设置
   - 确认网络连接正常
   - 查看日志文件获取详细错误信息

2. **文档处理失败**
   - 确认文档格式为.docx或.doc
   - 检查文档是否损坏
   - 确认文档大小不超过50MB

3. **服务器启动失败**
   - 检查端口是否被占用
   - 确认所有依赖已正确安装
   - 查看启动日志获取错误信息

### 日志文件

日志文件位置：
- 应用日志: `logs/app.log`
- 错误日志: `logs/error.log`
- API调用日志: `logs/api.log`

## 📞 技术支持

如有问题或建议，请通过以下方式联系：

- 项目仓库: [GitHub链接]
- 邮箱: support@paper-eval.com
- 文档: [在线文档链接]

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。
