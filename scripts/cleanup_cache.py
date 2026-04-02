#!/usr/bin/env python3
"""
Shorts-Fission 缓存清理脚本

清理目标：
1. Remotion PNG 序列（remotion-caption/out/png_*）
2. 临时视频文件（remotion-caption/out/*.mp4, *.webm）
3. 过期的变体临时文件

用法：
  python scripts/cleanup_cache.py [--dry-run] [--max-age-hours 24]
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'backend'))

from loguru import logger


class CacheCleaner:
    """缓存清理器"""
    
    def __init__(self, dry_run: bool = False, max_age_hours: int = 24):
        self.dry_run = dry_run
        self.max_age = timedelta(hours=max_age_hours)
        self.now = datetime.now()
        
        # 缓存目录
        self.remotion_out = PROJECT_ROOT / 'remotion-caption' / 'out'
        self.temp_variants = PROJECT_ROOT / 'backend' / 'temp_variants'
        
        # 统计
        self.stats = {
            'png_cleaned': 0,
            'video_cleaned': 0,
            'size_cleaned': 0,
            'errors': 0,
        }
    
    def clean_all(self) -> dict:
        """执行所有清理任务"""
        logger.info(f"[CacheCleaner] 开始清理 (dry_run={self.dry_run}, max_age={self.max_age})")
        
        # 1. 清理 PNG 序列
        self._clean_png_sequences()
        
        # 2. 清理临时视频文件
        self._clean_temp_videos()
        
        # 3. 清理过期变体临时文件
        self._clean_temp_variants()
        
        logger.info(f"[CacheCleaner] 清理完成: {self.stats}")
        return self.stats
    
    def _clean_png_sequences(self):
        """清理 PNG 序列目录"""
        if not self.remotion_out.exists():
            return
        
        # 清理 png_* 目录
        for item in self.remotion_out.iterdir():
            if item.is_dir() and item.name.startswith('png_'):
                self._clean_dir_if_old(item, 'png_cleaned')
    
    def _clean_temp_videos(self):
        """清理临时视频文件"""
        if not self.remotion_out.exists():
            return
        
        # 清理测试视频文件
        patterns = ['caption_*.mp4', 'caption_*.webm', 'test_*.mp4', 'test_*.webm']
        
        for pattern in patterns:
            for file in self.remotion_out.glob(pattern):
                self._clean_file_if_old(file, 'video_cleaned')
    
    def _clean_temp_variants(self):
        """清理过期变体临时文件"""
        if not self.temp_variants.exists():
            return
        
        for item in self.temp_variants.iterdir():
            if item.is_dir():
                self._clean_dir_if_old(item, 'video_cleaned')
    
    def _clean_dir_if_old(self, dir_path: Path, stat_key: str):
        """如果目录过期则清理"""
        try:
            # 获取目录修改时间
            mtime = datetime.fromtimestamp(dir_path.stat().st_mtime)
            age = self.now - mtime
            
            if age > self.max_age:
                size = self._get_dir_size(dir_path)
                
                if self.dry_run:
                    logger.info(f"[DRY-RUN] 将删除: {dir_path} (age={age}, size={self._format_size(size)})")
                else:
                    logger.info(f"[CLEAN] 删除: {dir_path} (age={age}, size={self._format_size(size)})")
                    shutil.rmtree(dir_path)
                
                self.stats[stat_key] += 1
                self.stats['size_cleaned'] += size
        
        except Exception as e:
            logger.error(f"[CacheCleaner] 清理目录失败: {dir_path}, error={e}")
            self.stats['errors'] += 1
    
    def _clean_file_if_old(self, file_path: Path, stat_key: str):
        """如果文件过期则清理"""
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            age = self.now - mtime
            
            if age > self.max_age:
                size = file_path.stat().st_size
                
                if self.dry_run:
                    logger.info(f"[DRY-RUN] 将删除: {file_path} (age={age}, size={self._format_size(size)})")
                else:
                    logger.info(f"[CLEAN] 删除: {file_path} (age={age}, size={self._format_size(size)})")
                    file_path.unlink()
                
                self.stats[stat_key] += 1
                self.stats['size_cleaned'] += size
        
        except Exception as e:
            logger.error(f"[CacheCleaner] 清理文件失败: {file_path}, error={e}")
            self.stats['errors'] += 1
    
    def _get_dir_size(self, dir_path: Path) -> int:
        """获取目录大小（字节）"""
        total = 0
        for item in dir_path.rglob('*'):
            if item.is_file():
                total += item.stat().st_size
        return total
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f}KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f}MB"
        else:
            return f"{size/(1024*1024*1024):.1f}GB"


def main():
    parser = argparse.ArgumentParser(description='Shorts-Fission 缓存清理')
    parser.add_argument('--dry-run', action='store_true', help='只显示将删除的内容，不实际删除')
    parser.add_argument('--max-age-hours', type=int, default=24, help='最大保留时间（小时），默认24小时')
    args = parser.parse_args()
    
    cleaner = CacheCleaner(dry_run=args.dry_run, max_age_hours=args.max_age_hours)
    stats = cleaner.clean_all()
    
    # 输出统计
    print("\n📊 清理统计:")
    print(f"  PNG 序列清理: {stats['png_cleaned']} 个目录")
    print(f"  视频文件清理: {stats['video_cleaned']} 个文件")
    print(f"  释放空间: {stats['size_cleaned'] / (1024*1024):.1f} MB")
    print(f"  错误数: {stats['errors']}")
    
    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
