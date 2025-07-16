from fastapi import APIRouter, Request
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db.database import ASession
from sqlmodel import select
from ..db import crud
from ..core.security import *
from fastapi import Depends

auth_router = APIRouter(prefix="/api/auth")

@auth_router.post("/login")
async def login(user_create: UserCreate, request: Request, session: ASession):
    try:
        statement = select(UserItem).where(UserItem.username == user_create.username)
        result = await session.execute(statement)
        user: Optional[UserItem] = result.scalars().first()
        
    except Exception as e:
        print(f"Error in login: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: Fail to login."
        )    
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password."
        )
    elif user and user.role == "banned":
        raise HTTPException(
            status_code=403,
            detail=f"User '{user_create.username}' is banned."
        ) 
    elif user and not user.verify_password(user_create.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password."
        )           
        
    # Write Session state: record the login user_id 
    request.session["user_id"] = user.id
    
    return {
        "code": 200,
        "msg": "login success",
        "data": {
            "user_id": str(user.id),
            "username": user.username,
            "role": user.role
        }
    }

        
        
    
    
@auth_router.post("/logout")
async def logout(request: Request, _ = Depends(check_login_and_get_user)):
    ### 权限：登录用户
    try:
        request.session.clear()
        
        return {
            "code": 200,
            "msg": "logout success",
            "data": None            
        }
    except Exception as e:
        print(f"Error in logout: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: Fail to logout."
        )
    
    