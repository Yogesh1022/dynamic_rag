# Database Initialization Script
# Run this to create the database tables

from sqlalchemy import create_engine
from app.models import Base
from app.core.config import settings
import asyncio


async def init_db():
    """Create all database tables."""
    from app.api.deps import engine
    
    print("Creating database tables...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
