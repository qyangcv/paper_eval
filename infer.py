#!/usr/bin/env python3
"""
论文评估推理主入口
整合批量推理、章节推理和质量评估三个模块的推理功能
"""

import sys
import os
from typing import List, Callable
from glob import glob

# 导入 pipeline 模块的推理函数
from pipeline.batch_inference import infer as batch_infer
from pipeline.chapter_inference import infer as chapter_infer
from pipeline.quality_assessment import infer as quality_infer
from utils.get_pkl_files import get_pkl_files


# ==================== 配置参数 ====================
# 输入根目录：PKL文件或包含PKL文件的目录
INPUT_ROOT = "data/processed/docx"
# 输出根目录
OUTPUT_ROOT = "data/output/docx/deepseek"
# 处理进程数
PROCESSES = 16
# 使用的模型名称
MODEL_NAME = "deepseek-chat"
# ==================== 配置参数 ====================


def run_inference(pkl_paths: List[str], output_ROOT: str, infer_module: Callable, model_name: str):
    """
    运行推理任务
    
    Args:
        pkl_paths: PKL文件路径列表
        output_ROOT: 输出目录
    """
    print(f"待处理文件数量: {len(pkl_paths)}")
    print("开始推理...")
    
    for pkl_path in pkl_paths:
        print(f"处理文件: {pkl_path}...")
        try:
            infer_module(pkl_path, output_ROOT, PROCESSES, model_name)
        except Exception as e:
            print(f"错误: {e}")  
    print("推理完成！")


def main(infer_module: Callable, model_name: str):
    # 获取PKL文件列表
    pkl_files = get_pkl_files(INPUT_ROOT)
    if not pkl_files:
        print("错误: 没有找到PKL文件")
        print(f"请检查输入路径: {INPUT_ROOT}")
        sys.exit(1)

    print(f"找到 {len(pkl_files)} 个PKL文件:")
    for pkl_file in pkl_files:
        print(f"  - {pkl_file}")
    
    # 创建输出目录
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    
    # 显示配置信息
    print(f"\n配置信息:")
    print(f"  输入路径: {INPUT_ROOT}")
    print(f"  输出目录: {OUTPUT_ROOT}")
    
    # 运行推理
    try:
        run_inference(pkl_files, OUTPUT_ROOT, infer_module, model_name)
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    infer_module = chapter_infer
    main(infer_module, MODEL_NAME)