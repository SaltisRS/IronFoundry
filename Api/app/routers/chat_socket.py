import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..modules.redis_client import RedisClient


router = APIRouter()


class WSConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.redis_client = RedisClient()
    
    async def connect_redis(self):
        await self.redis_client.connect()
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await websocket.send_text({"message_type": "ToClanChat",
                                   "message": 
                                       {"sender": "IronFoundry",
                                        "message": "Any messages in clan-chat are now shared to discord!"
                                        }
                                   })
        await self.connect_redis()
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
            
    async def get_online(self):
        await self.broadcast("Checking Online Status")
        return len(self.active_connections)

manager = WSConnectionManager()

@router.websocket("/")
async def ws_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
        
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await websocket.close()

async def redis_hook():
    async with manager.redis_client.subscribe("chat-send") as subscriber:
        async for event in subscriber:
            await manager.broadcast(event)