#!/usr/bin/env python3
"""
Shorts Fission 功能测试脚本
测试：
1. 删除视频功能（包括变体文件和数据库记录）
2. 继续生成变体功能（累加模式）
"""

import asyncio
import aiohttp
import json
import os
import sys
from pathlib import Path

# API 基础地址
API_BASE = "http://localhost:8000"

class TestRunner:
    def __init__(self):
        self.session = None
        self.test_results = []
    
    async def setup(self):
        """初始化测试环境"""
        self.session = aiohttp.ClientSession()
        print("=" * 60)
        print("Shorts Fission 功能测试")
        print("=" * 60)
    
    async def teardown(self):
        """清理测试环境"""
        if self.session:
            await self.session.close()
    
    def log(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"\n{status} - {test_name}")
        if message:
            print(f"   {message}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
    
    async def api_get(self, endpoint: str) -> dict:
        """GET 请求"""
        async with self.session.get(f"{API_BASE}{endpoint}") as resp:
            return await resp.json()
    
    async def api_post(self, endpoint: str) -> dict:
        """POST 请求"""
        async with self.session.post(f"{API_BASE}{endpoint}") as resp:
            return await resp.json()
    
    async def api_delete(self, endpoint: str) -> dict:
        """DELETE 请求"""
        async with self.session.delete(f"{API_BASE}{endpoint}") as resp:
            return await resp.json()
    
    async def test_1_initial_state(self):
        """测试1: 检查初始状态"""
        try:
            data = await self.api_get("/api/videos")
            total = data.get("total", 0)
            self.log(
                "初始状态检查",
                True,
                f"当前视频数量: {total}"
            )
            return data.get("videos", [])
        except Exception as e:
            self.log("初始状态检查", False, str(e))
            return []
    
    async def test_2_delete_video_with_variants(self):
        """测试2: 删除视频功能（包括变体）"""
        try:
            # 获取现有视频
            videos = await self.api_get("/api/videos")
            video_list = videos.get("videos", [])
            
            if not video_list:
                self.log("删除视频功能", False, "没有可删除的视频")
                return False
            
            # 选择第一个视频
            video = video_list[0]
            video_id = video["id"]
            variant_count = video.get("variant_count", 0)
            
            print(f"\n   准备删除视频 {video_id}（变体数: {variant_count}）")
            
            # 检查变体文件是否存在
            variant_dir = Path(f"/root/.openclaw/workspace/projects/shorts-fission/data/variants/{video_id}")
            files_before = list(variant_dir.glob("*.mp4")) if variant_dir.exists() else []
            print(f"   删除前变体文件: {len(files_before)} 个")
            
            # 执行删除
            result = await self.api_delete(f"/api/videos/{video_id}")
            print(f"   删除结果: {result}")
            
            # 检查数据库中是否还有该视频
            videos_after = await self.api_get("/api/videos")
            video_ids = [v["id"] for v in videos_after.get("videos", [])]
            
            # 检查变体文件是否被删除
            files_after = list(variant_dir.glob("*.mp4")) if variant_dir.exists() else []
            
            # 验证结果
            db_deleted = video_id not in video_ids
            files_deleted = len(files_after) == 0
            
            passed = db_deleted and files_deleted
            
            self.log(
                "删除视频功能",
                passed,
                f"数据库删除: {'✅' if db_deleted else '❌'} | 文件删除: {'✅' if files_deleted else '❌'}"
            )
            
            return passed
            
        except Exception as e:
            self.log("删除视频功能", False, str(e))
            return False
    
    async def test_3_continue_generate_variants(self):
        """测试3: 继续生成变体功能（累加模式）"""
        try:
            # 获取现有视频
            videos = await self.api_get("/api/videos")
            video_list = videos.get("videos", [])
            
            if not video_list:
                self.log("继续生成变体功能", False, "没有可用的视频")
                return False
            
            # 找一个已完成的视频
            completed_video = None
            for v in video_list:
                if v.get("status") == "completed":
                    completed_video = v
                    break
            
            if not completed_video:
                # 使用第一个视频
                completed_video = video_list[0]
            
            video_id = completed_video["id"]
            initial_count = completed_video.get("target_variant_count", 0)
            
            print(f"\n   视频ID: {video_id}")
            print(f"   当前变体目标数: {initial_count}")
            
            # 添加 2 个变体（累加模式）
            add_count = 2
            result = await self.api_post(
                f"/api/videos/{video_id}/set-variant-count?count={add_count}&append=true"
            )
            
            new_count = result.get("new_count", 0)
            expected_count = initial_count + add_count
            
            print(f"   请求新增: {add_count}")
            print(f"   预期总数: {expected_count}")
            print(f"   实际总数: {new_count}")
            
            passed = new_count == expected_count
            
            self.log(
                "继续生成变体功能",
                passed,
                f"累加计算: {'✅' if passed else '❌'} | 新目标数: {new_count}"
            )
            
            return passed
            
        except Exception as e:
            self.log("继续生成变体功能", False, str(e))
            return False
    
    async def test_4_variant_db_cleanup(self):
        """测试4: 验证变体数据库记录清理"""
        try:
            # 获取所有视频
            videos = await self.api_get("/api/videos")
            video_list = videos.get("videos", [])
            
            orphan_variants = 0
            
            for video in video_list:
                video_id = video["id"]
                
                # 检查变体文件
                variant_dir = Path(f"/root/.openclaw/workspace/projects/shorts-fission/data/variants/{video_id}")
                actual_files = list(variant_dir.glob("final_*.mp4")) if variant_dir.exists() else []
                
                # 获取数据库中的变体
                variants_data = await self.api_get(f"/api/variants/{video_id}")
                db_variants = variants_data.get("total", 0)
                
                print(f"\n   视频 {video_id}:")
                print(f"   - 数据库记录: {db_variants}")
                print(f"   - 实际文件: {len(actual_files)}")
                
                # 检查是否有孤儿记录（有数据库记录但无文件）
                if db_variants > 0 and len(actual_files) == 0:
                    orphan_variants += db_variants
            
            self.log(
                "变体数据库清理验证",
                orphan_variants == 0,
                f"孤儿变体: {orphan_variants} 个"
            )
            
            return orphan_variants == 0
            
        except Exception as e:
            self.log("变体数据库清理验证", False, str(e))
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        await self.setup()
        
        try:
            # 测试1: 初始状态
            await self.test_1_initial_state()
            
            # 测试3: 继续生成变体（在删除之前测试）
            await self.test_3_continue_generate_variants()
            
            # 测试2: 删除功能
            await self.test_2_delete_video_with_variants()
            
            # 测试4: 数据库清理验证
            await self.test_4_variant_db_cleanup()
            
        finally:
            await self.teardown()
        
        # 输出测试摘要
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test']}")
        
        print(f"\n通过: {passed}/{total}")
        print("=" * 60)
        
        return passed == total


async def main():
    runner = TestRunner()
    success = await runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
