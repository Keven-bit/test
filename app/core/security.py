from typing import Optional, Annotated
from fastapi import Request, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from .errors import HTTPException
from ..db.schemas import UserItem
from ..db.database import ASession
    
    
async def check_login_and_get_user(request: Request, session: ASession) -> Optional[UserItem]:
    """
    Check login, and return current UserItem if logged in. 
    """
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        raise HTTPException(
            status_code=401,
            detail="Please log in to access this page."
        )
    
    user = await session.get(UserItem, current_user_id)
    if user.role == "banned":
        raise HTTPException(
            status_code=403,
            detail="User is banned."
        )        
    
    return user


async def check_admin_and_get_user(request: Request, user: UserItem=Depends(check_login_and_get_user)) -> Optional[int]:
    """
    Check admin, return current user_id if user is admin.
    Dependence check_login first check login. 
    If user is admin, return UserItem (no need to handle if it's not required).
    If not, raise error and return None.
    """    
    current_user_role = user.role
    if current_user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Lack permission."
        )
    
    else:
        return user
    
    
# 已弃用，统一用check_login_and_get_user检查login
# async def check_login_and_get_id(request: Request) -> Optional[int]:
#     """
#     Check login, without getting UserItem from db.
#     If user logged in, return current user_id (no need to handle if it's not required).
#     If no user logged in, raise error and return None.
#     """
#     current_user_id = request.session.get("user_id")
#     if not current_user_id:
#         raise HTTPException(
#             status_code=401,
#             detail="Please log in to access this page."
#         )
        
#     else:
#         return current_user_id