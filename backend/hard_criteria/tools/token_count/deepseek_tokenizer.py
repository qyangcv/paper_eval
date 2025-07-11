"""
DeepSeek Tokenizer 官方工具，用于计算文本文件的token数量

功能：
- 使用transformers库的AutoTokenizer计算token数量
- 支持多种文本格式（.txt, .md等）
- 提供详细的统计信息

安装依赖：
    pip install transformers

使用方法：
    python deepseek_tokenizer.py -f <文件路径>
    python deepseek_tokenizer.py --file <文件路径>

示例：
    python deepseek_tokenizer.py -f test.md
    python deepseek_tokenizer.py --file /path/to/document.txt
"""

import os
import argparse
import warnings

# 全局变量
_transformers = None
_tokenizer = None

def _safe_import_transformers():
    """安全导入transformers库"""
    global _transformers
    if _transformers is None:
        try:
            import transformers
            _transformers = transformers
        except ImportError:
            warnings.warn("transformers库未安装，请运行: pip install transformers")
            _transformers = None
    return _transformers

def get_tokenizer():
    """获取tokenizer实例"""
    global _tokenizer
    if _tokenizer is None:
        transformers = _safe_import_transformers()
        if transformers:
            try:
                _tokenizer = transformers.AutoTokenizer.from_pretrained(
                    "./", trust_remote_code=True
                )
            except Exception as e:
                warnings.warn(f"初始化tokenizer失败: {e}")
    return _tokenizer

def count_tokens(file_path):
    """
    计算文件的token数量
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        int: token数量，失败时返回0
    """
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在")
        return 0
    
    # 获取tokenizer
    tokenizer = get_tokenizer()
    if not tokenizer:
        print("错误: 无法获取tokenizer")
        return 0
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 计算token数量
        tokens = tokenizer.encode(content)
        
        # 输出统计信息
        file_name = os.path.basename(file_path)
        print(f"文件: {file_name}")
        print(f"字符数: {len(content):,}")
        print(f"Token数: {len(tokens):,}")
        print(f"压缩比: {len(content)/len(tokens):.2f} 字符/token")
        
        return len(tokens)
        
    except Exception as e:
        print(f"错误: 处理文件时出现异常: {e}")
        return 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="计算文本文件的token数量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python deepseek_tokenizer.py -f document.txt
  python deepseek_tokenizer.py --file /path/to/file.md
        """
    )
    
    parser.add_argument(
        '-f', '--file',
        required=True,
        help='要计算token数量的文件路径'
    )
    
    args = parser.parse_args()
    
    # 计算token数量
    token_count = count_tokens(args.file)
    
    if token_count > 0:
        print(f"\n✓ 处理完成，总token数: {token_count:,}")
    else:
        print("\n✗ 处理失败")
        exit(1)

if __name__ == "__main__":
    main()
