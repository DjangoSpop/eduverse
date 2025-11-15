"""
Gamification models for XP, levels, badges, and rewards.

Models for the gamification system that keeps learners engaged
and motivated through game-like progression mechanics.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import uuid


class BadgeRarity(str, Enum):
    """Badge rarity levels"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class BadgeDefinition(BaseModel):
    """
    Definition of an achievement badge.

    Defines the criteria and metadata for earning a badge.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Badge name")
    description: str = Field(..., description="What the badge represents")
    icon_key: str = Field(..., description="Icon asset key")
    rarity: BadgeRarity = Field(default=BadgeRarity.COMMON)
    criteria_type: str = Field(
        ...,
        description="Type of criteria: lessons_completed, streak_days, xp_milestone, subject_mastery, etc."
    )
    criteria_value: int = Field(..., ge=1, description="Value required to earn")
    xp_reward: int = Field(default=0, ge=0, description="XP bonus for earning")
    subject_area: Optional[str] = Field(
        None,
        description="Subject-specific badge (null for general)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "badge-001",
                "name": "Ocean Explorer",
                "description": "Complete 5 ocean-themed lessons",
                "icon_key": "badges/ocean_explorer",
                "rarity": "uncommon",
                "criteria_type": "theme_lessons_completed",
                "criteria_value": 5,
                "xp_reward": 100
            }
        }


class LevelDefinition(BaseModel):
    """
    Level progression definition.

    Defines XP requirements and rewards for each level.
    """
    level: int = Field(..., ge=1, description="Level number")
    xp_required: int = Field(..., ge=0, description="Total XP needed to reach")
    xp_from_previous: int = Field(
        ...,
        ge=0,
        description="XP needed from previous level"
    )
    title: str = Field(..., description="Level title (e.g., 'Novice Explorer')")
    rewards: List[str] = Field(
        default_factory=list,
        description="Rewards unlocked at this level"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "level": 5,
                "xp_required": 1000,
                "xp_from_previous": 200,
                "title": "Skilled Adventurer",
                "rewards": ["New avatar options", "Special effects"]
            }
        }


class XPTransaction(BaseModel):
    """
    Record of XP earned or spent.

    Tracks all XP changes for audit and analytics.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    learner_id: str = Field(..., description="Learner ID")
    amount: int = Field(..., description="XP amount (positive for earned, negative for spent)")
    source: str = Field(
        ...,
        description="Source of XP: challenge_completed, lesson_completed, badge_earned, etc."
    )
    source_id: Optional[str] = Field(
        None,
        description="ID of the source (challenge ID, lesson ID, etc.)"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "xp-12345",
                "learner_id": "learner-456",
                "amount": 50,
                "source": "challenge_completed",
                "source_id": "challenge-789",
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class RewardItem(BaseModel):
    """
    Unlockable reward item.

    Represents avatars, themes, effects, or other cosmetic rewards.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Reward name")
    description: str = Field(..., description="Reward description")
    category: str = Field(
        ...,
        description="Category: avatar, theme, effect, sticker, etc."
    )
    asset_key: str = Field(..., description="Asset reference key")
    unlock_requirement: str = Field(
        ...,
        description="How to unlock: level_5, badge_ocean_explorer, etc."
    )
    rarity: BadgeRarity = Field(default=BadgeRarity.COMMON)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "reward-001",
                "name": "Astronaut Avatar",
                "description": "Dress up as an astronaut!",
                "category": "avatar",
                "asset_key": "avatars/astronaut_01",
                "unlock_requirement": "level_10",
                "rarity": "rare"
            }
        }


class DailyChallenge(BaseModel):
    """
    Daily challenge for bonus XP.

    Provides additional motivation for daily engagement.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = Field(default_factory=datetime.utcnow, description="Challenge date")
    title: str = Field(..., description="Challenge title")
    description: str = Field(..., description="What needs to be done")
    requirement: str = Field(
        ...,
        description="Specific requirement: complete_1_lesson, earn_100_xp, etc."
    )
    requirement_value: int = Field(..., ge=1)
    xp_reward: int = Field(..., ge=0, description="Bonus XP for completion")
    expires_at: datetime = Field(..., description="Challenge expiration time")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "daily-001",
                "date": "2024-01-15T00:00:00",
                "title": "Math Master Monday",
                "description": "Complete 2 math lessons today!",
                "requirement": "complete_math_lessons",
                "requirement_value": 2,
                "xp_reward": 100,
                "expires_at": "2024-01-15T23:59:59"
            }
        }


