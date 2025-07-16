from fastapi import APIRouter, Depends
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db.database import ASession
from sqlmodel import select
from ..core.security import *

languages_router = APIRouter(prefix="/api/languages")

@languages_router.post("/")
async def register_language(
    language: LanguageItem, 
    session: ASession,
    _ = Depends(check_login_and_get_user)
):
    try:
        session.add(language)
        await session.commit()
        return {
            "code": 200,
            "msg": "language registered",
            "data": {
                "name": language.name
            }
        }
    except Exception as e:
        print(f"Failed to register language:{e}")
        raise HTTPException(
            status_code=500,
            detail="Server Error: Failed to register language."
        )
        
@languages_router.get("/")
async def check_language_list(session: ASession):
    try:
        name_list = []
        statement = select(LanguageItem.name)
        results = await session.execute(statement)
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
    