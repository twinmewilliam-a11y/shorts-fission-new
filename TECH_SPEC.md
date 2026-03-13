# Shorts Fission - 技术规格说明书

## 1. API 设计

### 1.1 REST API 端点

#### 账号管理
```
POST   /api/accounts                 # 添加监控账号
GET    /api/accounts                 # 获取账号列表
DELETE /api/accounts/{id}            # 删除账号
```

#### 视频管理
```
POST   /api/videos/single            # 添加单个视频
POST   /api/videos/upload            # 批量上传视频文件
POST   /api/videos/{id}/set-variant-count  # 设置变体数量并开始处理
GET    /api/videos                   # 获取视频列表 (含状态)
GET    /api/videos/{id}              # 获取视频详情
DELETE /api/videos/{id}              # 删除视频
```

#### 变体管理
```
POST   /api/videos/{id}/variants     # 开始生成变体
GET    /api/videos/{id}/variants     # 获取变体列表
GET    /api/variants/{id}            # 获取变体详情
DELETE /api/variants/{id}            # 删除变体
```

#### 下载
```
GET    /api/videos/{id}/download     # 下载源视频
GET    /api/variants/{id}/download   # 下载单个变体
POST   /api/variants/batch-download  # 批量下载变体 (ZIP)
GET    /api/videos/{id}/metadata     # 下载元数据包
```

#### WebSocket
```
WS     /ws/progress/{video_id}       # 实时进度推送
```

### 1.2 数据模型

#### Video 模型
```python
class VideoStatus(Enum):
    PENDING = "pending"           # 等待下载
    DOWNLOADING = "downloading"   # 下载中
    DOWNLOADED = "downloaded"     # 已下载，待处理
    PROCESSING = "processing"     # 变体生成中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败

class Video(Base):
    id: int
    platform: str              # youtube / tiktok
    video_id: str              # 平台视频ID
    url: str                   # 原始链接
    account_id: str            # 来源账号
    title: str
    description: str
    duration: int              # 时长(秒)
    thumbnail: str
    upload_date: datetime
    status: VideoStatus
    variant_count: int         # 已生成变体数量
    target_variant_count: int  # 目标变体数量
    download_progress: int     # 下载进度 0-100
    variant_progress: int      # 变体生成进度 0-100
    source_path: str           # 源视频路径
    created_at: datetime
    updated_at: datetime
```

#### Variant 模型
```python
class VariantStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Variant(Base):
    id: int
    video_id: int
    variant_index: int         # 第几个变体 (1-50)
    status: VariantStatus
    title: str
    description: str
    effects_applied: str       # 应用的三层参数 (JSON)
    file_path: str
    file_size: int
    created_at: datetime
    completed_at: datetime
```

---

## 2. 变体引擎 v4.0

### 2.1 架构概述

v4.0 采用 **三层合成架构**：

```
文字层（字幕）→ 中间层（画中画）→ 背景层（模糊）
```

### 2.2 背景层参数

| 特效 | 参数范围 | FFmpeg 滤镜 |
|------|----------|-------------|
| 全景模糊 | σ = 40-60 | `gblur=sigma={val}` |
| 放大 | 130-160% | `scale=iw*{val}:ih*{val}` |
| 变速 | 1.05-1.2x | `setpts={1/val}*PTS` |
| 镜像翻转 | 50% 概率 | `hflip` |
| 裁剪 | 3-5% | `crop=iw*(1-val):ih*(1-val)` |
| 旋转 | ±10° | `rotate={rad}:c=black` |

### 2.3 中间层参数

**模式 1：portrait_crop（竖屏裁剪）**
| 特效 | 参数范围 | 说明 |
|------|----------|------|
| 缩放 | 与背景层同比例 | 视觉一致 |
| 裁剪 | 剩余 55-65% | 只裁上下边缘 |
| 位置 | 居中 | overlay 默认 |

**模式 2：landscape（横屏显示）**
| 特效 | 参数范围 | 说明 |
|------|----------|------|
| 宽度 | 100-120% | 保持比例 |
| 屏幕占比 | 55-65% | 高度比例 |
| 位置 | 居中 | overlay 默认 |

### 2.4 文字层参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 字幕来源 | WhisperX | 自动提取 |
| 位置 X | 屏幕中央 | X轴居中 |
| 位置 Y | 顶部向下 1/3 | Y轴位置 |
| 字体大小 | 40-50px | 随机 |
| 样式 | 3种艺术字 | 粗描边/细描边+阴影/渐变描边 |

### 2.5 FFmpeg 命令模板

```bash
ffmpeg -i input.mp4 \
  -filter_complex "
    # 背景层
    [0:v]hflip,
         scale=iw*1.5:ih*1.5,
         gblur=sigma=50,
         rotate=0.05:c=black,
         crop=iw*0.92:ih*0.92,
         setpts=0.90*PTS[bg];
    
    # 中间层
    [0:v]scale=iw*1.5:ih*1.5,
         crop=iw:ih*0.62:0:ih*0.19,
         setpts=0.90*PTS[fg];
    
    # 合成
    [bg][fg]overlay=(W-w)/2:(H-h)/2[video]
  " \
  -map "[video]" -map 0:a \
  -filter:a "atempo=1.11" \
  -c:v mpeg4 -q:v 8 \
  -c:a aac \
  -y output_pip.mp4
```

