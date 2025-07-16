from ..db.schemas import *
from typing import List, Tuple, Any
from ..db.database import ASession
from sqlmodel import select, func
from ..core.evaluation import test_code
from ..core.errors import HTTPException
import asyncio

PROBLEM_DATA_PATH = "data/problems"


# ============================= Problems ============================= #


# Get specific fields of problem.
async def get_problem_fields(
    problem_id: str, 
    session: ASession,
    fields: List[str] | None = None,
):
    """
    Get specific fields of problem with specific id.
    Return dict like {field: field_value, ...}
    """
    # If fields is not None, get info of fields; or get the whole model.
    if fields:
        selected_fields = [getattr(ProblemItem, field) for field in fields]
        statement = select(*selected_fields).where(ProblemItem.id == problem_id)
    else:
        statement = select(ProblemItem).where(ProblemItem.id == problem_id)
    
    result = await session.execute(statement)
    problem_data = result.first() # Only one result expected
    
    if not problem_data:
        return None
    
    # Convert to dict
    if fields:
        return dict(zip(fields, problem_data))
    else:
        return problem_data[0].model_dump()


# Utilized for get_problem_list. Get id and title of all problems.
async def get_all_problems_meta(session: ASession):
    """
    Read db problem data and return as ProblemList.
    """
    problemlist = []
    statement = select(ProblemItem.id, ProblemItem.title)
    results = await session.execute(statement)
    for problem in results:
        problemlist.append({
            "id": problem.id,
            "title": problem.title,
        })
    
    return problemlist


# Write problem into db
async def write_problem(data: ProblemItem, session: ASession) -> None:
    """
    Write data to db.
    """
    logvisibility = LogVisibility(
        problem_id=data.id
    )
    session.add(logvisibility)
    session.add(data)
    await session.commit()


# delete problem from db
async def delete_problem_db(problem_id: str, session: ASession) -> None:
    """
    Delete data in db.
    """
    problem = await session.get(ProblemItem, problem_id) # Select by Primary_key!
    await session.delete(problem)
    await session.commit()
        

# Check if problem exist in db.
async def problem_exists(problem_id: str, session: ASession) -> bool:
    """
    Check if problem exist in db. Return Bool.
    """
    result = await session.execute(
        select(ProblemItem).where(ProblemItem.id == problem_id)
    )
    problem = result.scalar_one_or_none()
    return problem is not None


# Get whole info of specific problem
async def get_problem_details(problem_id: str, session: ASession):
    result = await session.execute(
        select(ProblemItem).where(ProblemItem.id == problem_id)
    )
    problem = result.scalar_one_or_none()
    return problem


async def get_logvis_by_problem_id(problem_id: str, session: ASession) -> Optional[LogVisibility]:
    try:
        statement = select(LogVisibility).where(LogVisibility.problem_id == problem_id)
        result = await session.execute(statement)
        logvis = result.scalar_one_or_none()
        return logvis
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error."
        )   
    


# ============================= Submissions ============================= #


async def submit_test_get_id(submit: SubmissionCreate, user_id: int, session: ASession):
    """
    Submit code to test, and return submission_id
    """
    # Extract required info of the problem
    problem_dict = await get_problem_fields(
        submit.problem_id, 
        session, 
        ["testcases", "time_limit", "memory_limit"]
    )
    testcases = problem_dict["testcases"]
    counts = len(testcases)*10
    raw_submission = {
        "user_id": user_id, 
        "problem_id": submit.problem_id,
        "code": submit.code,
        "status": "pending",
        "score": None,
        "counts": counts,
    }
    
    submission = SubmissionItem(**raw_submission)
    session.add(submission)
    await session.commit()
    await session.refresh(submission)
    
    # Start async evaluation
    asyncio.create_task(test_code(
        session=session,
        submission_id=submission.id,
        code=submit.code,
        testcases=testcases,
        language=submit.language,
        time_limit=problem_dict["time_limit"],
        memory_limit=problem_dict["memory_limit"]
    ))
    
    return submission.id


