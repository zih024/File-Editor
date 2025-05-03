from fastapi import FastAPI
from .routers import auth
from .routers import users
from .routers import files

app = FastAPI()


@app.get("/")
async def health_check():
    return "ok"

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
