from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError

# Custom exception handler
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "msg": exc.detail,
            "data": None,
        }
    )

# Custom exception handler for params/format error
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "msg": "Invalid parameters.",
            "data": None,
        }
    )
