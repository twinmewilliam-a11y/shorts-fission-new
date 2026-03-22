# Remotion 方案规划

## 背景

ASS 字幕的词级动画有局限性：
- `\t()` 标签只能做简单的缩放/颜色渐变
- 无法实现真正的"逐词弹出"效果
- FFmpeg 渲染时所有层同时显示

## 目标

实现 **MrBeast 风格的逐词弹出动画**：
- 当前词放大 + 高亮
- 之前的词保持正常
- 之后的词半透明或隐藏

---

## 技术方案

### Remotion 简介

Remotion 是一个使用 React 创建视频的框架：
- 使用 CSS/JS 动画
- 支持精确的帧级控制
- 可编程的字幕动画

### 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│              Remotion Animated Caption 架构                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  输入: WhisperX 词级时间戳                                      │
│  [{word: "Hello", start: 0.0, end: 0.5}, ...]                  │
│                                                                 │
│  处理流程:                                                       │
│  1. 生成 Remotion 项目 (React + CSS)                           │
│  2. 渲染视频帧 (逐帧渲染)                                        │
│  3. 合成最终视频 (FFmpeg)                                       │
│                                                                 │
│  输出: 带词级动画的视频                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. WordAnimation.tsx

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

interface WordAnimationProps {
  words: Array<{word: string; start: number; end: number}>;
  template: 'pop_highlight' | 'karaoke_flow' | 'hype_gaming';
  position: 'center' | 'bottom' | 'top';
}

export const WordAnimation: React.FC<WordAnimationProps> = ({
  words,
  template,
  position
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  return (
    <div style={{
      position: 'absolute',
      ...getPosition(position),
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'center',
      fontFamily: 'Arial Black',
    }}>
      {words.map((wordData, index) => {
        const startFrame = wordData.start * fps;
        const endFrame = wordData.end * fps;
        
        // 当前词判断
        const isCurrentWord = frame >= startFrame && frame < endFrame;
        
        // 动画参数
        const scale = isCurrentWord ? 1.15 : 1;
        const opacity = frame < startFrame ? 0.5 : 1;
        const color = isCurrentWord ? '#FFD700' : '#FFFFFF';
        
        // 弹簧动画
        const springValue = spring({
          frame: frame - startFrame,
          fps,
          config: { damping: 100, stiffness: 200 }
        });
        
        return (
          <span
            key={index}
            style={{
              marginLeft: 8,
              marginRight: 8,
              fontSize: isCurrentWord ? 58 : 50,
              fontWeight: 'bold',
              color,
              textShadow: '3px 3px 0 #000',
              transform: `scale(${isCurrentWord ? interpolate(springValue, [0, 1], [1, 1.15]) : 1})`,
              opacity: interpolate(opacity, [0, 1], [0.5, 1]),
              transition: 'all 0.1s ease-out',
            }}
          >
            {wordData.word}
          </span>
        );
      })}
    </div>
  );
};
```

#### 2. generateRemotionProject()

```python
def generate_remotion_project(
    words_data: List[Dict],
    output_dir: str,
    template: str = 'pop_highlight',
    position: str = 'center',
    video_width: int = 1080,
    video_height: int = 1920,
) -> Dict:
    """
    生成 Remotion 项目
    
    1. 创建项目目录结构
    2. 生成 WordAnimation.tsx
    3. 生成 composition 配置
    4. 返回渲染命令
    """
    # 创建目录
    project_dir = Path(output_dir) / 'remotion-caption'
    src_dir = project_dir / 'src'
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成 words.json
    words_json = json.dumps(words_data, ensure_ascii=False)
    (src_dir / 'words.json').write_text(words_json)
    
    # 生成 WordAnimation.tsx
    component_code = generate_component_code(template, position)
    (src_dir / 'WordAnimation.tsx').write_text(component_code)
    
    # 生成 Root.tsx
    root_code = generate_root_code(words_data, video_width, video_height)
    (src_dir / 'Root.tsx').write_text(root_code)
    
    # 返回渲染命令
    return {
        'success': True,
        'project_dir': str(project_dir),
        'render_command': f'npx remotion render src/Root.tsx Caption out/video.mp4',
    }
```

#### 3. 渲染流程

```bash
# 1. 生成 Remotion 项目
python3 -c "
from app.services.remotion_caption import generate_remotion_project
generate_remotion_project(words_data, '/tmp/caption', 'pop_highlight', 'center')
"

# 2. 渲染字幕视频
cd /tmp/caption/remotion-caption
npx remotion render src/Root.tsx Caption out/caption.mp4

# 3. 合成到原视频
ffmpeg -i original.mp4 -i caption.mp4 \
  -filter_complex "[0:v][1:v]overlay=0:0" \
  -c:a copy output.mp4
```

---

## 实施计划

### Phase 1: 基础设施 (1-2天)

| 任务 | 描述 |
|------|------|
| 安装 Remotion | `npm install remotion` |
| 创建项目模板 | Remotion 项目结构 |
| 实现 WordAnimation.tsx | React 组件 |

### Phase 2: 集成 (1天)

| 任务 | 描述 |
|------|------|
| remotion_caption.py | Python 生成器 |
| 集成到 celery_tasks | 替换 ASS 流程 |
| 前端参数传递 | 模板选择 |

### Phase 3: 优化 (1天)

| 任务 | 描述 |
|------|------|
| 3种模板实现 | pop_highlight, karaoke_flow, hype_gaming |
| 性能优化 | 并行渲染 |
| 缓存策略 | 避免重复渲染 |

---

## 性能考虑

| 方案 | 渲染时间 | 质量 |
|------|---------|------|
| ASS | ~10s | 中等 |
| Remotion | ~2-5分钟 | 高 |

**优化策略**:
- 使用 GPU 加速
- 只渲染字幕层，再合成
- 缓存已渲染的字幕视频

---

## 风险

| 风险 | 缓解 |
|------|------|
| Remotion 渲染慢 | 只渲染字幕层，批量处理 |
| 服务器资源消耗 | 限制并发渲染任务 |
| 依赖 Node.js | 已安装，无额外工作 |

---

## 结论

Remotion 方案可以实现**真正的逐词动画**，但渲染时间会增加。建议：
1. **短期**: 继续使用 ASS + 修复位置问题
2. **中期**: 实现 Remotion 方案作为高级选项
3. **长期**: 默认使用 Remotion

---

*Created: 2026-03-22*
*Author: T.W*
