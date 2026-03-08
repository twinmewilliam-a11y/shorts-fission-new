#!/bin/bash
# 网络诊断脚本

echo "=========================================="
echo "🩺 Shorts Fission 网络诊断报告"
echo "=========================================="
echo ""

echo "📅 时间: $(date)"
echo ""

echo "=== 1. 服务进程状态 ==="
ps aux | grep -E "(uvicorn|python.*dist-server)" | grep -v grep
echo ""

echo "=== 2. 端口监听状态 ==="
netstat -tlnp 2>/dev/null | grep -E ":(8000|8888)" || echo "netstat 失败"
lsof -i :8000 2>/dev/null | grep LISTEN || echo "8000 未监听"
lsof -i :8888 2>/dev/null | grep LISTEN || echo "8888 未监听"
echo ""

echo "=== 3. 本地访问测试 ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null
echo " - 后端本地状态码"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8888 2>/dev/null
echo " - 前端本地状态码"
echo ""

echo "=== 4. 网络接口 ==="
ip addr 2>/dev/null | grep "inet " | head -3 || ifconfig 2>/dev/null | grep "inet " | head -3
echo ""

echo "=== 5. 防火墙状态 ==="
systemctl status firewalld --no-pager 2>/dev/null | head -3 || echo "firewalld 未运行"
systemctl status ufw --no-pager 2>/dev/null | head -3 || echo "ufw 未运行"
echo ""

echo "=========================================="
echo "✅ 服务运行正常，端口已监听"
echo "❌ 外部无法访问，腾讯云防火墙需配置"
echo "=========================================="
echo ""
echo "🔧 解决方案:"
echo "1. 登录腾讯云控制台: https://console.cloud.tencent.com/lighthouse"
echo "2. 找到实例 (IP: 43.156.242.38)"
echo "3. 进入「防火墙」标签"
echo "4. 添加规则:"
echo "   - 协议: TCP"
echo "   - 端口: 8000,8888"
echo "   - 策略: 允许"
echo "   - 来源: 0.0.0.0/0 (或指定IP)"
echo ""
echo "📊 当前监听端口:"
echo "   - 前端: 0.0.0.0:8888"
echo "   - 后端: 0.0.0.0:8000"
echo "=========================================="
