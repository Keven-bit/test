from fastapi import APIRouter, Depends
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db import crud
from ..db.database import ASession



submissions_router = APIRouter(prefix="/api/submissions")

@submissions_router.post("/")
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
    
@submissions_router.get("/{submission_id}")
async def get_result(submission_id: int, session: ASession):
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
 
        
@submissions_router.get("/")
async def get_result_list(
    session: ASession,
    params: SubmissionListQuery = Depends()
):
    ## 403 限本人或管理员 待补全
    try:
        submissionlist = crud.get_submission_list(params, session)
        total = crud.get_submission_counts(params, session)
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "total": total,
                "submissions": submissionlist
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )
        

@submissions_router.get("/{submission_id}/rejudge")
async def rejudge(submission_id: int, session: ASession):
    ## 403 限管理员 待补全
    
    if not await crud.submission_exists(submission_id):
        raise HTTPException(
            status_code=404,
            detail=f"Problem with ID {submit.problem_id} not found"
        )
    
    try:
        crud.submission_rejudge(submission_id, session)
        return{
            "code": 200,
            "msg": "rejudge started",
            "data": {
                "submission_id": submission_id,
                "status": "pending"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )



        
    