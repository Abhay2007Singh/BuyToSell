import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

_db_url = os.getenv("DATABASE_URL", "sqlite:///./buytosell.db")

if _db_url.startswith("postgresql://"):
    ASYNC_DATABASE_URL = _db_url.replace("postgresql://", "postgresql+asyncpg://")
elif _db_url.startswith("sqlite://"):
    ASYNC_DATABASE_URL = _db_url.replace("sqlite://", "sqlite+aiosqlite://")
else:
    ASYNC_DATABASE_URL = _db_url

_engine_kwargs = {}
if ASYNC_DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

async_engine = create_async_engine(ASYNC_DATABASE_URL, **_engine_kwargs)
async_session_maker = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

async def get_async_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
