from pydantic import BaseModel
from typing import List, Optional, Literal
from sqlmodel import Field, SQLModel, JSON, Relationship
from datetime import datetime


class SampleItem(BaseModel):
    input: str
    output: str

class ProblemItem(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    title: str
    description: str
    input_description: str
    output_description: str
    samples: List[SampleItem] = Field(default_factory=list, sa_type=JSON)
    constraints: str
    testcases: List[SampleItem] = Field(default_factory=list, sa_type=JSON)
    # optional
    hint: str = ""
    source: str = ""
    tags: List[str] = Field(default_factory=list, sa_type=JSON)
    time_limit: float = 0.0
    memory_limit: int = 0
    author: str = ""
    difficulty: str = ""
    
    submissions: List["SubmissionItem"] = Relationship(back_populates="problem")
    
    
class ProblemListItem(BaseModel):
    id: str
    title: str
    

# --- User ---
class UserItem(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    
    submissions: List["SubmissionItem"] = Relationship(back_populates="user")


# --- Submission ---    
class SubmissionCreate(BaseModel):
    problem_id: str
    language: str
    code: str


class SubmissionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user_item.id")
    problem_id: str = Field(foreign_key="problem_item.id")
    code: str
    status: Literal["pending", "error", "success"] = "pending"
    score: int | None = None
    counts: int 
    
    user: Optional[UserItem] = Relationship(back_populates="submissions")
    problem: Optional[ProblemItem] = Relationship(back_populates="submissions")
    