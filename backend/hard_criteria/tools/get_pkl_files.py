from glob import glob
import os

def get_pkl_files(INPUT_ROOT: str) -> list[str]:
    """
    获取PKL文件列表
    
    Args:
        INPUT_ROOT: 输入路径（文件或目录）
        
    Returns:
        PKL文件路径列表
    """
    if os.path.isfile(INPUT_ROOT):
        if INPUT_ROOT.endswith('.pkl'):
            return [INPUT_ROOT]
        else:
            print(f"错误: {INPUT_ROOT} 不是PKL文件")
            return []
    elif os.path.isdir(INPUT_ROOT):
        pkl_files = glob(os.path.join(INPUT_ROOT, "*.pkl"))
        return sorted(pkl_files)
    else:
        print(f"错误: {INPUT_ROOT} 不存在")
        return []