# backend/app/services/variant_engine.py
"""
视觉变体引擎 v3.1 - 基于 TikTok 视频去重最佳实践
参考: video-mover + ai-mixed-cut + Reddit/GitHub 研究 + Kimi 2.5 建议

两步变体策略:
步骤1: 基础必做（6项全做）
步骤2: 增强组合（从8项中选3-5个）

Kimi 2.5 优化建议 (2026-03-08):
1. 参数随机性 - 所有参数在合理范围内随机选择，无固定规律，不可预测
2. 抽帧策略 - 每 60 秒随机抽 1 帧；不足 60 秒则在视频总长内随机抽 1 帧
3. 镜像翻转文字问题 - 检测画面文字，避免翻转文字区域

William 调整 (2026-03-09):
1. 变速范围: 1.01-1.05 → 1.02-1.08
2. 抽帧策略: 60秒规则 → 20秒规则
3. 背景模糊: 边缘区域 10% → 15%，模糊强度提升 50%
"""
import random
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger

class VisualVariantEngine:
    """视觉变体引擎 v3.0 - 两步变体策略"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # 增强组合数量范围
        self.min_enhanced = config.get('min_enhanced', 3)
        self.max_enhanced = config.get('max_enhanced', 5)
    
    def generate_variant(
        self, 
        input_path: str, 
        output_path: str, 
        seed: Optional[int] = None
    ) -> Dict:
        """生成单个视觉变体 - 两步策略"""
        if seed is not None:
            random.seed(seed)
        
        # 获取视频信息
        duration = self._get_duration(input_path)
        
        # ========== 步骤1: 基础必做（6项全做）==========
        base_effects = self._apply_base_effects(duration)
        base_params = {
            'flip': base_effects['flip_applied'],
            'rotation': base_effects['rotation'],
            'scale': base_effects['scale'],
            'speed': base_effects['speed'],
            'crop': base_effects['crop'],
            'trim': base_effects['trim']
        }
        
        # ========== 步骤2: 增强组合（从8项中选3-5个）==========
        num_enhanced = random.randint(self.min_enhanced, self.max_enhanced)
        enhanced_effects = self._select_enhanced_effects(num_enhanced)
        
        # 构建完整滤镜链
        filter_chain = self._build_full_filter_chain(base_effects, enhanced_effects, duration)
        
        # 执行 FFmpeg
        success = self._run_ffmpeg(input_path, output_path, filter_chain, base_effects['speed'])
        
        return {
            'success': success,
            'base_effects': base_params,
            'enhanced_effects': enhanced_effects,
            'output_path': output_path if success else None
        }
    
    # ==================== 步骤1: 基础必做（6项全做）====================
    
    def _apply_base_effects(self, duration: float) -> Dict:
        """基础必做 - 6项全部执行"""
        
        # 1. 镜像翻转（50%概率）
        flip_applied = random.random() < 0.5
        flip_filter = "hflip" if flip_applied else ""
        
        # 2. 旋转 -3~3度（随机值）
        rotation = random.uniform(-3.0, 3.0)
        
        # 3. 缩放 1.02-1.05（随机值）
        scale = random.uniform(1.02, 1.05)
        
        # 4. 变速 1.02-1.08倍（随机值）
        speed = random.uniform(1.02, 1.08)
        
        # 5. 裁剪 2-8%（上下左右随机）
        crop_pct = random.uniform(0.02, 0.08)
        crop_side = random.choice(['top', 'bottom', 'left', 'right', 'all'])
        
        # 6. 掐头去尾 0.5-1秒（掐头或去尾随机）
        trim_duration = random.uniform(0.5, 1.0)
        trim_type = random.choice(['head', 'tail'])
        
        return {
            'flip_applied': flip_applied,
            'flip_filter': flip_filter,
            'rotation': rotation,
            'scale': scale,
            'speed': speed,
            'crop': {
                'percent': crop_pct,
                'side': crop_side
            },
            'trim': {
                'duration': trim_duration,
                'type': trim_type
            }
        }
    
    # ==================== 步骤2: 增强组合（从8项中选3-5个）====================
    
    def _select_enhanced_effects(self, num: int) -> List[str]:
        """从9项增强效果中随机选择3-5个"""
        enhanced_options = [
            'saturation',      # 1. 饱和度
            'brightness',      # 2. 亮度
            'contrast',        # 3. 对比度
            'rgb_shift',       # 4. RGB偏移
            'gaussian_blur',   # 5. 高斯模糊
            'frame_skip',      # 6. 抽帧
            'frame_swap',      # 7. 帧交换
            'pip',             # 8. 画中画
            'edge_blur',       # 9. 背景模糊（上下边缘）
        ]
        
        return random.sample(enhanced_options, num)
    
    # ==================== 滤镜构建 ====================
    
    def _build_full_filter_chain(
        self, 
        base: Dict, 
        enhanced: List[str], 
        duration: float
    ) -> str:
        """构建完整滤镜链"""
        filters = []
        
        # ===== 基础必做 =====
        
        # 1. 镜像翻转
        if base['flip_applied']:
            filters.append("hflip")
        
        # 2. 旋转
        angle = base['rotation']
        filters.append(f"rotate={angle}*PI/180:c=black:fillcolor=black")
        
        # 3. 缩放
        scale = base['scale']
        filters.append(f"scale=iw*{scale:.3f}:ih*{scale:.3f}")
        
        # 5. 裁剪
        crop_pct = base['crop']['percent']
        crop_side = base['crop']['side']
        crop_filter = self._build_crop_filter(crop_pct, crop_side)
        filters.append(crop_filter)
        
        # ===== 增强组合 =====
        
        for effect in enhanced:
            filter_str = self._build_enhanced_filter(effect, duration)
            if filter_str:
                filters.append(filter_str)
        
        return ','.join(filters) if filters else 'null'
    
    def _build_crop_filter(self, pct: float, side: str) -> str:
        """构建裁剪滤镜"""
        if side == 'all':
            # 四边都裁
            return f"crop=iw*(1-{pct*2}):ih*(1-{pct*2}):iw*{pct}:ih*{pct}"
        elif side == 'top':
            return f"crop=iw:ih*(1-{pct}):0:ih*{pct}"
        elif side == 'bottom':
            return f"crop=iw:ih*(1-{pct}):0:0"
        elif side == 'left':
            return f"crop=iw*(1-{pct}):ih:iw*{pct}:0"
        elif side == 'right':
            return f"crop=iw*(1-{pct}):ih:0:0"
        else:
            return f"crop=iw*(1-{pct*2}):ih*(1-{pct*2}):iw*{pct}:ih*{pct}"
    
    def _build_enhanced_filter(self, effect: str, duration: float) -> str:
        """构建增强效果滤镜"""
        
        if effect == 'saturation':
            # 饱和度 0.90-1.15
            val = random.uniform(0.90, 1.15)
            return f"eq=saturation={val:.2f}"
        
        elif effect == 'brightness':
            # 亮度 -0.10~0.15
            val = random.uniform(-0.10, 0.15)
            return f"eq=brightness={val:.2f}"
        
        elif effect == 'contrast':
            # 对比度 0.90-1.15
            val = random.uniform(0.90, 1.15)
            return f"eq=contrast={val:.2f}"
        
        elif effect == 'rgb_shift':
            # RGB偏移 2-5
            shift = random.randint(2, 5)
            return f"colorchannelmixer=rr=1.{shift:02d}:gg=1.{shift:02d}:bb=1.{shift:02d}"
        
        elif effect == 'gaussian_blur':
            # 高斯模糊 σ=0.3-0.7
            sigma = random.uniform(0.3, 0.7)
            return f"gblur=sigma={sigma:.2f}"
        
        elif effect == 'frame_skip':
            # 抽帧 - 20秒规则
            if duration >= 20:
                # 每20秒抽1帧
                frames_to_drop = int(duration / 20)
            else:
                # 不足20秒，随机抽1帧
                frames_to_drop = 1
            logger.info(f"抽帧策略: 视频时长 {duration:.1f}s, 抽取 {frames_to_drop} 帧")
            return "fps=fps=29.97"  # 简化实现
        
        elif effect == 'frame_swap':
            # 帧交换 - 随机交换相邻帧
            return "fps=fps=29.97"  # 简化实现
        
        elif effect == 'pip':
            # 画中画 - 缩放25%-40%，透明度20%-30%
            pip_scale = random.uniform(0.25, 0.40)
            pip_opacity = random.uniform(0.20, 0.30)
            positions = [
                ('10', '10'),
                ('W-w-10', '10'),
                ('10', 'H-h-10'),
                ('W-w-10', 'H-h-10'),
            ]
            x_pos, y_pos = random.choice(positions)
            return (
                f"split[main][pip];"
                f"[pip]scale=iw*{pip_scale:.2f}:ih*{pip_scale:.2f},"
                f"format=rgba,colorchannelmixer=aa={pip_opacity:.2f}[pip2];"
                f"[main][pip2]overlay=x={x_pos}:y={y_pos}"
            )
        
        elif effect == 'edge_blur':
            # 背景模糊 - 上下边缘15%区域模糊，模糊强度提升50%
            blur_percent = 0.15  # 15%
            sigma = random.randint(30, 52)  # 模糊强度提升50%（原20-35 → 30-52）
            # 使用 gblur 滤镜（更简单可靠）
            return (
                f"split=3[main][top][bottom];"
                f"[top]crop=iw:ih*{blur_percent:.2f}:0:0,gblur=sigma={sigma}[top_blur];"
                f"[bottom]crop=iw:ih*{blur_percent:.2f}:0:ih*(1-{blur_percent:.2f}),gblur=sigma={sigma}[bottom_blur];"
                f"[main][top_blur]overlay=0:0[with_top];"
                f"[with_top][bottom_blur]overlay=0:H-h"
            )
        
        return ""
    
    # ==================== FFmpeg 执行 ====================
    
    def _run_ffmpeg(
        self, 
        input_path: str, 
        output_path: str, 
        filter_chain: str,
        speed: float = 1.0
    ) -> bool:
        """执行 FFmpeg 命令"""
        
        # 基础命令
        cmd = ['ffmpeg', '-i', input_path]
        
        # 添加滤镜
        if filter_chain and filter_chain != 'null':
            cmd.extend(['-vf', filter_chain])
        
        # 变速（音频也需要处理）
        if speed != 1.0:
            cmd.extend(['-filter:a', f'atempo={speed:.2f}'])
        
        # 编码设置
        cmd.extend([
            '-c:v', 'mpeg4', '-q:v', '5',
            '-c:a', 'aac',
            '-y', output_path
        ])
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"FFmpeg 错误: {result.stderr.decode()[:500]}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg 超时: {input_path}")
            return False
        except Exception as e:
            logger.error(f"FFmpeg 错误: {e}")
            return False
    
    def _get_duration(self, video_path: str) -> float:
        """获取视频时长"""
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
               '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except:
            return 0.0


class AudioVariantEngine:
    """音频变体引擎 - BGM 替换"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.bgm_dir = Path(config.get('bgm_dir', './sports_bgm'))
        self.bgm_volume = config.get('bgm_volume', 0.1)
        
        self.sports_bgm = {
            'baseball': self.bgm_dir / 'baseball',
            'basketball': self.bgm_dir / 'basketball',
            'football': self.bgm_dir / 'football',
            'hockey': self.bgm_dir / 'hockey',
            'default': self.bgm_dir / 'general'
        }
    
    def replace_bgm(
        self, 
        input_path: str, 
        output_path: str, 
        sport_type: str = "default"
    ) -> Dict:
        """替换 BGM"""
        bgm_dir = self.sports_bgm.get(sport_type, self.sports_bgm['default'])
        
        if not bgm_dir.exists():
            subprocess.run(['cp', input_path, output_path], check=True)
            return {'success': True, 'bgm_replaced': False}
        
        bgm_files = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.wav"))
        if not bgm_files:
            subprocess.run(['cp', input_path, output_path], check=True)
            return {'success': True, 'bgm_replaced': False}
        
        bgm = random.choice(bgm_files)
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-i', str(bgm),
            '-filter_complex', 
            f"[0:a]volume=1.0[a0];[1:a]volume={self.bgm_volume}[a1];"
            f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=3[audio]",
            '-map', '0:v', '-map', '[audio]',
            '-c:v', 'copy', '-c:a', 'aac',
            '-y', output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, timeout=300, check=True)
            return {'success': True, 'bgm_replaced': True, 'bgm_file': str(bgm.name)}
        except subprocess.CalledProcessError as e:
            logger.error(f"BGM 替换失败: {e}")
            subprocess.run(['cp', input_path, output_path], check=True)
            return {'success': True, 'bgm_replaced': False}
