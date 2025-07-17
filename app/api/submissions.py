from fastapi import APIRouter, Depends
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db import crud
from ..db.database import ASession
from ..core.security import *
from sqlmodel import select

submissions_router = APIRouter(prefix="/api/submissions")

@submissions_router.post("/", dependencies=[Depends(rate_limit)])
async def submit(
    submit: SubmissionCreate,
    session: ASession,
    user: UserItem = Depends(check_login_and_get_user)
):  
    if not await crud.problem_exists(submit.problem_id, session):
        raise HTTPException(
            status_code=404,
            detail=f"Problem with ID {submit.problem_id} not found"
        )
    
    try:
        # Get submission id, and start async evaluation.
        submission_id = await crud.submit_test_get_id(submit, user.id, session)
        user.submit_count += 1
        session.add(user)
        await session.commit()
    
        return{
            "code": 200,
            "msg": "success",
            "data": {
                "submission_id": submission_id,
                "status": "pending",
            }
        }
        
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )
    
@submissions_router.get("/{submission_id}")
async def get_result(
    submission_id: str, 
    session: ASession, 
    user: UserItem = Depends(check_login_and_get_user)
):
    if not await crud.submission_exists(submission_id, session):
        raise HTTPException(
            status_code=404,
            detail=f"Submission not found"
        )
    
    # Get required fields
    try:
        sub_dict = await crud.get_submission_fields(submission_id, session, ["status", "score", "counts", "user_id"])

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )        
    
    # Only submission owner or admin can view it     
    if user.id != sub_dict["user_id"] and user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Lack Permission."
        )
    
    return {
        "code": 200,
        "msg": "success",
        "data":{
            "score": sub_dict["score"],
            "counts": sub_dict["counts"],
        }
    }

 
        
@submissions_router.get("/")
async def get_result_list(
    session: ASession,
    params: SubmissionListQuery = Depends(),
    user: UserItem = Depends(check_login_and_get_user)
):
    if params.user_id is None and params.problem_id is None:
        raise HTTPException(
            status_code=400,
            detail="Params error."
        )
    if params.page is None and params.page_size is not None:
        params.page = 1
    elif params.page is not None and params.page_size is None:
        raise HTTPException(
            status_code=400,
            detail="Params error."
        )
    
    # Admin can view all submissions
    if user.role == "admin":
        try:
            submissionlist = await crud.get_submission_list(params, session)
            total = await crud.get_submission_counts(params, session)
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
            
    # Non-admin users can only query their own submissions.
    else:
        if params.user_id is None:
            params.user_id = user.id
        elif params.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Lack Permission. You can only query your own submissions."
            )
        
        try:
            submissionlist = await crud.get_submission_list(params, session)
            total = await crud.get_submission_counts(params, session)
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
        

@submissions_router.put("/{submission_id}/rejudge")
async def rejudge(
    submission_id: str, 
    session: ASession, 
    _ = Depends(check_admin_and_get_user)
): 
    if not await crud.submission_exists(submission_id, session):
        raise HTTPException(
            status_code=404,
            detail=f"Problem not found"
        )
    
    try:
        await crud.submission_rejudge(submission_id, session)
        return{
            "code": 200,
            "msg": "rejudge started",
            "data": {
                "submission_id": submission_id,
                "status": "pending"
            }
        }
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {e}"  
        )


# ========== Submission logs ========== #

@submissions_router.get("/{submission_id}/log")
async def get_submission_log(
    submission_id: str, 
    session: ASession, 
    user: UserItem = Depends(check_login_and_get_user)
):
    response_status: Optional[int] = None
    submit_user: Optional[UserItem] = None
    log_vis: Optional[LogVisibility] = None
    
    try:
        log_vis: LogVisibility = await crud.get_logvis_by_submission_id(submission_id, session)
        submission_log: Optional[SubmissionLog] = await crud.get_submission_log_by_id(submission_id, session)
        
        if submission_log is None:
            response_status = 404
            raise HTTPException(
                status_code=404,
                detail="Submission does not exist."
            )
        
        public_cases = log_vis.public_cases
            
        if public_cases:
            response_status = 200
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "details": submission_log.details,
                    "score": submission_log.score,
                    "counts": submission_log.counts
                }
            }
        else:
            submit_user: UserItem = await crud.get_user_by_submission_id(submission_id, session)
            if user.role == "admin":
                response_status = 200
                return {
                    "code": 200,
                    "msg": "success",
                    "data": {
                        "details": submission_log.details,
                        "score": submission_log.score,
                        "counts": submission_log.counts
                    }
                }            
            elif user.id != submit_user.id:
                response_status = 403
                raise HTTPException(
                    status_code=403,
                    detail="Lack Permission"
                )
            else:
                response_status = 200
                return {
                    "code": 200,
                    "msg": "success",
                    "data": {
                        "score": submission_log.score,
                        "counts": submission_log.counts
                    }
                }     
    except HTTPException:
        raise
    finally:
        if user and log_vis:
            log_access = LogAccess(
                user_id=user.id,
                problem_id=log_vis.problem_id,
                action="view_log",
                status=response_status
            )
            session.add(log_access)
            await session.commit()
    
                            
        
        
    