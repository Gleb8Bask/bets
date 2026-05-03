from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import auth, users, markets, wallet


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates tables on startup if they don't exist.
    # In production use: alembic upgrade head
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,    prefix=settings.API_PREFIX)
app.include_router(users.router,   prefix=settings.API_PREFIX)
app.include_router(markets.router, prefix=settings.API_PREFIX)
app.include_router(wallet.router,  prefix=settings.API_PREFIX)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
