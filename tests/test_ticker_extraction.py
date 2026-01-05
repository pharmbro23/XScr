"""Test ticker extraction logic."""

import pytest
from app.summarizer.ticker_extractor import extract_tickers


def test_extract_dollar_sign_tickers():
    """Test extraction of $TICKER format."""
    text = "Buying $TSLA and $AAPL today"
    tickers = extract_tickers(text)
    assert "TSLA" in tickers
    assert "AAPL" in tickers


def test_extract_parenthesis_tickers():
    """Test extraction of (TICKER) format."""
    text = "Tesla (TSLA) looking strong"
    tickers = extract_tickers(text)
    assert "TSLA" in tickers


def test_extract_crypto_tickers():
    """Test extraction of crypto tickers."""
    text = "BTC and ETH both up today"
    tickers = extract_tickers(text)
    assert "BTC" in tickers
    assert "ETH" in tickers


def test_filter_false_positives():
    """Test that common false positives are filtered out."""
    text = "IT is the best way TO invest"
    tickers = extract_tickers(text)
    assert "IT" not in tickers
    assert "TO" not in tickers


def test_mixed_ticker_formats():
    """Test extraction from mixed formats."""
    text = "Long $TSLA, short (AAPL), and holding BTC"
    tickers = extract_tickers(text)
    assert "TSLA" in tickers
    assert "AAPL" in tickers
    assert "BTC" in tickers


def test_empty_text_returns_empty_list():
    """Test that empty text returns empty list."""
    assert extract_tickers("") == []


def test_no_tickers_returns_empty_list():
    """Test that text with no tickers returns empty list."""
    text = "Just some commentary about the market"
    assert extract_tickers(text) == []


def test_duplicate_tickers_are_deduplicated():
    """Test that duplicate tickers appear only once."""
    text = "$TSLA is great. I love $TSLA. TSLA to the moon!"
    tickers = extract_tickers(text)
    assert tickers.count("TSLA") == 1
