# Shorts Fission - 短视频裂变系统

## 项目简介

Shorts Fission 是一个短视频裂变系统，能够将 1 条源视频自动生成 10-20 条独特变体视频，支持大规模账号矩阵发布。

## 核心功能

- **视频下载**：支持 YouTube/TikTok 单视频下载、批量下载、实时监控
- **视频上传**：支持批量上传本地视频文件，自动检测分辨率
- **延迟处理**：下载/上传后不立即处理，用户可在详情页选择变体数量
- **变体生成 v4.0**：背景模糊+画中画（PIP）三层架构
- **Web 界面**：实时进度显示、状态追踪、一键下载

## 技术栈

### 后端
- FastAPI + SQLAlchemy
- Celery + Redis (异步任务)
- yt-dlp-api (代理下载服务)
- Scrapling (绕过 Cloudflare)
- FFmpeg (视频处理)
- WhisperX (字幕提取)

### 前端
- React 18 + TypeScript
- Vite + TailwindCSS
- WebSocket (实时进度)

## 服务架构

```
前端(8888) → Shorts Fission API(8000) → Celery → yt-dlp-api(8001) → YouTube
```

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 8888 | React + Vite |
| 后端 API | 8000 | FastAPI |
| yt-dlp-api | 8001 | 视频下载代理 |
| Redis | 6379 | Celery 消息队列 |

## 快速开始

### Docker 部署（推荐）

```bash
# 克隆项目
cd /root/.openclaw/workspace/projects/shorts-fission

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 手动部署

#### 1. 启动 yt-dlp-api 服务

```bash
cd /root/.openclaw/workspace/projects/yt-dlp-api
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > logs/service.log 2>&1 &
```

#### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动 Celery Worker

```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_tasks worker --loglevel=info
```

#### 4. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev -- --port 8888

# 生产构建
npm run build
```

## 项目结构

```
shorts-fission/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── main.py         # FastAPI 入口
│   │   ├── config.py       # 配置
│   │   ├── database.py     # 数据库
│   │   ├── models/         # 数据模型
│   │   ├── api/            # API 路由
│   │   ├── services/       # 业务逻辑
│   │   │   ├── downloader.py      # 视频下载（含 yt-dlp-api 客户端）
│   │   │   ├── variant_engine.py  # 变体引擎 v4.0 PIP
│   │   │   └── scrapling_downloader.py  # Scrapling 下载器
│   │   └── tasks/          # Celery 任务
│   ├── cookies.txt         # YouTube cookies
│   └── requirements.txt
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── pages/
│   │   │   └── Videos.tsx  # 视频管理页面
│   │   ├── components/
│   │   │   ├── VideoCard.tsx        # 视频卡片
│   │   │   ├── VideoDetailModal.tsx # 视频详情弹窗（三层参数显示）
│   │   │   ├── VideoUploader.tsx    # 视频上传组件
│   │   │   └── Toast.tsx            # 通知组件
│   │   └── hooks/          # Hooks
│   └── package.json
├── docs/                   # 📄 技术文档
│   ├── TikTok_Visual_Dedup_v3.0.md  # 视觉去重方案 v3.0（已废弃）
│   ├── TikTok_Visual_Dedup_v4.0_PIP.md  # 视觉去重方案 v4.0（当前）
│   └── Smart_BGM_Matching_v1.0.md   # 智能 BGM 匹配
├── data/                   # 数据目录
│   ├── videos/             # 源视频
│   └── variants/           # 变体视频
├── config/                 # 配置文件
├── luts/                   # LUT 滤镜
├── masks/                  # 遮罩素材
├── sports_bgm/             # 球类 BGM 库
├── tasks/                  # 任务规划文档
├── CHANGELOG.md            # 版本更新记录
├── docker-compose.yml
└── README.md
```

## API 端点

