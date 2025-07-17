from typing import Optional, Annotated
from fastapi import Request, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from .errors import HTTPException
from ..db.schemas import UserItem
from ..db.database import ASession
from config.settings import WINDOW_SECONDS, MAX_REQUESTS
from datetime import datetime, timedelta,timezone
import time

    
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
        
    try:
        user = await session.get(UserItem, current_user_id)
    except Exception as e:
        print("Fail to get user info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: Fail to get user info."  
        )
        
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
    
# =========== Rate limit =========== #   
    
# Key of the dict indicates IP or ID; value is list of timestamps of the "key"
request_timestamps: dict[str, list[datetime]] = {}


def check_and_record_request(key: str) -> bool:
    """
    Check whether the request of the key exceeds the limit.
    Return True: permit for the request
    Return False: exceed the limit.
    """
    now = datetime.now(timezone.utc)

    if key not in request_timestamps:
        request_timestamps[key] = []   
    
    timestamps = request_timestamps[key]
    
    # Clear timestamps earlier than WINDOW_SECONDS
    timestamps[:] = [
        ts for ts in timestamps if (now - ts).total_seconds() < WINDOW_SECONDS
    ]
    
    if len(timestamps) >= MAX_REQUESTS:
        return False
    else:
        timestamps.append(now)
        return True
    

def get_key(request: Request):
    return request.client.host


async def rate_limit(request_key: str = Depends(get_key)):
    if not check_and_record_request(request_key):
        raise HTTPException(
            status_code=429,
            detail=f"Too Many Requests."
        )