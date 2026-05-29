from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.reviews import router as reviews_router
from app.api.routes.webhooks import router as webhooks_router
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
app.include_router(webhooks_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(loc) for loc in err.get("loc", []) if loc != "body"),
            "message": err.get("msg", "参数校验失败"),
            "type": err.get("type", "validation_error"),
        }
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"message": "请求参数不合法", "errors": errors})


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
