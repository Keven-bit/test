from pydantic import BaseModel, Field as PydanticField, field_validator, ValidationError
from typing import List, Optional
from sqlmodel import Field, SQLModel, JSON, Relationship
from datetime import datetime, timezone
from enum import Enum
import bcrypt


# =============== Problem =============== #

class SampleItem(BaseModel):
    input: str
    output: str

class ProblemItem(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    description: str
    input_description: str
    output_description: str
    samples: List[SampleItem] = Field(sa_type=JSON)
    constraints: str
    testcases: List[SampleItem] = Field(sa_type=JSON)
    # optional
    hint: str = ""
    source: str = ""
    tags: List[str] = Field(default_factory=list, sa_type=JSON)
    time_limit: float = 3.0
    memory_limit: int = 128
    author: str = ""
    difficulty: str = ""
    
    submissions: List["SubmissionItem"] = Relationship(back_populates="problem")
    
    
class ProblemListItem(BaseModel):
    id: str
    title: str
    

# =============== User =============== #

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    BANNED = "banned"
    
class UserCreate(BaseModel):
    # Check name and password length
    username: str = PydanticField(min_length=3, max_length=40)
    password: str = PydanticField(min_length=6)

class UserItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: UserRole = UserRole.USER
    join_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submit_count: int = 0
    resolve_count: int = 0
    
    submissions: List["SubmissionItem"] = Relationship(back_populates="user")
    
    @classmethod
    def create_with_hashed_password(cls, user_create: UserCreate, role: UserRole = "user"):
        hashed_password = bcrypt.hashpw(user_create.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        return cls(username=user_create.username,hashed_password=hashed_password, role=role)
    
    def verify_password(self, password:str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))
    

class UserListQuery(BaseModel):
    """
    schema for user list query.
    """
    page: int | None = None
    page_size: int | None = None
    
    @field_validator('*', mode="after")
    @classmethod
    def validate_query_params(cls, value, info):
        """
        validates query params, if params are wrong, raises ValueError.
        """
        data = info.data
        
        page = data.get("page")
        page_size = data.get("page_size")
        
        if page is None and page_size is not None:
            data['page'] = 1
        elif page is not None and page_size is None:
            raise ValueError  
    
        return value  
    
    
# =============== Submission =============== #  

class SubmissionCreate(BaseModel):
    problem_id: str
    language: str
    code: str


class SubmissionStatus(str, Enum):
    PENDING = "pending"
    ERROR = "error"
    SUCCESS = "success"


class SubmissionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user_item.id")
    problem_id: str = Field(foreign_key="problem_item.id")
    code: str
    status: SubmissionStatus = SubmissionStatus.PENDING
    score: int | None = None
    counts: int 
    
    user: Optional[UserItem] = Relationship(back_populates="submissions")
    problem: Optional[ProblemItem] = Relationship(back_populates="submissions")
    
    
class SubmissionListQuery(BaseModel):
    """
    schema for submission list query.
    """
    user_id: int | None = None
    problem_id: str | None = None
    status: SubmissionStatus | None = None
    page: int | None = None
    page_size: int | None = None
    
    @field_validator('*', mode="after")
    @classmethod
    def validate_query_params(cls, value, info):
        """
        validates query params, if params are wrong, raises ValueError.
        """
        data = info.data
        
        if data.get("user_id") is None and data.get("problem_id") is None:
            raise ValueError
        
        page = data.get("page")
        page_size = data.get("page_size")
        
        if page is None and page_size is not None:
            data['page'] = 1
        elif page is not None and page_size is None:
            raise ValueError  
        
        return value  
        
        
# =============== Language =============== #

class LanguageItem(SQLModel, table=True):
    name: str = Field(primary_key=True)
    file_ext: str
    complie_cmd: str | None = None
    run_cmd: str
    time_limit: float = None
    memory_limit: int = None
    
    
    