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
    session: ASession,
    params: LogAccessQuery = Depends(),
    _ = Depends(check_admin_and_get_user)
):
    if params.user_id is None and params.problem_id is None:
        raise HTTPException(
            status_code=400,
            detail=f"Params error."
        )  
        
    if params.page is None and params.page_size is not None:
        params.page = 1
    elif params.page is not None and params.page_size is None:
        raise HTTPException(
            status_code=400,
            detail=f"Params error."
        )   
    
    access_list = await crud.get_log_access_list(params, session)
    return {
        "code": 200,
        "msg": "success",
        "data": access_list
    }