from fastapi import APIRouter
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db.database import ASession
from sqlmodel import select
from ..db import crud

users_router = APIRouter(prefix="/api/users")

@users_router.post("/admin")
async def create_admin(username: str, password: str, session: ASession):
    try:
        




@users_router.post("/")
async def register_user(user_create: UserCreate, session: ASession):
    try:
        if crud.user_exists(user_create.username):
            raise HTTPException(
                status_code=400,
                detail=f"username '{user_create.username}' already exists."
            )
        else:
            user = UserItem.create_with_hashed_password(user_create)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            return {
                "code": 200,
                "msg": "register success",
                "data":{
                    "user_id": str(user.id),  
                    "username": user.username,
                    "join_time": user.join_time,
                    "role": "user",
                    "submit_count": 0,
                    "resolve_count": 0
                }
            }
    except Exception as e:
        print(f"Fail to register: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: Fail to register."
        )

 
 
    
@users_router.get("/{user_id}")
async def get_user(username: str, session: ASession):
    
    


@users_router.put("/{user_id}/role")
async def update_role(role: UserRole, session: ASession):
    