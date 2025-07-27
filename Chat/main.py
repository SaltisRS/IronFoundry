from typing import AsyncGenerator
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import asyncio
import uuid

from Chat.chat_server import ChatServer, Connect, Disconnect, BroadcastFromClient, BroadcastFromDiscord

ALLOWED_CODE = "IF"
chat_server = ChatServer(allowed_code=ALLOWED_CODE)

async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:

    run_task = asyncio.create_task(chat_server.run())
    yield

    await chat_server.shutdown()
    run_task.cancel()
    try:
        await run_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)


@app.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket, verification_code: str):
    await websocket.accept()
    conn_id = str(uuid.uuid4())
    await chat_server.cmd_queue.put(Connect(conn_id, websocket, verification_code))

    try:
        while True:
            data = await websocket.receive_text()
            await chat_server.cmd_queue.put(BroadcastFromClient(conn_id, data))
    except WebSocketDisconnect:
        await chat_server.cmd_queue.put(Disconnect(conn_id))


class DiscordPayload(BaseModel):
    sender: str
    message: str
    code: str


@app.post("/publish")
async def send_discord_message(payload: DiscordPayload):
    if payload.code != ALLOWED_CODE:
        raise HTTPException(status_code=403, detail="Invalid verification code")

    await chat_server.cmd_queue.put(BroadcastFromDiscord(payload.sender, payload.message, payload.code))
    return {"status": "ok"}
