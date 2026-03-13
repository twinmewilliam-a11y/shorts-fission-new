# backend/app/services/scrapling_downloader.py
"""
Scrapling 下载服务 - 使用 Scrapling 绕过反爬保护
支持 YouTube/TikTok 等平台的无 cookies 下载
"""
import subprocess
import json
import os
import re
from pathlib import Path
from typing import Dict, Optional
from loguru import logger

# 尝试导入 Scrapling
try:
    from scrapling.fetchers import Fetcher, StealthyFetcher, StealthySession
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False
    logger.warning("Scrapling 未安装，将使用传统下载方式")


class ScraplingDownloader:
    """基于 Scrapling 的下载器 - 绕过 Cloudflare 等反爬保护"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.headless = config.get('headless', True)
        self.use_stealth = config.get('use_stealth', True)
        self.yt_dlp_path = config.get('yt_dlp_path', 'yt-dlp')
        self.cookies_file = config.get('cookies_file')  # cookies 文件路径
        
    def is_available(self) -> bool:
        """检查 Scrapling 是否可用"""
        return SCRAPLING_AVAILABLE
    
    def get_page_content(self, url: str, use_stealth: bool = None) -> Optional[str]:
        """获取页面内容
        
        Args:
            url: 目标 URL
            use_stealth: 是否使用隐身模式（默认使用配置）
        
        Returns:
            页面 HTML 内容
            
        Note:
            Scrapling 的 page 对象是 Element 类型，获取完整 HTML 用 html_content
            而不是 html（html 返回的是元素片段）
        """
        if not SCRAPLING_AVAILABLE:
            logger.warning("Scrapling 不可用")
            return None
        
        use_stealth = use_stealth if use_stealth is not None else self.use_stealth
        
        try:
            if use_stealth:
                logger.info(f"使用隐身模式抓取: {url}")
                page = StealthyFetcher.fetch(url, headless=self.headless)
            else:
                logger.info(f"使用 HTTP 模式抓取: {url}")
                page = Fetcher.get(url, impersonate='chrome')
            
            # 使用 html_content 获取完整页面 HTML（Scrapling 设计：page 是 Element 类型）
            return page.html_content
            
        except Exception as e:
            logger.error(f"Scrapling 抓取失败: {e}")
            return None
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """获取视频信息（使用 yt-dlp + Scrapling cookies）
        
        Args:
            url: 视频 URL
        
        Returns:
            视频信息字典
        """
        if not SCRAPLING_AVAILABLE:
            return None
        
        try:
            # 使用 Scrapling 获取页面，提取必要信息
            if self.use_stealth:
                page = StealthyFetcher.fetch(url, headless=self.headless)
            else:
                page = Fetcher.get(url, impersonate='chrome')
            
            # 提取标题
            title = page.css('title::text').get() or ''
            
            return {
                'url': url,
                'title': title,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return None
    
    def download_with_yt_dlp(
        self, 
        url: str, 
        output_dir: str,
        format_id: str = None,
        no_watermark: bool = True,
        cookies_file: str = None
    ) -> Dict:
        """使用 yt-dlp 下载视频（Scrapling 已验证 URL 可访问）
        
        Args:
            url: 视频 URL
            output_dir: 输出目录
            format_id: 格式 ID（可选）
            no_watermark: 是否去水印
            cookies_file: cookies 文件路径（可选）
        
        Returns:
            下载结果
        """
        output_template = os.path.join(output_dir, '%(id)s.%(ext)s')
        
        cmd = [self.yt_dlp_path]
        
        # 格式选择
        if format_id:
            cmd.extend(['-f', format_id])
        else:
            cmd.extend(['-f', 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best'])
        
        cmd.extend([
            '--merge-output-format', 'mp4',
            '-o', output_template,
            '--no-playlist',
            '--no-warnings',
            '--newline',
            '--print', '%(filepath)s',
        ])
        
        # 添加 cookies 支持
        if cookies_file and os.path.exists(cookies_file):
            cmd.extend(['--cookies', cookies_file])
            logger.info(f"使用 cookies: {cookies_file}")
        
        # TikTok 去水印
        if no_watermark and 'tiktok.com' in url:
            # Scrapling 可以获取无水印版本
            pass
        
        cmd.append(url)
        
        try:
            logger.info(f"执行 yt-dlp: {' '.join(cmd[:5])}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                filepath = result.stdout.strip().split('\n')[-1]
                if os.path.exists(filepath):
                    return {
                        'success': True,
                        'filepath': filepath,
                        'filename': os.path.basename(filepath)
                    }
            
            return {
                'success': False,
                'error': result.stderr or '下载失败'
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '下载超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download(
        self, 
        url: str, 
        output_dir: str,
        format_id: str = None,
        no_watermark: bool = True,
        use_stealth: bool = None,
        cookies_file: str = None
    ) -> Dict:
        """下载视频
        
        Args:
            url: 视频 URL
            output_dir: 输出目录
            format_id: 格式 ID
            no_watermark: 去水印
            use_stealth: 使用隐身模式
            cookies_file: cookies 文件路径
        
        Returns:
            下载结果
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        use_stealth = use_stealth if use_stealth is not None else self.use_stealth
        cookies_file = cookies_file or self.cookies_file
        
        # 先用 Scrapling 验证 URL 可访问
        if SCRAPLING_AVAILABLE and use_stealth:
            logger.info("使用 Scrapling 验证 URL...")
            content = self.get_page_content(url, use_stealth=True)
            if content:
                logger.info("URL 验证通过，开始下载...")
        
        # 使用 yt-dlp 下载（支持 cookies）
        return self.download_with_yt_dlp(url, output_dir, format_id, no_watermark, cookies_file)


class ScraplingSession:
    """Scrapling Session 管理器 - 复用浏览器连接"""
    
    _instance = None
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.session = None
        self.headless = self.config.get('headless', True)
    
    @classmethod
    def get_instance(cls, config: Dict = None):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def __enter__(self):
        if SCRAPLING_AVAILABLE and self.config.get('use_session', False):
            self.session = StealthySession(headless=self.headless)
            self.session.__enter__()
        return self
    
    def __exit__(self, *args):
        if self.session:
            self.session.__exit__(*args)
            self.session = None
    
    def fetch(self, url: str) -> Optional[str]:
        """使用 Session 抓取页面
        
        Note:
            使用 html_content 获取完整页面 HTML（Scrapling 设计：page 是 Element 类型）
        """
        if not SCRAPLING_AVAILABLE:
            return None
        
        if self.session:
            page = self.session.fetch(url)
            return page.html_content
        else:
            page = StealthyFetcher.fetch(url, headless=self.headless)
            return page.html_content
