"""
进度管理工具函数模块

包含：
- update_stage_progress：更新阶段进度
- update_progress：更新任务进度

注意：这些函数主要用于内部进度管理
"""
from pathlib import Path
from loguru import logger

from app.config import settings


def update_stage_progress(video_id: int, stage: str, progress: int):
    """更新阶段进度到数据库"""
    try:
        import sqlite3
        db_path = Path(settings.DATA_DIR) / 'shorts_fission.db'
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("UPDATE videos SET variant_progress = ? WHERE id = ?", (progress, video_id))
        conn.commit()
        conn.close()
        logger.info(f"[阶段进度] {stage}: {progress}%")
    except Exception as e:
        logger.warning(f"[阶段进度] 更新失败: {e}")


def update_progress(video_id: int, progress: int, message: str = None):
    """更新任务进度"""
    try:
        import sqlite3
        db_path = Path(settings.DATA_DIR) / 'shorts_fission.db'
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 更新下载进度
        c.execute("UPDATE videos SET download_progress = ? WHERE id = ?", (progress, video_id))
        
        # 添加进度记录（可选）
        if message:
            c.execute("""
                INSERT INTO progress_logs (video_id, progress, message, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (video_id, progress, message))
        
        conn.commit()
        conn.close()
        
        if message:
            logger.info(f"[进度更新] {progress}%: {message}")
        
    except Exception as e:
        logger.warning(f"[进度更新] 失败: {e}")


# ==================== 导出 ====================

__all__ = [
    'update_stage_progress',
    'update_progress'
]