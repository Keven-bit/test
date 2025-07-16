from fastapi import APIRouter, Depends
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..core.security import *
from ..db.database import ASession
from sqlmodel import select
from ..db import crud

users_router = APIRouter(prefix="/api/users")

@users_router.post("/admin")
async def create_admin(
    user_create: UserCreate,
    session: ASession,
    _ = Depends(check_admin_and_get_user)
):
    if await crud.user_exists(user_create.username, session):
        raise HTTPException(
            status_code=400,
            detail=f"username '{user_create.username}' already exists."
        )
    else:
        try:
            user = UserItem.create_with_hashed_password(user_create, role="admin")
            session.add(user)
            await session.commit()
        
            return {
                "code": 200,
                "msg": "success",
                "data":{
                    "user_id": str(user.id),  
                    "username": user.username
                }
            }
        except Exception as e:
            print(f"Fail to register: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Server Error: Fail to register."
            )
            

@users_router.post("/")
async def register_user(user_create: UserCreate, session: ASession):
    if await crud.user_exists(user_create.username, session):
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


@users_router.get("/{user_id}")
async def get_user(
    user_id,
    session: ASession,
    current_user: UserItem = Depends(check_login_and_get_user)
):
    if current_user.role == "admin" or current_user.id == user_id:
        # Get user (target) / check existence
        user: Optional[UserItem] = await crud.get_user_by_id(user_id, session)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail=f"User '{user_id}' does not exist."
            )
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "user_id": str(user.id),  
                "username": user.username,
                "join_time": user.join_time,
                "role": user.role,
                "submit_count": user.submit_count,
                "resolve_count": user.resolve_count
            }
        }
        
    else:
        raise HTTPException(
            status_code=403,
            detail="Lack permission."
        )


@users_router.put("/{user_id}/role")
async def update_role(
    user_id: str,
    role: UserRole,
    session: ASession,
    _ = Depends(check_admin_and_get_user)
):
    target_user: Optional[UserItem] = await crud.get_user_by_id(user_id, session)
    
    if target_user is None:
        raise HTTPException(
            status_code=404,
            detail=f"User '{user_id}' does not exist."
        )
    
    try:
        target_user.role = role
        session.add(target_user)
        await session.commit()
        
        return {
            "code": 200,
            "msg": "role updated",
            "data": {
                "user_id": str(user_id),
                "role": role
            }
        }
    except Exception as e:
        print(f"Fail to change role: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: Fail to change role."
        )
        

@users_router.get("/")
async def get_user_list(
    session: ASession,
    params: UserListQuery = Depends(),
    _ = Depends(check_admin_and_get_user)
):
    try:
        user_list = await crud.get_user_list_page(params, session)
        total = await crud.get_user_counts(session)
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "total": total,
                "users": user_list
            }
        }
        
    except Exception as e:
        print(f"Fail to get user list: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: Fail to get user list."
        )    

    
    
    
    