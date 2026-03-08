#!/bin/bash
# Direct deployment script (no Docker)
# Usage: ./deploy-direct.sh [port]

set -e

PROJECT_DIR="/root/.openclaw/workspace/projects/shorts-fission"
DEPLOY_PORT="${1:-8888}"

echo "🚀 Shorts Fission 直接部署脚本"
echo "================================"

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "📋 部署配置:"
echo "  项目目录: $PROJECT_DIR"
echo "  前端端口: $DEPLOY_PORT"
echo "  后端端口: 8000"
echo "  服务器IP: $SERVER_IP"
echo ""

# Check dependencies
echo "🔍 检查依赖..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 未安装"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js 未安装"; exit 1; }
command -v redis-cli >/dev/null 2>&1 || { echo "❌ Redis 未安装"; exit 1; }
echo "✅ 依赖检查通过"

# Start Redis if not running
echo ""
echo "📦 启动 Redis..."
if ! redis-cli ping >/dev/null 2>&1; then
    redis-server --daemonize yes
    sleep 2
fi
if redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis 运行中"
else
    echo "❌ Redis 启动失败"
    exit 1
fi

# Build frontend
echo ""
echo "📦 构建前端..."
cd "$PROJECT_DIR/frontend"
npm run build 2>&1 | tail -5
echo "✅ 前端构建完成"

# Create production server
echo ""
echo "🔧 创建生产环境配置..."
mkdir -p "$PROJECT_DIR/dist"
cp -r "$PROJECT_DIR/frontend/dist"/* "$PROJECT_DIR/dist/"

# Create production server script
cat > "$PROJECT_DIR/dist-server.py" << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        # API proxy
        if self.path.startswith('/api/') or self.path.startswith('/ws/'):
            self.send_response(502)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Backend not running on port 8000"}')
            return
        
        # SPA fallback
        if not os.path.exists(os.path.join(DIRECTORY, self.path.lstrip('/'))) and '.' not in self.path:
            self.path = '/index.html'
        
        return super().do_GET()

with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Serving at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
EOF

chmod +x "$PROJECT_DIR/dist-server.py"

# Start backend
echo ""
echo "▶️  启动后端服务..."
cd "$PROJECT_DIR/backend"
source venv/bin/activate

# Kill existing processes
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1

# Start backend in background
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$PROJECT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PROJECT_DIR/backend.pid"
echo "✅ 后端启动 (PID: $BACKEND_PID)"

# Start frontend server
echo ""
echo "▶️  启动前端服务..."
cd "$PROJECT_DIR"
nohup python3 dist-server.py $DEPLOY_PORT > "$PROJECT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$PROJECT_DIR/frontend.pid"
echo "✅ 前端启动 (PID: $FRONTEND_PID, Port: $DEPLOY_PORT)"

# Wait for services
echo ""
echo "⏳ 等待服务启动..."
sleep 3

# Health check
echo ""
echo "🏥 健康检查..."
if curl -s "http://localhost:8000/health" >/dev/null 2>&1 || curl -s "http://localhost:8000/docs" >/dev/null 2>&1; then
    echo "✅ 后端服务正常"
else
    echo "⚠️  后端服务可能未就绪，查看日志: tail -f $PROJECT_DIR/backend.log"
fi

if curl -s "http://localhost:$DEPLOY_PORT" >/dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "⚠️  前端服务可能未就绪"
fi

echo ""
echo "================================"
echo "🎉 部署完成!"
echo ""
echo "📊 访问地址:"
echo "  前端: http://$SERVER_IP:$DEPLOY_PORT"
echo "  后端: http://$SERVER_IP:8000"
echo "  API文档: http://$SERVER_IP:8000/docs"
echo ""
echo "🛠️  管理命令:"
echo "  查看后端日志: tail -f $PROJECT_DIR/backend.log"
echo "  查看前端日志: tail -f $PROJECT_DIR/frontend.log"
echo "  停止后端: kill \$(cat $PROJECT_DIR/backend.pid)"
echo "  停止前端: kill \$(cat $PROJECT_DIR/frontend.pid)"
echo ""
echo "⚠️  安全提示:"
echo "  - 当前使用 HTTP，生产环境建议配置 HTTPS"
echo "  - 建议配置防火墙限制访问IP"
echo "  - 默认端口: 前端 $DEPLOY_PORT, 后端 8000"
echo "================================"