class Leaderboard(BaseModel):
    """
    Leaderboard entry.

    Supports friendly competition and social motivation.
    """
    rank: int = Field(..., ge=1, description="Current rank")
    learner_id: str = Field(..., description="Learner ID")
    learner_name: str = Field(..., description="Display name")
    avatar_key: str = Field(..., description="Avatar")
    score: int = Field(..., ge=0, description="Score (XP or other metric)")
    metric_type: str = Field(
        ...,
        description="What's being ranked: total_xp, weekly_xp, lessons_completed, etc."
    )
    time_period: str = Field(
        ...,
        description="Time period: all_time, weekly, monthly, daily"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "learner_id": "learner-456",
                "learner_name": "Emma",
                "avatar_key": "avatars/girl_01",
                "score": 2500,
                "metric_type": "weekly_xp",
                "time_period": "weekly"
            }
        }


class GamificationState(BaseModel):
    """
    Current gamification state for a learner.

    Aggregates all gamification data for quick access.
    """
    learner_id: str = Field(..., description="Learner ID")
    total_xp: int = Field(default=0, ge=0, description="Lifetime XP")
    current_level: int = Field(default=1, ge=1, description="Current level")
    xp_to_next_level: int = Field(default=100, ge=0, description="XP needed for next level")
    level_progress_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Progress to next level (0-1)"
    )
    badges_earned: List[str] = Field(
        default_factory=list,
        description="List of badge IDs earned"
    )
    unlocked_rewards: List[str] = Field(
        default_factory=list,
        description="List of reward IDs unlocked"
    )
    daily_challenge_completed: bool = Field(
        default=False,
        description="Whether today's daily challenge is complete"
    )
    current_streak_days: int = Field(default=0, ge=0)
    longest_streak_days: int = Field(default=0, ge=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "learner_id": "learner-456",
                "total_xp": 1250,
                "current_level": 5,
                "xp_to_next_level": 150,
                "level_progress_percentage": 0.60,
                "badges_earned": ["badge-001", "badge-003"],
                "unlocked_rewards": ["reward-001", "reward-002"],
                "daily_challenge_completed": True,
                "current_streak_days": 7,
                "longest_streak_days": 14
            }
        }


class XPAwardRequest(BaseModel):
    """Request to award XP to a learner"""
    learner_id: str = Field(..., description="Learner ID")
    amount: int = Field(..., gt=0, description="XP amount to award")
    source: str = Field(..., description="Source of XP")
    source_id: Optional[str] = Field(None, description="Source ID")
    metadata: Dict = Field(default_factory=dict)


class XPAwardResponse(BaseModel):
    """Response from XP award operation"""
    learner_id: str
    xp_awarded: int
    total_xp: int
    previous_level: int
    current_level: int
    level_up: bool = Field(..., description="Whether learner leveled up")
    new_badges: List[str] = Field(
        default_factory=list,
        description="Badges earned from this action"
    )
    new_rewards: List[str] = Field(
        default_factory=list,
        description="Rewards unlocked"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "learner_id": "learner-456",
                "xp_awarded": 50,
                "total_xp": 1300,
                "previous_level": 5,
                "current_level": 5,
                "level_up": False,
                "new_badges": [],
                "new_rewards": []
            }
        }
