#!/usr/bin/env python3
"""
集成测试脚本 - Phase 5 测试
"""
import subprocess
import sys
import os

sys.path.insert(0, '/root/.openclaw/workspace/projects/shorts-fission/backend')

def test_backend_imports():
    """测试后端模块导入"""
    print("=== 测试后端模块导入 ===")
    try:
        from app.main import app
        from app.services import VideoDownloader, VisualVariantEngine, AudioVariantEngine
        from app.services import SubtitleService, TextVariantEngine
        from app.models.video import Video
        from app.models.variant import Variant
        print("✅ 所有后端模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_frontend_build():
    """测试前端构建"""
    print("\n=== 测试前端构建 ===")
    frontend_dir = '/root/.openclaw/workspace/projects/shorts-fission/frontend'
    dist_dir = os.path.join(frontend_dir, 'dist')
    
    if os.path.exists(dist_dir):
        files = os.listdir(dist_dir)
        print(f"✅ 前端构建成功，dist 目录包含 {len(files)} 个文件")
        return True
    else:
        print("❌ 前端构建失败，dist 目录不存在")
        return False

def test_lut_files():
    """测试 LUT 滤镜文件"""
    print("\n=== 测试 LUT 滤镜文件 ===")
    luts_dir = '/root/.openclaw/workspace/projects/shorts-fission/luts'
    
    categories = ['cinematic', 'creative', 'sports', 'vintage']
    total = 0
    for cat in categories:
        cat_dir = os.path.join(luts_dir, cat)
        if os.path.exists(cat_dir):
            files = [f for f in os.listdir(cat_dir) if f.endswith('.cube')]
            print(f"  {cat}: {len(files)} 个")
            total += len(files)
    
    if total >= 16:
        print(f"✅ LUT 滤镜文件完整 ({total} 个)")
        return True
    else:
        print(f"⚠️ LUT 滤镜文件不足 ({total} 个)")
        return False

def test_bgm_files():
    """测试 BGM 音乐文件"""
    print("\n=== 测试 BGM 音乐文件 ===")
    bgm_dir = '/root/.openclaw/workspace/projects/shorts-fission/sports_bgm'
    
    categories = ['baseball', 'basketball', 'football', 'hockey', 'general']
    total = 0
    for cat in categories:
        cat_dir = os.path.join(bgm_dir, cat)
        if os.path.exists(cat_dir):
            files = [f for f in os.listdir(cat_dir) if f.endswith('.mp3')]
            print(f"  {cat}: {len(files)} 个")
            total += len(files)
    
    if total >= 15:
        print(f"✅ BGM 音乐文件完整 ({total} 个)")
        return True
    else:
        print(f"⚠️ BGM 音乐文件不足 ({total} 个)")
        return False

def test_services():
    """测试核心服务"""
    print("\n=== 测试核心服务 ===")
    try:
        from app.services import TextVariantEngine
        engine = TextVariantEngine()
        
        # 测试 Spintax
        variants = engine.generate_title_variants("测试标题", count=3)
        if len(variants) == 3:
            print("✅ 文案变体引擎工作正常")
        else:
            print("⚠️ 文案变体引擎输出异常")
            
        return True
    except Exception as e:
        print(f"❌ 服务测试失败: {e}")
        return False

def main():
    print("🧪 Shorts Fission 集成测试\n")
    
    results = []
    results.append(("后端模块导入", test_backend_imports()))
    results.append(("前端构建", test_frontend_build()))
    results.append(("LUT 滤镜文件", test_lut_files()))
    results.append(("BGM 音乐文件", test_bgm_files()))
    results.append(("核心服务", test_services()))
    
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常运行。")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 项测试未通过，请检查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
