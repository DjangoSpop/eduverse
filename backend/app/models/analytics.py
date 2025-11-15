"""
Analytics models for tracking learning sessions and performance.

Models for session data, events, and analytics insights.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class SessionEvent(BaseModel):
    """Individual event within a learning session"""
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp"
    )
    event_type: str = Field(
        ...,
        description="Type of event (challenge_started, challenge_completed, scene_entered, etc.)"
    )
    event_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data"
    )
    success: Optional[bool] = Field(
        None,
        description="Whether the event represents a success (if applicable)"
    )
    xp_earned: int = Field(default=0, ge=0, description="XP earned from this event")


class ChallengeAttempt(BaseModel):
    """Record of a single challenge attempt"""
    challenge_id: str = Field(..., description="Challenge identifier")
    challenge_type: str = Field(..., description="Type of challenge")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    success: bool = Field(..., description="Whether completed successfully")
    attempts_count: int = Field(default=1, ge=1, description="Number of attempts")
    hint_used: bool = Field(default=False, description="Whether hint was used")
    time_spent_seconds: float = Field(default=0.0, ge=0.0)
    xp_earned: int = Field(default=0, ge=0)
    learner_answer: Optional[str] = Field(
        None,
        description="Learner's answer (if applicable)"
    )
    correct_answer: Optional[str] = Field(
        None,
        description="Correct answer for reference"
    )


class SceneProgress(BaseModel):
    """Progress through a single scene"""
    scene_id: str = Field(..., description="Scene identifier")
    scene_name: str = Field(..., description="Scene name")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    time_spent_seconds: float = Field(default=0.0, ge=0.0)
    challenges_attempted: int = Field(default=0, ge=0)
    challenges_completed: int = Field(default=0, ge=0)
    objects_interacted: int = Field(default=0, ge=0, description="Number of objects interacted with")
    xp_earned: int = Field(default=0, ge=0)
    completed: bool = Field(default=False)


class LearningSession(BaseModel):
    """
    Complete learning session record.

    Tracks everything that happens during a single play session.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    learner_id: str = Field(..., description="Learner who played this session")
    lesson_id: str = Field(..., description="Lesson being played")
    lesson_title: str = Field(..., description="Lesson title")
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session start time"
    )
    ended_at: Optional[datetime] = Field(
        None,
        description="Session end time (null if ongoing)"
    )
    total_duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total session duration"
    )
    scenes_progress: List[SceneProgress] = Field(
        default_factory=list,
        description="Progress through each scene"
    )
    challenges: List[ChallengeAttempt] = Field(
        default_factory=list,
        description="All challenge attempts"
    )
    events: List[SessionEvent] = Field(
        default_factory=list,
        description="Detailed event log"
    )
    total_xp_earned: int = Field(default=0, ge=0, description="Total XP earned")
    completion_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Lesson completion percentage (0-1)"
    )
    success_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Challenge success rate (0-1)"
    )
    difficulty_level_start: int = Field(default=3, ge=1, le=5)
    difficulty_level_end: int = Field(default=3, ge=1, le=5)
    status: str = Field(
        default="in_progress",
        description="Session status: in_progress, completed, abandoned"
    )
    device_info: Optional[Dict[str, str]] = Field(
        None,
        description="Device and platform information"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "session-12345",
                "learner_id": "learner-456",
                "lesson_id": "lesson-789",
                "lesson_title": "Ocean Adventure",
                "started_at": "2024-01-15T10:00:00",
                "total_xp_earned": 150,
                "completion_percentage": 0.65,
                "success_rate": 0.80,
                "status": "in_progress"
            }
        }


class SessionStartRequest(BaseModel):
    """Request to start a new learning session"""
    learner_id: str = Field(..., description="Learner ID")
    lesson_id: str = Field(..., description="Lesson ID")
    device_info: Optional[Dict[str, str]] = Field(
        None,
        description="Device information"
    )


class SessionEventRequest(BaseModel):
    """Request to log an event in a session"""
    session_id: str = Field(..., description="Session ID")
    event_type: str = Field(..., description="Event type")
    event_data: Dict[str, Any] = Field(default_factory=dict)
    success: Optional[bool] = None
    xp_earned: int = Field(default=0, ge=0)


class SessionEndRequest(BaseModel):
    """Request to end a session"""
    session_id: str = Field(..., description="Session ID")
    completion_percentage: float = Field(..., ge=0.0, le=1.0)
    status: str = Field(
        default="completed",
        description="Final status: completed or abandoned"
    )


class SessionSummary(BaseModel):
    """Summary of a completed session"""
    session_id: str
    learner_id: str
    lesson_title: str
    duration_minutes: float
    total_xp_earned: int
    challenges_completed: int
    challenges_attempted: int
    success_rate: float
    completion_percentage: float
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session-12345",
                "learner_id": "learner-456",
                "lesson_title": "Ocean Adventure",
                "duration_minutes": 18.5,
                "total_xp_earned": 150,
                "challenges_completed": 12,
                "challenges_attempted": 15,
                "success_rate": 0.80,
                "completion_percentage": 1.0,
                "started_at": "2024-01-15T10:00:00",
                "ended_at": "2024-01-15T10:18:30"
            }
        }


class AnalyticsInsight(BaseModel):
    """Analytics insight for teachers/parents"""
    insight_type: str = Field(
        ...,
        description="Type of insight: strength, weakness, recommendation, achievement"
    )
    subject_area: Optional[str] = Field(None, description="Related subject")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed insight")
    data_points: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supporting data"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="Recommended actions"
    )


class LearnerAnalytics(BaseModel):
    """Comprehensive analytics for a learner"""
    learner_id: str
    time_period_days: int = Field(
        ...,
        description="Time period for analytics (e.g., 7, 30, 90)"
    )
    total_sessions: int = Field(default=0, ge=0)
    total_time_minutes: float = Field(default=0.0, ge=0.0)
    average_session_duration_minutes: float = Field(default=0.0, ge=0.0)
    total_xp_earned: int = Field(default=0, ge=0)
    overall_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    subjects_practiced: List[str] = Field(default_factory=list)
    insights: List[AnalyticsInsight] = Field(default_factory=list)
    progress_trend: str = Field(
        ...,
        description="Overall trend: improving, stable, declining"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "learner_id": "learner-456",
                "time_period_days": 30,
                "total_sessions": 15,
                "total_time_minutes": 285.0,
                "average_session_duration_minutes": 19.0,
                "total_xp_earned": 2150,
                "overall_success_rate": 0.82,
                "subjects_practiced": ["Math", "Science", "Reading"],
                "insights": [],
                "progress_trend": "improving",
                "generated_at": "2024-01-15T12:00:00"
            }
        }