### 视频
- `POST /api/videos/single` - 添加单个视频（下载）
- `POST /api/videos/upload` - 批量上传视频文件
- `POST /api/videos/{id}/set-variant-count` - 设置变体数量并开始处理
- `GET /api/videos` - 视频列表
- `GET /api/videos/{id}` - 视频详情

### 变体
- `POST /api/videos/{id}/variants` - 开始生成变体
- `GET /api/videos/{id}/variants` - 变体列表

### 下载
- `GET /api/videos/{id}/download` - 下载源视频
- `GET /api/variants/{id}/download` - 下载变体
- `POST /api/variants/batch-download` - 批量下载

### WebSocket
- `WS /ws/progress/{video_id}` - 实时进度

## 处理流程

```
添加视频 → 下载完成 → 点击卡片 → 选择变体数量 → 开始生成变体
上传视频 → 自动完成 → 点击卡片 → 选择变体数量 → 开始生成变体
```

### 视频状态流转
```
pending → downloading → downloaded → processing → completed
                                    ↘ failed
```

## 变体引擎 v4.0（当前版本）

> 详细技术方案见：[TikTok 视觉去重方案 v4.0 PIP](./docs/TikTok_Visual_Dedup_v4.0_PIP.md)

### 三层架构

```
┌─────────────────────────────────────┐  ◄── 文字层（字幕）
│     文字层 (字幕烧录)                │
│   • ASS override 标签精确位置        │
│   • 无字幕则不显示此层               │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐  │  ◄── 中间层（画中画）
│  │      中间层 (画中画)            │  │
│  │   • portrait_crop：竖屏裁剪    │  │
│  │   • landscape：横屏显示        │  │
│  └───────────────────────────────┘  │
│                                     │
│      背景层 (强化版)                 │  ◄── 背景层
│   • 全景模糊 σ=40-60                │
│   • 放大 130-160%                   │
│   • 变速 1.05-1.2x                  │
│   • 镜像 50%、旋转 ±10°             │
│                                     │
└─────────────────────────────────────┘
         ▼
    9:16 竖屏输出 + 原声
```

### 背景层（必做特效）

| 特效 | 参数 | 说明 |
|------|------|------|
| 全景模糊 | σ = 40-60 | 高斯模糊 |
| 放大 | 130-160% | 填满画面 |
| 变速 | 1.05-1.2x | 同步变速 |
| 镜像翻转 | 50% 概率 | 水平翻转 |
| 裁剪 | 3-5% | 边缘裁剪 |
| 旋转 | ±10° | 轻微旋转 |

### 中间层（两种模式）

**模式 1：portrait_crop（默认）**
- 缩放：与背景层同比例
- 裁剪：上下裁剪，剩余 55-65%
- 位置：居中

**模式 2：landscape（横屏）**
- 宽度：100-120%
- 屏幕占比：55-65%
- 位置：居中

### 文字层

- 来源：WhisperX 字幕提取
- 位置：X轴居中，Y轴顶部向下1/3
- 样式：ASS override 标签精确控制
- 无字幕：跳过此层

## 配置

编辑 `backend/.env`:

```env
# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data/shorts_fission.db

# Redis
REDIS_URL=redis://localhost:6379/0

# 代理（访问 TikTok）
PROXY_ENABLED=false
PROXY_URL=http://127.0.0.1:7890

# yt-dlp-api
YT_DLP_API_URL=http://localhost:8001
```

## 相关项目

- **yt-dlp-api**: `/root/.openclaw/workspace/projects/yt-dlp-api/` - YouTube 视频下载代理服务

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v4.0 | 2026-03-13 | 背景模糊+画中画三层架构，替代 v3.0 |
| v3.0 | 2026-03-08 | 两步策略（已废弃） |
| v2.0 | 2026-03-08 | 延迟处理流程、批量上传 |
| v1.0 | 2026-03-07 | 初始版本 |

详见 [CHANGELOG.md](./CHANGELOG.md)

## 许可证

MIT License

---

**版本**: 4.0.0
**更新日期**: 2026-03-13
**状态**: ✅ 生产就绪
