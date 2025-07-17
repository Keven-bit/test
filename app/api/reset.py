from fastapi import APIRouter, Depends
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db import crud
from ..db.database import ASession
from ..core.security import *
from sqlmodel import select
from config.settings import *


reset_router = APIRouter(prefix="/api/reset")


@reset_router.post("/")
async def reset_system(
    session: ASession,
    request: Request,
    _ = Depends(check_admin_and_get_user)
):
    # Delete all data
    await crud.delete_all_data(session)
    
    # Create new initial admin
    admin_create = UserCreate(
        username=INITIAL_ADMIN_USERNAME,
        password=INITIAL_ADMIN_PASSWORD
    )
    new_admin = UserItem.create_with_hashed_password(admin_create, role="admin")
    session.add(new_admin)
    await session.commit()
    
    request.session.clear()
    
    return {
        "code": 200,
        "msg": "system reset successfully",
        "data": None
    }
    
    
    
    
    

