"""Twitter authentication using Playwright."""

import logging
import json
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser

from ..config import settings
from ..database import get_session_cookies, save_session_cookies

logger = logging.getLogger(__name__)


def authenticate_twitter() -> dict:
    """
    Authenticate with Twitter using Playwright and return session cookies.
    
    Returns:
        Dictionary of session cookies
        
    Raises:
        RuntimeError: If authentication fails
    """
    logger.info("Starting Twitter authentication with Playwright...")
    
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=False)  # Non-headless for 2FA
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page: Page = context.new_page()
        
        try:
            # Navigate to Twitter login
            logger.info("Navigating to Twitter login page...")
            page.goto("https://twitter.com/i/flow/login", wait_until="networkidle")
            
            # Wait for username input and fill it
            logger.info("Entering username...")
            page.wait_for_selector('input[autocomplete="username"]', timeout=15000)
            page.fill('input[autocomplete="username"]', settings.twitter_username)
            page.keyboard.press("Enter")
            
            # Check if phone/email verification is needed
            page.wait_for_timeout(2000)
            
            # Try to detect unusual activity prompt (phone/email verification)
            if page.locator('input[data-testid="ocfEnterTextTextInput"]').count() > 0:
                logger.warning("Twitter is asking for additional verification (phone/email)")
                logger.warning("Please complete the verification manually in the browser window")
                page.wait_for_selector('input[name="password"]', timeout=120000)  # Wait up to 2 min
            
            # Wait for password input and fill it
            logger.info("Entering password...")
            page.wait_for_selector('input[name="password"]', timeout=15000)
            page.fill('input[name="password"]', settings.twitter_password)
            page.keyboard.press("Enter")
            
            # Check for 2FA
            page.wait_for_timeout(3000)
            if page.locator('input[data-testid="ocfEnterTextTextInput"]').count() > 0:
                logger.warning("2FA detected - please enter your code manually in the browser")
                page.wait_for_url("**/home", timeout=120000)  # Wait up to 2 min for manual 2FA
            else:
                # Wait for redirect to home page
                logger.info("Waiting for authentication to complete...")
                page.wait_for_url("**/home", timeout=30000)
            
            logger.info("✅ Authentication successful!")
            
            # Extract cookies
            cookies = context.cookies()
            cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
            
            # Save to database
            save_session_cookies(cookie_dict)
            
            return cookie_dict
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise RuntimeError(f"Twitter authentication failed: {e}")
        finally:
            browser.close()


def ensure_session() -> dict:
    """
    Ensure a valid Twitter session exists, authenticating if necessary.
    
    Returns:
        Dictionary of session cookies
    """
    # Try to get existing session
    cookies = get_session_cookies()
    
    if cookies:
        logger.info("Found existing Twitter session cookies")
        # TODO: Validate cookies are still valid by making a test request
        return cookies
    
    # No session exists, authenticate
    logger.info("No existing session found, authenticating...")
    return authenticate_twitter()
