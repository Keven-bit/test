from fastapi import FastAPI
from .api import problems
from .core import errors
from .database import get_async_session
from fastapi.exceptions import HTTPException, RequestValidationError
from contextlib import asynccontextmanager
from .database import create_db_and_tables


# Async table generation when start up
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(
    title="Simple OJ System - Student Template",
    description="A simple online judge system for programming assignments",
    version="1.0.0",
    lifespan=lifespan
)

# Register custom exception handler
app.exception_handler(HTTPException)(errors.custom_http_exception_handler)
app.exception_handler(RequestValidationError)(errors.custom_validation_exception_handler)

app.include_router(problems.problems_router)

@app.get("/")
async def welcome():
    return "Welcome!"






