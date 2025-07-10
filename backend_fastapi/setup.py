"""
安装和设置脚本
自动安装依赖并配置环境
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"🔄 {description}...")
    try:
        # 将命令分割为列表，避免shell解释问题
        if isinstance(command, str):
            # 对于pip install命令，使用列表形式避免shell解释
            if command.startswith('pip install'):
                cmd_parts = command.split()
            else:
                cmd_parts = command
        else:
            cmd_parts = command

        result = subprocess.run(cmd_parts, check=True, capture_output=True, text=True, cwd=os.getcwd())
        print(f"✅ {description}完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失败: {e}")
        if e.stdout:
            print(f"输出: {e.stdout}")
        if e.stderr:
            print(f"错误: {e.stderr}")
        return False

def install_dependencies():
    """安装Python依赖"""
    print("📦 安装Python依赖包...")
    
    # 基础依赖
    basic_deps = [
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "python-multipart>=0.0.6",
        "aiofiles>=23.0.0",
        "python-docx>=0.8.11",
        "psutil>=5.9.0",
        "python-dotenv>=1.0.0"
    ]
    
    # AI模型依赖（可选）
    ai_deps = [
        "openai>=1.0.0",
        "google-generativeai>=0.3.0",
        "requests>=2.31.0"
    ]
    
    all_deps = basic_deps + ai_deps
    
    for dep in all_deps:
        if not run_command(f"pip install {dep}", f"安装 {dep}"):
            print(f"⚠️ 安装 {dep} 失败，但继续安装其他依赖")
    
    print("✅ 依赖安装完成")

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("请安装Python 3.8或更高版本")
        return False
    
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def create_directories():
    """创建必要的目录"""
    print("📁 创建必要的目录...")
    
    directories = [
        "logs",
        "temp", 
        "data",
        "data/raw",
        "data/processed",
        "data/output"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        print(f"✅ 创建目录: {directory}")

def check_env_file():
    """检查.env文件"""
    print("🔧 检查环境配置...")
    
    env_path = Path(".env")
    if env_path.exists():
        print("✅ 找到.env配置文件")
        
        # 检查是否配置了API密钥
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "DEEPSEEK_API_KEY=sk-" in content:
            print("✅ DeepSeek API密钥已配置")
        else:
            print("⚠️ DeepSeek API密钥未配置")
            
        if "GEMINI_API_KEY=" in content and "your_gemini_api_key" not in content:
            print("✅ Gemini API密钥已配置")
        else:
            print("⚠️ Gemini API密钥未配置")
            
        if "QWEN_API_KEY=" in content and "your_qwen_api_key" not in content:
            print("✅ Qwen API密钥已配置")
        else:
            print("⚠️ Qwen API密钥未配置")
            
    else:
        print("❌ 未找到.env配置文件")
        print("请确保.env文件存在于当前目录")
        return False
    
    return True

def test_installation():
    """测试安装是否成功"""
    print("🧪 测试安装...")
    
    try:
        # 测试导入主要模块
        import fastapi
        import uvicorn
        import docx
        import psutil
        import dotenv
        
        print("✅ 所有依赖模块导入成功")
        
        # 测试启动应用（不实际启动服务器）
        try:
            from main import app
            print("✅ 应用模块加载成功")
        except Exception as e:
            print(f"⚠️ 应用模块加载失败: {e}")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def main():
    """主安装流程"""
    print("🚀 论文评价分析系统 - 后端安装脚本")
    print("=" * 50)
    
    # 1. 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 2. 安装依赖
    install_dependencies()
    
    # 3. 创建目录
    create_directories()
    
    # 4. 检查配置文件
    if not check_env_file():
        print("\n❌ 配置检查失败")
        print("请确保.env文件存在并正确配置API密钥")
        sys.exit(1)
    
    # 5. 测试安装
    if not test_installation():
        print("\n❌ 安装测试失败")
        sys.exit(1)
    
    print("\n🎉 安装完成！")
    print("=" * 50)
    print("现在您可以启动服务器:")
    print("  python run_server.py")
    print("\n或者运行测试:")
    print("  python -m tests.run_tests")
    print("\nAPI文档地址:")
    print("  http://localhost:8000/docs")

if __name__ == "__main__":
    main()
