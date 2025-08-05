from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.users import router as users_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

