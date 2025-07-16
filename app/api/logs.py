from fastapi import APIRouter, Request
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db.database import ASession
from sqlmodel import select
from ..db import crud
from ..core.security import *
from fastapi import Depends


logs_router = APIRouter(prefix="/api/logs")


@logs_router.get("/access/")
async def get_access_logs(
    params: LogAccessQuery,
    session: ASession,
    _ = Depends(check_admin_and_get_user)
):
    access_list = await crud.get_log_access_list(params, session)
    return {
        "code": 200,
        "msg": "success",
        "data": access_list
    }