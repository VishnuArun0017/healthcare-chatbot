from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Profile(BaseModel):
    age: Optional[int] = None
    sex: Optional[Literal["male", "female", "other"]] = None
    diabetes: bool = False
    hypertension: bool = False
    pregnancy: bool = False
    city: Optional[str] = None

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: Optional[int]):
        if value is None:
            return value
        if value < 0:
            raise ValueError("Age cannot be negative")
        if value > 130:
            raise ValueError("Age must be realistic (≤130)")
        return value

    @field_validator("city")
    @classmethod
    def normalize_city(cls, value: Optional[str]):
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class ChatRequest(BaseModel):
    text: str
    lang: Literal["en", "hi", "ta", "te", "kn", "ml"] = "en"
    profile: Profile

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Query text must not be empty")
        return value.strip()


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

