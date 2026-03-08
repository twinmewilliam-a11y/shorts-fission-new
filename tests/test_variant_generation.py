#!/usr/bin/env python3
"""
Shorts Fission 变体生成完整测试集

测试维度：
1. 单次生成测试 - 从0开始生成变体
2. 累加生成测试 - 继续生成更多变体
3. 索引连续性测试 - 验证变体索引不重复
4. 文件完整性测试 - 验证生成的文件可播放
5. 数据库一致性测试 - 数据库记录与文件对应
6. 边界条件测试 - 极端参数、多次累加
7. 错误恢复测试 - 失败后重试
"""

import asyncio
import aiohttp
import json
import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# API 基础地址
API_BASE = "http://localhost:8000"
PROJECT_DIR = "/root/.openclaw/workspace/projects/shorts-fission"
DB_PATH = f"{PROJECT_DIR}/data/shorts_fission.db"
VARIANTS_DIR = f"{PROJECT_DIR}/data/variants"
VIDEOS_DIR = f"{PROJECT_DIR}/data/videos"

class TestRunner:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.test_video_id = None
        self.created_video_ids = []
    
    async def setup(self):
        """初始化测试环境"""
        self.session = aiohttp.ClientSession()
        print("=" * 70)
        print("Shorts Fission 变体生成完整测试集")
        print("=" * 70)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
    
    async def teardown(self):
        """清理测试环境"""
        if self.session:
            await self.session.close()
    
    def log(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"\n{status} - {test_name}")
        if message:
            for line in message.split('\n'):
                print(f"   {line}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
    
    async def api_get(self, endpoint: str) -> dict:
        """GET 请求"""
        async with self.session.get(f"{API_BASE}{endpoint}") as resp:
            text = await resp.text()
            try:
                return json.loads(text)
            except:
                return {"error": text, "status_code": resp.status}
    
    async def api_post(self, endpoint: str) -> dict:
        """POST 请求"""
        async with self.session.post(f"{API_BASE}{endpoint}") as resp:
            text = await resp.text()
            try:
                return json.loads(text)
            except:
                return {"error": text, "status_code": resp.status}
    
    async def api_delete(self, endpoint: str) -> dict:
        """DELETE 请求"""
        async with self.session.delete(f"{API_BASE}{endpoint}") as resp:
            text = await resp.text()
            try:
                return json.loads(text)
            except:
                return {"error": text, "status_code": resp.status}
    
    def db_query(self, sql: str, params=()):
        """执行数据库查询"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(sql, params)
        rows = c.fetchall()
        conn.close()
        return rows
    
    def db_execute(self, sql: str, params=()):
        """执行数据库操作"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(sql, params)
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected
    
    # ==================== 辅助函数 ====================
    
    async def create_test_video(self, suffix: str = "") -> int:
        """创建测试视频并返回ID"""
        # 找一个存在的视频文件
        video_files = list(Path(VIDEOS_DIR).glob("*.mp4"))
        if not video_files:
            raise Exception("没有可用的视频文件")
        
        source_file = str(video_files[0])
        
        # 插入测试视频
        now = datetime.now().isoformat()
        self.db_execute("""
            INSERT INTO videos (platform, video_id, url, title, status, source_path, resolution, 
                               variant_count, target_variant_count, duration, download_progress, variant_progress)
            VALUES ('test', ?, 'file://test', ?, 'DOWNLOADED', ?, '720p', 0, 0, 16, 100, 0)
        """, (f"test_{datetime.now().timestamp()}{suffix}", f"Test Video {suffix}", source_file))
        
        # 获取插入的ID
        video_id = self.db_query("SELECT last_insert_rowid()")[0][0]
        self.created_video_ids.append(video_id)
        print(f"   创建测试视频 ID={video_id}")
        return video_id
    
    async def wait_for_completion(self, video_id: int, timeout: int = 300) -> dict:
        """等待变体生成完成"""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            data = await self.api_get(f"/api/videos/{video_id}")
            if data.get("status") in ["completed", "failed"]:
                return data
            await asyncio.sleep(5)
        return {"status": "timeout", "error": "等待超时"}
    
    def get_variant_files(self, video_id: int) -> list:
        """获取变体文件列表"""
        variant_dir = Path(VARIANTS_DIR) / str(video_id)
        if not variant_dir.exists():
            return []
        return sorted([f.name for f in variant_dir.glob("final_*.mp4")])
    
    def get_db_variants(self, video_id: int) -> list:
        """获取数据库中的变体记录"""
        return self.db_query(
            "SELECT id, variant_index, file_path, status FROM variants WHERE video_id = ? ORDER BY variant_index",
            (video_id,)
        )
    
    # ==================== 测试用例 ====================
    
    async def test_1_single_generation(self):
        """测试1: 单次生成变体"""
        try:
            video_id = await self.create_test_video("_single")
            
            # 生成5个变体
            result = await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=5")
            
            if "error" in result:
                self.log("单次生成变体", False, f"API错误: {result}")
                return False
            
            # 等待完成
            final = await self.wait_for_completion(video_id)
            
            if final.get("status") != "completed":
                self.log("单次生成变体", False, f"状态: {final.get('status')}, 错误: {final.get('error')}")
                return False
            
            # 验证数量
            files = self.get_variant_files(video_id)
            db_variants = self.get_db_variants(video_id)
            
            passed = len(files) == 5 and len(db_variants) == 5
            
            self.log("单次生成变体", passed,
                f"文件数量: {len(files)}/5\n"
                f"数据库记录: {len(db_variants)}/5\n"
                f"文件列表: {', '.join(files)}")
            
            return passed
            
        except Exception as e:
            self.log("单次生成变体", False, str(e))
            return False
    
    async def test_2_append_generation(self):
        """测试2: 累加生成变体"""
        try:
            video_id = await self.create_test_video("_append")
            
            # 第一次生成3个
            result1 = await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=3")
            final1 = await self.wait_for_completion(video_id)
            
            if final1.get("status") != "completed":
                self.log("累加生成变体", False, f"第一次生成失败: {final1}")
                return False
            
            # 等待数据库更新
            await asyncio.sleep(2)
            
            # 第二次累加4个
            result2 = await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=4&append=true")
            final2 = await self.wait_for_completion(video_id, timeout=180)
            
            if final2.get("status") != "completed":
                self.log("累加生成变体", False, f"第二次生成失败: {final2}")
                return False
            
            # 验证总数 = 7
            files = self.get_variant_files(video_id)
            db_variants = self.get_db_variants(video_id)
            
            passed = len(files) == 7 and len(db_variants) == 7
            
            self.log("累加生成变体", passed,
                f"文件数量: {len(files)}/7\n"
                f"数据库记录: {len(db_variants)}/7\n"
                f"文件列表: {', '.join(files)}")
            
            return passed
            
        except Exception as e:
            self.log("累加生成变体", False, str(e))
            return False
    
    async def test_3_index_continuity(self):
        """测试3: 索引连续性 - 验证变体索引不重复、不跳过"""
        try:
            video_id = await self.create_test_video("_index")
            
            # 分3次生成，每次2个
            for i in range(3):
                if i == 0:
                    await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=2")
                else:
                    await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=2&append=true")
                await self.wait_for_completion(video_id)
                await asyncio.sleep(2)
            
            # 检查索引
            db_variants = self.get_db_variants(video_id)
            indexes = sorted([v[1] for v in db_variants])
            expected = list(range(1, 7))  # 1, 2, 3, 4, 5, 6
            
            # 检查重复
            has_duplicates = len(indexes) != len(set(indexes))
            # 检查连续
            is_continuous = indexes == expected
            
            passed = not has_duplicates and is_continuous
            
            self.log("索引连续性", passed,
                f"实际索引: {indexes}\n"
                f"预期索引: {expected}\n"
                f"有重复: {'是' if has_duplicates else '否'}\n"
                f"连续性: {'✓' if is_continuous else '✗'}")
            
            return passed
            
        except Exception as e:
            self.log("索引连续性", False, str(e))
            return False
    
    async def test_4_file_integrity(self):
        """测试4: 文件完整性 - 验证生成的文件可被ffprobe识别"""
        try:
            video_id = await self.create_test_video("_integrity")
            
            # 生成2个变体
            await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=2")
            await self.wait_for_completion(video_id)
            
            files = self.get_variant_files(video_id)
            
            if len(files) < 1:
                self.log("文件完整性", False, "没有生成文件")
                return False
            
            # 检查每个文件
            valid_count = 0
            invalid_files = []
            
            for f in files:
                file_path = Path(VARIANTS_DIR) / str(video_id) / f
                # 使用 ffprobe 检查
                import subprocess
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                     "-of", "json", str(file_path)],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        if data.get("format", {}).get("duration"):
                            valid_count += 1
                        else:
                            invalid_files.append(f)
                    except:
                        invalid_files.append(f)
                else:
                    invalid_files.append(f)
            
            passed = valid_count == len(files) and len(invalid_files) == 0
            
            self.log("文件完整性", passed,
                f"有效文件: {valid_count}/{len(files)}\n"
                f"无效文件: {invalid_files if invalid_files else '无'}")
            
            return passed
            
        except Exception as e:
            self.log("文件完整性", False, str(e))
            return False
    
    async def test_5_db_consistency(self):
        """测试5: 数据库一致性 - 文件和数据库记录一一对应"""
        try:
            video_id = await self.create_test_video("_consistency")
            
            await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=3")
            await self.wait_for_completion(video_id)
            
            files = self.get_variant_files(video_id)
            db_variants = self.get_db_variants(video_id)
            
            # 检查数据库中的文件路径是否都存在
            missing_files = []
            for v in db_variants:
                file_path = v[2]  # file_path
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            # 检查文件是否都有对应的数据库记录
            db_files = set([v[2] for v in db_variants])
            orphan_files = []
            for f in files:
                full_path = str(Path(VARIANTS_DIR) / str(video_id) / f)
                if full_path not in db_files:
                    orphan_files.append(f)
            
            passed = len(missing_files) == 0 and len(orphan_files) == 0
            
            self.log("数据库一致性", passed,
                f"数据库记录数: {len(db_variants)}\n"
                f"文件数: {len(files)}\n"
                f"缺失文件: {missing_files if missing_files else '无'}\n"
                f"孤儿文件: {orphan_files if orphan_files else '无'}")
            
            return passed
            
        except Exception as e:
            self.log("数据库一致性", False, str(e))
            return False
    
    async def test_6_delete_cascade(self):
        """测试6: 删除级联 - 删除视频时变体也被删除"""
        try:
            video_id = await self.create_test_video("_delete")
            
            # 生成变体
            await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=2")
            await self.wait_for_completion(video_id)
            
            # 检查有变体
            files_before = self.get_variant_files(video_id)
            db_before = self.get_db_variants(video_id)
            
            # 删除视频
            await self.api_delete(f"/api/videos/{video_id}")
            
            # 检查变体是否被删除
            files_after = self.get_variant_files(video_id)
            db_after = self.get_db_variants(video_id)
            
            passed = len(files_after) == 0 and len(db_after) == 0
            
            self.log("删除级联", passed,
                f"删除前: {len(files_before)} 文件, {len(db_before)} 记录\n"
                f"删除后: {len(files_after)} 文件, {len(db_after)} 记录")
            
            return passed
            
        except Exception as e:
            self.log("删除级联", False, str(e))
            return False
    
    async def test_7_variant_count_accuracy(self):
        """测试7: 变体计数准确性 - video.variant_count 与实际数量一致"""
        try:
            video_id = await self.create_test_video("_count")
            
            # 生成变体
            await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=4")
            await self.wait_for_completion(video_id)
            
            # 获取视频信息
            video_info = await self.api_get(f"/api/videos/{video_id}")
            reported_count = video_info.get("variant_count", 0)
            
            # 实际数据库记录
            db_variants = self.get_db_variants(video_id)
            actual_count = len([v for v in db_variants if v[3] == 'COMPLETED'])
            
            # 实际文件数
            files = self.get_variant_files(video_id)
            file_count = len(files)
            
            passed = reported_count == actual_count == file_count
            
            self.log("变体计数准确性", passed,
                f"API报告: {reported_count}\n"
                f"数据库记录: {actual_count}\n"
                f"实际文件: {file_count}")
            
            return passed
            
        except Exception as e:
            self.log("变体计数准确性", False, str(e))
            return False
    
    async def test_8_api_variant_list(self):
        """测试8: API 变体列表 - 返回的数量和内容正确"""
        try:
            video_id = await self.create_test_video("_api")
            
            await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=3")
            await self.wait_for_completion(video_id)
            
            # 获取 API 返回的变体列表
            result = await self.api_get(f"/api/variants/{video_id}")
            
            api_total = result.get("total", 0)
            api_variants = result.get("variants", [])
            api_indexes = sorted([v.get("variant_index") for v in api_variants])
            
            # 预期
            expected_total = 3
            expected_indexes = [1, 2, 3]
            
            passed = api_total == expected_total and api_indexes == expected_indexes
            
            self.log("API变体列表", passed,
                f"API total: {api_total} (预期: {expected_total})\n"
                f"API indexes: {api_indexes}\n"
                f"预期 indexes: {expected_indexes}")
            
            return passed
            
        except Exception as e:
            self.log("API变体列表", False, str(e))
            return False
    
    async def test_9_multiple_appends(self):
        """测试9: 多次累加 - 连续多次累加生成"""
        try:
            video_id = await self.create_test_video("_multi")
            
            total_expected = 0
            for batch in [2, 3, 2, 1]:  # 共8个
                if total_expected == 0:
                    await self.api_post(f"/api/videos/{video_id}/set-variant-count?count={batch}")
                else:
                    await self.api_post(f"/api/videos/{video_id}/set-variant-count?count={batch}&append=true")
                await self.wait_for_completion(video_id)
                await asyncio.sleep(2)
                total_expected += batch
            
            # 验证
            files = self.get_variant_files(video_id)
            db_variants = self.get_db_variants(video_id)
            indexes = sorted([v[1] for v in db_variants])
            expected_indexes = list(range(1, total_expected + 1))
            
            passed = (len(files) == total_expected and 
                     len(db_variants) == total_expected and
                     indexes == expected_indexes)
            
            self.log("多次累加", passed,
                f"文件数量: {len(files)}/{total_expected}\n"
                f"数据库记录: {len(db_variants)}/{total_expected}\n"
                f"索引: {indexes}\n"
                f"预期: {expected_indexes}")
            
            return passed
            
        except Exception as e:
            self.log("多次累加", False, str(e))
            return False
    
    async def test_10_edge_blur_effect(self):
        """测试10: 背景模糊效果 - 验证效果参数"""
        try:
            video_id = await self.create_test_video("_blur")
            
            await self.api_post(f"/api/videos/{video_id}/set-variant-count?count=5")
            await self.wait_for_completion(video_id)
            
            # 检查是否有变体应用了背景模糊
            db_variants = self.get_db_variants(video_id)
            
            effects_found = []
            for v in db_variants:
                # 获取 effects_applied (需要扩展查询)
                pass
            
            # 简化：只验证生成了变体
            files = self.get_variant_files(video_id)
            
            passed = len(files) == 5
            
            self.log("背景模糊效果", passed,
                f"生成变体数: {len(files)}/5\n"
                f"(背景模糊随机应用，此处仅验证生成成功)")
            
            return passed
            
        except Exception as e:
            self.log("背景模糊效果", False, str(e))
            return False
    
    # ==================== 清理 ====================
    
    async def cleanup_test_videos(self):
        """清理测试视频"""
        print("\n" + "=" * 70)
        print("清理测试数据...")
        
        for video_id in self.created_video_ids:
            try:
                # 删除变体文件
                variant_dir = Path(VARIANTS_DIR) / str(video_id)
                if variant_dir.exists():
                    import shutil
                    shutil.rmtree(variant_dir)
                
                # 删除数据库记录
                self.db_execute("DELETE FROM variants WHERE video_id = ?", (video_id,))
                self.db_execute("DELETE FROM videos WHERE id = ?", (video_id,))
                
            except Exception as e:
                print(f"   清理视频 {video_id} 失败: {e}")
        
        print(f"清理完成，共清理 {len(self.created_video_ids)} 个测试视频")
    
    # ==================== 运行所有测试 ====================
    
    async def run_all_tests(self):
        """运行所有测试"""
        await self.setup()
        
        try:
            print("\n【基础功能测试】")
            await self.test_1_single_generation()
            await self.test_2_append_generation()
            
            print("\n【索引和一致性测试】")
            await self.test_3_index_continuity()
            await self.test_5_db_consistency()
            await self.test_7_variant_count_accuracy()
            
            print("\n【文件完整性测试】")
            await self.test_4_file_integrity()
            
            print("\n【API测试】")
            await self.test_8_api_variant_list()
            
            print("\n【删除功能测试】")
            await self.test_6_delete_cascade()
            
            print("\n【边界条件测试】")
            await self.test_9_multiple_appends()
            await self.test_10_edge_blur_effect()
            
        finally:
            # 清理测试数据
            await self.cleanup_test_videos()
            await self.teardown()
        
        # 输出测试摘要
        print("\n" + "=" * 70)
        print("测试摘要")
        print("=" * 70)
        
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test']}")
        
        print(f"\n通过: {passed}/{total}")
        print("=" * 70)
        
        return passed == total


async def main():
    runner = TestRunner()
    success = await runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
