#!/usr/bin/env python
import os
import sys
import shutil
import subprocess
from pathlib import Path
import logging
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查所需依赖是否已安装"""
    logger.info("检查依赖...")
    
    # 检查是否设置了 DEEPSEEK_API_KEY
    if not os.environ.get("DEEPSEEK_API_KEY"):
        logger.warning("DEEPSEEK_API_KEY 环境变量未设置")
        api_key = input("请输入您的 DeepSeek API 密钥以继续 (或按 Enter 退出): ")
        if not api_key:
            logger.error("未提供 API 密钥。退出...")
            return False
        
        # 为本次会话设置 API 密钥
        os.environ["DEEPSEEK_API_KEY"] = api_key
        logger.info("✓ 已为本次会话设置 DEEPSEEK_API_KEY")
        
        # 建议永久设置
        if os.name == 'nt':  # Windows
            cmd = "set DEEPSEEK_API_KEY=your_key"
        else:  # Unix/Linux/MacOS
            cmd = "export DEEPSEEK_API_KEY=your_key"
        logger.info(f"若要永久设置，请使用: {cmd}")
    else:
        logger.info("✓ 已找到 DEEPSEEK_API_KEY")
    
    # 检查所需目录是否存在
    dirs = ["data/raw/docx", "data/processed", "data/output"]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        
    return True

def prepare_sample_file(docx_path):
    """准备用于评估的示例文件"""
    logger.info(f"准备示例文件: {docx_path}")
    
    if not os.path.exists(docx_path):
        logger.error(f"未找到示例文件: {docx_path}")
        return False
    
    # 如果不在目标位置，将 docx 文件复制到 data/raw/docx
    filename = os.path.basename(docx_path)
    dest_path = os.path.join("data/raw/docx", filename)
    
    if docx_path != dest_path:
        shutil.copy(docx_path, dest_path)
        logger.info(f"已复制 {docx_path} 到 {dest_path}")
    
    # 将 docx 转换为 md，使用 docx2md.py 而不是 pandoc
    md_filename = os.path.splitext(filename)[0] + ".md"
    md_path = os.path.join("data/raw/docx", md_filename)
    image_dir = os.path.join("data/raw/docx/images")
    
    # 确保图片目录存在
    os.makedirs(image_dir, exist_ok=True)
    
    # 使用 docx2md.py 进行转换
    cmd = f"{sys.executable} utils/docx_tools/docx2md.py \"{dest_path}\" -o \"{md_path}\" -i \"{image_dir}\""
    logger.info(f"正在将 docx 转换为 md...")
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        logger.info(f"✓ 已创建 Markdown 文件: {md_path}")
    except subprocess.SubprocessError as e:
        logger.error(f"将 docx 转换为 md 失败: {e}")
        return False
    
    # 使用项目的工具将 md 转换为 pkl
    try:
        # 创建一个直接调用函数的简单脚本，而不修改原始脚本
        temp_script = "temp_md2pkl.py"
        
        # 确保输出目录存在
        os.makedirs("data/processed/docx", exist_ok=True)
        
        # 获取绝对路径以避免路径问题 - 保存到 data/processed/docx 以匹配 infer.py 的期望
        abs_md_path = os.path.abspath(md_path)
        abs_pkl_path = os.path.abspath(f"data/processed/docx/{os.path.splitext(filename)[0]}.pkl")
        
        # 修复字符串字面量的路径格式（将反斜杠替换为双反斜杠）
        abs_md_path_str = abs_md_path.replace("\\", "\\\\")
        abs_pkl_path_str = abs_pkl_path.replace("\\", "\\\\")
        
        # 创建一个导入原始模块并使用我们路径调用其函数的简单脚本
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(f"""
import sys
sys.path.append("utils/docx_tools")
from md2pkl import read_md, extract_abstracts, extract_reference, extract_chapters
import pickle

def main():
    # 使用带有转义反斜杠的显式字符串
    md = read_md(r'{abs_md_path}')
    zh_abs, en_abs = extract_abstracts(md)
    ref = extract_reference(md)
    chapters = extract_chapters(md)
    data = {{
        'zh_abs': zh_abs,
        'en_abs': en_abs,
        'ref': ref,
        'chapters': chapters
    }}
    with open(r'{abs_pkl_path}', 'wb') as f:
        pickle.dump(data, f)
    print('已保存到 ' + r'{abs_pkl_path}')

if __name__ == '__main__':
    main()
""")
        
        # 运行新脚本
        subprocess.run([sys.executable, temp_script], check=True)
        logger.info(f"✓ 已将 md 转换为 pkl 并保存到 {abs_pkl_path}")
        
        # 清理
        os.remove(temp_script)
        
    except Exception as e:
        logger.error(f"将 md 转换为 pkl 失败: {e}")
        return False
    
    return True

def run_inference():
    """运行推理过程"""
    logger.info("正在运行推理...")
    try:
        subprocess.run([sys.executable, "infer.py"], check=True)
        logger.info("✓ 推理成功完成")
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"推理失败: {e}")
        return False

def convert_output():
    """将 JSON 输出转换为 Markdown"""
    logger.info("正在将 JSON 输出转换为 Markdown...")
    try:
        # 输出目录匹配 infer.py 的 OUTPUT_ROOT 变量
        output_dir = "data/output/docx/deepseek"
        
        # 查找最新的 JSON 输出并转换
        outputs = list(Path(output_dir).glob("*.json"))
        if not outputs:
            logger.warning(f"在 {output_dir} 中未找到 JSON 输出")
            return False
        
        # 按创建时间排序，最新的在前
        latest_output = sorted(outputs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        logger.info(f"正在转换 {latest_output} 为 Markdown")
        
        # 运行转换脚本，使用适当的 Python 路径以找到 config 模块
        cmd = f"{sys.executable} -c \"import sys; sys.path.insert(0, '.'); from utils.json2md import json2md; json2md(r'{latest_output}', r'{latest_output.with_suffix('.md')}');\""
        subprocess.run(cmd, shell=True, check=True)
        logger.info("✓ 转换完成")
        
        md_output = latest_output.with_suffix('.md')
        if md_output.exists():
            logger.info(f"结果保存到: {md_output}")
        
        return True
    except Exception as e:
        logger.error(f"转换失败: {e}")
        return False

def main():
    """运行测试的主函数"""
    logger.info("=== 论文评估测试脚本 ===")
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 询问用户提供 docx 文件路径
    docx_path = input("请输入要评估的示例 .docx 文件路径 (或按 Enter 跳过): ")
    
    if docx_path:
        # 准备示例文件
        if not prepare_sample_file(docx_path):
            logger.error("准备示例文件失败")
            return
    else:
        # 检查是否有已准备好的 pkl 文件
        pkl_files = list(Path("data/processed").glob("*.pkl"))
        if not pkl_files:
            logger.error("未找到 pkl 文件且未提供示例文件")
            return
        logger.info(f"使用现有的 pkl 文件: {[p.name for p in pkl_files]}")
    
    # 运行推理
    if not run_inference():
        return
    
    # 转换输出
    convert_output()
    
    logger.info("=== 测试完成 ===")

if __name__ == "__main__":
    main() 