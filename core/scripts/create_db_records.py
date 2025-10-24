from app import database, models
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
import asyncio

async def init_models():
    """Initialize database models with retries (Render-safe)."""
    retries = 5
    delay = 5  # seconds between retries

    for attempt in range(1, retries + 1):
        try:
            print(f"[DB INIT] Attempt {attempt}/{retries} - connecting...")
            async with database.engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.create_all)
            print("[DB INIT] ✅ Database connected and tables created.")
            break  # Success!
        except OperationalError as e:
            print(f"[DB INIT] ❌ Connection failed: {e}")
            if attempt < retries:
                print(f"[DB INIT] Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                print("[DB INIT] ❌ Database unreachable after several attempts.")
                raise
        except Exception as e:
            print(f"[DB INIT] Unexpected error: {e}")
            raise

async def close_db():
    """Close database connections (on shutdown)."""
    print("[DB CLOSE] Disposing SQLAlchemy engine...")
    await database.engine.dispose()
    print("[DB CLOSE] ✅ Connections closed.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events with resilience."""
    print("🚀 App starting up — initializing database...")
    await init_models()

    yield  # Application runs here

    print("🛑 App shutting down — closing database connections...")
    await close_db()
