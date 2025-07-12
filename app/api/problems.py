from fastapi import APIRouter
from ..schemas.problem import *
from ..core.errors import HTTPException
from ..crud import problem_crud
from ..database import ASession


problems_router = APIRouter()

@problems_router.get("/api/problems")
async def check_problem_list(session: ASession):
    
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
            "data": await problem_crud.get_all_problems_meta(session=session)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"
        )

@problems_router.post("/api/problems")
async def add_problem(problemitem: ProblemItem, session: ASession):

    # request_count = get_request_count() # 请求次数计数函数 还没写
    # if request_count > 100:
    #     raise HTTPException(
    #         status_code=429,
    #         detail="Rate limit exceeded. Please retry later."
    #         headers={"Retry-After": "60"}
    #     )
    
    ### 401 未登录(已登录用户) 还没写
    
    if await problem_crud.problem_exists(problemitem.id, session=session):
        raise HTTPException(
            status_code=409,
            detail=f"ID:{problemitem.id} already exists."
        )
        
    try:   
        await problem_crud.write_problem(problemitem, session=session)
        
        return {
            "code": 200,
            "msg": "add success",
            "data": {
                problemitem.id: problemitem.title
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"
        )
    
@problems_router.delete("/api/problems/{problem_id}")
async def delete_problem(problem_id: str, session: ASession):
    # 请求次数计数函数 还没写
    ### 401 未登录(已登录用户) 还没写
    if not await problem_crud.problem_exists(problem_id, session=session):
        raise HTTPException(
            status_code=404,
            detail=f"Problem with ID {problem_id} not found"
        )
    try:        
        # delete target problem (and get title of target problem)
        target_dict = await problem_crud.get_problem_fields(problem_id, fields=["title"], session=session)
        problem_title = target_dict["title"]
        await problem_crud.delete_problem_db(problem_id, session=session)
        
        
        return {
            "code": 200,
            "msg": "delete success",
            "data": {problem_id: problem_title}
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )
    
@problems_router.get("/api/problems/{problem_id}")
async def check_problem(problem_id: str, session: ASession):

    # 请求次数计数函数 还没写
    ### 401 未登录(已登录用户) 还没写
    if not await problem_crud.problem_exists(problem_id, session=session):
        raise HTTPException(
            status_code=404,
            detail=f"Problem with ID {problem_id} not found"
        )
    try:    
        problem_item = await problem_crud.check_problem_db(problem_id, session=session)
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