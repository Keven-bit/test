from pydantic import BaseModel
from typing import List, Dict

class SampleItem(BaseModel):
    input: str
    output: str

class ProblemItem(BaseModel):
    id: str
    title: str
    description: str
    input_description: str
    output_description: str
    samples: List[SampleItem]
    constraints: str
    testcases: List[SampleItem]
    hint: str | None = None
    source: str | None = None
    tags: List[str] | None = None
    time_limit: float | None = None
    memory_limit: int | None = None
    author: str | None = None
    difficulty: str | None = None
    
class ProblemListItem(BaseModel):
    id: str
    title: str
    
class ProblemList(BaseModel):
    List[ProblemListItem]
    
