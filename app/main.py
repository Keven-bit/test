from fastapi import FastAPI
from .api import problems, submissions, languages, users, auth
from .core import errors
from fastapi.exceptions import HTTPException, RequestValidationError
from contextlib import asynccontextmanager
from .db.database import create_db_and_tables


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
app.include_router(submissions.submissions_router)
app.include_router(languages.languages_router)
app.include_router(users.users_router)
app.include_router(auth.auth_router)

@app.get("/")
async def welcome():
    return "Welcome!"






