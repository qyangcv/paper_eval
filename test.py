#!/usr/bin/env python3
"""
测试脚本：完整测试文档上传、处理和分析功能
测试文件：龚礼盛-本科毕业论文.docx
"""

import asyncio
import json
import time
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import UploadFile
from fastapi.testclient import TestClient
from backend_fastapi.main import app
from backend_fastapi.utils.redis_client import get_redis_manager
from backend_fastapi.api.document import upload_document, process_document_api
from backend_fastapi.api.analysis import (
    get_basic_info,
    get_overall_stats, 
    get_chapter_stats,
    get_ref_stats,
    get_soft_eval,
    get_hard_eval
)

# 测试文件路径
TEST_FILE_PATH = "/Users/yang/Documents/bupt/code/github/paper_eval/backend_fastapi/data/raw/龚礼盛-本科毕业论文.docx"

def print_separator(title: str):
    """打印分隔符"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_json_pretty(data, title: str = "结果"):
    """美化打印JSON数据"""
    print(f"\n📋 {title}:")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data)

async def create_mock_upload_file(file_path: str) -> UploadFile:
    """创建模拟的UploadFile对象"""
    import io
    from typing import BinaryIO
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"测试文件不存在: {file_path}")
    
    # 读取文件内容
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    # 创建模拟的文件对象
    file_like = io.BytesIO(file_content)
    file_like.name = os.path.basename(file_path)
    
    # 创建UploadFile对象 - 使用正确的参数
    upload_file = UploadFile(
        file=file_like,
        filename=os.path.basename(file_path),
        size=len(file_content)
    )
    
    return upload_file

async def test_document_upload():
    """测试文档上传"""
    print_separator("1. 测试文档上传")
    
    try:
        # 创建模拟的上传文件
        upload_file = await create_mock_upload_file(TEST_FILE_PATH)
        
        # 调用上传函数
        result = await upload_document(upload_file)
        
        print("✅ 文档上传成功!")
        
        # 处理返回结果 - 可能是dict或Pydantic模型
        try:
            # 尝试调用dict()方法（Pydantic模型）
            result_dict = result.dict()  # type: ignore
            print_json_pretty(result_dict, "上传结果")
            return result_dict.get('task_id')
        except AttributeError:
            # 如果没有dict()方法，检查是否是字典
            if isinstance(result, dict):
                print_json_pretty(result, "上传结果")
                return result.get('task_id')
            else:
                # 其他类型，尝试获取属性
                print_json_pretty(str(result), "上传结果")
                return getattr(result, 'task_id', None)
        
    except Exception as e:
        print(f"❌ 文档上传失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_document_process(task_id: str):
    """测试文档处理"""
    print_separator("2. 测试文档处理")
    
    try:
        # 准备请求数据
        request_data = {
            "task_id": task_id,
            "model_config": {}
        }
        
        # 调用处理函数
        result = await process_document_api(request_data)
        
        print("✅ 文档处理启动成功!")
        print_json_pretty(result, "处理结果")
        
        # 等待处理完成
        print("\n⏳ 等待文档处理完成...")
        redis_mgr = await get_redis_manager()
        
        max_wait_time = 300  # 最大等待5分钟
        wait_interval = 5    # 每5秒检查一次
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            document_info = await redis_mgr.get_document(task_id)
            if document_info and document_info.get('status') == 'processed':
                print("✅ 文档处理完成!")
                return True
            elif document_info and document_info.get('status') == 'failed':
                print(f"❌ 文档处理失败: {document_info.get('error', '未知错误')}")
                return False
            
            # 显示进度
            progress = document_info.get('progress', 0) if document_info else 0
            message = document_info.get('message', '等待处理') if document_info else '等待处理'
            print(f"⏳ 处理进度: {progress*100:.1f}% - {message}")
            
            await asyncio.sleep(wait_interval)
            elapsed_time += wait_interval
        
        print("⚠️ 文档处理超时")
        return False
        
    except Exception as e:
        print(f"❌ 文档处理失败: {e}")
        return False

async def check_redis_data(task_id: str):
    """检查Redis中的数据"""
    print_separator("3. 检查Redis中的数据")
    
    try:
        redis_mgr = await get_redis_manager()
        document_info = await redis_mgr.get_document(task_id)
        
        if not document_info:
            print("❌ Redis中没有找到文档数据")
            return False
        
        print("✅ Redis数据检查:")
        print(f"📄 文档ID: {document_info.get('id')}")
        print(f"📄 文件名: {document_info.get('filename')}")
        print(f"📄 状态: {document_info.get('status')}")
        print(f"📄 文件大小: {document_info.get('size')} bytes")
        print(f"📄 有Markdown内容: {'是' if document_info.get('md_content') else '否'}")
        print(f"📄 有图片: {len(document_info.get('images', []))} 张")
        print(f"📄 有参考文献: {len(document_info.get('references', []))} 条")
        print(f"📄 有结构化数据: {'是' if document_info.get('pkl_data') else '否'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查Redis数据失败: {e}")
        return False

async def test_analysis_routes(task_id: str):
    """测试所有分析路由"""
    print_separator("4. 测试分析路由")
    
    # 测试路由列表
    test_routes = [
        ("基础信息", get_basic_info),
        ("整体统计", get_overall_stats),
        ("章节统计", get_chapter_stats),
        ("参考文献统计", get_ref_stats),
        ("软指标评估", get_soft_eval),
        ("问题分析", get_hard_eval)
    ]
    
    results = {}
    
    for route_name, route_func in test_routes:
        print(f"\n🔄 测试 {route_name}...")
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 调用路由函数
            result = await route_func(task_id)
            
            # 记录结束时间
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ {route_name} 测试成功! (耗时: {duration:.2f}秒)")
            
            # 打印完整的原始响应
            print(f"\n� {route_name} - 原始响应:")
            print("-" * 60)
            print_json_pretty(result, f"{route_name}完整响应")
            print("-" * 60)
            
            results[route_name] = {
                "success": True,
                "duration": duration,
                "data_size": len(str(result)) if result else 0
            }
            
        except Exception as e:
            print(f"❌ {route_name} 测试失败: {e}")
            results[route_name] = {
                "success": False,
                "error": str(e),
                "duration": 0
            }
    
    return results

def print_test_summary(results: dict):
    """打印测试总结"""
    print_separator("5. 测试总结")
    
    success_count = sum(1 for r in results.values() if r.get("success"))
    total_count = len(results)
    total_time = sum(r.get("duration", 0) for r in results.values())
    
    print(f"\n📊 测试结果总览:")
    print(f"   ✅ 成功: {success_count}/{total_count}")
    print(f"   ⏱️ 总耗时: {total_time:.2f}秒")
    print(f"   📈 成功率: {success_count/total_count*100:.1f}%")
    
    print(f"\n📋 详细结果:")
    for route_name, result in results.items():
        status = "✅" if result.get("success") else "❌"
        duration = result.get("duration", 0)
        
        if result.get("success"):
            data_size = result.get("data_size", 0)
            print(f"   {status} {route_name}: {duration:.2f}秒 (数据大小: {data_size} 字符)")
        else:
            error = result.get("error", "未知错误")
            print(f"   {status} {route_name}: 失败 - {error}")

async def main():
    """主测试函数"""
    print_separator("开始测试文档处理和分析功能")
    print(f"🔄 测试文件: {TEST_FILE_PATH}")
    
    # 检查测试文件是否存在
    if not os.path.exists(TEST_FILE_PATH):
        print(f"❌ 测试文件不存在: {TEST_FILE_PATH}")
        return
    
    try:
        # 1. 测试文档上传
        task_id = await test_document_upload()
        if not task_id:
            print("❌ 无法继续测试，文档上传失败")
            return
        
        print(f"\n📋 任务ID: {task_id}")
        
        # 2. 测试文档处理
        process_success = await test_document_process(task_id)
        if not process_success:
            print("❌ 无法继续测试，文档处理失败")
            return
        
        # 3. 检查Redis数据
        redis_ok = await check_redis_data(task_id)
        if not redis_ok:
            print("⚠️ Redis数据有问题，但继续测试分析功能")
        
        # 4. 测试分析路由
        analysis_results = await test_analysis_routes(task_id)
        
        # 5. 打印总结
        print_test_summary(analysis_results)
        
        print(f"\n🎉 测试完成! 任务ID: {task_id}")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())