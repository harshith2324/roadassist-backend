from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, mechanics, parts, requests, admin, vehicles

settings = get_settings()

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="""
## RoadAssist API

Connects stranded vehicle owners with nearby roadside mechanics in real time.

### Key features
- **Geospatial search** — find mechanics within X km using PostGIS
- **Parts inventory** — search for a specific part across all nearby mechanics
- **Job tracking** — full status trail from request → accepted → in_progress → completed
- **Triggers** — low-stock alerts and rating updates fire automatically in the DB
- **Stored procedures** — job acceptance is an atomic DB-side transaction
""",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(mechanics.router)
app.include_router(parts.router)
app.include_router(requests.router)
app.include_router(vehicles.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "RoadAssist API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
