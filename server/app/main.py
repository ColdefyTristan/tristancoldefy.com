from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.routers.auth import router as auth_router
from app.routers.familledle import router as familledle_router
from app.routers.mtg import router as mtg_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="My API", lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        payload = exc.detail
    else:
        payload = {"code": "HTTP_ERROR", "message": str(exc.detail), "fields": {}}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    fields = {}
    for err in exc.errors():
        loc = err.get("loc", [])
        if loc and loc[0] in ("body", "query", "path"):
            key = ".".join(str(x) for x in loc[1:])
        else:
            key = ".".join(str(x) for x in loc)
        fields[key] = "invalid"
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Invalid request.",
            "fields": fields,
        },
    )


app.include_router(auth_router)
app.include_router(familledle_router)
app.include_router(mtg_router)
