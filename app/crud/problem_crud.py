from ..schemas.problem import *
from typing import List
from fastapi.exceptions import HTTPException
from ..database import ASession
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession


PROBLEM_DATA_PATH = "data/problems"


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

