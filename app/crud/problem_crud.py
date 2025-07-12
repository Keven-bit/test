import aiofiles
import json
from pathlib import Path
from ..schemas import problem
from typing import List, Dict, Any
from fastapi.exceptions import HTTPException


PROBLEM_DATA_PATH = "data/problems"

async def get_all_problems_meta():
    """
    Read local problem data and return as ProblemList.
    """
    problemlist = []
    data_path = Path(PROBLEM_DATA_PATH)
    for file in data_path.glob("*.json"):
        async with aiofiles.open(file, "r") as f:
            content = await f.read()
            problem_data = json.load(content)
            problemlist.append({
                "id": problem_data["id"],
                "title": problem_data["title"]
            })
    return problemlist

async def write_json(file_path: str, data: Dict[str, Any]) -> None:
    """
    Write data to file_path as json.
    """
    try:
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File write error: {e}"
        )

async def problem_exists(problem_id: str, data_path: str = PROBLEM_DATA_PATH) -> bool:
    file_path = Path(data_path) / f"problem_{problem_id}.json"
    return await aiofiles.os.path.exists(file_path)
