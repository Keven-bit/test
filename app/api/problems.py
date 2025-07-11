from fastapi import APIRouter
from ..schemas import problem
from ..core.errors import HTTPException
from ..crud import problem_crud
from pathlib import Path
from typing import List, Dict
import json
import aiofiles


problems_router = APIRouter()
PROBLEM_DATA_PATH = "data/problems"

@problems_router.get("/api/problems")
async def check_problem_list():
    try:   
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
        
        ### 401 未登录(已登录用户) 还没写
        
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
    
@problems_router.delete("/api/problems/{problem_id}")
async def delete_problem(problem_id: str):
    try:
        # 请求次数计数函数 还没写
        ### 401 未登录(已登录用户) 还没写
        filename = f"problem_{problem_id}.json"
        data_path = Path(PROBLEM_DATA_PATH)
        file_path = data_path/filename
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Problem with ID {problem_id} not found"
            )
            
        # delete target problem (and get title of target problem)
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()

        problem_item = problem.ProblemItem(**json.loads(content))
        problem_title = problem_item.title
        
        await aiofiles.os.remove(file_path)
        
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
async def check_problem(problem_id: str):
    try:
        # 请求次数计数函数 还没写
        ### 401 未登录(已登录用户) 还没写
        data_path = Path(PROBLEM_DATA_PATH)
        filename = f"problem_{problem_id}.json"
        file_path = data_path/filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Problem with ID {problem_id} not found"
            )
        
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            
        problem_item = problem.ProblemItem(**json.loads(content))
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