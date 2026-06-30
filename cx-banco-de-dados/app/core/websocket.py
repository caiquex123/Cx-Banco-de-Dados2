from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket = None):
        if user_id in self.active_connections:
            if websocket:
                self.active_connections[user_id].remove(websocket)
            else:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        message_str = json.dumps(message)
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(message_str)
                except:
                    # Connection might be closed
                    pass

    async def broadcast_to_user(self, message: dict, user_id: int):
        """Broadcast message to specific user"""
        message_str = json.dumps(message)
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_str)
                except:
                    pass

manager = ConnectionManager()
