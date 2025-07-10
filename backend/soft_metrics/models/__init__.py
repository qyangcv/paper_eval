"""
模型模块
包含与各种大语言模型接口

注意事项：
- 使用前需要配置相应的API密钥
- 各模型的参数格式可能有所不同
- 建议根据任务选择合适的模型

包含以下模型接口：
- qwen: Qwen 模型接口
    可用模型：qwen-max
- deepseek: DeepSeek 模型接口  
    可用模型：deepseek-chat, deepseek-reasoner
- gemini: Google Gemini 模型接口
    可用模型：gemini-2.5-flash-preview-05-20

使用方法：
    from backend.models.qwen import request_qwen
    from backend.models.deepseek import request_deepseek  
    from backend.models.gemini import request_gemini
    
    # 调用示例
    response = request_qwen("请分析这段文本")
    response = request_deepseek("评估论文质量", "deepseek-chat")
    response = request_gemini("生成摘要")
"""
