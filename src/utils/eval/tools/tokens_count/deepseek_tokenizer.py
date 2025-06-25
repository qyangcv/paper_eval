# pip3 install transformers
# python3 deepseek_tokenizer.py
import os
import warnings

# 使用torch_helper中的安全导入方法
try:
    from utils.eval.tools.torch_helper import get_transformers
    
    def _safe_import_transformers():
        return get_transformers()
except ImportError:
    # 如果torch_helper导入失败，继续使用原有的延迟导入方法
    _transformers = None
    _tokenizer = None

    def _safe_import_transformers():
        """Safely import transformers module without triggering Streamlit file watcher issues."""
        global _transformers, _tokenizer
        if _transformers is None:
            try:
                import transformers
                _transformers = transformers
            except ImportError:
                warnings.warn("Failed to import transformers library. Tokenization functionality will be unavailable.")
                _transformers = None
        return _transformers

def get_tokenizer():
    """Safely get the tokenizer instance."""
    global _tokenizer
    if _tokenizer is None:
        transformers = _safe_import_transformers()
        if transformers:
            try:
                _tokenizer = transformers.AutoTokenizer.from_pretrained(
                    "./", trust_remote_code=True
                )
            except Exception as e:
                warnings.warn(f"Failed to initialize tokenizer: {e}")
    return _tokenizer

def count_tokens(file_path):
    f_name = os.path.basename(file_path)
    
    # 初始化tokenizer
    tokenizer = get_tokenizer()
    if not tokenizer:
        print(f"Tokenizer not available. Cannot count tokens for {f_name}.")
        return 0
    
    # 读取MD文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f'{f_name} text length: {len(content)}')
    
    # 计算token数量
    tokens = tokenizer.encode(content)
    print(f'{f_name} token length: {len(tokens)}')
    return len(tokens)

if __name__ == "__main__":
    # 测试单个文件
    test_file = "/Users/yang/Documents/bupt/code/paper_eval/qy_data_pipeline/double_check/23.黄加宇-市优_run1_review.md"
    if os.path.exists(test_file):
        token_count = count_tokens(test_file)
        print(f"文件 {test_file} 的token数量: {token_count}")
    else:
        print(f"文件 {test_file} 不存在")
