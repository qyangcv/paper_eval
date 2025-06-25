# pip3 install transformers
# python3 deepseek_tokenizer.py
import transformers
import os

def count_tokens(file_path):
    f_name = os.path.basename(file_path)
    
    # 初始化tokenizer
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        "./", trust_remote_code=True
    )
    
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