---

## 3. 下载模块

### 3.1 下载优先级

```
1. Scrapling（绕过 Cloudflare，无需 cookies）
2. yt-dlp-api（代理服务，支持 cookies）
3. 直接 yt-dlp（备用）
```

### 3.2 yt-dlp-api 集成

```python
class YtDlpApiClient:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
    
    async def download(self, url: str, output_path: str) -> dict:
        # 创建下载任务
        response = await self.client.post(f"{self.base_url}/download", json={
            "url": url,
            "output_path": output_path
        })
        task_id = response.json()["task_id"]
        
        # 轮询任务状态
        while True:
            status = await self.get_task_status(task_id)
            if status["status"] == "completed":
                return status
            await asyncio.sleep(2)
```

### 3.3 Scrapling 下载器

```python
class ScraplingDownloader:
    def download(self, url: str) -> bytes:
        page = Page(url, stealth=True)
        response = page.fetch()
        return response.content
```

---

## 4. WebSocket 进度推送

### 4.1 消息格式

```json
{
    "type": "variant_progress",
    "video_id": 123,
    "current": 8,
    "total": 15,
    "percent": 53,
    "status": "processing",
    "current_variant": {
        "index": 9,
        "layer_params": {
            "background": {"blur": 50, "scale": 1.5},
            "middle": {"mode": "portrait_crop", "remaining": 0.62},
            "text": {"has_subtitle": true, "font_size": 45}
        }
    }
}
```

### 4.2 前端实现

```typescript
const socket = new WebSocket(`/ws/progress/${videoId}`);

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setProgress(data.percent);
    setCurrentVariant(data.current);
};
```

---

## 5. 字幕处理

### 5.1 WhisperX 集成

```python
def extract_subtitles(video_path: str) -> Optional[str]:
    """提取字幕并生成 ASS 文件"""
    model = whisperx.load_model("base")
    audio = whisperx.load_audio(video_path)
    result = model.transcribe(audio)
    
    # 生成 ASS 文件
    ass_content = generate_ass(result["segments"])
    ass_path = video_path.replace(".mp4", ".ass")
    with open(ass_path, "w") as f:
        f.write(ass_content)
    
    return ass_path
```

### 5.2 ASS Override 标签

```python
# 精确位置控制
override = r'{\an8\pos(' + str(pos_x) + ',' + str(pos_y) + r')\fs45\bord3\shad1\c&HFFFFFF&\3c&H000000&}'

# 标签说明
# \an8     - 顶部居中对齐
# \pos(x,y) - 精确位置
# \fs<size> - 字体大小
# \bord<px> - 描边宽度
# \c&HBGR&  - 字体颜色（BGR格式）
```

---

## 6. 项目结构

```
shorts-fission/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── video.py
│   │   │   └── variant.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── videos.py
│   │   │   │   ├── variants.py
│   │   │   │   └── downloads.py
│   │   │   └── websocket.py
│   │   ├── services/
│   │   │   ├── downloader.py
│   │   │   ├── variant_engine.py      # v4.0 PIP
│   │   │   ├── scrapling_downloader.py
│   │   │   └── subtitle_extractor.py
│   │   └── tasks/
│   │       └── celery_tasks.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Videos.tsx
│   │   │   └── Downloads.tsx
│   │   ├── components/
│   │   │   ├── VideoCard.tsx
│   │   │   ├── VideoDetailModal.tsx
│   │   │   ├── VideoUploader.tsx
│   │   │   └── Toast.tsx
│   │   └── hooks/
│   │       └── useWebSocket.ts
│   └── package.json
├── docs/
│   ├── TikTok_Visual_Dedup_v4.0_PIP.md
│   ├── TikTok_Visual_Dedup_v3.0.md
│   └── Smart_BGM_Matching_v1.0.md
├── data/
│   ├── videos/
│   └── variants/
├── config/
├── luts/
├── masks/
├── sports_bgm/
├── tasks/
├── CHANGELOG.md
├── docker-compose.yml
└── README.md
```

---

## 7. 部署配置

### docker-compose.yml

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "8888:8888"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - redis
    volumes:
      - ./data:/app/data

  celery:
    build: ./backend
    command: celery -A app.tasks.celery_tasks worker --loglevel=info
    depends_on:
      - redis
    volumes:
      - ./data:/app/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

---

## 8. 性能指标

| 指标 | 值 |
|------|-----|
| 短视频（<30s）单变体 | 30-60 秒 |
| 中视频（30-120s）单变体 | 1-3 分钟 |
| 长视频（>120s）单变体 | 3-5 分钟 |
| FFmpeg 超时 | 1800 秒 |
| 编码质量 | q:v 8 |
| 最大变体数 | 50 |

---

**生成时间**: 2026-03-13
**版本**: 4.0
**状态**: ✅ 生产就绪
