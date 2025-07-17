from ..db.schemas import *
from typing import List, Tuple, Any
from ..db.database import ASession
from sqlmodel import select, func, delete
from ..core.evaluation import test_code
from ..core.errors import HTTPException
import asyncio
import uuid
from sqlalchemy.orm import selectinload

PROBLEM_DATA_PATH = "data/problems"


# ============================= Problems ============================= #

async def get_problem_by_id(problem_id: str, session: ASession):
    result = await session.execute(
        select(ProblemItem).where(ProblemItem.id == problem_id)
    )
    problem = result.scalar_one_or_none()
    return problem


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
    # First, delete all data related to this problem.
    result = await session.execute(
        select(SubmissionItem.id).where(SubmissionItem.problem_id == problem_id)
    )
    submission_delete_ids = result.scalars().all()
    if submission_delete_ids:
        await session.execute(
            delete(SubmissionLog).where(SubmissionLog.submission_id.in_(submission_delete_ids))
        )
    await session.execute(
        delete(SubmissionItem).where(SubmissionItem.problem_id == problem_id)
    )
    await session.execute(
        delete(LogVisibility).where(LogVisibility.problem_id == problem_id)
    )
    await session.execute(
        delete(LogAccess).where(LogAccess.problem_id == problem_id)
    )
    await session.execute(
        delete(ProblemItem).where(ProblemItem.id == problem_id)
    )

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
     
     
    
# ============================= Users ============================= #

async def user_exists(username: str, session: ASession) -> bool:
    statement = select(UserItem.username).where(UserItem.username == username)
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None

async def get_user_by_id(user_id: str, session: ASession) -> Optional[UserItem]:
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


# ============================= Submissions ============================= #


