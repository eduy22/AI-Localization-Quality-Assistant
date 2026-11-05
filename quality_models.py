
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class QualityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1)
    severity: Literal["Critical", "Major", "Minor"]
    source_excerpt: str
    target_excerpt: str
    explanation: str = Field(min_length=1)
    suggestion: str


class QualityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_assessment: str = Field(min_length=1)
    issues: list[QualityIssue]


def validate_assessment(data):
    """
    Validate the structure of an AI assessment.
    Return a normalized Python dictionary.
    """
    assessment = QualityAssessment.model_validate(data)

    return assessment.model_dump()
