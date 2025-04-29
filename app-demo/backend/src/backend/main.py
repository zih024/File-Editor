from fastapi import FastAPI
from .routers import auth
from .database import init_db

app = FastAPI()

@app.on_event('startup')
async def startup_db_client():
    init_db()

@app.get("/")
async def health_check():
    return "ok"

app.include_router(auth.router)
