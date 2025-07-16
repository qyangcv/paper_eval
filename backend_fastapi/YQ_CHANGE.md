
- 修改 `api/document.py` 和 `task.py` 中的数据存储方式为 Redis。安装 Redis：`pip install redis aioredis`
- 修改了 `api/document.py` 的 `upload_document()` 和 `process_document()` 函数，`upload_document()` 读取的文档会存储在 Redis 中，`process_document()` 会对文档进行所有需要的预处理，包括：docx转markdown、提取图片、提取参考文献，并将预处理得到的信息全部存入 Redis
- 新增路由所需函数，位于`api/eval_module.py`，`api/eval_module.py` 调用 `pipeline/` 目录下对应的模块执行实际功能
    1. `api.eval_module.hard_eval()` 调用 `pipeline.hard_eval.eval()`
    2. `api.eval_module.soft_eval()` 调用 `pipeline.soft_eval.eval()`
    3. `api.eval_module.ref_eval()` 调用 `pipeline.reference_eval.eval()`
    4. `api.eval_module.img_eval()` 调用 `pipeline.image_eval.hard_eval.eval()`
    5. 这4个`eval()`是最底层向大模型发送请求分析论文的函数，后续在这里修改
- 新增路由，位于`api/analysis.py`：
    - 参考文献分析接口: `GET /api/analysis/{task_id}/reference-stats`
    - 评价维度接口: `GET /api/analysis/{task_id}/evaluation`
    - 问题分析接口: `GET /api/analysis/{task_id}/issues`
    - 图片分析接口： `GET /api/analysis/{task_id}/image`
- `api/analysis.py` 路由函数直接Return `api/eval_module.py` 中对应的函数，响应的数据格式为：
    1. 硬指标评价接口：
        ```python
        @router.get("/{task_id}/issues")
        async def get_hard_eval(document_id: str):
            return await hard_eval(document_id)
        ```
        响应：
        ```json
        {
            "summary": {
                "total_issues": 15,
                "issue_types": ["格式错误", "语法问题", "逻辑不清"],
                "severity_distribution": {
                "高": 5,
                "中": 5,
                "低": 8
                }
            },
            "by_chapter": {
                "摘要": [
                {
                    "id": "1",
                    "type": "格式错误",
                    "severity": "中",
                    "sub_chapter": "1.1_研究背景",
                    "original_text": "原文内容",
                    "detail": "问题描述",
                    "suggestion": "改进建议"
                }
                ]
            }
        }   
        ```
    2. 软指标评价接口：
        ```python
        @router.get("/{task_id}/evaluation")
        async def get_soft_eval(document_id: str):
            return await soft_eval(document_id)
        ```
        响应：
       ```json 
        {
            "overall_score": 7.75,
            "dimensions": [
                {
                "name": "选题创新性",
                "score": 8,
                "full_score": 10,
                "weight": 1.0,
                "focus_chapter": ["1.2_国内外研究现状", "1.3_研究内容与创新点"],
                "comment": "评价总结",
                "advantages": ["优势1", "优势2"],
                "weaknesses": ["不足1", "不足2"],
                "suggestions": ["建议1", "建议2"]
                }
            ]
        }
        ```
    3. 参考文献评价接口：
        ```python
        @router.get("/{task_id}/reference-stats")
        async def get_ref_stats(document_id: str):
            return await ref_eval(document_id)
        ```
        响应：
        ```json
        {
            "total_issues": 5,
            "detail": [
                {
                    "id": 1,
                    "original_text": "[4]Lin, H. et al. ... 190-220",
                    "suggestions": ["建议1", "建议2", "建议3"]
                }
            ]
        }
        ```
    4. 图片查重评价接口
        ```python
        @router.get("{task_id}/image")
        async def get_img_eval(document_id: str):
            return await img_eval(document_id)
        ```
        响应：
        ```json
        {
            "total_reused": 5,
            "detail": [
                {
                    "image_id": "redis中的图片id，如image_4",
                    "image_title": "图2-1_Transformer_Encoder结构图",
                    "image_info": "base64编码的图片信息",
                    "image_type": ".png/.jpg等",
                    "reused_link": ["web_link_1", "web_link_2"],
                    "reused_sim": ["相似度_1", "相似度_2"]
                }
            ]
        }
        ```