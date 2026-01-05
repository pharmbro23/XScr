"""Google Gemini LLM client for tweet summarization."""

import logging
import json
import time
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..config import settings
from .schemas import TweetSummary

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.google_api_key)


SUMMARIZATION_PROMPT = """You are a financial analyst assistant. Analyze the following tweet for investment signals and provide a structured summary.

Tweet text:
{tweet_text}

Please provide a JSON response with this EXACT structure:
{{
  "summary_bullets": ["bullet1", "bullet2", ...],
  "tickers": ["TSLA", "AAPL", ...],
  "action": "buy|sell|add|trim|short|cover|watch|unknown",
  "time_horizon": "intraday|days|weeks|months|years|unknown",
  "confidence": "low|medium|high",
  "key_claims": ["claim1", "claim2", ...],
  "risks_or_unknowns": ["risk1", "risk2", ...],
  "what_to_verify": ["item1", "item2", ...]
}}

Guidelines:
- summary_bullets: Up to 5 concise points summarizing the tweet's investment thesis
- tickers: Extract all mentioned stock/crypto tickers
- action: Primary investment action (use "unknown" if no clear action)
- time_horizon: Suggested holding period (use "unknown" if not specified)
- confidence: Your confidence in the signal (low/medium/high)
- key_claims: Factual claims that drive the thesis
- risks_or_unknowns: Potential risks or uncertainties
- what_to_verify: What a trader should independently verify

If the tweet has NO investment signal (e.g., just news/commentary), set action to "unknown" and note that in summary_bullets.

Return ONLY valid JSON, no other text."""


def summarize_tweet(tweet_text: str, handle: str, max_retries: int = 3) -> Optional[TweetSummary]:
    """
    Summarize a tweet using Google Gemini API.
    
    Args:
        tweet_text: The tweet text to summarize
        handle: Twitter handle for context
        max_retries: Maximum number of retry attempts
        
    Returns:
        TweetSummary object or None if summarization fails
    """
    logger.info(f"Summarizing tweet from @{handle}...")
    
    model = genai.GenerativeModel(
        model_name=settings.llm_model,
        generation_config={
            "temperature": 0.3,  # Lower temperature for more consistent JSON
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        },
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    
    for attempt in range(max_retries):
        try:
            # Format prompt
            prompt = SUMMARIZATION_PROMPT.format(tweet_text=tweet_text)
            
            # Call Gemini
            response = model.generate_content(prompt)
            
            # Extract text from response
            if not response.text:
                logger.warning(f"Empty response from Gemini (attempt {attempt + 1}/{max_retries})")
                continue
            
            # Parse JSON
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.strip("`").strip()
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
            
            # Parse and validate
            summary_dict = json.loads(response_text)
            summary = TweetSummary(**summary_dict)
            
            logger.info(f"✅ Successfully summarized tweet (action: {summary.action}, confidence: {summary.confidence})")
            return summary
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from Gemini (attempt {attempt + 1}/{max_retries}): {e}")
            logger.debug(f"Response text: {response.text[:200]}...")
            
        except Exception as e:
            logger.error(f"Error calling Gemini API (attempt {attempt + 1}/{max_retries}): {e}")
        
        # Exponential backoff
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            logger.info(f"Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    logger.error(f"Failed to summarize tweet after {max_retries} attempts")
    return None
