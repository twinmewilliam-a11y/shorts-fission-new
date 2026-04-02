#!/bin/bash
# Shorts Fission 启动脚本

set -e

PROJECT_DIR="/root/.openclaw/workspace/projects/shorts-fission"

echo "🚀 启动 Shorts Fission 短视频裂变系统..."

# 检查 Redis
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis 未安装，请先安装 Redis"
    exit 1
fi

# 启动 Redis (如果未运行)
if ! redis-cli ping &> /dev/null; then
    echo "📦 启动 Redis..."
    redis-server --daemonize yes
fi

# 启动后端
echo "🔧 启动后端服务..."
cd "$PROJECT_DIR/backend"
source venv/bin/activate

# 启动 Celery Worker (后台)
celery -A app.tasks.celery_tasks worker --loglevel=info &
CELERY_PID=$!

# 启动 FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端
echo "🎨 启动前端服务..."
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 服务启动成功！"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断信号
trap "kill $CELERY_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
