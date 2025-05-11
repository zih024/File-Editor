from fastapi import (APIRouter, WebSocket, WebSocketDisconnect, status, Depends)
import jwt
from typing import Annotated
from backend.database import db_dependency
from backend.routers.auth import get_user, TokenData
from backend.routers.auth import SECRET_KEY, ALGORITHM
from backend.models import User
import json



router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket, code: int = status.WS_1000_NORMAL_CLOSURE):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            await websocket.close(code=code)
    async def send_message(self, message: str, websocket: WebSocket):
        # Send start chunk
        await websocket.send_text(json.dumps({
            "message_id": "1",
            "type": "start"
        }))
        
        # Send content chunk
        await websocket.send_text(json.dumps({
            "message_id": "1",
            "type": "chunk",
            "content": message
        }))
        
        # Send end chunk
        await websocket.send_text(json.dumps({
            "message_id": "1",
            "type": "end"
        }))
    

manager = ConnectionManager()

async def ws_get_current_user(
    websocket: WebSocket,
    db: db_dependency,
):
    auth_token = websocket.cookies.get("auth_token")
    print(auth_token)
    if not auth_token:
        await manager.disconnect(websocket, status.WS_1008_POLICY_VIOLATION)
        return None

    try:
        payload = jwt.decode(auth_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(username)
        if username is None:
            await manager.disconnect(websocket, status.WS_1008_POLICY_VIOLATION)
            return None
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        await manager.disconnect(websocket, status.WS_1008_POLICY_VIOLATION)
        return None

    user = get_user(db, token_data.username)
    if user is None:
        await manager.disconnect(websocket, status.WS_1008_POLICY_VIOLATION)
        return None

    return user
        

@router.websocket("/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: Annotated[User, Depends(ws_get_current_user)],
):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_message(data + " user: " + current_user.name, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

