from fastapi import FastAPI
from .api import problems, submissions, languages, users, auth, logs, reset, export, import_data
from .core import errors
from .db.schemas import *
from fastapi.exceptions import HTTPException, RequestValidationError
from contextlib import asynccontextmanager
from .db.database import create_db_and_tables, get_db_async_session, engine
from sqlmodel import select
from starlette.middleware.sessions import SessionMiddleware
from config.settings import *


# Start up logics
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Async table generation
    await create_db_and_tables()
    
    # Creat initial admin user
    async for session in get_db_async_session():
        statement = select(UserItem).where(UserItem.username == INITIAL_ADMIN_USERNAME)
        admin_user = (await session.execute(statement)).scalars().first()
        if not admin_user:
            admin_create = UserCreate(
                username=INITIAL_ADMIN_USERNAME,
                password=INITIAL_ADMIN_PASSWORD
            )
            new_admin = UserItem.create_with_hashed_password(admin_create, role="admin")

            session.add(new_admin)
            await session.commit()
            await session.refresh(new_admin)
            print(f"Initial admin user created. admin id: '{new_admin.id}'")
        else:
            print(f"Initial admin user already exists. admin id: '{admin_user.id}'")
            
    yield
    await engine.dispose()


app = FastAPI(
    title="Simple OJ System - Student Template",
    description="A simple online judge system for programming assignments",
    version="1.0.0",
    lifespan=lifespan
)


# Add SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=SESSION_EXPIRATION_MINUTES
)


# Register custom exception handler
app.exception_handler(HTTPException)(errors.custom_http_exception_handler)
app.exception_handler(RequestValidationError)(errors.custom_validation_exception_handler)


# Register routers
app.include_router(problems.problems_router)
app.include_router(submissions.submissions_router)
app.include_router(languages.languages_router)
app.include_router(users.users_router)
app.include_router(auth.auth_router)
app.include_router(logs.logs_router)
app.include_router(reset.reset_router)
app.include_router(export.export_router)
app.include_router(import_data.import_router)

@app.get("/")
async def welcome():
    return "Welcome!"






