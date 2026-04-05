# Shorts-Fission v4.1.7 GitHub 迁移计划

## 目标
将当前项目整理后上传到: https://github.com/twinmewilliam-a11y/shorts-fission-new

## 步骤

### Step 1: 创建临时目录
```bash
mkdir -p /tmp/shorts-fission-clean
cd /tmp/shorts-fission-clean
```

### Step 2: 复制核心代码（排除大文件）
```bash
# 复制后端代码（排除 venv/ 和 __pycache__/）
rsync -av --exclude='venv/' --exclude='__pycache__/' --exclude='*.pyc' \
  /root/.openclaw/workspace/projects/shorts-fission/backend/ ./backend/

# 复制前端代码（排除 node_modules/）
rsync -av --exclude='node_modules/' --exclude='dist/' \
  /root/.openclaw/workspace/projects/shorts-fission/frontend/ ./frontend/

# 复制文档
rsync -av /root/.openclaw/workspace/projects/shorts-fission/docs/ ./docs/

# 复制配置文件
rsync -av /root/.openclaw/workspace/projects/shorts-fission/config/ ./config/

# 复制素材（LUT、BGM、PIP）
rsync -av /root/.openclaw/workspace/projects/shorts-fission/luts/ ./luts/
rsync -av /root/.openclaw/workspace/projects/shorts-fission/sports_bgm/ ./sports_bgm/
rsync -av /root/.openclaw/workspace/projects/shorts-fission/pips/ ./pips/

# 复制 Remotion Caption（排除 out/）
rsync -av --exclude='out/' --exclude='node_modules/' \
  /root/.openclaw/workspace/projects/shorts-fission/remotion-caption/ ./remotion-caption/

# 复制测试代码
rsync -av /root/.openclaw/workspace/projects/shorts-fission/tests/ ./tests/

# 复制根目录文件
cp /root/.openclaw/workspace/projects/shorts-fission/*.md .
cp /root/.openclaw/workspace/projects/shorts-fission/*.json .
cp /root/.openclaw/workspace/projects/shorts-fission/*.yml .
cp /root/.openclaw/workspace/projects/shorts-fission/.gitignore .
```

### Step 3: 创建 .gitignore
```bash
# 确保 .gitignore 完整
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
ENV/

# Node
node_modules/
.npm
dist/

# 数据文件
data/
variants/
*.db
*.sqlite3

# 日志
*.log
logs/

# IDE
.idea/
.vscode/
*.swp
*.swo

# 环境变量
.env
.env.local
*.local

# 临时文件
*.tmp
*.temp
.cache/

# 操作系统
.DS_Store
Thumbs.db

# Cookies
cookies.txt

# Remotion 输出
remotion-caption/out/
dump.rdb
EOF
```

### Step 4: 创建环境变量模板
```bash
cat > backend/.env.example << 'EOF'
# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data/shorts_fission.db

# Redis
REDIS_URL=redis://localhost:6379/0

# 代理（访问 TikTok）
PROXY_ENABLED=false
PROXY_URL=http://127.0.0.1:7890

# yt-dlp-api
YT_DLP_API_URL=http://localhost:8001

# WhisperX
WHISPERX_ENABLED=true
WHISPERX_MODEL=large-v2
WHISPERX_DEVICE=cuda

# Gemini API（字幕翻译）
GEMINI_API_KEY=your_gemini_api_key_here
EOF
```

### Step 5: 更新 README.md
添加以下内容：
- 项目简介
- 快速开始
- 环境配置
- Docker 部署
- 技术栈

### Step 6: 初始化 Git 仓库
```bash
cd /tmp/shorts-fission-clean
git init
git add .
git commit -m "Initial commit: Shorts-Fission v4.1.7

Features:
- v4.0 PIP 三层架构（背景模糊+画中画+字幕）
- v4.1 词级动画字幕（3种模板）
- v4.1.4 字幕翻译功能
- v4.1.5 API Key 安全修复
- v4.1.6 FFmpeg 编码优化
- v4.1.7 变体详情页三层参数显示

Tech Stack:
- Backend: FastAPI + Celery + Redis
- Frontend: React + TypeScript + Vite
- Video: FFmpeg + WhisperX
"
```

### Step 7: 关联远程仓库并推送
```bash
git remote add origin https://github.com/twinmewilliam-a11y/shorts-fission-new.git
git branch -M main
git push -u origin main
```

### Step 8: 创建 v4.1.7 Release
```bash
git tag -a v4.1.7 -m "Release v4.1.7

变体详情页三层参数显示优化

Changelog:
- 前端：三层参数分区显示（背景层/中间层/文字层）
- 后端：effects_applied 格式优化为 '[背景层]...[中间层]...[文字层]...'
- 兼容旧格式数据

Full changelog: CHANGELOG.md
"
git push origin v4.1.7
```

## 预计大小
- 代码 + 配置 + 素材: < 50MB
- 排除: data/, venv/, node_modules/, *.db

## 注意事项
1. **敏感信息检查**: 确保 .env 文件不被提交
2. **API Key**: 已在 v4.1.5 中移除硬编码
3. **Cookies**: cookies.txt 已在 .gitignore 中
4. **数据文件**: data/ 目录不提交

## 完成后
- 确认 GitHub 仓库大小 < 100MB
- 确认 README.md 显示正常
- 确认 Release 页面正常
- 更新本地 Memory 记录迁移完成

---
Created: 2026-04-03
Author: T.W (Twin William)
