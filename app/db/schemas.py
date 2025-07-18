from pydantic import BaseModel, Field as PydanticField, field_validator, model_validator
from typing import List, Optional, Dict
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.types import JSON
from datetime import datetime, timezone
from enum import Enum
import bcrypt
import uuid


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
    log_visibility: Optional["LogVisibility"] = Relationship(back_populates="problem")
    
    
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
    id: Optional[str] = Field(default=None, primary_key=True)
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
        return cls(
            username=user_create.username,
            hashed_password=hashed_password,
            role=role,
            id=str(uuid.uuid4())
        )
    
    def verify_password(self, password:str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))
    

class UserListQuery(BaseModel):
    """
    schema for user list query.
    """
    page: int | None = None
    page_size: int | None = None
    
    
    
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
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="useritem.id")
    problem_id: str = Field(foreign_key="problemitem.id")
    language: str
    code: str
    status: SubmissionStatus = SubmissionStatus.PENDING
    score: int | None = None
    counts: int 
    
    user: Optional[UserItem] = Relationship(back_populates="submissions") 
    problem: Optional[ProblemItem] = Relationship(back_populates="submissions") 
    submission_log: Optional["SubmissionLog"] = Relationship(back_populates="submission")
    
class SubmissionListQuery(BaseModel):
    """
    schema for submission list query.
    """
    user_id: str | None = None
    problem_id: str | None = None
    status: SubmissionStatus | None = None
    page: int | None = None
    page_size: int | None = None
    
        
# =============== Submission Log =============== #

class CaseResult(str, Enum):
    AC = "AC"
    WA = "WA"
    TLE = "TLE"
    MLE = "MLE"
    RE = "RE"
    CE = "CE"
    UNK = "UNK"
    
    
class CaseItem(BaseModel):
    id: int
    result: CaseResult
    time: float
    memory: int
    

class SubmissionLog(SQLModel, table=True):
    submission_id: str = Field(primary_key=True, foreign_key="submissionitem.id")
    details: List[Dict] = Field(sa_type=JSON)
    score: int
    counts: int
    
    submission: Optional[SubmissionItem] = Relationship(back_populates="submission_log")
    
    
class LogVisibility(SQLModel, table=True):
    problem_id: str = Field(primary_key=True, foreign_key="problemitem.id")
    public_cases: bool = False 

    problem: Optional[ProblemItem] = Relationship(back_populates="log_visibility")
    

# =============== Log Access =============== #

class LogAccessQuery(BaseModel):
    user_id: str | None = None
    problem_id: str | None = None
    page: int | None = None
    page_size: int | None = None
    

class LogAccess(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    problem_id: str
    action: str = "view_log"
    time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str


class LogVisibilityUpdate(BaseModel):
    public_cases: bool = False

        
# =============== Language =============== #

class LanguageItem(SQLModel, table=True):
    name: str = Field(primary_key=True)
    file_ext: str
    complie_cmd: str | None = None
    run_cmd: str
    time_limit: float | None = None
    memory_limit: int | None = None
    

# =============== Import =============== #  

class ImportUserData(BaseModel):
    user_id: str
    username: str
    password: str
    role: str
    join_time: str
    submit_count: int
    resolve_count: int


class ImportProblemData(BaseModel):
    id: str
    title: str
    description: str
    input_description: str
    output_description: str
    samples: List[Dict] 
    constraints: str
    testcases: List[Dict] 
    hint: str
    source: str
    tags: List[str] = PydanticField(default_factory=list)
    time_limit: float
    memory_limit: int
    author: str
    difficulty: str
    public_cases: bool = False


class ImportSubmissionData(BaseModel):
    submission_id: str
    user_id: str
    problem_id: str
    language: str
    code: str
    status: str
    details: List[Dict] 
    score: int
    counts: int


class ImportFileSchema(BaseModel):
    users: List[ImportUserData]
    problems: List[ImportProblemData]
    submissions: List[ImportSubmissionData]
    

    
    
    