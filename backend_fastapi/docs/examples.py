"""
API示例数据
提供各种API接口的示例请求和响应数据
"""

# 文档上传示例
DOCUMENT_UPLOAD_EXAMPLES = {
    "success_response": {
        "summary": "文档上传成功",
        "value": {
            "task_id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "论文.docx",
            "file_size": 1024000,
            "upload_time": "2025-07-17T01:10:56.228579",
            "status": "uploaded"
        }
    },
    "error_response": {
        "summary": "文件格式不支持",
        "value": {
            "success": False,
            "error": "不支持的文件格式",
            "detail": "不支持的文件格式: .pdf。支持的格式: .docx, .doc",
            "error_type": "ValidationError"
        }
    }
}

# 文档处理示例
DOCUMENT_PROCESS_EXAMPLES = {
    "success_response": {
        "summary": "文档处理成功",
        "value": {
            "success": True,
            "message": "文档处理完成",
            "document_id": "123e4567-e89b-12d3-a456-426614174000",
            "structure": {
                "file_path": "/tmp/document.pkl",
                "file_size": 2048,
                "has_zh_abs": True,
                "has_en_abs": True,
                "has_ref": True,
                "chapter_count": 5,
                "chapters": [
                    {
                        "index": 0,
                        "name": "第一章 绪论",
                        "content_length": 1500,
                        "image_count": 2
                    }
                ]
            },
            "summary": {
                "zh_abstract_length": 300,
                "en_abstract_length": 250,
                "reference_length": 800,
                "chapter_count": 5,
                "total_content_length": 15000,
                "total_images": 12
            }
        }
    }
}

# 评估请求示例
EVALUATION_REQUEST_EXAMPLES = {
    "start_evaluation": {
        "summary": "开始评估请求",
        "value": {
            "document_id": "123e4567-e89b-12d3-a456-426614174000",
            "model_name": "deepseek-chat",
            "evaluation_type": "full"
        }
    },
    "chapter_evaluation": {
        "summary": "章节评估请求",
        "value": {
            "document_id": "123e4567-e89b-12d3-a456-426614174000",
            "chapter_index": 0,
            "model_name": "deepseek-chat"
        }
    }
}

# 评估结果示例
EVALUATION_RESULT_EXAMPLES = {
    "success_response": {
        "summary": "评估完成",
        "value": {
            "success": True,
            "message": "评估已完成",
            "task_id": "task-123e4567-e89b-12d3-a456-426614174000",
            "result": {
                "overall_score": 425,
                "dimensions": {
                    "创新性": 85,
                    "技术深度": 78,
                    "实验设计": 92,
                    "写作质量": 80,
                    "学术规范": 90
                },
                "summary": "该论文在实验设计方面表现突出，学术规范性良好，但在技术深度方面还有提升空间。",
                "detailed_analysis": {
                    "strengths": [
                        "实验设计合理，数据充分",
                        "学术写作规范，引用准确",
                        "研究问题明确，目标清晰"
                    ],
                    "weaknesses": [
                        "技术方法描述不够详细",
                        "创新点阐述不够突出",
                        "部分章节逻辑衔接不够紧密"
                    ],
                    "suggestions": [
                        "建议补充技术实现的详细描述",
                        "加强创新点的理论分析",
                        "优化章节间的逻辑过渡"
                    ]
                },
                "chapter_scores": [
                    {"chapter": "第一章 绪论", "score": 85},
                    {"chapter": "第二章 相关工作", "score": 78},
                    {"chapter": "第三章 方法设计", "score": 82},
                    {"chapter": "第四章 实验结果", "score": 92},
                    {"chapter": "第五章 总结与展望", "score": 80}
                ]
            }
        }
    }
}

# 任务状态示例
TASK_STATUS_EXAMPLES = {
    "running": {
        "summary": "任务进行中",
        "value": {
            "success": True,
            "task_id": "task-123e4567-e89b-12d3-a456-426614174000",
            "status": "running",
            "progress": 0.65,
            "message": "正在评估第3章...",
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:35:30",
            "duration": 330.5
        }
    },
    "completed": {
        "summary": "任务完成",
        "value": {
            "success": True,
            "task_id": "task-123e4567-e89b-12d3-a456-426614174000",
            "status": "completed",
            "progress": 1.0,
            "message": "评估完成",
            "result": {"overall_score": 425},
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:40:00",
            "duration": 600.0
        }
    }
}

# 数据分析示例
ANALYSIS_EXAMPLES = {
    "radar_chart": {
        "summary": "雷达图数据",
        "value": {
            "success": True,
            "chart_type": "radar",
            "data": {
                "dimensions": ["创新性", "技术深度", "实验设计", "写作质量", "学术规范"],
                "scores": [85, 78, 92, 80, 90]
            },
            "options": {
                "title": "论文质量评估雷达图",
                "max_score": 100,
                "overall_score": 425
            }
        }
    },
    "bar_chart": {
        "summary": "柱状图数据",
        "value": {
            "success": True,
            "chart_type": "bar",
            "data": {
                "categories": ["第一章 绪论", "第二章 相关工作", "第三章 方法设计", "第四章 实验结果", "第五章 总结与展望"],
                "scores": [85, 78, 82, 92, 80]
            },
            "options": {
                "title": "各章节评分对比",
                "y_axis_title": "评分",
                "x_axis_title": "章节",
                "has_evaluation": True
            }
        }
    }
}

# 健康检查示例
HEALTH_CHECK_EXAMPLES = {
    "healthy": {
        "summary": "系统健康",
        "value": {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00",
            "version": "1.0.0",
            "uptime": 3600.5,
            "system": {
                "cpu_percent": 25.5,
                "memory_percent": 45.2,
                "disk_percent": 60.1,
                "python_version": "3.9.7"
            },
            "models": {
                "deepseek-chat": {
                    "provider": "deepseek",
                    "available": True,
                    "name": "deepseek-chat"
                },
                "qwen": {
                    "provider": "alibaba",
                    "available": True,
                    "name": "qwen"
                }
            }
        }
    }
}

# 汇总所有示例
API_EXAMPLES = {
    "document": {
        "upload": DOCUMENT_UPLOAD_EXAMPLES,
        "process": DOCUMENT_PROCESS_EXAMPLES
    },
    "evaluation": {
        "request": EVALUATION_REQUEST_EXAMPLES,
        "result": EVALUATION_RESULT_EXAMPLES
    },
    "task": {
        "status": TASK_STATUS_EXAMPLES
    },
    "analysis": {
        "charts": ANALYSIS_EXAMPLES
    },
    "health": {
        "check": HEALTH_CHECK_EXAMPLES
    }
}
