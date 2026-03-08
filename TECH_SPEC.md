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
POST   /api/videos/batch             # 批量下载 (账号+时间范围)
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
    variant_index: int         # 第几个变体 (1-20)
    status: VariantStatus
    title: str
    description: str
    tags: str                  # JSON
    effects_applied: str       # 应用的特效列表 (JSON)
    file_path: str
    file_size: int
    created_at: datetime
    completed_at: datetime
```

---

## 2. 视觉变体引擎

### 2.1 特效池

```python
EFFECTS_POOL = {
    # 基础特效 (来自 ai-mixed-cut)
    'lut_color': 'LUT调色',
    'dynamic_zoom': '动态缩放',
    'color_shift_sbc': '颜色调整',
    'texture_noise': '纹理噪声',
    'mask_overlay': '遮罩叠加',
    'transition_xfade': '转场效果',
    
    # 高级特效 (来自 video-mover)
    'frame_swap': '帧交换',
    'frequency_scramble': '频域扰乱',
    'blur_edge': '边缘模糊',
    'blur_background': '背景模糊区域',
    'color_shift_rgb': 'RGB通道偏移',
    'flip_horizontal': '水平镜像',
    'rotation': '旋转',
    'crop': '裁剪',
    'fade': '淡入淡出',
    'pip': '画中画',
}
```

### 2.2 FFmpeg 滤镜实现

```python
EFFECT_FILTERS = {
    'lut_color': "lut3d=file='{lut_path}'",
    'dynamic_zoom': "zoompan=z='{zoom}':d=1:s=1080x1920",
    'color_shift_sbc': "eq=saturation={sat}:brightness={bright}:contrast={cont}",
    'texture_noise': "noise=alls={level}:allf=t",
    'flip_horizontal': "hflip",
    'rotation': "rotate={angle}*PI/180:c=black",
    'crop': "crop=iw*(1-{pct}):ih*(1-{pct})",
    'fade': "fade=t=in:st=0:d=0.3,fade=t=out:st=-0.3:d=0.3",
    'blur_edge': "boxblur=lr:{strength}:cr:{strength}",
}
```

### 2.3 变体生成流程

```python
def generate_variant(input_path, output_path, seed=None):
    # 1. 随机选择 1-5 种特效
    num_effects = random.randint(1, 5)
    selected = random.sample(EFFECTS_POOL.keys(), num_effects)
    
    # 2. 构建滤镜链
    filter_chain = build_filter_chain(selected)
    
    # 3. 执行 FFmpeg
    ffmpeg -i input.mp4 -vf filter_chain -c:v libx264 output.mp4
```

---

## 3. 下载模块

### 3.1 yt-dlp 命令

```bash
# 单视频下载
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
       -o "{output_path}" \
       --no-playlist \
       --write-info-json \
       --write-thumbnail \
       "{url}"

# 获取账号视频列表
yt-dlp --flat-playlist --dump-json "{account_url}"

# TikTok 无水印
yt-dlp --no-mark-watched "{tiktok_url}"
```

### 3.2 实时监控

```python
async def monitor_accounts(accounts):
    while True:
        for account in accounts:
            # 检查新视频
            new_videos = check_new_videos(account)
            
            # 立即下载
            for video in new_videos:
                download_video(video)
                notify_user(video)
        
        # 等待下一次检查
        await asyncio.sleep(CHECK_INTERVAL)
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
        "effects": ["lut_color", "dynamic_zoom", "texture_noise"]
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

## 5. 项目结构

```
shorts-fission/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Accounts.tsx
│   │   │   ├── Videos.tsx
│   │   │   ├── Variants.tsx
│   │   │   └── Downloads.tsx
│   │   ├── components/
│   │   └── hooks/
│   └── package.json
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   └── main.py
│   ├── models/
│   ├── services/
│   └── tasks/
├── config/
├── data/
├── docker-compose.yml
└── Dockerfile
```

---

## 6. 部署配置

### docker-compose.yml

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - db
    volumes:
      - ./data:/app/data

  celery:
    build: ./backend
    command: celery -A tasks worker --loglevel=info
    depends_on:
      - redis
    volumes:
      - ./data:/app/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: shorts_fission
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

**生成时间**: 2026-03-07
**版本**: 1.0
