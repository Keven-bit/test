from fastapi import APIRouter
from ..schemas import problem
from ..core.errors import HTTPException
from ..crud import problem_crud
from pathlib import Path
from typing import List, Dict



problems_router = APIRouter()
PROBLEM_DATA_PATH = "data/problems"

@problems_router.get("/api/problems")
async def check_problem_list():
    try:
        # if not problem.ProblemList:
        #     raise HTTPException(
        #         status_code=404,
        #         detail='题目列表不存在'
        #     ) # 舍弃
        
        # request_count = get_request_count() # 请求次数计数函数还没写
        # if request_count > 100:
        #     raise HTTPException(
        #         status_code=429,
        #         detail="Rate limit exceeded. Please retry later."
        #         headers={"Retry-After": "60"}
        #     )

        return {
            "code": 200,
            "msg": "success",
            "data": await problem_crud.get_all_problems_meta()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"
        )

@problems_router.post("/api/problems")
async def add_problem(problemitem: problem.ProblemItem):
    try:
        # request_count = get_request_count() # 请求次数计数函数 还没写
        # if request_count > 100:
        #     raise HTTPException(
        #         status_code=429,
        #         detail="Rate limit exceeded. Please retry later."
        #         headers={"Retry-After": "60"}
        #     )
        
        ### 401 未登录 还没写
        
        filename = f"problem_{problemitem.id}.json"
        file_path = Path(PROBLEM_DATA_PATH)/filename
        
        if file_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"ID:{problemitem.id} already exists."
            )
        
        await problem_crud.write_json(file_path, problemitem.model_dump())
        
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
    
    