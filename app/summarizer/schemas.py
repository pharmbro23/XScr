"""Pydantic schemas for LLM output validation."""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Investment action types."""
    BUY = "buy"
    SELL = "sell"
    ADD = "add"
    TRIM = "trim"
    SHORT = "short"
    COVER = "cover"
    WATCH = "watch"
    UNKNOWN = "unknown"


class TimeHorizon(str, Enum):
    """Investment time horizons."""
    INTRADAY = "intraday"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Confidence levels for the analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TweetSummary(BaseModel):
    """Structured output from LLM summarization."""
    
    summary_bullets: List[str] = Field(
        description="Up to 5 key summary points",
        max_length=5
    )
    tickers: List[str] = Field(
        description="List of ticker symbols mentioned",
        default_factory=list
    )
    action: ActionType = Field(
        description="Primary investment action suggested",
        default=ActionType.UNKNOWN
    )
    time_horizon: TimeHorizon = Field(
        description="Suggested investment time horizon",
        default=TimeHorizon.UNKNOWN
    )
    confidence: ConfidenceLevel = Field(
        description="Confidence level of the analysis",
        default=ConfidenceLevel.LOW
    )
    key_claims: List[str] = Field(
        description="Key factual claims made in the tweet",
        default_factory=list
    )
    risks_or_unknowns: List[str] = Field(
        description="Identified risks or unknowns",
        default_factory=list
    )
    what_to_verify: List[str] = Field(
        description="What should be independently verified",
        default_factory=list
    )
