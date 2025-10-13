from app import database, models
from contextlib import asynccontextmanager
from fastapi import FastAPI

async def init_models():
    async with database.engine.begin() as conn:
        # await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)

async def close_db():
    """Close database connections (call on shutdown)"""
    await database.engine.dispose()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print("Creating database tables...")
    await init_models()
    print("Database initialized")
    
    yield
    
    # Shutdown
    print("Closing database connections...")
    await close_db()
    print("Database connections closed")