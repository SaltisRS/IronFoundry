from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from cachetools import TTLCache
import asyncio

app = FastAPI(debug=True)

VERIFICATION_CODE = "IF"

connected_clients: List[WebSocket] = []

message_cache = TTLCache(maxsize=512, ttl=60)

class ChatPayload(BaseModel):
    clanName: str
    sender: str
    message: str
    rank: Optional[str] = None
    iconId: Optional[int] = None
    isLeagueWorld: Optional[bool] = False


class WebSocketMessage(BaseModel):
    message_type: str
    message: Dict[str, Any]

def make_message_key(payload: ChatPayload) -> str:
    return f"{payload.clanName}:{payload.sender}:{payload.message}"


# --- WebSocket endpoint for Runelite clients to connect to receive messages ---

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


@app.get("/send")
async def send_clan_chats(
    entries: List[ChatPayload],
    verification_code: str = Header(..., alias="verification-code")
):
    if verification_code != VERIFICATION_CODE:
        raise HTTPException(status_code=403, detail="Invalid verification code")

    new_entries = []

    for entry in entries:
        key = make_message_key(entry)
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

async def forward_to_discord_bot(chat_payload: ChatPayload):
    # TODO: Implement actual forwarding here.
    #   await httpx.post("https://discordbot/api/send", json=chat_payload.dict())
    print(f"Forwarding to Discord bot: {chat_payload}")
