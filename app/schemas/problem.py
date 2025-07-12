from pydantic import BaseModel
from typing import List, Dict
from sqlmodel import Field, Session, SQLModel, create_engine, select, JSON


class Config:
    from_attributes = True

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
    
class ProblemListItem(BaseModel):
    id: str
    title: str
    
# class ProblemList(BaseModel):
#     data: List[ProblemListItem]
    
