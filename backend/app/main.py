from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.reviews import router as reviews_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AI PR Review 助手",
    description="基于 GitHub PR 与 LLM 的智能代码评审工具",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviews_router)


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
