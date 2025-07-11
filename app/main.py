from fastapi import FastAPI
from .api import problems
from .core import errors

from fastapi.exceptions import HTTPException, RequestValidationError


app = FastAPI(
    title="Simple OJ System - Student Template",
    description="A simple online judge system for programming assignments",
    version="1.0.0"
)

# Register custom exception handler
app.exception_handler(HTTPException)(errors.custom_http_exception_handler)
app.exception_handler(RequestValidationError)(errors.custom_validation_exception_handler)

app.include_router(problems.problems_router)

@app.get("/")
async def welcome():
    return "Welcome!"






