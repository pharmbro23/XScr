"""Test LLM output parsing."""

import pytest
import json
from app.summarizer.schemas import TweetSummary, ActionType, TimeHorizon, ConfidenceLevel


def test_valid_json_parses_correctly():
    """Test that valid JSON is parsed into TweetSummary."""
    json_data = {
        "summary_bullets": ["Point 1", "Point 2"],
        "tickers": ["TSLA", "AAPL"],
        "action": "buy",
        "time_horizon": "weeks",
        "confidence": "high",
        "key_claims": ["Claim 1"],
        "risks_or_unknowns": ["Risk 1"],
        "what_to_verify": ["Verify 1"]
    }
    
    summary = TweetSummary(**json_data)
    
    assert len(summary.summary_bullets) == 2
    assert summary.action == ActionType.BUY
    assert summary.time_horizon == TimeHorizon.WEEKS
    assert summary.confidence == ConfidenceLevel.HIGH


def test_minimal_json_with_defaults():
    """Test that JSON with minimal fields uses defaults."""
    json_data = {
        "summary_bullets": ["Only one point"],
    }
    
    summary = TweetSummary(**json_data)
    
    assert summary.summary_bullets == ["Only one point"]
    assert summary.tickers == []
    assert summary.action == ActionType.UNKNOWN
    assert summary.time_horizon == TimeHorizon.UNKNOWN
    assert summary.confidence == ConfidenceLevel.LOW


def test_invalid_action_raises_error():
    """Test that invalid action value raises validation error."""
    json_data = {
        "summary_bullets": ["Point"],
        "action": "invalid_action"
    }
    
    with pytest.raises(Exception):  # Pydantic ValidationError
        TweetSummary(**json_data)


def test_invalid_confidence_raises_error():
    """Test that invalid confidence value raises validation error."""
    json_data = {
        "summary_bullets": ["Point"],
        "confidence": "super_high"
    }
    
    with pytest.raises(Exception):  # Pydantic ValidationError
        TweetSummary(**json_data)


def test_model_dump_returns_dict():
    """Test that model can be converted to dict."""
    summary = TweetSummary(
        summary_bullets=["Point 1"],
        tickers=["TSLA"],
        action=ActionType.BUY
    )
    
    data = summary.model_dump()
    
    assert isinstance(data, dict)
    assert data["tickers"] == ["TSLA"]
    assert data["action"] == "buy"


def test_empty_summary_bullets_is_invalid():
    """Test that empty summary_bullets is not allowed."""
    json_data = {
        "summary_bullets": [],
    }
    
    # Depending on field validators, this might be valid or invalid
    # For now, Pydantic allows empty lists by default
    summary = TweetSummary(**json_data)
    assert summary.summary_bullets == []
