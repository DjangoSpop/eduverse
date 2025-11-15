"""
Learner profile models for tracking student progress and preferences.

Models for individual learners, their progress, achievements, and
personalized learning data.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class LearningPreferences(BaseModel):
    """Learner's preferences and learning style"""
    preferred_themes: List[str] = Field(
        default_factory=list,
        description="Favorite environment themes"
    )
    preferred_interaction_types: List[str] = Field(
        default_factory=list,
        description="Preferred types of challenges"
    )
    difficulty_preference: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Preferred difficulty level"
    )
    voice_enabled: bool = Field(
        default=True,
        description="Whether voice interactions are enabled"
    )
    hints_enabled: bool = Field(
        default=True,
        description="Whether hints are shown"
    )


class PerformanceMetrics(BaseModel):
    """Overall performance statistics"""
    total_lessons_completed: int = Field(default=0, ge=0)
    total_challenges_attempted: int = Field(default=0, ge=0)
    total_challenges_completed: int = Field(default=0, ge=0)
    success_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall success rate (0-1)"
    )
    average_completion_time_minutes: float = Field(
        default=0.0,
        ge=0.0,
        description="Average time to complete a lesson"
    )
    total_xp_earned: int = Field(default=0, ge=0, description="Total XP points")
    current_level: int = Field(default=1, ge=1, description="Current level")
    xp_to_next_level: int = Field(default=100, ge=0, description="XP needed for next level")


class SubjectProgress(BaseModel):
    """Progress in a specific subject area"""
    subject_area: str = Field(..., description="Subject name (Math, Science, etc.)")
    lessons_completed: int = Field(default=0, ge=0)
    mastery_level: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Mastery percentage (0-1)"
    )
    last_practiced: Optional[datetime] = Field(
        None,
        description="Last time this subject was practiced"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Strong areas in this subject"
    )
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        description="Areas needing more practice"
    )


class Achievement(BaseModel):
    """Individual achievement or badge"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Achievement name")
    description: str = Field(..., description="What the achievement represents")
    icon_key: str = Field(..., description="Icon asset key")
    earned_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When it was earned"
    )
    rarity: str = Field(
        default="common",
        description="Rarity level: common, uncommon, rare, epic, legendary"
    )


class StreakData(BaseModel):
    """Learning streak information"""
    current_streak_days: int = Field(default=0, ge=0, description="Current consecutive days")
    longest_streak_days: int = Field(default=0, ge=0, description="Longest streak achieved")
    last_activity_date: Optional[datetime] = Field(
        None,
        description="Last day of activity"
    )
    streak_freeze_count: int = Field(
        default=0,
        ge=0,
        description="Number of streak freezes available"
    )


class AdaptiveDifficultyState(BaseModel):
    """Current adaptive difficulty state"""
    current_difficulty: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Current difficulty level (1-5)"
    )
    recent_success_rate: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Success rate over last 10 challenges"
    )
    adjustment_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of difficulty adjustments"
    )
    last_adjusted: Optional[datetime] = Field(
        None,
        description="Last adjustment timestamp"
    )


class LearnerProfile(BaseModel):
    """
    Complete learner profile.

    Tracks all aspects of a learner's progress, preferences,
    and personalized learning journey.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Learner's name")
    age: int = Field(..., ge=4, le=18, description="Learner's age")
    grade_level: Optional[str] = Field(
        None,
        description="Grade level (e.g., 'Grade 2', 'K')"
    )
    avatar_key: str = Field(
        default="avatars/default",
        description="Avatar asset key"
    )
    preferences: LearningPreferences = Field(
        default_factory=LearningPreferences,
        description="Learning preferences"
    )
    performance: PerformanceMetrics = Field(
        default_factory=PerformanceMetrics,
        description="Overall performance metrics"
    )
    subject_progress: List[SubjectProgress] = Field(
        default_factory=list,
        description="Progress by subject area"
    )
    achievements: List[Achievement] = Field(
        default_factory=list,
        description="Earned achievements and badges"
    )
    streak: StreakData = Field(
        default_factory=StreakData,
        description="Learning streak data"
    )
    adaptive_state: AdaptiveDifficultyState = Field(
        default_factory=AdaptiveDifficultyState,
        description="Adaptive difficulty state"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Profile creation timestamp"
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity timestamp"
    )
    parent_email: Optional[str] = Field(
        None,
        description="Parent/guardian email for reports"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "learner-12345",
                "name": "Emma",
                "age": 7,
                "grade_level": "Grade 2",
                "avatar_key": "avatars/girl_01",
                "performance": {
                    "total_lessons_completed": 15,
                    "success_rate": 0.85,
                    "total_xp_earned": 1250,
                    "current_level": 3
                }
            }
        }


class LearnerCreateRequest(BaseModel):
    """Request to create a new learner profile"""
    name: str = Field(..., min_length=1, max_length=50, description="Learner's name")
    age: int = Field(..., ge=4, le=18, description="Age")
    grade_level: Optional[str] = None
    parent_email: Optional[str] = None


class LearnerUpdateRequest(BaseModel):
    """Request to update learner profile"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=4, le=18)
    grade_level: Optional[str] = None
    avatar_key: Optional[str] = None
    preferences: Optional[LearningPreferences] = None


class LearnerResponse(BaseModel):
    """Response with learner profile data"""
    id: str
    name: str
    age: int
    grade_level: Optional[str]
    avatar_key: str
    performance: PerformanceMetrics
    streak: StreakData
    created_at: datetime
    last_active: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "learner-12345",
                "name": "Emma",
                "age": 7,
                "grade_level": "Grade 2",
                "avatar_key": "avatars/girl_01",
                "performance": {},
                "streak": {},
                "created_at": "2024-01-01T00:00:00",
                "last_active": "2024-01-15T10:30:00"
            }
        }
