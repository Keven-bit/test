from fastapi import APIRouter, Body
from ..db.schemas import ProblemItem, LogVisibility, LogVisibilityUpdate
from ..core.errors import HTTPException
from ..db import crud
from ..db.database import ASession
from ..core.security import *


problems_router = APIRouter(prefix="/api/problems")

@problems_router.get("/")
async def get_problem_list(
    session: ASession, 
    _ = Depends(check_login_and_get_user)
):
    # request_count = get_request_count() # 请求次数计数函数还没写
    # if request_count > 100:
    #     raise HTTPException(
    #         status_code=429,
    #         detail="Rate limit exceeded. Please retry later."
    #         headers={"Retry-After": "60"}
    #     )
    
    try:
        return {
            "code": 200,
            "msg": "success",
            "data": await crud.get_all_problems_meta(session=session)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"
        )

@problems_router.post("/")
async def add_problem(
    problemitem: ProblemItem, 
    session: ASession,
    _ = Depends(check_login_and_get_user)
):

    # request_count = get_request_count() # 请求次数计数函数 还没写
    # if request_count > 100:
    #     raise HTTPException(
    #         status_code=429,
    #         detail="Rate limit exceeded. Please retry later."
    #         headers={"Retry-After": "60"}
    #     )
    
    if await crud.problem_exists(problemitem.id, session=session):
        raise HTTPException(
            status_code=409,
            detail=f"ID:{problemitem.id} already exists."
        )
        
    try:   
        await crud.write_problem(problemitem, session=session)
        
        return {
            "code": 200,
            "msg": "add success",
            "data": {
                "id": problemitem.id,
                "title": problemitem.title
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"
        )
    
@problems_router.delete("/{problem_id}")
async def delete_problem(
    problem_id: str, 
    session: ASession,
    _ = Depends(check_admin_and_get_user)
):
    # 请求次数计数函数 还没写

    if not await crud.problem_exists(problem_id, session=session):
        raise HTTPException(
            status_code=404,
            detail=f"Problem with ID {problem_id} not found"
        )
    try:        
        # delete target problem (and get title of target problem)
        target_dict = await crud.get_problem_fields(problem_id, fields=["title"], session=session)
        problem_title = target_dict["title"]
        await crud.delete_problem_db(problem_id, session=session)
        
        
        return {
            "code": 200,
            "msg": "delete success",
            "data": {
                "id": problem_id,
                "title": problem_title
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )
    
@problems_router.get("/{problem_id}")
async def get_problem(
    problem_id: str, 
    session: ASession,
    _ = Depends(check_login_and_get_user)
):
    # 请求次数计数函数 还没写
    
    if not await crud.problem_exists(problem_id, session=session):
        raise HTTPException(
            status_code=404,
            detail=f"Problem with ID {problem_id} not found"
        )
    try:    
        problem_item = await crud.get_problem_details(problem_id, session=session)
        return {
            "code": 200,
            "msg": "success",
            "data": problem_item,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )
        
        
@problems_router.put("/{problem_id}/log_visibility")
async def set_log_visibility(
    problem_id: str,
    session: ASession, 
    logvis_data: Optional[LogVisibilityUpdate] = Body(None),
    _ = Depends(check_admin_and_get_user)
):
    logvis: Optional[LogVisibility] = await crud.get_logvis_by_problem_id(problem_id, session)
    if logvis:
        public_cases = logvis_data.public_cases
        logvis.public_cases = public_cases
        session.add(logvis)
        await session.commit()
        
        return {
            "code": 200,
            "msg": "log visibility updated",
            "data": {
                "problem_id": problem_id,
                "public_cases": public_cases
            }
        }
    else:
        raise HTTPException(
            status_code=404,
            detail="Problem does not exist."
        )