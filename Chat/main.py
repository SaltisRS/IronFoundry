from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, Request
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from cachetools import TTLCache
import asyncio
from loguru import logger

app = FastAPI(debug=True)

VERIFICATION_CODE = "IF"

connected_clients: List[WebSocket] = []

message_cache = TTLCache(maxsize=512, ttl=60)

class ChatEntry(BaseModel):
    clan_name: str
    sender: str
    message: str
    rank: Optional[str] = None
    icon_id: Optional[int] = None
    is_league_world: Optional[bool] = False
    

class WebSocketMessage(BaseModel):
    message_type: str
    message: Dict[str, Any]

@app.websocket("/recieve")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    # Send connected message on connect
    connected_message = {
        "message_type": "ToClanChat",
        "message": {
            "sender": "System",
            "message": "Connected to IF Chat"
        }
    }

    await websocket.send_json(connected_message)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


@app.post("/send")
async def send_clan_chats(
    request: Request,
    verification_code: str = Header(..., alias="verification-code")):
    
    if verification_code != VERIFICATION_CODE:
        raise HTTPException(status_code=403, detail="Invalid verification code")

    data = await request.json()
    
    entries: List[ChatEntry] = []
    
    logger.info(data)
    for key, value in data.items():
        if key.isdigit():
            try:
                entry = ChatEntry.model_validate(value)
                entries.append(entry)
            except Exception as e:
                logger.error(f"Failed to parse entry at index {key}: {e}")

    new_entries = []
    for entry in entries:
        key = f"{entry.clan_name}:{entry.sender}:{entry.message}"
        if key in message_cache:
            continue
        message_cache[key] = True
        new_entries.append(entry)

    for entry in new_entries:
        asyncio.create_task(forward_to_discord_bot(entry))

    return {"received": len(entries), "forwarded": len(new_entries)}


@app.post("/publish")
async def discord_to_runelite(
    payload: WebSocketMessage,
    verification_code: str = Header(..., alias="verification-code")
):
    if verification_code != VERIFICATION_CODE:
        raise HTTPException(status_code=403, detail="Invalid verification code")

    disconnected = []
    for ws in connected_clients:
        try:
            await ws.send_json(payload.model_dump())
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        connected_clients.remove(ws)

    return {"status": "broadcasted", "clients": len(connected_clients)}


# --- Stub: forward message to Discord bot ---

async def forward_to_discord_bot(entry: ChatEntry):
    # TODO: Implement actual forwarding here.
    #   await httpx.post("https://discordbot/api/send", json=chat_payload.dict())
    print(f"Forwarding to Discord bot: {entry.__repr__()}")
