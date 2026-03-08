#!/usr/bin/env python3
"""
生成示例 BGM 音乐文件
使用 FFmpeg 生成简单的背景音乐占位符
"""
import subprocess
import os
from pathlib import Path

def generate_bgm(output_path: str, duration: int = 30, style: str = "upbeat"):
    """生成简单的 BGM 音频文件"""
    
    # 不同风格的音频参数
    styles = {
        "upbeat": "sine=frequency=440:beep_factor=4",  # 欢快
        "dramatic": "sine=frequency=220:beep_factor=2",  # 戏剧性
        "energetic": "sine=frequency=880:beep_factor=8",  # 活力
        "calm": "sine=frequency=330:beep_factor=1",  # 平静
    }
    
    audio_filter = styles.get(style, styles["upbeat"])
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"{audio_filter},volume=0.3",
        "-t", str(duration),
        "-ar", "44100",
        "-ac", "2",
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, timeout=60)
        return True
    except Exception as e:
        print(f"生成失败: {e}")
        return False

def main():
    bgm_dir = Path("/root/.openclaw/workspace/projects/shorts-fission/sports_bgm")
    
    # 各球类 BGM 配置
    bgm_configs = {
        "baseball": [
            ("bgm_01_upbeat.mp3", "upbeat"),
            ("bgm_02_dramatic.mp3", "dramatic"),
            ("bgm_03_calm.mp3", "calm"),
        ],
        "basketball": [
            ("bgm_01_energetic.mp3", "energetic"),
            ("bgm_02_upbeat.mp3", "upbeat"),
            ("bgm_03_dramatic.mp3", "dramatic"),
        ],
        "football": [
            ("bgm_01_dramatic.mp3", "dramatic"),
            ("bgm_02_energetic.mp3", "energetic"),
            ("bgm_03_upbeat.mp3", "upbeat"),
        ],
        "hockey": [
            ("bgm_01_energetic.mp3", "energetic"),
            ("bgm_02_dramatic.mp3", "dramatic"),
            ("bgm_03_upbeat.mp3", "upbeat"),
        ],
        "general": [
            ("bgm_01_upbeat.mp3", "upbeat"),
            ("bgm_02_calm.mp3", "calm"),
            ("bgm_03_energetic.mp3", "energetic"),
        ],
    }
    
    total = 0
    for sport, files in bgm_configs.items():
        sport_dir = bgm_dir / sport
        sport_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, style in files:
            output_path = sport_dir / filename
            if generate_bgm(str(output_path), duration=30, style=style):
                print(f"✅ {sport}/{filename}")
                total += 1
            else:
                print(f"❌ {sport}/{filename}")
    
    print(f"\n总计生成 {total} 个 BGM 文件")

if __name__ == "__main__":
    main()
