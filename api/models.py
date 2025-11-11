from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class Profile(BaseModel):
    age: Optional[int] = None
    sex: Optional[Literal["male", "female", "other"]] = None
    diabetes: bool = False
    hypertension: bool = False
    pregnancy: bool = False
    city: Optional[str] = None


class ChatRequest(BaseModel):
    text: str
    lang: Literal["en", "hi", "ta", "te", "kn", "ml"] = "en"
    profile: Profile


class MentalHealthSafety(BaseModel):
    crisis: bool = False
    matched: List[str] = Field(default_factory=list)
    first_aid: List[str] = Field(default_factory=list)


class PregnancySafety(BaseModel):
    concern: bool = False
    matched: List[str] = Field(default_factory=list)


class Safety(BaseModel):
    red_flag: bool = False
    matched: List[str] = Field(default_factory=list)
    mental_health: MentalHealthSafety = Field(default_factory=MentalHealthSafety)
    pregnancy: PregnancySafety = Field(default_factory=PregnancySafety)


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
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    safety: Safety

