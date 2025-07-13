from fastapi import APIRouter
from db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from db import crud
from pathlib import Path
from typing import List, Dict
import json
import aiofiles
from db.database import ASession


submissions_router = APIRouter()

@submissions_router.post("/api/submissions/")
async def submit(
    submit: SubmissionCreate,
    session = ASession
):
    ## 429 提交频率超限 待补全
    ## 403 用户被禁用(登录用户) 待补全
    
    if not await crud.problem_exists(submit.problem_id):
        raise HTTPException(
            status_code=404,
            detail=f"Problem with ID {submit.problem_id} not found"
        )
    
    try:
        # Get submission id, and start async evaluation.
        submission_id = crud.submit_test_get_id(submit, session)
        return{
            "code": 200,
            "msg": "success",
            "data": {
                "submission_id": submission_id,
                "status": "pending",
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )
    
@submissions_router.post("/api/submissions/{submission_id}")
async def check_result(submission_id: int, session: ASession):
    ## 403 限本人或管理员 待补全
    
    if not await crud.submission_exists(submission_id):
        raise HTTPException(
            status_code=404,
            detail=f"Problem with ID {submit.problem_id} not found"
        )
    
    # Get required fields
    try:
        sub_dict = crud.get_submission_fields(submission_id, ["status", "score", "counts"])
        return {
            "code": 200,
            "msg": sub_dict["status"],
            "data":{
                "score": sub_dict["score"],
                "counts": sub_dict["counts"],
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )