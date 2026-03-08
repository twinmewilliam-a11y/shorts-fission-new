# backend/app/services/downloader.py
"""
视频下载服务 - 支持 YouTube/TikTok 单视频、批量下载、实时监控
支持通过 yt-dlp-api 代理服务下载（更稳定）
"""
import asyncio
import subprocess
import json
import os
import re
import httpx
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

# yt-dlp-api 服务地址
YT_DLP_API_URL = os.getenv("YT_DLP_API_URL", "http://localhost:8001")

class VideoDownloader:
    """视频下载器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.proxy_url = config.get('proxy_url')
        self.proxy_enabled = config.get('proxy_enabled', False)
        self.yt_dlp_path = config.get('yt_dlp_path', 'yt-dlp')
        self.max_concurrent = config.get('max_concurrent_downloads', 3)
        self.use_api = config.get('use_yt_dlp_api', True)  # 默认使用API
    
    # ==================== 单视频下载 ====================
    
    def download_single(
        self, 
        url: str, 
        output_dir: str,
        no_watermark: bool = True
    ) -> Dict:
        """下载单个视频"""
        # 检测平台
        platform = self._detect_platform(url)
        
        # 生成输出路径
        output_template = os.path.join(output_dir, '%(id)s.%(ext)s')
        
        # 构建 yt-dlp 命令
        cmd = self._build_download_command(url, output_template, no_watermark)
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                # 解析下载信息
                info = self._parse_download_info(url, output_dir)
                return {
                    'success': True,
                    'platform': platform,
                    'video_id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'file_path': info.get('file_path'),
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'platform': platform,
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '下载超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _build_download_command(
        self, 
        url: str, 
        output_template: str,
        no_watermark: bool
    ) -> List[str]:
        """构建 yt-dlp 下载命令
        
        默认下载 720p 格式，合并为 MP4
        
        格式选择优先级：
        1. 720p MP4 视频 + 最佳音频 → 合并 MP4
        2. 720p 任意格式 → 合并 MP4
        3. 最佳可用格式 → 合并 MP4
        """
        cmd = [
            self.yt_dlp_path,
            # 格式选择：720p优先，合并为MP4
            '-f', 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720][ext=mp4]/best[height<=720]/best',
            '-o', output_template,
            '--no-playlist',
            '--write-info-json',
            '--write-thumbnail',
            '--no-mtime',
            '--no-check-certificate',
            '--geo-bypass',
            # 合并输出格式：强制 MP4
            '--merge-output-format', 'mp4',
            # 用户代理
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--add-header', 'Accept-Language:en-US,en;q=0.9',
        ]
        
        # YouTube 特殊处理
        if 'youtube.com' in url or 'youtu.be' in url:
            # 使用多种 player_client 绕过限制
            cmd.extend([
                '--remote-components', 'ejs:github',  # 解决 JS challenge
                '--extractor-args', 'youtube:player_client=web',
                '--sleep-requests', '1',  # 请求间隔，避免被限制
            ])
        
        # TikTok 无水印
        if no_watermark and 'tiktok' in url:
            cmd.append('--no-mark-watched')
        
        # 代理 - 使用 SOCKS5 代理
        if self.proxy_enabled and self.proxy_url:
            # 添加 SOCKS5 代理支持
            cmd.extend([
                '--proxy', self.proxy_url,
                '--socket-timeout', '30',
            ])
        
        # Cookies 文件 - 使用项目目录下的 cookies.txt
        cookies_file = '/root/.openclaw/workspace/projects/shorts-fission/backend/cookies.txt'
        if os.path.exists(cookies_file):
            cmd.extend(['--cookies', cookies_file])
            logger.info(f"使用 cookies 文件: {cookies_file}")
        
        cmd.append(url)
        return cmd
    
    def _detect_platform(self, url: str) -> str:
        """检测视频平台"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'tiktok.com' in url:
            return 'tiktok'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        elif 'instagram.com' in url:
            return 'instagram'
        else:
            return 'unknown'
    
    def _parse_download_info(self, url: str, output_dir: str) -> Dict:
        """解析下载的视频信息"""
        # 尝试读取 info.json
        info_files = list(Path(output_dir).glob('*.info.json'))
        if info_files:
            with open(info_files[0], 'r', encoding='utf-8') as f:
                info = json.load(f)
                # 查找视频文件
                video_files = list(Path(output_dir).glob(f"{info.get('id', '')}.*"))
                video_file = next((f for f in video_files if f.suffix in ['.mp4', '.webm', '.mkv']), None)
                
                # 获取分辨率信息
                resolution = None
                if video_file:
                    resolution = self._get_video_resolution(str(video_file))
                
                # 从 info.json 获取分辨率作为备选
                if not resolution and 'height' in info:
                    height = info.get('height')
                    if height:
                        resolution = f"{height}p"
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'description': info.get('description'),
                    'file_path': str(video_file) if video_file else None,
                    'resolution': resolution,
                }
        
        return {}
    
    def _get_video_resolution(self, video_path: str) -> Optional[str]:
        """使用 ffprobe 获取视频分辨率"""
        try:
            import subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                 '-show_entries', 'stream=height', '-of', 'csv=p=0', video_path],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                height = int(result.stdout.strip())
                return f"{height}p"
        except Exception as e:
            logger.warning(f"获取视频分辨率失败: {e}")
        return None
    
    # ==================== 批量下载 ====================
    
    def get_account_videos(
        self, 
        account_url: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """获取账号下所有视频列表"""
        cmd = [
            self.yt_dlp_path,
            '--flat-playlist',
            '--dump-json',
        ]
        
        if self.proxy_enabled and self.proxy_url:
            cmd.extend(['--proxy', self.proxy_url])
        
        cmd.append(account_url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            videos = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        video = {
                            'id': data.get('id'),
                            'title': data.get('title'),
                            'url': data.get('url') or f"https://www.youtube.com/watch?v={data.get('id')}",
                            'upload_date': data.get('upload_date'),
                        }
                        videos.append(video)
                    except json.JSONDecodeError:
                        continue
            
            # 按日期筛选
            if start_date or end_date:
                videos = self._filter_by_date(videos, start_date, end_date)
            
            return videos
            
        except Exception as e:
            logger.error(f"获取账号视频列表失败: {e}")
            return []
    
    def _filter_by_date(
        self, 
        videos: List[Dict], 
        start_date: Optional[str], 
        end_date: Optional[str]
    ) -> List[Dict]:
        """按日期筛选视频"""
        filtered = []
        
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) if end_date else None
        
        for video in videos:
            if video.get('upload_date'):
                try:
                    upload = datetime.strptime(video['upload_date'], "%Y%m%d")
                    if start and upload < start:
                        continue
                    if end and upload > end:
                        continue
                    filtered.append(video)
                except ValueError:
                    continue
        
        return filtered
    
    def batch_download(
        self,
        account_url: str,
        output_dir: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_count: int = 50
    ) -> Dict:
        """批量下载账号视频"""
        # 获取视频列表
        videos = self.get_account_videos(account_url, start_date, end_date)
        videos = videos[:max_count]  # 限制数量
        
        results = {
            'total': len(videos),
            'success': 0,
            'failed': 0,
            'videos': []
        }
        
        for video in videos:
            result = self.download_single(video['url'], output_dir)
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            results['videos'].append({
                'id': video['id'],
                'title': video.get('title'),
                **result
            })
        
        return results


class AccountMonitor:
    """账号实时监控服务"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.downloader = VideoDownloader(config)
        self.check_interval = config.get('monitor_check_interval', 300)  # 5分钟
        self.monitored_accounts: Dict[str, Dict] = {}
        self.downloaded_videos: set = set()
        self._load_state()
    
    def _load_state(self):
        """加载已下载视频状态"""
        state_file = Path(self.config.get('data_dir', './data')) / 'downloaded_videos.json'
        if state_file.exists():
            with open(state_file, 'r') as f:
                data = json.load(f)
                self.downloaded_videos = set(data.get('downloaded', []))
    
    def _save_state(self):
        """保存已下载视频状态"""
        state_file = Path(self.config.get('data_dir', './data')) / 'downloaded_videos.json'
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump({'downloaded': list(self.downloaded_videos)}, f)
    
    def add_account(self, account_url: str, account_id: str):
        """添加监控账号"""
        self.monitored_accounts[account_url] = {
            'account_id': account_id,
            'added_at': datetime.now().isoformat(),
            'enabled': True
        }
    
    def remove_account(self, account_url: str):
        """移除监控账号"""
        if account_url in self.monitored_accounts:
            del self.monitored_accounts[account_url]
    
    def is_downloaded(self, video_id: str) -> bool:
        """检查视频是否已下载"""
        return video_id in self.downloaded_videos
    
    def mark_downloaded(self, video_id: str):
        """标记视频已下载"""
        self.downloaded_videos.add(video_id)
        self._save_state()
    
    async def check_new_videos(self, account_url: str) -> List[Dict]:
        """检查账号是否有新视频"""
        videos = self.downloader.get_account_videos(account_url)
        
        new_videos = []
        for video in videos[:20]:  # 只检查最近20个
            if not self.is_downloaded(video['id']):
                new_videos.append(video)
        
        return new_videos
    
    async def start_monitoring(self, callback=None):
        """启动监控循环"""
        logger.info("启动账号监控服务...")
        
        while True:
            for account_url, account_info in self.monitored_accounts.items():
                if not account_info.get('enabled'):
                    continue
                
                try:
                    new_videos = await self.check_new_videos(account_url)
                    
                    for video in new_videos:
                        logger.info(f"发现新视频: {video.get('title', video['id'])}")
                        
                        # 下载视频
                        output_dir = Path(self.config.get('videos_dir', './data/videos'))
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        result = self.downloader.download_single(
                            video['url'], 
                            str(output_dir)
                        )
                        
                        if result['success']:
                            self.mark_downloaded(video['id'])
                            
                            # 回调通知
                            if callback:
                                await callback(account_info['account_id'], video, result)
                        else:
                            logger.error(f"下载失败: {result.get('error')}")
                
                except Exception as e:
                    logger.error(f"检查账号 {account_url} 时出错: {e}")
            
            # 等待下一次检查
            await asyncio.sleep(self.check_interval)


# ==================== yt-dlp-api 下载器 ====================

class YtDlpApiClient:
    """yt-dlp-api 服务客户端 - 支持同步和异步调用"""
    
    def __init__(self, base_url: str = YT_DLP_API_URL):
        self.base_url = base_url
    
    def download_video_sync(
        self, 
        url: str, 
        output_dir: str,
        format_type: str = "720p"
    ) -> Dict:
        """同步下载视频 - 用于 Celery 任务"""
        import httpx
        import shutil
        
        try:
            # 使用同步客户端
            with httpx.Client(timeout=600.0) as client:
                # 创建下载任务
                response = client.post(
                    f"{self.base_url}/download",
                    json={
                        "url": url,
                        "format": format_type
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"API请求失败: {response.text}"
                    }
                
                task = response.json()
                task_id = task["task_id"]
                
                # 等待下载完成
                max_wait = 600  # 10分钟
                waited = 0
                interval = 2
                
                while waited < max_wait:
                    import time
                    time.sleep(interval)
                    waited += interval
                    
                    # 检查任务状态
                    status_response = client.get(
                        f"{self.base_url}/tasks/{task_id}"
                    )
                    
                    if status_response.status_code != 200:
                        continue
                    
                    status = status_response.json()
                    
                    if status["status"] == "completed":
                        # 复制文件到目标目录
                        if status.get("file_path"):
                            src_path = Path(status["file_path"])
                            dst_path = Path(output_dir) / src_path.name
                            shutil.copy2(src_path, dst_path)
                            
                            return {
                                "success": True,
                                "video_id": status.get("url", "").split("/")[-1],
                                "file_path": str(dst_path),
                                "file_size": status.get("file_size"),
                                "resolution": status.get("resolution"),
                            }
                    
                    elif status["status"] == "failed":
                        return {
                            "success": False,
                            "error": status.get("error", "下载失败")
                        }
                
                return {
                    "success": False,
                    "error": "下载超时"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_video(
        self, 
        url: str, 
        output_dir: str,
        format_type: str = "720p"
    ) -> Dict:
        """通过 yt-dlp-api 下载视频"""
        try:
            # 创建下载任务
            response = await self.client.post(
                f"{self.base_url}/download",
                json={
                    "url": url,
                    "format": format_type
                }
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API请求失败: {response.text}"
                }
            
            task = response.json()
            task_id = task["task_id"]
            
            # 等待下载完成
            max_wait = 600  # 10分钟
            waited = 0
            interval = 2
            
            while waited < max_wait:
                await asyncio.sleep(interval)
                waited += interval
                
                # 检查任务状态
                status_response = await self.client.get(
                    f"{self.base_url}/tasks/{task_id}"
                )
                
                if status_response.status_code != 200:
                    continue
                
                status = status_response.json()
                
                if status["status"] == "completed":
                    # 复制文件到目标目录
                    if status.get("file_path"):
                        import shutil
                        src_path = Path(status["file_path"])
                        dst_path = Path(output_dir) / src_path.name
                        shutil.copy2(src_path, dst_path)
                        
                        return {
                            "success": True,
                            "video_id": status.get("url", "").split("/")[-1],
                            "file_path": str(dst_path),
                            "file_size": status.get("file_size"),
                            "resolution": status.get("resolution"),
                        }
                
                elif status["status"] == "failed":
                    return {
                        "success": False,
                        "error": status.get("error", "下载失败")
                    }
            
            return {
                "success": False,
                "error": "下载超时"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_video_info(self, url: str) -> Dict:
        """获取视频信息"""
        try:
            response = await self.client.get(
                f"{self.base_url}/info",
                params={"url": url}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def update_cookies(self, cookies_content: str) -> Dict:
        """更新cookies"""
        try:
            response = await self.client.post(
                f"{self.base_url}/cookies",
                data=cookies_content
            )
            
            return response.json()
            
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
