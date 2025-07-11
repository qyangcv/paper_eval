#!/usr/bin/env python3
"""
论文全文评估脚本
评估论文所有章节，并基于章节评估结果进行整体评估

用法:
    python full_paper_eval.py <输入文件路径> [--model MODEL_NAME] [--output OUTPUT_PATH]
    
示例:
    python full_paper_eval.py data/raw/docx/paper.docx --model deepseek-chat
    python full_paper_eval.py data/processed/docx/paper.pkl --output results/paper_eval.json
"""

import os
import sys
import json
import argparse
import logging
import time
import re
import pickle
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 设置工具目录的相对路径
TOOLS_DIR = os.path.join(project_root, "backend", "hard_metrics", "tools", "docx_tools")

# 导入项目模块
try:
    from models.deepseek import request_deepseek
    from models.gemini import request_gemini
    from models.qwen import request_qwen
    from prompts.chapter_prompt import p_chapter_assessment
    from prompts.overall_prompt import p_overall_assessment
    from tools.logger import get_logger
except ImportError as e:
    print(f"导入错误: {e}")
    print("确保您在正确的项目结构中运行此脚本")
    sys.exit(1)

# 设置日志记录器
logger = get_logger(__name__)

def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """
    从模型响应中提取JSON数据
    
    Args:
        response: 模型原始响应
    
    Returns:
        Optional[Dict[str, Any]]: 提取的JSON数据，如果提取失败则返回None
    """
    try:
        # 尝试直接解析为JSON
        data = json.loads(response)
        
        # 检查是否为ChatCompletion格式 (choices[].message.content)
        if 'choices' in data and data['choices'] and 'message' in data['choices'][0]:
            content = data['choices'][0]['message'].get('content', '')
            
            # 尝试从content中提取JSON代码块
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
                return json.loads(content)
            
            # 如果没有代码块，但content可以解析成JSON，则直接解析
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 如果content无法解析成JSON，且content本身有内容，那么原样返回
                if content.strip():
                    logger.warning("响应没有有效的JSON格式，但有内容")
                    return {"raw_content": content}
        elif isinstance(data, dict):
            # 如果已经是字典类型，则直接返回
            return data
        
        return None
    except json.JSONDecodeError:
        # 尝试从普通文本中提取JSON代码块
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                content = json_match.group(1)
                return json.loads(content)
            except json.JSONDecodeError:
                logger.warning("无法解析提取的代码块为JSON")
        
        logger.warning("无法从响应中提取有效的JSON数据")
        return None

