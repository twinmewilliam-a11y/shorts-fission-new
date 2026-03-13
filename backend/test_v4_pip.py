#!/usr/bin/env python3
"""
v4.0 PIP 变体引擎测试脚本

测试三层合成架构：
1. 背景层：全景模糊 + v3.0 强化版
2. 中间层：画中画（60-70% 缩放）
3. 文字层：字幕（暂不测试）

Usage:
    python test_v4_pip.py <input_video> [output_video]
"""
import sys
import os
from pathlib import Path

# 添加后端路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.variant_engine import PIPVariantEngineV4
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stderr, level="DEBUG")


def test_pip_variant(input_path: str, output_path: str = None):
    """测试 PIP 变体生成"""
    
    if not os.path.exists(input_path):
        print(f"❌ 输入文件不存在: {input_path}")
        return False
    
    # 默认输出路径
    if not output_path:
        output_path = input_path.replace('.mp4', '_v4_pip.mp4')
    
    print(f"🎬 输入: {input_path}")
    print(f"📁 输出: {output_path}")
    print()
    
    # 创建引擎（禁用 WhisperX，只测试视频处理）
    engine = PIPVariantEngineV4({
        'min_enhanced': 3,
        'max_enhanced': 5,
        'whisperx_enabled': False,  # 暂不测试字幕
    })
    
    # 生成变体
    result = engine.generate_variant(input_path, output_path)
    
    print()
    if result['success']:
        print("✅ 变体生成成功！")
        print()
        print("📋 参数:")
        params = result['params']
        print(f"   • 全景模糊: σ={params['bg_blur']:.1f}")
        print(f"   • 背景放大: {params['bg_scale']*100:.0f}%")
        print(f"   • 变速: {params['speed']:.2f}x")
        print(f"   • 镜像翻转: {'是' if params['mirror'] else '否'}")
        print(f"   • 旋转: {params['rotation']:.1f}°")
        print(f"   • 裁剪: {params['crop_ratio']*100:.0f}%")
        print(f"   • 中间层缩放: {params['fg_scale']*100:.0f}%")
        print(f"   • 增强效果: {', '.join(params['enhance_effects'])}")
        print()
        print(f"📁 输出文件: {result['output_path']}")
        
        # 获取输出文件大小
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"📦 文件大小: {size_mb:.2f} MB")
        
        return True
    else:
        print("❌ 变体生成失败")
        print(f"错误: {result.get('error', '未知错误')}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python test_v4_pip.py <input_video> [output_video]")
        print()
        print("示例:")
        print("  python test_v4_pip.py test_video.mp4")
        print("  python test_v4_pip.py test_video.mp4 output_pip.mp4")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_video = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = test_pip_variant(input_video, output_video)
    sys.exit(0 if success else 1)
