from fastapi import APIRouter, Depends, UploadFile, File
from ..db.schemas import *
from ..core.errors import HTTPException, RequestValidationError
from ..db import crud
from ..db.database import ASession
from ..core.security import *
from sqlmodel import select
from config.settings import *
from pydantic import ValidationError
import json

import_router = APIRouter(prefix="/api/import")

@import_router.post("/")
async def import_data(
    session: ASession,
    file: UploadFile = File(...),
    _ = Depends(check_admin_and_get_user)
):
    # Check file type
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files supported")
    
    # Read and load file to dict
    content = await file.read()
    
    try:
        data = json.loads(content.decode('utf-8'))  
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail="File format error: {e}"
        )    
        
    try:
        data_schema = ImportFileSchema(**data)
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail="File format error: {e}"
        )

    # Validate and import data
    await crud.validate_and_import(data_schema, session=session)
    
    return {"code": 200, "msg": "import success", "data": None}
