from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="My API", lifespan=lifespan)


app.include_router(auth_router)