def check_dependencies() -> bool:
    """
    检查所需依赖是否已安装
    
    Returns:
        bool: 检查是否通过
    """
    logger.info("检查依赖...")
    
    # 检查所需目录是否存在
    dirs = [
        os.path.join(project_root, "data", "raw", "docx"), 
        os.path.join(project_root, "data", "processed", "docx"),
        os.path.join(project_root, "data", "output")
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # 检查docx转换工具是否存在
    docx2md_path = os.path.join(TOOLS_DIR, "docx2md.py")
    md2pkl_path = os.path.join(TOOLS_DIR, "md2pkl.py")
    
    if not (os.path.exists(docx2md_path) and os.path.exists(md2pkl_path)):
        logger.error(f"缺少必要的文档处理工具。请确保以下文件存在:")
        logger.error(f"- {docx2md_path}")
        logger.error(f"- {md2pkl_path}")
        return False
        
    return True

def process_docx_file(docx_path: str) -> Optional[str]:
    """
    处理docx文件，将其转换为pkl格式
    
    Args:
        docx_path: docx文件路径
    
    Returns:
        Optional[str]: 生成的pkl文件路径，如果处理失败则返回None
    """
    logger.info(f"处理文档文件: {docx_path}")
    
    if not os.path.exists(docx_path):
        logger.error(f"未找到文件: {docx_path}")
        return None
    
    if not docx_path.lower().endswith('.docx'):
        logger.error(f"文件 {docx_path} 不是.docx格式")
        return None
        
    # 确保所有必要的目录都存在
    raw_docx_dir = os.path.join(project_root, "data", "raw", "docx")
    processed_dir = os.path.join(project_root, "data", "processed", "docx")
    
    # 创建必要的目录
    os.makedirs(raw_docx_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # 如果不在目标位置，将 docx 文件复制到 data/raw/docx
    filename = os.path.basename(docx_path)
    dest_docx_path = os.path.join(raw_docx_dir, filename)
    
    if docx_path != dest_docx_path:
        shutil.copy(docx_path, dest_docx_path)
        logger.info(f"已复制 {docx_path} 到 {dest_docx_path}")
    
    # 将 docx 转换为 md
    md_filename = os.path.splitext(filename)[0] + ".md"
    md_path = os.path.join(raw_docx_dir, md_filename)
    image_dir = os.path.join(raw_docx_dir, "images")
    
    # 确保图片目录存在
    os.makedirs(image_dir, exist_ok=True)
    
    # 使用 docx2md.py 进行转换
    docx2md_path = os.path.join(TOOLS_DIR, "docx2md.py")
    cmd = f"{sys.executable} \"{docx2md_path}\" \"{dest_docx_path}\" -o \"{md_path}\" -i \"{image_dir}\""
    logger.info(f"正在将 docx 转换为 md...")
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        logger.info(f"已创建 Markdown 文件: {md_path}")
    except subprocess.SubprocessError as e:
        logger.error(f"将 docx 转换为 md 失败: {e}")
        return None
    
    # 使用项目的工具将 md 转换为 pkl
    try:
        # 创建一个直接调用函数的临时脚本
        temp_script = os.path.join(project_root, "temp_md2pkl.py")
        
        # 获取绝对路径以避免路径问题
        abs_md_path = os.path.abspath(md_path)
        pkl_filename = f"{os.path.splitext(filename)[0]}.pkl"
        abs_pkl_path = os.path.abspath(os.path.join(processed_dir, pkl_filename))
        
        # 修复字符串字面量的路径格式（将反斜杠替换为双反斜杠）
        abs_md_path_str = abs_md_path.replace("\\", "\\\\")
        abs_pkl_path_str = abs_pkl_path.replace("\\", "\\\\")
        
        # 创建一个导入原始模块并使用我们路径调用其函数的简单脚本
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(f"""import sys
sys.path.append(r'{TOOLS_DIR}')
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

if __name__ == '__main__':
    main()
""")
        
        # 运行临时脚本
        subprocess.run([sys.executable, temp_script], check=True)
        logger.info(f"已将 md 转换为 pkl 并保存到 {abs_pkl_path}")
        
        # 清理
        os.remove(temp_script)
        
        return abs_pkl_path
        
    except Exception as e:
        logger.error(f"将 md 转换为 pkl 失败: {e}")
        return None

def load_chapters(pkl_file: str) -> List[Dict[str, Any]]:
    """
    从PKL文件中加载所有章节信息
    
    Args:
        pkl_file: PKL文件路径
        
    Returns:
        List[Dict[str, Any]]: 章节信息列表
    """
    try:
        logger.info(f"正在从PKL文件加载章节内容: {pkl_file}")
        with open(pkl_file, 'rb') as f:
            data = pickle.load(f)
            
        if 'chapters' not in data or not isinstance(data['chapters'], list) or not data['chapters']:
            raise ValueError("PKL文件中没有找到有效的章节数据")
            
        chapters = []
        for i, chapter in enumerate(data['chapters'], 1):
            title = None
            content = None
            
            if isinstance(chapter, dict):
                # 获取章节标题
                if 'chapter_name' in chapter and chapter['chapter_name']:
                    title = chapter['chapter_name']
                elif 'title' in chapter and chapter['title']:
                    title = chapter['title']
                elif 'heading' in chapter and chapter['heading']:
                    title = chapter['heading']
                
                # 获取章节内容
                if 'content' in chapter and chapter['content']:
                    content = chapter['content']
                elif 'text_content' in chapter and chapter['text_content']:
                    content = chapter['text_content']
            elif isinstance(chapter, str):
                content = chapter
                title = f"章节 {i}"
                
            if content:
                chapters.append({
                    "index": i,
                    "title": title or f"章节 {i}",
                    "content": content
                })
            
        logger.info(f"已加载 {len(chapters)} 个章节")
        return chapters
    except Exception as e:
        logger.error(f"加载章节内容失败: {e}")
        raise

def request_model(prompt: str, model_name: str) -> Dict[str, Any]:
    """
    调用模型进行推理
    
    Args:
        prompt: 提示词
        model_name: 模型名称
        
    Returns:
        Dict[str, Any]: 推理结果
    """
    logger.info(f"正在使用模型 {model_name} 进行推理...")
    logger.debug(f"提示词长度: {len(prompt)} 字符")

    try:
        if model_name.startswith("deepseek"):
            response = request_deepseek(prompt, model_name)
            return {'input': prompt, 'output': response}
        elif model_name == "gemini":
            response = request_gemini(prompt)
            return {'input': prompt, 'output': response}
        elif model_name == "qwen":
            response = request_qwen(prompt)
            return {'input': prompt, 'output': response}
        else:
            raise ValueError(f"不支持的模型: {model_name}")
    except Exception as e:
        logger.error(f"模型推理失败: {e}")
        return {'input': prompt, 'error': str(e)}

def generate_chapter_prompt(chapter: Dict[str, Any]) -> str:
    """
    生成章节评估提示词
    
    Args:
        chapter: 章节信息
        
    Returns:
        str: 提示词
    """
    title = chapter["title"]
    content = chapter["content"]
    content_with_title = f"# {title}\n\n{content}"
    return p_chapter_assessment.replace("{content}", content_with_title)

def process_chapter(chapter: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    """
    处理单个章节的评估
    
    Args:
        chapter: 章节信息
        model_name: 使用的模型
        
    Returns:
        Dict[str, Any]: 评估结果
    """
    chapter_idx = chapter["index"]
    chapter_title = chapter["title"]
    
    logger.info(f"正在评估章节 {chapter_idx}: {chapter_title}")
    
    # 生成提示词
    prompt = generate_chapter_prompt(chapter)
    
    # 调用模型
    result = request_model(prompt, model_name)
    
    # 提取评估结果
    if 'error' in result:
        logger.error(f"章节 {chapter_idx} 评估失败: {result['error']}")
        return {
            "chapter": chapter_title,
            "index": chapter_idx,
            "error": result['error']
        }
    
    # 提取JSON评估结果
    eval_data = extract_json_from_response(result.get('output', '{}'))
    
    if not eval_data:
        logger.warning(f"章节 {chapter_idx} 无法提取有效的评估结果")
        return {
            "chapter": chapter_title,
            "index": chapter_idx,
            "error": "无法提取有效的评估结果"
        }
    
    # 构造标准格式结果
    evaluation = {
        "chapter": chapter_title,
        "index": chapter_idx,
        "summary": eval_data.get('summary', ''),
        "strengths": eval_data.get('strengths', []),
        "weaknesses": eval_data.get('weaknesses', []),
        "suggestions": eval_data.get('suggestions', [])
    }
    
    return evaluation

def evaluate_overall(chapter_evaluations: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
    """
    基于所有章节的评估结果进行整体评估
    
    Args:
        chapter_evaluations: 所有章节的评估结果
        model_name: 使用的模型
        
    Returns:
        Dict[str, Any]: 整体评估结果
    """
    logger.info("开始进行整体评估...")
    
    # 准备章节评估结果作为输入
    chapter_eval_str = json.dumps(chapter_evaluations, ensure_ascii=False, indent=2)
    
    # 生成整体评估提示词
    prompt = p_overall_assessment.replace("{chapter_evaluations}", chapter_eval_str)
    
    # 调用模型
    result = request_model(prompt, model_name)
    
    # 提取评估结果
    if 'error' in result:
        logger.error(f"整体评估失败: {result['error']}")
        return {
            "chapter": "全篇",
            "index": 0,
            "error": result['error']
        }
    
    # 提取JSON评估结果
    eval_data = extract_json_from_response(result.get('output', '{}'))
    
    if not eval_data:
        logger.warning("无法提取有效的整体评估结果")
        return {
            "chapter": "全篇",
            "index": 0,
            "error": "无法提取有效的整体评估结果" 
        }
    
    # 构造标准格式结果
    evaluation = {
        "chapter": "全篇",
        "index": 0,
        "summary": eval_data.get('summary', ''),
        "strengths": eval_data.get('strengths', []),
        "weaknesses": eval_data.get('weaknesses', []),
        "suggestions": eval_data.get('suggestions', [])
    }
    
    return evaluation

def save_evaluations(all_evaluations: List[Dict[str, Any]], output_path: str) -> str:
    """
    保存评估结果到单个文件
    
    Args:
        all_evaluations: 所有评估结果
        output_path: 输出文件路径
        
    Returns:
        str: 保存的文件路径
    """
    # 确保输出文件的目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 保存所有评估结果到一个文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_evaluations, f, ensure_ascii=False, indent=4)
    
    logger.info(f"所有评估结果已保存至: {output_path}")
    return output_path

def generate_score_prompt(all_evaluations: List[Dict[str, Any]]) -> str:
    """
    根据评估结果生成评分提示词
    
    Args:
        all_evaluations: 所有评估结果
        
    Returns:
        str: 评分提示词
    """
    # 构建提示词内容
    scoring_dimensions = [
        {'index': 1, 'module': '摘要', 'full_score': 5},
        {'index': 2, 'module': '选题背景和意义', 'full_score': 5},
        {'index': 3, 'module': '选题的理论意义与应用价值', 'full_score': 5},
        {'index': 4, 'module': '相关工作的国内外现状综述', 'full_score': 5},
        {'index': 5, 'module': '主要工作和贡献总结', 'full_score': 5},
        {'index': 6, 'module': '相关工作或相关技术的介绍', 'full_score': 5},
        {'index': 7, 'module': '论文的创新性', 'full_score': 25},
        {'index': 8, 'module': '实验完成度', 'full_score': 20},
        {'index': 9, 'module': '总结和展望', 'full_score': 5},
        {'index': 10, 'module': '工作量', 'full_score': 5},
        {'index': 11, 'module': '论文撰写质量', 'full_score': 10},
        {'index': 12, 'module': '参考文献', 'full_score': 5},
    ]
    
    # 格式化评估结果为字符串以便于模型阅读
    evaluations_str = json.dumps(all_evaluations, ensure_ascii=False, indent=2)
    dimensions_str = json.dumps(scoring_dimensions, ensure_ascii=False, indent=2)
    
    prompt = f"""
你是一位经验丰富的学术论文评分专家，你的任务是对一篇学位论文进行评分。你将收到该论文各个章节的详细评价结果，需要据此给出各个维度的评分。

# 评估维度与满分
请对以下维度进行评分，满分值如下：
{dimensions_str}

# 打分规则
1. 每个维度的得分不得超过满分值
2. 分数应当根据论文各章节的评估结果合理给出，不应过高或过低
3. 得分应为整数
4. 总分为各维度得分之和，总分满分为100分

# 输出格式
你必须严格按照以下JSON格式输出评分结果：
```json
[
    {{"index": 1, "module": "摘要", "full_score": 5, "score": 分数}},
    {{"index": 2, "module": "选题背景和意义", "full_score": 5, "score": 分数}},
    ...
]
```

# 论文评估结果
以下是论文各章节的评估结果，请仔细阅读后给出评分：
{evaluations_str}
"""
    return prompt

def score_paper(all_evaluations: List[Dict[str, Any]], model_name: str) -> List[Dict[str, Any]]:
    """
    对论文进行打分
    
    Args:
        all_evaluations: 所有评估结果
        model_name: 使用的模型
        
    Returns:
        List[Dict[str, Any]]: 评分结果
    """
    logger.info("开始对论文进行评分...")
    
    # 生成评分提示词
    prompt = generate_score_prompt(all_evaluations)
    
    # 调用模型
    result = request_model(prompt, model_name)
    
    # 提取评分结果
    if 'error' in result:
        logger.error(f"论文评分失败: {result['error']}")
        # 返回默认评分
        return [
            {'index': 1, 'module': '摘要', 'full_score': 5, 'score': 3},
            {'index': 2, 'module': '选题背景和意义', 'full_score': 5, 'score': 3},
            {'index': 3, 'module': '选题的理论意义与应用价值', 'full_score': 5, 'score': 3},
            {'index': 4, 'module': '相关工作的国内外现状综述', 'full_score': 5, 'score': 3},
            {'index': 5, 'module': '主要工作和贡献总结', 'full_score': 5, 'score': 3},
            {'index': 6, 'module': '相关工作或相关技术的介绍', 'full_score': 5, 'score': 3},
            {'index': 7, 'module': '论文的创新性', 'full_score': 25, 'score': 15},
            {'index': 8, 'module': '实验完成度', 'full_score': 20, 'score': 12},
            {'index': 9, 'module': '总结和展望', 'full_score': 5, 'score': 3},
            {'index': 10, 'module': '工作量', 'full_score': 5, 'score': 3},
            {'index': 11, 'module': '论文撰写质量', 'full_score': 10, 'score': 6},
            {'index': 12, 'module': '参考文献', 'full_score': 5, 'score': 3},
        ]
    
    # 提取JSON评分结果
    score_data = extract_json_from_response(result.get('output', '{}'))
    
    if not score_data or not isinstance(score_data, list):
        logger.warning("无法提取有效的评分结果")
        return [
            {'index': 1, 'module': '摘要', 'full_score': 5, 'score': 3},
            {'index': 2, 'module': '选题背景和意义', 'full_score': 5, 'score': 3},
            {'index': 3, 'module': '选题的理论意义与应用价值', 'full_score': 5, 'score': 3},
            {'index': 4, 'module': '相关工作的国内外现状综述', 'full_score': 5, 'score': 3},
            {'index': 5, 'module': '主要工作和贡献总结', 'full_score': 5, 'score': 3},
            {'index': 6, 'module': '相关工作或相关技术的介绍', 'full_score': 5, 'score': 3},
            {'index': 7, 'module': '论文的创新性', 'full_score': 25, 'score': 15},
            {'index': 8, 'module': '实验完成度', 'full_score': 20, 'score': 12},
            {'index': 9, 'module': '总结和展望', 'full_score': 5, 'score': 3},
            {'index': 10, 'module': '工作量', 'full_score': 5, 'score': 3},
            {'index': 11, 'module': '论文撰写质量', 'full_score': 10, 'score': 6},
            {'index': 12, 'module': '参考文献', 'full_score': 5, 'score': 3},
        ]
    
    # 验证和修正评分
    for item in score_data:
        if 'score' in item and 'full_score' in item:
            # 确保分数不超过满分且为整数
            item['score'] = min(int(item['score']), item['full_score'])
    
    return score_data

def save_scores(scores: List[Dict[str, Any]], output_path: str) -> str:
    """
    保存评分结果到文件
    
    Args:
        scores: 评分结果
        output_path: 输出文件的基础路径
        
    Returns:
        str: 保存的文件路径
    """
    # 构建评分结果保存路径
    output_dir = os.path.dirname(output_path)
    basename = os.path.basename(output_path)
    name_part = os.path.splitext(basename)[0]
    score_path = os.path.join(output_dir, f"{name_part}_score.json")
    
    # 保存评分结果
    with open(score_path, 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=4)
    
    logger.info(f"评分结果已保存至: {score_path}")
    
    # 计算总分
    total_score = sum(item['score'] for item in scores if 'score' in item)
    total_possible = sum(item['full_score'] for item in scores if 'full_score' in item)
    logger.info(f"论文总分: {total_score}/{total_possible}")
    
    return score_path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="论文全文评估工具")
    parser.add_argument("input_path", help="输入文件路径，支持.docx或.pkl格式")
    parser.add_argument("--model", "-m", default="deepseek-chat", help="评估使用的模型名称 (deepseek-chat, gemini, qwen)")
    parser.add_argument("--output", "-o", help="输出文件路径 (.json)")
    parser.add_argument("--max-workers", "-w", type=int, default=1, help="最大并行评估的章节数")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--no-score", action="store_true", help="不进行评分环节")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")
    
    start_time = time.time()
    
    try:
        # 检查依赖
        if not check_dependencies():
            logger.error("依赖检查失败，无法继续")
            sys.exit(1)
        
        pkl_file_path = args.input_path
        
        # 处理输入文件
        if args.input_path.lower().endswith('.docx'):
            logger.info("检测到.docx输入，进行文件转换")
            pkl_file_path = process_docx_file(args.input_path)
            if not pkl_file_path:
                logger.error("文件转换失败，无法继续")
                sys.exit(1)
        elif not args.input_path.lower().endswith('.pkl'):
            logger.error(f"不支持的输入文件格式: {args.input_path}")
            logger.error("请提供.docx或.pkl格式的文件")
            sys.exit(1)
        
        # 加载所有章节
        chapters = load_chapters(pkl_file_path)
        
        if not chapters:
            logger.error("未找到有效的章节内容")
            sys.exit(1)
        
        # 设置输出文件路径
        if args.output:
            output_path = args.output
        else:
            # 使用输入文件名作为输出文件名
            input_name = os.path.splitext(os.path.basename(args.input_path))[0]
            output_dir = os.path.join(project_root, "data", "output")
            output_path = os.path.join(output_dir, f"{input_name}_eval.json")
            
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 评估所有章节
        logger.info(f"开始评估 {len(chapters)} 个章节, 并行度: {args.max_workers}")
        chapter_evaluations = []
        
        if args.max_workers > 1:
            # 并行评估
            with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
                # 提交所有任务
                future_to_chapter = {
                    executor.submit(process_chapter, chapter, args.model): chapter
                    for chapter in chapters
                }
                
                # 获取结果
                for future in as_completed(future_to_chapter):
                    chapter = future_to_chapter[future]
                    try:
                        evaluation = future.result()
                        chapter_evaluations.append(evaluation)
                        logger.info(f"章节 {evaluation.get('index')} 评估完成")
                    except Exception as e:
                        logger.error(f"章节 {chapter['index']} 处理失败: {e}")
                        chapter_evaluations.append({
                            "chapter": chapter['title'],
                            "index": chapter['index'],
                            "error": str(e)
                        })
                    
                # 按章节序号排序
                chapter_evaluations.sort(key=lambda x: x.get('index', 0))
        else:
            # 串行评估
            for chapter in chapters:
                evaluation = process_chapter(chapter, args.model)
                chapter_evaluations.append(evaluation)
        
        # 进行整体评估
        overall_evaluation = evaluate_overall(chapter_evaluations, args.model)
        
        # 合并所有评估结果（将整体评估放在首位）
        all_evaluations = [overall_evaluation] + chapter_evaluations
        
        # 保存评估结果
        output_file = save_evaluations(all_evaluations, output_path)
        
        # 进行论文评分环节
        if not args.no_score:
            logger.info("开始对论文进行评分...")
            paper_scores = score_paper(all_evaluations, args.model)
            score_file = save_scores(paper_scores, output_path)
            
            # 计算总分
            total_score = sum(item['score'] for item in paper_scores if 'score' in item)
            total_possible = sum(item['full_score'] for item in paper_scores if 'full_score' in item)
        else:
            score_file = None
            total_score = 0
            total_possible = 100
        
        # 计算总耗时
        elapsed_time = time.time() - start_time
        logger.info(f"评估完成，总耗时: {elapsed_time:.2f} 秒")
        
        print(f"\n评估完成！结果已保存至: {output_file}")
        print(f"- 整体评估: index=0, chapter='全篇'")
        print(f"- 章节评估: {len(chapter_evaluations)} 个章节 (index=1~{len(chapter_evaluations)})")
        
        if not args.no_score:
            print(f"\n论文评分结果已保存至: {score_file}")
            print(f"- 总分: {total_score}/{total_possible}")
    
    except Exception as e:
        logger.error(f"评估过程出错: {e}")
        import traceback
        traceback.print_exc()
        elapsed_time = time.time() - start_time
        logger.info(f"程序异常退出，已运行: {elapsed_time:.2f} 秒")
        sys.exit(1)

if __name__ == "__main__":
    main() 