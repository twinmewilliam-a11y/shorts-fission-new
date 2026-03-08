# backend/app/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # video_id -> list of websocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, video_id: int):
        await websocket.accept()
        if video_id not in self.active_connections:
            self.active_connections[video_id] = []
        self.active_connections[video_id].append(websocket)

    def disconnect(self, websocket: WebSocket, video_id: int):
        if video_id in self.active_connections:
            self.active_connections[video_id].remove(websocket)
            if not self.active_connections[video_id]:
                del self.active_connections[video_id]

    async def send_progress(self, video_id: int, data: dict):
        """Send progress update to all connections for a video"""
        if video_id in self.active_connections:
            message = json.dumps(data)
            for connection in self.active_connections[video_id]:
                try:
                    await connection.send_text(message)
                except:
                    pass

    async def broadcast(self, message: str):
        """Broadcast to all connections"""
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_text(message)
                except:
                    pass

manager = ConnectionManager()

@router.websocket("/progress/{video_id}")
async def websocket_progress(websocket: WebSocket, video_id: int):
    """WebSocket endpoint for real-time progress updates"""
    await manager.connect(websocket, video_id)
    try:
        while True:
            # Keep connection alive, wait for any client message
            data = await websocket.receive_text()
            # Echo back or handle client commands
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, video_id)

# Helper function to be called from tasks
async def notify_variant_progress(
    video_id: int,
    current: int,
    total: int,
    variant_index: int = None,
    effects: list = None,
    status: str = "processing"
):
    """Send progress notification to all connected clients"""
    percent = int((current / total) * 100) if total > 0 else 0
    
    data = {
        "type": "variant_progress",
        "video_id": video_id,
        "current": current,
        "total": total,
        "percent": percent,
        "status": status
    }
    
    if variant_index is not None:
        data["current_variant"] = {
            "index": variant_index,
            "effects": effects or []
        }
    
    await manager.send_progress(video_id, data)
