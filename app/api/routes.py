"""FastAPI routes for managing tracked handles."""

import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..database import (
    add_tracked_handle,
    remove_tracked_handle,
    list_tracked_handles,
    TrackedHandle,
)
from ..scheduler import poll_tweets_once

logger = logging.getLogger(__name__)

router = APIRouter()


class AddHandleRequest(BaseModel):
    """Request model for adding a handle."""
    handle: str = Field(..., description="Twitter handle (with or without @)")


class HandleResponse(BaseModel):
    """Response model for a tracked handle."""
    id: int
    handle: str
    user_id: str | None
    last_seen_tweet_id: str | None
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class PollStatsResponse(BaseModel):
    """Response model for polling statistics."""
    tweets_fetched: int
    tweets_processed: int
    tweets_skipped_duplicate: int
    alerts_sent: int
    errors: int


@router.post("/tracks", response_model=HandleResponse, status_code=status.HTTP_201_CREATED)
async def add_handle(request: AddHandleRequest):
    """Add a new Twitter handle to track."""
    try:
        handle = add_tracked_handle(request.handle)
        logger.info(f"Added handle: @{handle.handle}")
        return HandleResponse(**handle.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding handle: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/tracks/{handle}", response_model=MessageResponse)
async def delete_handle(handle: str):
    """Remove a tracked Twitter handle."""
    try:
        removed = remove_tracked_handle(handle)
        if not removed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Handle '{handle}' not found")
        
        logger.info(f"Removed handle: @{handle}")
        return MessageResponse(message=f"Handle '{handle}' removed successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing handle: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/tracks", response_model=list[HandleResponse])
async def get_handles():
    """List all tracked Twitter handles."""
    try:
        handles = list_tracked_handles()
        return [HandleResponse(**h.__dict__) for h in handles]
    except Exception as e:
        logger.error(f"Error listing handles: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/health", response_model=MessageResponse)
async def health_check():
    """Health check endpoint."""
    # TODO: Could add Telegram connectivity check here
    return MessageResponse(message="OK")


@router.post("/manual-poll", response_model=PollStatsResponse)
async def trigger_manual_poll():
    """Manually trigger a poll cycle (for testing)."""
    try:
        logger.info("Manual poll triggered via API")
        stats = poll_tweets_once()
        return PollStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error during manual poll: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
