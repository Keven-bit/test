from schemas import *
from typing import List, Dict
from database import ASession
from sqlmodel import select
from core.evaluation import test_code, monitor_memory_usage
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
        return problem_data.model_dump()


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
    statement = select(ProblemItem.id).where(ProblemItem.id == problem_id)
    result = await session.execute(statement)
    return result.first() is not None


# Get whole info of specific problem
async def check_problem_db(problem_id: str, session: ASession):
    problem = await session.get(ProblemItem, problem_id)
    return problem


# ============================= Submissions ============================= #


async def submit_test_get_id(submit: SubmissionCreate, session: ASession):
    """
    Submit code to test, and return submission_id
    """
    # Extract required info of the problem
    problem_dict = get_problem_fields(
        submit.problem_id, 
        session, 
        ["testcases", "time_limit", "memory_limit"]
    )
    testcases = problem_dict["testcases"]
    counts = len(testcases)*10
    raw_submission = {
        "user_id": "", ### 待补全
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
    return result.first() is not None


async def get_submission_fields(
    submission_id: str, 
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
        return submission_data.model_dump()