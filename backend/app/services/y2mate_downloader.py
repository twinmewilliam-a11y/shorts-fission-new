"""
RapidAPI y2mate YouTube 下载器
支持 720p/1080p 高清下载
API: https://rapidapi.com/y2mate-youtube-video-and-mp3-downloader
"""
import requests
import os
from typing import Dict, Optional, List
from pathlib import Path
from loguru import logger


class Y2MateDownloader:
    """y2mate YouTube 下载器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.api_host = "y2mate-youtube-video-and-mp3-downloader.p.rapidapi.com"
        self.base_url = f"https://{self.api_host}/rapidapi-y2mate"
        
        if not self.api_key:
            raise ValueError("RapidAPI Key 未设置。请设置 RAPIDAPI_KEY 环境变量")
    
    def _get_headers(self) -> Dict:
        """获取 API 请求头"""
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
    
    def extract_video_id(self, url: str) -> str:
        """从 URL 提取视频 ID"""
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        elif "/shorts/" in url:
            return url.split("/shorts/")[1].split("?")[0]
        return url
    
    def get_video_info(self, url: str) -> Dict:
        """
        获取视频信息和可用格式
        
        Args:
            url: YouTube URL
        
        Returns:
            视频信息和格式列表
        """
        try:
            response = requests.get(
                self.base_url,
                headers=self._get_headers(),
                params={"url": url, "proxy": "0"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取视频信息失败: {e}")
            return {"error": str(e)}
    
    def get_available_qualities(self, info: Dict) -> List[Dict]:
        """获取可用的视频质量列表"""
        qualities = []
        for fmt in info.get("formats", []):
            height = fmt.get("height", 0)
            if height >= 360:  # 只返回 360p 及以上
                qualities.append({
                    "format_id": fmt.get("format_id"),
                    "quality": f"{height}p",
                    "height": height,
                    "width": fmt.get("width"),
                    "ext": fmt.get("ext"),
                    "resolution": fmt.get("resolution"),
                    "url": fmt.get("url")
                })
        # 按分辨率排序（从高到低）
        qualities.sort(key=lambda x: x["height"], reverse=True)
        return qualities
    
    def download_video(
        self, 
        url: str, 
        output_path: str,
        target_quality: str = "720p",
        max_quality: bool = False
    ) -> Dict:
        """
        下载视频
        
        Args:
            url: YouTube URL
            output_path: 输出文件路径
            target_quality: 目标质量 (720p, 1080p, best 等)
            max_quality: 是否下载最高可用质量
        
        Returns:
            下载结果
        """
        # 获取视频信息
        info = self.get_video_info(url)
        
        if "error" in info:
            return {"success": False, "error": info["error"]}
        
        video_id = self.extract_video_id(url)
        title = info.get("title", f"video_{video_id}")
        
        # 获取可用质量列表
        qualities = self.get_available_qualities(info)
        
        if not qualities:
            return {"success": False, "error": "未找到可用的视频格式"}
        
        # 选择最佳格式
        selected_format = None
        
        if max_quality:
            # 选择最高质量
            selected_format = qualities[0]
        else:
            # 解析目标质量
            target_height = int(target_quality.replace("p", "")) if "p" in target_quality else 720
            
            # 查找最接近目标质量的格式（不低于目标质量）
            for q in qualities:
                if q["height"] >= target_height:
                    selected_format = q
                    break
            
            # 如果没有找到，使用最高可用质量
            if not selected_format:
                selected_format = qualities[0]
        
        if not selected_format:
            return {"success": False, "error": "无法选择视频格式"}
        
        download_url = selected_format["url"]
        actual_quality = selected_format["quality"]
        
        # 下载文件
        try:
            logger.info(f"开始下载视频 {video_id}, 质量: {actual_quality}")
            
            # 检查是否是 HLS/m3u8 流
            if ".m3u8" in download_url or "manifest.googlevideo.com" in download_url:
                # 使用 ffmpeg 下载 HLS 流
                logger.info("检测到 HLS 流，使用 ffmpeg 下载")
                
                # 确保输出目录存在
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                
                # 使用 ffmpeg 下载 (按照 y2mate 文档)
                import subprocess
                cmd = [
                    "ffmpeg",
                    "-n",  # 不覆盖已存在文件
                    "-user_agent", "Mozilla/5.0 (Linux; Android 11; T8 Build/R01005) AppleWebKit/537.36",
                    "-i", download_url,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-preset", "veryfast",
                    "-y",  # 覆盖已存在文件
                    output_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode != 0:
                    logger.error(f"ffmpeg 下载失败: {result.stderr}")
                    return {"success": False, "error": f"ffmpeg 下载失败: {result.stderr[:200]}"}
                
            else:
                # 直接下载
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
                "video_id": video_id,
                "title": title,
                "quality": actual_quality,
                "resolution": selected_format["resolution"],
                "format": selected_format["ext"],
                "file_path": output_path,
                "file_size": file_size,
            }
            
        except Exception as e:
            logger.error(f"下载失败: {e}")
            return {"success": False, "error": str(e)}


# 便捷函数
def download_with_y2mate(
    url: str, 
    output_dir: str,
    api_key: Optional[str] = None,
    quality: str = "720p"
) -> Dict:
    """
    使用 y2mate 下载视频的便捷函数
    
    Args:
        url: YouTube URL
        output_dir: 输出目录
        api_key: RapidAPI Key (可选)
        quality: 目标质量 (720p, 1080p, best)
    
    Returns:
        下载结果
    """
    try:
        downloader = Y2MateDownloader(api_key)
        video_id = downloader.extract_video_id(url)
        output_path = os.path.join(output_dir, f"{video_id}.mp4")
        
        return downloader.download_video(url, output_path, target_quality=quality)
        
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python y2mate_downloader.py <youtube_url> [api_key]")
        sys.exit(1)
    
    url = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = download_with_y2mate(url, "./downloads", api_key, quality="720p")
    print(result)
