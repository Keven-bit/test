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
    hint: str | None = ""
    source: str | None = ""
    tags: List[str] | None = []
    time_limit: float | None = 0.0
    memory_limit: int | None = 0
    author: str | None = ""
    difficulty: str | None = ""
    
class ProblemListItem(BaseModel):
    id: str
    title: str
    
class ProblemList(BaseModel):
    List[ProblemListItem]
    
