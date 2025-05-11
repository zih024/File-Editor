import asyncio
import os
import uuid
import jwt
from typing import Annotated, Any
from fastapi import (
    APIRouter,
    WebSocket,
    status,
    Depends,
    WebSocketDisconnect,
)

from backend.database import db_dependency
from backend.routers.auth import get_user, TokenData
from backend.routers.auth import SECRET_KEY, ALGORITHM
from backend.models import User
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(
        self, websocket: WebSocket, code: int = status.WS_1000_NORMAL_CLOSURE
    ):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            try:
                await websocket.close(code=code)
            except RuntimeError:
                # WebSocket already closed
                pass

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_json(self, data: Any, websocket: WebSocket):
        await websocket.send_json(data)


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
    current_user: Annotated[User | None, Depends(ws_get_current_user)],
):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            stream = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": data},
                ],
                stream=True,
            )

            message_id = str(uuid.uuid4())

            await manager.send_json(
                {
                    "message_id": message_id,
                    "type": "start",
                },
                websocket,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    logger.info(chunk.choices[0].delta.content)
                    content = chunk.choices[0].delta.content
                    await manager.send_json(
                        {
                            "message_id": message_id,
                            "type": "chunk",
                            "content": content,
                        },
                        websocket,
                    )
                    await asyncio.sleep(0.01)

            await manager.send_json(
                {
                    "message_id": message_id,
                    "type": "end",
                },
                websocket,
            )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
