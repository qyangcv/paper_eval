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
from pipeline.overall_assess import infer as overall_assess
from tools.logger import get_logger

# 创建日志记录器
logger = get_logger(__name__)


# ==================== 脚本执行参数 ====================
# 输入根目录：MD文件或包含MD文件的目录
INPUT_ROOT = "data/processed/docx"
# 输出根目录
OUTPUT_ROOT = "data/output/docx"
# api请求并行数
PROCESSES = 16
# 使用的模型名称
MODEL_NAME = "deepseek-chat"
# ==================== 脚本执行参数 ====================


def get_md_files(root_path: str) -> List[str]:
    """
    获取指定目录下的所有MD文件
    
    Args:
        root_path: 根目录路径
        
    Returns:
        List[str]: MD文件路径列表
    """
    md_files = []
    
    if os.path.isfile(root_path) and root_path.endswith('.md'):
        # 如果输入是单个MD文件
        md_files.append(root_path)
    elif os.path.isdir(root_path):
        # 如果输入是目录，搜索其中的MD文件
        pattern = os.path.join(root_path, "**", "*.md")
        md_files = glob(pattern, recursive=True)
    
    return md_files


def run_inference(md_paths: List[str], output_root: str, model_name: str):
    """
    运行推理任务
    
    Args:
        md_paths: MD文件路径列表
        output_root: 输出目录
        model_name: 使用的模型名称
    """
    logger.info(f"待处理文件数量: {len(md_paths)}")
    logger.info("开始推理...")
    
    for md_path in md_paths:
        logger.info(f"处理文件: {md_path}...")
        try:
            # 调用overall_assess.infer函数
            # 参数：md_path, metrics=None, num_processes=1, model_name, save_dir
            result = overall_assess(
                md_path=md_path,
                metrics=None,  # 使用默认评估指标
                num_processes=1,  # overall_assess内部不支持多进程
                model_name=model_name,
                save_dir=output_root
            )
            logger.info(f"文件 {md_path} 处理完成")
        except Exception as e:
            logger.error(f"处理文件 {md_path} 时出错: {e}")  
    logger.info("推理完成！")


def main(model_name: str):
    # 确保输入目录存在
    os.makedirs(INPUT_ROOT, exist_ok=True)
    
    # 获取MD文件列表
    md_files = get_md_files(INPUT_ROOT)
    if not md_files:
        logger.error("错误: 没有找到MD文件")
        logger.error(f"请检查输入路径: {INPUT_ROOT}")
        sys.exit(1)

    logger.info(f"找到 {len(md_files)} 个MD文件:")
    for md_file in md_files:
        logger.info(f"  - {md_file}")
    
    # 创建输出目录
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    
    # 显示配置信息
    logger.info(f"\n配置信息:")
    logger.info(f"  - 输入路径: {INPUT_ROOT}")
    logger.info(f"  - 输出目录: {OUTPUT_ROOT}")
    logger.info(f"  - 模型名称: {model_name}")
    
    # 运行推理
    try:
        run_inference(md_files, OUTPUT_ROOT, model_name)
    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 执行推理
    main(MODEL_NAME)