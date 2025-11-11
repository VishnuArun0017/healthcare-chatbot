from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any


class Profile(BaseModel):
    age: Optional[int] = None
    sex: Optional[Literal["male", "female", "other"]] = None
    diabetes: bool = False
    hypertension: bool = False
    city: Optional[str] = None


class ChatRequest(BaseModel):
    text: str
    lang: Literal["en", "hi"] = "en"
    profile: Profile


class Safety(BaseModel):
    red_flag: bool = False
    matched: List[str] = []


class Fact(BaseModel):
    type: str
    data: Any


class Citation(BaseModel):
    source: str
    id: str
    topic: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    route: Literal["graph", "vector"]
    facts: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []
    safety: Safety


