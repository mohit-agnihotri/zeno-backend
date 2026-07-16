from pydantic import BaseModel
from typing import List, Optional

class ParsedResume(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    college: Optional[str] = None
    graduation_year: Optional[int] = None
    projects: List[str] = []
    experience: List[str] = []

class ATSScoreResponse(BaseModel):
    score: int
    feedback: List[str]
    missing_keywords: List[str] = []
