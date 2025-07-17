from fastapi import APIRouter, Depends
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db import crud
from ..db.database import ASession
from ..core.security import *
from sqlmodel import select
from config.settings import *

export_router = APIRouter(prefix="/api/export")

@export_router.get("/")
async def export_data(
    session: ASession,
    _ = Depends(check_admin_and_get_user)
):
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "users": await crud.export_users_data(session),
            "problems": await crud.export_problems_data(session),
            "submissions": await crud.export_submissions_data(session)
        }
    }

