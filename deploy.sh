#!/bin/bash
# Production deployment script for Shorts Fission
# Usage: ./deploy.sh [port]

set -e

PROJECT_DIR="/root/.openclaw/workspace/projects/shorts-fission"
DEPLOY_PORT="${1:-80}"

echo "🚀 Shorts Fission 生产部署脚本"
echo "================================"

# Check if running as root for port 80
if [ "$DEPLOY_PORT" = "80" ] && [ "$EUID" -ne 0 ]; then
    echo "⚠️  端口 80 需要 root 权限，请使用 sudo 运行"
    exit 1
fi

cd "$PROJECT_DIR"

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "📋 部署配置:"
echo "  项目目录: $PROJECT_DIR"
echo "  部署端口: $DEPLOY_PORT"
echo "  服务器IP: $SERVER_IP"
echo ""

# Check Docker
echo "🔍 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✅ Docker 检查通过"

# Build frontend
echo ""
echo "📦 构建前端..."
cd "$PROJECT_DIR/frontend"
npm run build 2>&1 | tail -5
echo "✅ 前端构建完成"

# Update nginx config with custom port if needed
if [ "$DEPLOY_PORT" != "80" ]; then
    echo ""
    echo "🔧 更新 Nginx 配置 (端口: $DEPLOY_PORT)..."
    sed -i "s/listen 80;/listen $DEPLOY_PORT;/g" "$PROJECT_DIR/nginx/nginx.conf"
fi

# Stop existing containers
echo ""
echo "🛑 停止现有容器..."
docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" down 2>/dev/null || true

# Start services
echo ""
echo "▶️  启动服务..."
docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" up -d --build

# Wait for services
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# Health check
echo ""
echo "🏥 健康检查..."
if curl -s "http://localhost:$DEPLOY_PORT/health" > /dev/null 2>&1; then
    echo "✅ 服务运行正常"
else
    echo "⚠️  健康检查失败，查看日志:"
    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" logs --tail=20
fi

echo ""
echo "================================"
echo "🎉 部署完成!"
echo ""
echo "📊 访问地址:"
echo "  本地: http://localhost:$DEPLOY_PORT"
echo "  内网: http://$SERVER_IP:$DEPLOY_PORT"
echo ""
echo "📚 API 文档: http://$SERVER_IP:$DEPLOY_PORT/docs"
echo ""
echo "🛠️  管理命令:"
echo "  查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.prod.yml down"
echo "  重启服务: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "⚠️  安全提示:"
echo "  - Redis 仅内部网络可访问"
echo "  - API 有速率限制 (10 req/s)"
echo "  - 下载接口限制 (5 req/min)"
echo "  - 如需 HTTPS，请配置 SSL 证书"
echo "================================"
