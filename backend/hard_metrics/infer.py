"""
论文评价入口文件
"""

# 导入标准库
import sys
import os
from typing import List, Callable
from glob import glob

# 导入项目模块
# finegrained_inference: 细粒度推理。c个章节d个评价维度，发起c*d次api请求。暂时废弃。
# chapter_inference: 粗粒度推理。c个章节d个评价维度，发起c次api请求。
# quality_assessment: 质量评估。c个章节d个评价维度，发起c次api请求。
from pipeline.finegrained_inference import infer as finegrained_infer
from pipeline.chapter_inference import infer as chapter_infer
from pipeline.quality_assessment import infer as quality_infer
from pipeline.overall_assess import infer as overall_assess
from tools.get_pkl_files import get_pkl_files
from tools.logger import get_logger

# 创建日志记录器
logger = get_logger(__name__)


# ==================== 脚本执行参数 ====================
# 输入根目录：PKL文件或包含PKL文件的目录
INPUT_ROOT = "data/processed/docx"
# 输出根目录
OUTPUT_ROOT = "data/output/docx/deepseek"
# api请求并行数
PROCESSES = 16
# 使用的模型名称
MODEL_NAME = "deepseek-chat"
# ==================== 脚本执行参数 ====================


def run_inference(pkl_paths: List[str], output_ROOT: str, infer_module: Callable, model_name: str):
    """
    运行推理任务
    
    Args:
        pkl_paths: PKL文件路径列表
        output_ROOT: 输出目录
    """
    logger.info(f"待处理文件数量: {len(pkl_paths)}")
    logger.info("开始推理...")
    
    for pkl_path in pkl_paths:
        logger.info(f"处理文件: {pkl_path}...")
        try:
            infer_module(pkl_path, output_ROOT, PROCESSES, model_name)
        except Exception as e:
            logger.error(f"错误: {e}")  
    logger.info("推理完成！")


def main(infer_module: Callable, model_name: str):
    # 确保输入目录存在
    os.makedirs(INPUT_ROOT, exist_ok=True)
    
    # 获取PKL文件列表
    pkl_files = get_pkl_files(INPUT_ROOT)
    if not pkl_files:
        logger.error("错误: 没有找到PKL文件")
        logger.error(f"请检查输入路径: {INPUT_ROOT}")
        sys.exit(1)

    logger.info(f"找到 {len(pkl_files)} 个PKL文件:")
    for pkl_file in pkl_files:
        logger.info(f"  - {pkl_file}")
    
    # 创建输出目录
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    
    # 显示配置信息
    logger.info(f"\n配置信息:")
    logger.info(f"  - 输入路径: {INPUT_ROOT}")
    logger.info(f"  - 输出目录: {OUTPUT_ROOT}")
    
    # 运行推理
    try:
        run_inference(pkl_files, OUTPUT_ROOT, infer_module, model_name)
    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 选择推理模块
    infer_module = chapter_infer
    # 执行推理
    main(infer_module, MODEL_NAME)