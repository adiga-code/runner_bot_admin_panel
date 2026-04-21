import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from auth import router as auth_router
from routers.users import router as users_router
from routers.logs import router as logs_router
from routers.workouts import router as workouts_router
from routers.analytics import router as analytics_router

app = FastAPI(title="28 Days Admin API", version="1.0.0")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(logs_router, prefix="/api", tags=["logs"])
app.include_router(workouts_router, prefix="/api/workouts", tags=["workouts"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
