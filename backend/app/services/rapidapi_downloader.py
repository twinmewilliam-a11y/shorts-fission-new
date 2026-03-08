"""
RapidAPI YouTube 下载器
使用 yt-api (https://rapidapi.com/ytjar/api/yt-api)
"""
import requests
import os
from typing import Dict, Optional
from pathlib import Path
import subprocess
from loguru import logger


class RapidAPIDownloader:
    """RapidAPI YouTube 下载器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.api_host = "yt-api.p.rapidapi.com"
        self.base_url = f"https://{self.api_host}"
        
        if not self.api_key:
            raise ValueError("RapidAPI Key 未设置。请设置 RAPIDAPI_KEY 环境变量或直接传入 api_key")
    
    def _get_headers(self) -> Dict:
        """获取 API 请求头"""
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
    
    def get_video_info(self, video_id: str) -> Dict:
        """
        获取视频信息
        
        Args:
            video_id: YouTube 视频 ID (如: dQw4w9WgXcQ)
        
        Returns:
            视频信息，包含可用的下载格式
        """
        url = f"{self.base_url}/dl"
        
        # 支持多种 ID 格式
        if "youtube.com" in video_id or "youtu.be" in video_id:
            # 提取视频 ID
            if "v=" in video_id:
                video_id = video_id.split("v=")[1].split("&")[0]
            elif "youtu.be/" in video_id:
                video_id = video_id.split("youtu.be/")[1].split("?")[0]
            elif "/shorts/" in video_id:
                video_id = video_id.split("/shorts/")[1].split("?")[0]
        
        querystring = {"id": video_id}
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=querystring)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取视频信息失败: {e}")
            return {"error": str(e)}
    
    def download_video(
        self, 
        video_id: str, 
        output_path: str,
        quality: str = "720p",
        format_type: str = "mp4"
    ) -> Dict:
        """
        下载视频
        
        Args:
            video_id: YouTube 视频 ID 或完整 URL
            output_path: 输出文件路径
            quality: 期望质量 (720p, 1080p, best 等)
            format_type: 格式 (mp4, webm 等)
        
        Returns:
            下载结果
        """
        # 获取视频信息
        info = self.get_video_info(video_id)
        
        if "error" in info:
            return {"success": False, "error": info["error"]}
        
        # 解析视频 ID
        if "youtube.com" in video_id or "youtu.be" in video_id:
            if "v=" in video_id:
                vid = video_id.split("v=")[1].split("&")[0]
            elif "youtu.be/" in video_id:
                vid = video_id.split("youtu.be/")[1].split("?")[0]
            elif "/shorts/" in video_id:
                vid = video_id.split("/shorts/")[1].split("?")[0]
            else:
                vid = video_id
        else:
            vid = video_id
        
        # 查找最佳格式
        download_url = None
        actual_quality = None
        
        # 检查是否有格式列表
        if "formats" in info:
            formats = info["formats"]
            
            # 按质量排序
            quality_order = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360, "240p": 240}
            target_height = quality_order.get(quality, 720)
            
            # 查找最接近目标质量的格式
            best_format = None
            best_height_diff = float('inf')
            
            for fmt in formats:
                if fmt.get("ext") == format_type or format_type == "best":
                    fmt_height = fmt.get("height", 0)
                    height_diff = abs(fmt_height - target_height)
                    
                    # 优先选择不低于目标质量的
                    if fmt_height >= target_height and height_diff < best_height_diff:
                        best_format = fmt
                        best_height_diff = height_diff
                    elif best_format is None and height_diff < best_height_diff:
                        best_format = fmt
                        best_height_diff = height_diff
            
            if best_format:
                download_url = best_format.get("url")
                actual_quality = f"{best_format.get('height', 'unknown')}p"
        
        # 如果没有找到格式，尝试使用默认链接
        if not download_url and "link" in info:
            download_url = info["link"]
            actual_quality = info.get("quality", "unknown")
        
        if not download_url:
            return {
                "success": False, 
                "error": "未找到可用的下载链接",
                "info": info
            }
        
        # 下载文件
        try:
            logger.info(f"开始下载视频 {vid}, 质量: {actual_quality}")
            
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 写入文件
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(output_path)
            
            logger.info(f"下载完成: {output_path}, 大小: {file_size / 1024 / 1024:.2f} MB")
            
            return {
                "success": True,
                "video_id": vid,
                "title": info.get("title", ""),
                "quality": actual_quality,
                "file_path": output_path,
                "file_size": file_size,
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
            }
            
        except Exception as e:
            logger.error(f"下载失败: {e}")
            return {"success": False, "error": str(e)}


# 兼容旧接口的函数
def download_with_rapidapi(
    url: str, 
    output_dir: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    使用 RapidAPI 下载视频的便捷函数
    
    Args:
        url: YouTube URL
        output_dir: 输出目录
        api_key: RapidAPI Key (可选，默认从环境变量读取)
    
    Returns:
        下载结果
    """
    try:
        downloader = RapidAPIDownloader(api_key)
        
        # 提取视频 ID
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        elif "/shorts/" in url:
            video_id = url.split("/shorts/")[1].split("?")[0]
        else:
            video_id = url
        
        output_path = os.path.join(output_dir, f"{video_id}.mp4")
        
        return downloader.download_video(url, output_path, quality="720p")
        
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python rapidapi_downloader.py <youtube_url> [api_key]")
        sys.exit(1)
    
    url = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = download_with_rapidapi(url, "./downloads", api_key)
    print(result)
