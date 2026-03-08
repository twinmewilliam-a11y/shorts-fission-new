#!/usr/bin/env python3
"""
测试变体引擎
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/projects/shorts-fission/backend')

from app.services.text_variant_service import TextVariantEngine, SpintaxEngine
from app.services.variant_engine import VisualVariantEngine, AudioVariantEngine

def test_spintax():
    """测试 Spintax 引擎"""
    print("=== 测试 Spintax 引擎 ===")
    
    text = "这是一个{精彩|绝妙|震撼}的{视频|短片}！{必看|收藏|转发}"
    
    engine = SpintaxEngine()
    
    # 生成 5 个变体
    for i in range(5):
        variant = engine.spin(text, seed=i)
        print(f"变体 {i+1}: {variant}")

def test_text_variants():
    """测试文案变体引擎"""
    print("\n=== 测试文案变体引擎 ===")
    
    engine = TextVariantEngine()
    
    # 生成标题变体
    titles = engine.generate_title_variants(
        "精彩进球集锦",
        category='sports_highlight',
        count=5
    )
    
    print("\n标题变体:")
    for t in titles:
        print(f"  {t['index']}: {t['title']}")
    
    # 生成描述变体
    descriptions = engine.generate_description_variants(
        "这是一段精彩的体育视频",
        category='sports_highlight',
        count=3
    )
    
    print("\n描述变体:")
    for d in descriptions:
        print(f"  {d['index']}: {d['description'][:50]}...")
    
    # 生成标签变体
    tags = engine.generate_tag_variants('football', count=3)
    
    print("\n标签变体:")
    for i, t in enumerate(tags):
        print(f"  {i+1}: {t}")

def test_visual_variant_engine():
    """测试视觉变体引擎"""
    print("\n=== 测试视觉变体引擎 ===")
    
    config = {
        'luts_dir': '/root/.openclaw/workspace/projects/shorts-fission/luts',
        'masks_dir': '/root/.openclaw/workspace/projects/shorts-fission/masks',
        'min_effects': 1,
        'max_effects': 3,
    }
    
    engine = VisualVariantEngine(config)
    
    # 检查 LUT 文件
    luts = list(engine.luts_dir.glob("**/*.cube"))
    print(f"LUT 文件数量: {len(luts)}")
    
    # 模拟生成变体（不实际执行 FFmpeg）
    for i in range(3):
        import random
        random.seed(i)
        num_effects = random.randint(1, 3)
        selected = random.sample(list(engine.all_effects.keys()), num_effects)
        print(f"变体 {i+1} 选择的特效: {selected}")

def test_audio_variant_engine():
    """测试音频变体引擎"""
    print("\n=== 测试音频变体引擎 ===")
    
    config = {
        'bgm_dir': '/root/.openclaw/workspace/projects/shorts-fission/sports_bgm',
        'bgm_volume': 0.3,
    }
    
    engine = AudioVariantEngine(config)
    
    # 检查 BGM 目录
    for sport, path in engine.sports_bgm.items():
        if path.exists():
            files = list(path.glob("*.mp3")) + list(path.glob("*.wav"))
            print(f"{sport}: {len(files)} 个 BGM 文件")
        else:
            print(f"{sport}: 目录不存在")

if __name__ == "__main__":
    test_spintax()
    test_text_variants()
    test_visual_variant_engine()
    test_audio_variant_engine()
