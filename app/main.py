import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, mechanics, parts, requests, admin, vehicles

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.middleware("http")
async def catch_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"detail": str(e), "trace": traceback.format_exc()})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(mechanics.router)
app.include_router(parts.router)
app.include_router(requests.router)
app.include_router(vehicles.router)
app.include_router(admin.router)

@app.get("/", tags=["Health"])
async def root():
    return {"service": "RoadAssist API", "version": settings.APP_VERSION, "status": "running"}

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
