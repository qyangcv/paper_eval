#!/bin/bash

# Redis安装和配置脚本 - macOS版本

echo "🚀 开始安装和配置Redis..."

# 检查操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✅ 检测到macOS系统"
    
    # 检查Homebrew是否安装
    if ! command -v brew &> /dev/null; then
        echo "❌ 未找到Homebrew，请先安装Homebrew:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # 安装Redis
    echo "📦 安装Redis..."
    brew install redis
    
    # 启动Redis服务
    echo "🔄 启动Redis服务..."
    brew services start redis
    
    echo "✅ Redis安装和启动完成"
    echo "📋 Redis服务信息:"
    echo "   - 主机: localhost"
    echo "   - 端口: 6379"
    echo "   - 状态: $(brew services list | grep redis | awk '{print $2}')"
    
else
    echo "❌ 此脚本仅支持macOS系统"
    echo "请根据您的操作系统手动安装Redis:"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install redis-server"
    echo "  sudo systemctl start redis-server"
    echo ""
    echo "CentOS/RHEL:"
    echo "  sudo yum install redis"
    echo "  sudo systemctl start redis"
    echo ""
    echo "Windows:"
    echo "  请下载并安装Redis for Windows"
    exit 1
fi

# 安装Python Redis依赖
echo "🐍 安装Python Redis依赖..."
pip install redis

# 测试Redis连接
echo "🔍 测试Redis连接..."
redis-cli ping

if [ $? -eq 0 ]; then
    echo "✅ Redis连接测试成功"
else
    echo "❌ Redis连接测试失败"
    exit 1
fi

echo ""
echo "🎉 Redis安装和配置完成！"
echo ""
echo "📝 接下来的步骤:"
echo "1. 复制 .env.example 为 .env 文件"
echo "2. 根据需要调整 .env 文件中的Redis配置"
echo "3. 运行测试脚本: python test_redis.py"
echo "4. 启动应用程序"
