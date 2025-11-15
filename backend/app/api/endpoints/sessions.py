"""
Sessions API endpoints for tracking learning sessions and analytics.

Handles session creation, event logging, and analytics retrieval.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.storage import memory_store
from app.models.analytics import (
    LearningSession,
    SessionStartRequest,
    SessionEventRequest,
    SessionEndRequest,
    SessionSummary,
    SessionEvent
)
from app.core.logging import get_logger
from app.utils.helpers import calculate_success_rate

logger = get_logger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start", response_model=LearningSession)
async def start_session(request: SessionStartRequest):
    """
    Start a new learning session.

    Args:
        request: Session start parameters

    Returns:
        Created session

    Raises:
        404: Learner or lesson not found
    """
    logger.info(f"Starting session: learner={request.learner_id}, lesson={request.lesson_id}")

    # Verify learner exists
    learner = memory_store.get_learner(request.learner_id)
    if not learner:
        raise HTTPException(
            status_code=404,
            detail=f"Learner not found: {request.learner_id}"
        )

    # Verify lesson exists
    lesson = memory_store.get_lesson(request.lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=404,
            detail=f"Lesson not found: {request.lesson_id}"
        )

    # Create session
    session = LearningSession(
        learner_id=request.learner_id,
        lesson_id=request.lesson_id,
        lesson_title=lesson.get("title", "Untitled Lesson"),
        device_info=request.device_info,
        status="in_progress"
    )

    # Store session
    memory_store.save_session(session.id, session.model_dump())

    logger.info(f"Session created: {session.id}")

    return session


@router.post("/event")
async def log_event(request: SessionEventRequest):
    """
    Log an event in a session.

    Args:
        request: Event details

    Returns:
        Success message

    Raises:
        404: Session not found
    """
    logger.debug(f"Logging event for session: {request.session_id}")

    # Retrieve session
    session_data = memory_store.get_session(request.session_id)
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_id}"
        )

    session = LearningSession(**session_data)

    # Create event
    event = SessionEvent(
        event_type=request.event_type,
        event_data=request.event_data,
        success=request.success,
        xp_earned=request.xp_earned
    )

    # Add to session
    session.events.append(event)
    session.total_xp_earned += request.xp_earned

    # Update session
    memory_store.update_session(session.id, session.model_dump())

    return {"message": "Event logged successfully", "event_type": request.event_type}


@router.post("/end")
async def end_session(request: SessionEndRequest):
    """
    End a learning session.

    Args:
        request: Session end parameters

    Returns:
        Session summary

    Raises:
        404: Session not found
    """
    logger.info(f"Ending session: {request.session_id}")

    # Retrieve session
    session_data = memory_store.get_session(request.session_id)
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_id}"
        )

    session = LearningSession(**session_data)

    # Update session
    session.ended_at = datetime.utcnow()
    session.completion_percentage = request.completion_percentage
    session.status = request.status

    # Calculate duration
    if session.started_at:
        duration = (session.ended_at - session.started_at).total_seconds()
        session.total_duration_seconds = duration

    # Calculate success rate
    if session.challenges:
        completed = sum(1 for c in session.challenges if c.success)
        session.success_rate = calculate_success_rate(completed, len(session.challenges))

    # Update storage
    memory_store.update_session(session.id, session.model_dump())

    logger.info(f"Session ended: {session.id} (duration={session.total_duration_seconds}s)")

    # Return summary
    return SessionSummary(
        session_id=session.id,
        learner_id=session.learner_id,
        lesson_title=session.lesson_title,
        duration_minutes=session.total_duration_seconds / 60.0,
        total_xp_earned=session.total_xp_earned,
        challenges_completed=sum(1 for c in session.challenges if c.success),
        challenges_attempted=len(session.challenges),
        success_rate=session.success_rate,
        completion_percentage=session.completion_percentage,
        started_at=session.started_at,
        ended_at=session.ended_at
    )


@router.get("/{session_id}", response_model=LearningSession)
async def get_session(session_id: str):
    """
    Retrieve session by ID.

    Args:
        session_id: Session identifier

    Returns:
        Complete session data

    Raises:
        404: Session not found
    """
    logger.debug(f"Retrieving session: {session_id}")

    session_data = memory_store.get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}"
        )

    return LearningSession(**session_data)


@router.get("/learner/{learner_id}", response_model=List[SessionSummary])
async def get_learner_sessions(
    learner_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all sessions for a learner.

    Args:
        learner_id: Learner identifier
        skip: Number of items to skip
        limit: Maximum items to return

    Returns:
        List of session summaries
    """
    logger.debug(f"Retrieving sessions for learner: {learner_id}")

    # Get learner's sessions
    sessions = memory_store.get_learner_sessions(learner_id)

    # Sort by start time (most recent first)
    sessions.sort(
        key=lambda x: x.get("started_at", ""),
        reverse=True
    )

    # Apply pagination
    paginated = sessions[skip:skip + limit]

    # Convert to summaries
    summaries = []
    for session_data in paginated:
        try:
            session = LearningSession(**session_data)
            duration = session.total_duration_seconds / 60.0 if session.total_duration_seconds else 0.0

            summary = SessionSummary(
                session_id=session.id,
                learner_id=session.learner_id,
                lesson_title=session.lesson_title,
                duration_minutes=duration,
                total_xp_earned=session.total_xp_earned,
                challenges_completed=sum(1 for c in session.challenges if c.success),
                challenges_attempted=len(session.challenges),
                success_rate=session.success_rate,
                completion_percentage=session.completion_percentage,
                started_at=session.started_at,
                ended_at=session.ended_at
            )
            summaries.append(summary)
        except Exception as e:
            logger.warning(f"Failed to create summary for session: {str(e)}")
            continue

    return summaries
