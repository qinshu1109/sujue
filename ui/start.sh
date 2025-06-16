#!/bin/bash

# 女娲智能Text-to-SQL系统前端启动脚本

echo "🚀 启动女娲智能Text-to-SQL系统前端..."

# 检查Node.js版本
if ! command -v node &> /dev/null; then
    echo "❌ 未找到Node.js，请先安装Node.js 16或更高版本"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js版本过低，需要16或更高版本，当前版本: $(node -v)"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ 未找到npm，请先安装npm"
    exit 1
fi

echo "✅ Node.js版本: $(node -v)"
echo "✅ npm版本: $(npm -v)"

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装项目依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖已存在，跳过安装"
fi

# 启动开发服务器
echo "🌐 启动开发服务器..."
echo "📱 前端界面将在 http://localhost:3000 启动"
echo "🔧 后端API需要在 http://localhost:8000 运行"
echo ""
echo "💡 提示："
echo "   - 使用 Ctrl+C 停止服务器"
echo "   - 支持热重载，修改代码将自动刷新"
echo "   - 支持中英文切换"
echo ""

npm start