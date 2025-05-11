from fastapi import FastAPI
from .routers import auth
from .routers import users
from .routers import files
from .routers import chat
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    logger.info("Health check")
    return "ok"

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(chat.router)