async def get_submission_by_id(submission_id: str, session: ASession):
    result = await session.execute(
        select(SubmissionItem).where(SubmissionItem.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    return submission


async def submit_test_get_id(submit: SubmissionCreate, user_id: str, session: ASession):
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
        "id": str(uuid.uuid4()),
        "user_id": user_id, 
        "problem_id": submit.problem_id,
        "language": submit.language,
        "code": submit.code,
        "status": "pending",
        "score": None,
        "counts": counts,
    }
    
    submission = SubmissionItem(**raw_submission)
    session.add(submission)
    await session.commit()
    
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


async def submission_exists(submission_id: str, session:ASession):
    """
    Check if submission exist in db. Return Bool.
    """
    statement = select(SubmissionItem.id).where(SubmissionItem.id == submission_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


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

async def submission_rejudge(submission_id: str, session: ASession):
    # Get necessary info of submission
    submission_dict = await get_submission_fields(
        submission_id, session,
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
    
  
async def get_submission_log_by_id(submission_id: str, session: ASession) -> Optional[SubmissionLog]:
    try:
        result = await session.execute(
            select(SubmissionLog).where(SubmissionLog.submission_id == submission_id)
        )    
        submission_log = result.scalar_one_or_none()
        return submission_log
    except Exception as e:
        print(f"Server Error in get_submission_log_by_id: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error."
        ) 
    
    
async def get_logvis_by_submission_id(submission_id: str, session: ASession):
    try:
        statement = (
            select(LogVisibility)
            .join(ProblemItem, LogVisibility.problem_id == ProblemItem.id)
            .join(SubmissionItem, ProblemItem.id == SubmissionItem.problem_id)
            .where(SubmissionItem.id == submission_id)
        )
        result = await session.execute(statement)
        log_visibility = result.scalar_one_or_none()
        return log_visibility
    except Exception as e:
        print(f"Server Error in get_logvis_by_submission_id: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error."
        ) 


async def get_user_by_submission_id(submission_id: str, session: ASession) -> Optional[UserItem]:
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
        print(f"Server Error in get_user_by_submission_id: {e}")
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
        
        rows: List[LogAccess] = result.scalars().all()
        
        result_list = []
        for row in rows:
            result_list.append({
                "user_id": row.user_id,
                "problem_id": row.problem_id,
                "action": row.action,
                "time": row.time,
                "status": row.status
            })

        return result_list
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error."
        )       

            
# ============================= Reset ============================= #

async def delete_all_data(session: ASession):
    await session.execute(delete(SubmissionLog))
    
    await session.execute(delete(SubmissionItem))
    
    await session.execute(delete(LogVisibility))
    
    await session.execute(delete(ProblemItem))
    
    await session.execute(delete(UserItem))
    
    await session.execute(delete(LanguageItem))
    
    await session.commit()
    

# ============================= Export ============================= #

async def export_users_data(session: ASession):
    exported_users = []
    result = await session.execute(select(UserItem))
    users = result.scalars().all()
    
    for user in users:
        exported_users.append({
            "user_id": user.id, 
            "username": user.username,
            "password": user.hashed_password,
            "role": user.role,
            "join_time": user.join_time.isoformat(),
            "submit_count": user.submit_count,
            "resolve_count": user.resolve_count
        })
        
    return exported_users

async def export_problems_data(session: ASession):
    exported_problems = []
    
    results = await session.execute(
        select(ProblemItem).options(selectinload(ProblemItem.log_visibility))
    )
    problems = results.scalars().all()
    
    for problem in problems:
        problem_dict = {
            "id": problem.id,
            "title": problem.title,
            "description": problem.description,
            "input_description": problem.input_description,
            "output_description": problem.output_description,
            "samples": problem.samples,
            "constraints": problem.constraints,
            "testcases": problem.testcases,
            "hint": problem.hint,
            "source": problem.source,
            "tags": problem.tags,
            "time_limit": problem.time_limit,
            "memory_limit": problem.memory_limit,
            "author": problem.author,
            "difficulty": problem.difficulty,
            "public_cases": problem.log_visibility.public_cases
        }
        exported_problems.append(problem_dict)
    return exported_problems

async def export_submissions_data(session: ASession):
    exported_submissions = []
    
    results = await session.execute(
        select(SubmissionItem).options(selectinload(SubmissionItem.submission_log))
    )
    submissions = results.scalars().all()
    
    for submission in submissions:
        submission_dict = {
            "submission_id": submission.id,
            "user_id": submission.user_id,
            "problem_id": submission.problem_id,
            "language": submission.language,
            "code": submission.code,
            "status": submission.status.value,
            "details": submission.submission_log.details if submission.submission_log else [],
            "score": submission.score,
            "counts": submission.counts
        }
        exported_submissions.append(submission_dict)
    return exported_submissions


# ============================= Import ============================= #

async def validate_and_import(
    data: ImportFileSchema,
    session: ASession
):
    for user_data in data.users:
        user = await get_user_by_id(user_data.user_id, session)
        
        if user:
            user.username = user_data.username
            user.hashed_password = user_data.password
            user.role = UserRole(user_data.role)
            user.join_time = datetime.fromisoformat(user_data.join_time)
            user.submit_count = user_data.submit_count
            user.resolve_count = user_data.resolve_count
            session.add(user)
            
        else:
            # Check if username exists 
            result_user_by_name = await session.execute(
                select(UserItem).where(UserItem.username == user_data.username)
            )
            user_by_name = result_user_by_name.scalar_one_or_none()
            
            if user_by_name:
                user_by_name.username = user_data.username
                user_by_name.hashed_password = user_data.password
                user_by_name.role = UserRole(user_data.role)
                user_by_name.join_time = datetime.fromisoformat(user_data.join_time)
                user_by_name.submit_count = user_data.submit_count
                user_by_name.resolve_count = user_data.resolve_count
                session.add(user_by_name)                
            else:
                new_user = UserItem(
                    id=user_data.user_id,
                    username=user_data.username,
                    hashed_password=user_data.password,
                    role=UserRole(user_data.role),
                    join_time=datetime.fromisoformat(user_data.join_time),
                    submit_count=user_data.submit_count,
                    resolve_count=user_data.resolve_count
                )
                session.add(new_user)
            
    await session.commit()       
            
    for problem_data in data.problems:
        result = await session.execute(
            select(ProblemItem).where(ProblemItem.id == problem_data.id)
        )
        problem = result.scalar_one_or_none()
        
        if problem:
            problem.title = problem_data.title
            problem.description = problem_data.description
            problem.input_description = problem_data.input_description
            problem.output_description = problem_data.output_description
            problem.samples = [s.model_dump() for s in problem_data.samples]
            problem.constraints = problem_data.constraints
            problem.testcases = [t.model_dump() for t in problem_data.testcases]
            problem.hint = problem_data.hint
            problem.source = problem_data.source
            problem.tags = problem_data.tags
            problem.time_limit = problem_data.time_limit
            problem.memory_limit = problem_data.memory_limit
            problem.author = problem_data.author
            problem.difficulty = problem_data.difficulty
            session.add(problem)
            
            log_vis: LogVisibility = get_logvis_by_problem_id(problem.id)
            log_vis.public_cases = problem_data.public_cases
            session.add(log_vis)
            
        else:
            new_problem = ProblemItem(
                id=problem_data.id,
                title=problem_data.title,
                description=problem_data.description,
                input_description=problem_data.input_description,
                output_description=problem_data.output_description,
                samples=problem_data.samples,
                constraints=problem_data.constraints,
                testcases=problem_data.testcases,
                hint=problem_data.hint,
                source=problem_data.source,
                tags=problem_data.tags,
                time_limit=problem_data.time_limit,
                memory_limit=problem_data.memory_limit,
                author=problem_data.author,
                difficulty=problem_data.difficulty
            )
            session.add(new_problem)       

            new_log_vis = LogVisibility(
                problem_id=problem_data.id,
                public_cases=problem_data.public_cases
            )
            
    await session.commit() 
            
    for submission_data in data.submissions:
        # user = await get_user_by_id(submission_data.user_id, session)
        # problem = await get_problem_by_id(submission_data.problem_id, session)
        
        # if user and problem:
            submission = await get_submission_by_id(submission_data.submission_id, session)
            if submission:
                submission.user_id = submission_data.user_id
                submission.problem_id = submission_data.problem_id
                submission.language = submission_data.language
                submission.code = submission_data.code
                submission.status = SubmissionStatus(submission_data.status)
                submission.score = submission_data.score
                submission.counts = submission_data.counts
                session.add(submission)
            else:
                new_submission = SubmissionItem(
                    id=submission_data.submission_id,
                    user_id=submission_data.user_id,
                    problem_id=submission_data.problem_id,
                    language=submission_data.language,
                    code=submission_data.code,
                    status=SubmissionStatus(submission_data.status),
                    score=submission_data.score,
                    counts=submission_data.counts                    
                )
                session.add(new_submission)
            
            submission_log = await get_submission_log_by_id(submission_data.submission_id,session)
            if submission_log:
                submission_log.details = [CaseItem(**d).model_dump() for d in submission_data.details]
                submission_log.score = submission_data.score
                submission_log.counts = submission_data.counts     
            else:
                new_submission_log = SubmissionLog(
                    submission_id=submission_data.submission_id,
                    details=[d for d in submission_data.details],
                    score=submission_data.score,
                    counts=submission_data.counts
                )
                session.add(new_submission_log)  
                                    
    await session.commit()           

    
                 