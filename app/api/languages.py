from fastapi import APIRouter, Depends
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db import crud
from ..db.database import ASession
from sqlmodel import select

submissions_router = APIRouter(prefix="/api/languages")

@submissions_router.post("/")
async def register_language(language: LanguageItem, session: ASession):
    try:
        # 403 用户无权限
        session.add(language)
        await session.commit()
    except Exception as e:
        print(f"Failed to register language:{e}")
        raise HTTPException(
            status_code=500,
            detail="Server Error: Failed to register language."
        )
        
@submissions_router.get("/")
async def check_language_list(sesssion: ASession):
    try:
        name_list = []
        statement = select(LanguageItem.name)
        results = sesssion.execute(statement)
        for language in results:
            name_list.append(language.name)
        return {
            "code": 200,
            "msg": "success",
            "data":{
                "name": name_list
            }
        }
    except Exception as e:
        print(f"Failed to get language list:{e}")
        raise HTTPException(
            status_code=500,
            detail="Server Error: Failed to get language list."
        )
    