async def submission_exists(submission_id: int, session:ASession):
    """
    Check if submission exist in db. Return Bool.
    """
    statement = select(SubmissionItem.id).where(SubmissionItem.id == submission_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def get_submission_fields(
    submission_id: int, 
    session: ASession,
    fields: List[str] | None = None,
):
    """
    Get specific fields of submission with specific id.
    Return dict like {field: field_value, ...}
    """
    # If fields is not None, get info of fields; or get the whole model.
    if fields:
        selected_fields = [getattr(SubmissionItem, field) for field in fields]
        statement = select(*selected_fields).where(SubmissionItem.id == submission_id)
    else:
        statement = select(SubmissionItem).where(SubmissionItem.id == submission_id)
    
    result = await session.execute(statement)
    submission_data = result.first() # Only one result expected
    
    if not submission_data:
        return None
    
    # Convert to dict
    if fields:
        return dict(zip(fields, submission_data))
    else:
        return submission_data[0].model_dump()
    

async def get_submission_list(params: SubmissionListQuery, session: ASession):
    """
    Return specific list page of submissions selected by params
    """
    statement = select(
        SubmissionItem.id,
        SubmissionItem.status,
        SubmissionItem.score,
        SubmissionItem.counts
    )
    if params.user_id is not None:
        statement = statement.where(SubmissionItem.user_id == params.user_id)
    if params.problem_id is not None:
        statement = statement.where(SubmissionItem.problem_id == params.problem_id)
    if params.status is not None:
        statement = statement.where(SubmissionItem.status == params.status)
    
    # Control demonstration range by 'page' and 'page_size'
    if params.page is not None and params.page_size is not None:
        offset = (params.page - 1)*params.page_size
        statement = statement.offset(offset).limit(params.page_size)
        
    result = await session.execute(statement)
    
    rows: List[Tuple[Any, ...]] = result.all()
    
    result_list = []
    for row in rows:
        if row[1] in ["error", "pending"]:
            result_list.append({
                "submission_id": str(row[0]),
                "status": row[1], 
            })
        elif row[1] == "success":
            result_list.append({
                "submission_id": str(row[0]),
                "status": row[1], 
                "score": row[2],
                "counts": row[3]                
            })
    
    return result_list

async def get_submission_counts(params: SubmissionListQuery, session: ASession):
    """
    Return total number of submissions selected by params
    """
    statement = select(func.count(SubmissionItem.id))
    if params.user_id is not None:
        statement = statement.where(SubmissionItem.user_id == params.user_id)
    if params.problem_id is not None:
        statement = statement.where(SubmissionItem.problem_id == params.problem_id)
    if params.status is not None:
        statement = statement.where(SubmissionItem.status == params.status)
    
    result = await session.execute(statement)
    
    total_count = result.scalar_one()
    
    return total_count

async def submission_rejudge(submission_id: int, session: ASession):
    # Get necessary info of submission
    submission_dict = await get_submission_fields(
        submission_id, 
        ["code", "language", "problem_id"]
    )
    
    # Get necessary info of problem
    problem_dict = await get_problem_fields(
    problem_id=submission_dict["problem_id"], 
    session=session, 
    fields=["testcases", "time_limit", "memory_limit"]
    )
    
    asyncio.create_task(test_code(
        session=session,
        submission_id=submission_id,
        code=submission_dict["code"],
        testcases=problem_dict["testcases"],
        language=submission_dict["language"],
        time_limit=problem_dict["time_limit"],
        memory_limit=problem_dict["memory_limit"],
    ))
    
  
async def get_submission_log_by_id(submission_id: int, session: ASession) -> Optional[SubmissionLog]:
    result = await session.execute(
        select(SubmissionLog).where(SubmissionLog.submission_id == submission_id)
    )    
    submission_log = result.scalar_one_or_none()
    return submission_log
    
    
async def get_logvis_by_submission_id(submission_id: int, session: ASession):
    try:
        statement = (
            select(LogVisibility)
            .join(ProblemItem, LogVisibility.problem_id == ProblemItem.id)
            .join(SubmissionItem, ProblemListItem.id == SubmissionItem.problem_id)
            .where(SubmissionItem.id == submission_id)
        )
        result = await session.execute(statement)
        log_visibility = result.scalar_one_or_none()
        return log_visibility
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error."
        ) 


async def get_user_by_submission_id(submission_id: int, session: ASession) -> Optional[UserItem]:
    try:
        statement = (
            select(UserItem)
            .join(SubmissionItem, UserItem.id == SubmissionItem.user_id)
            .where(SubmissionItem.id == submission_id)
        )
        result = await session.execute(statement)
        submit_user = result.scalar_one_or_none()
        return submit_user
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error."
        )   
        
# ============================= Submission Logs ============================= #
async def get_log_access_list(params: LogAccessQuery, session: ASession):
    try:
        statement = select(LogAccess)
        if params.user_id is not None:
            statement = statement.where(LogAccess.user_id == params.user_id)
        if params.problem_id is not None:
            statement = statement.where(LogAccess.problem_id == params.problem_id)
        
        # Control demonstration range by 'page' and 'page_size'
        if params.page is not None and params.page_size is not None:
            offset = (params.page - 1)*params.page_size
            statement = statement.offset(offset).limit(params.page_size)
            
        result = await session.execute(statement)
        
        rows: List[Tuple[Any, ...]] = result.all()
        
        result_list = []
        for row in rows:
            result_list.append({
                "user_id": row[1],
                "problem_id": row[2],
                "action": row[3],
                "time": row[4],
                "status": row[5]
            })

        return result_list
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error."
        )       

            
        
    
# ============================= Users ============================= #

async def user_exists(username: str, session: ASession) -> bool:
    statement = select(UserItem.username).where(UserItem.username == username)
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None

async def get_user_by_id(user_id: int, session: ASession) -> Optional[UserItem]:
    """
    An alternative of "user_exists" function: 
    return Optional[UserItem], if UserItem, user exists; if None, user does not exist.
    """
    try:
        statement = select(UserItem).where(UserItem.id == user_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    
    except Exception as e:
        print(f"Fail to get user info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: Fail to get user info."
        )
        

async def get_user_list_page(
    params: UserListQuery,
    session: ASession
):
    statement = select(
        UserItem.id,
        UserItem.username,
        UserItem.role,
        UserItem.join_time,
        UserItem.submit_count,
        UserItem.resolve_count
    )
    if params.page is not None and params.page_size is not None:
        offset = (params.page - 1) * params.page_size
        statement = statement.offset(offset).limit(params.page_size)
    result = await session.execute(statement)
    
    rows: List[Tuple[Any, ...]] = result.all()
    
    user_list = []
    for row in rows:
        user_list.append({
            "user_id": str(row[0]),
            "username": row[1],
            "role": row[2],
            "join_time": row[3],
            "submit_count": row[4],
            "resolve_count": row[5]
        })
    
    return user_list


async def get_user_counts(session: ASession):
    """
    Return total number of users
    """
    statement = select(func.count(UserItem.id))
    result = await session.execute(statement)
    total_count = result.scalar_one()
    
    return total_count

