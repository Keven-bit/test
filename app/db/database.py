from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import Annotated 
from fastapi import Depends
import contextlib 


DATABASE_URL = "sqlite+aiosqlite:///./app.db"

engine = create_async_engine(DATABASE_URL, echo=True)

# Generate instance of AsyncSession
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@contextlib.asynccontextmanager
async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session
        

async def get_db_async_session():
    async with get_async_session() as session:
        yield session

# Used in dependency Injection of session between functions and db, will be used in api and crud functions!
# Async Session dependence
ASession = Annotated[AsyncSession, Depends(get_db_async_session)]
