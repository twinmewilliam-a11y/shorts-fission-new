#!/usr/bin/env python3
"""
测试下载功能
"""
import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/projects/shorts-fission/backend')

from app.services.downloader import VideoDownloader

def test_single_download():
    """测试单视频下载"""
    downloader = VideoDownloader({
        'videos_dir': '/root/.openclaw/workspace/projects/shorts-fission/data/videos',
    })
    
    # 测试 YouTube 短视频
    test_url = "https://www.youtube.com/shorts/abc123"  # 替换为真实URL
    
    print("测试下载功能...")
    print(f"URL: {test_url}")
    print(f"平台检测: {downloader._detect_platform(test_url)}")
    
    # 获取视频信息
    videos = downloader.get_account_videos("https://www.youtube.com/@MLB")
    print(f"获取到 {len(videos)} 个视频")
    
    if videos:
        print(f"第一个视频: {videos[0]}")

if __name__ == "__main__":
    test_single_download()
