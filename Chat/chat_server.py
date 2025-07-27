import asyncio
from fastapi import WebSocket
from typing import Dict, Set
import hashlib
from loguru import logger

ConnId = str
Msg = str
VerificationCode = str


class Command:
    pass


class Connect(Command):
    def __init__(self, conn_id, websocket: WebSocket, code: VerificationCode):
        self.conn_id = conn_id
        self.websocket = websocket
        self.code = code


class Disconnect(Command):
    def __init__(self, conn_id: ConnId):
        self.conn_id = conn_id


class BroadcastFromClient(Command):
    def __init__(self, conn_id: ConnId, msg: Msg):
        self.conn_id = conn_id
        self.msg = msg


class BroadcastFromDiscord(Command):
    def __init__(self, sender: str, msg: Msg, code: VerificationCode):
        self.sender = sender
        self.msg = msg
        self.code = code


class ChatServer:
    def __init__(self, allowed_code: VerificationCode):
        self.allowed_code = allowed_code
        self.sessions: Dict[ConnId, WebSocket] = {}
        self.cmd_queue: asyncio.Queue[Command] = asyncio.Queue()
        self.recent_messages: Set[str] = set()

    async def run(self):
        while True:
            cmd = await self.cmd_queue.get()

            if isinstance(cmd, Connect):
                if cmd.code != self.allowed_code:
                    await cmd.websocket.close(code=1008)
                    logger.warning(f"Denied connection with invalid code: {cmd.code}")
                    continue

                self.sessions[cmd.conn_id] = cmd.websocket
                logger.info(f"[+] {cmd.conn_id} connected")

                try:
                    await cmd.websocket.send_json({
                        "message_type": "ToClanChat",
                        "message": {
                            "sender": "System",
                            "message": "Connected to: IF CC"
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to send welcome message to {cmd.conn_id}: {e}")


            elif isinstance(cmd, Disconnect):
                if cmd.conn_id in self.sessions:
                    del self.sessions[cmd.conn_id]
                    logger.info(f"[-] {cmd.conn_id} disconnected")

            elif isinstance(cmd, BroadcastFromClient):
                await self.broadcast("user", cmd.msg, skip=cmd.conn_id)

            elif isinstance(cmd, BroadcastFromDiscord):
                if cmd.code != self.allowed_code:
                    logger.info(f"[!] Invalid code from Discord: {cmd.code}")
                    continue

                msg_hash = self._hash(cmd.sender, cmd.msg)
                if msg_hash in self.recent_messages:
                    logger.info("[!] Duplicate message skipped.")
                    continue

                self.recent_messages.add(msg_hash)
                if len(self.recent_messages) > 1000:
                    self.recent_messages.pop()

                await self.broadcast(cmd.sender, cmd.msg)
    


    async def shutdown(self):
        logger.info("[!] Shutting down ChatServer...")

        await self.broadcast("System", "Stopping Chat Server")

        logger.info(f"[!] Final connected clients: {len(self.sessions)}")
        
        for conn_id, ws in list(self.sessions.items()):
            try:
                await ws.close(code=1001, reason="Server shutdown")
            except Exception as e:
                logger.info(f"Error closing websocket {conn_id}: {e}")

        self.sessions.clear()
        self.recent_messages.clear()


    async def broadcast(self, sender: str, msg: str, skip: ConnId = None):
        payload = {
            "message_type": "ToClanChat",
            "message": {
                "sender": sender,
                "message": msg
            }
        }

        to_remove = []

        for conn_id, ws in self.sessions.items():
            if conn_id == skip:
                continue
            try:
                await ws.send_json(payload)
            except Exception:
                to_remove.append(conn_id)

        for conn_id in to_remove:
            del self.sessions[conn_id]

    def _hash(self, sender: str, msg: str) -> str:
        return hashlib.sha256(f"{sender}:{msg}".encode()).hexdigest()
