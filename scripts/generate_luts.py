#!/usr/bin/env python3
"""
生成示例 LUT 滤镜文件 (.cube 格式)
LUT (Look-Up Table) 用于视频调色
"""

import os
from pathlib import Path

def generate_cube_lut(filename: str, name: str, color_shift: tuple):
    """生成一个简单的 .cube LUT 文件"""
    r_shift, g_shift, b_shift = color_shift
    
    content = f"""TITLE "{name}"
# Generated LUT for Shorts Fission
# LUT size: 32

LUT_3D_INPUT_SIZE 32
LUT_3D_OUTPUT_SIZE 32

"""
    
    # 生成 32x32x32 的 LUT 数据
    for b in range(32):
        for g in range(32):
            for r in range(32):
                # 计算输出值（带偏移）
                r_out = min(1.0, max(0.0, r / 31.0 + r_shift))
                g_out = min(1.0, max(0.0, g / 31.0 + g_shift))
                b_out = min(1.0, max(0.0, b / 31.0 + b_shift))
                content += f"{r_out:.6f} {g_out:.6f} {b_out:.6f}\n"
    
    return content

def main():
    luts_dir = Path("/root/.openclaw/workspace/projects/shorts-fission/luts")
    
    # 定义 LUT 滤镜
    luts = {
        # Cinematic 系列
        "cinematic/warm_golden.cube": ("Warm Golden", (0.05, 0.02, -0.03)),
        "cinematic/cool_blue.cube": ("Cool Blue", (-0.02, 0.0, 0.08)),
        "cinematic/orange_teal.cube": ("Orange Teal", (0.1, -0.05, -0.08)),
        "cinematic/moody_shadows.cube": ("Moody Shadows", (-0.1, -0.05, 0.0)),
        
        # Vintage 系列
        "vintage/faded_film.cube": ("Faded Film", (0.02, 0.0, 0.02)),
        "vintage/sepia_tone.cube": ("Sepia Tone", (0.1, 0.05, -0.1)),
        "vintage/retro_70s.cube": ("Retro 70s", (0.08, 0.03, -0.05)),
        "vintage/classic_bw.cube": ("Classic B&W", (0.0, 0.0, 0.0)),
        
        # Sports 系列
        "sports/high_contrast.cube": ("High Contrast", (0.05, 0.05, 0.05)),
        "sports/vivid_colors.cube": ("Vivid Colors", (0.1, 0.08, 0.06)),
        "sports/dramatic.cube": ("Dramatic", (0.08, 0.0, -0.05)),
        "sports/energetic.cube": ("Energetic", (0.05, 0.1, 0.0)),
        
        # Creative 系列
        "creative/neon_pop.cube": ("Neon Pop", (0.15, 0.1, 0.2)),
        "creative/dreamy.cube": ("Dreamy", (0.05, 0.08, 0.1)),
        "creative/matrix_green.cube": ("Matrix Green", (-0.1, 0.15, -0.1)),
        "creative/sunset_glow.cube": ("Sunset Glow", (0.12, 0.05, -0.08)),
    }
    
    for lut_path, (name, shift) in luts.items():
        full_path = luts_dir / lut_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = generate_cube_lut(str(full_path), name, shift)
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"✅ 创建 LUT: {lut_path}")
    
    print(f"\n总计创建 {len(luts)} 个 LUT 滤镜")

if __name__ == "__main__":
    main()
