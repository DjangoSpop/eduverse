"""
Scene specification models for Unity world generation.

These models define the complete structure of an interactive lesson,
including scenes, game objects, challenges, and learning objectives.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
from enum import Enum
import uuid


class ThemeType(str, Enum):
    """Available environment themes for lessons"""
    OCEAN = "ocean"
    SPACE = "space"
    JUNGLE = "jungle"
    CITY = "city"
    LAB = "lab"
    FANTASY = "fantasy"


class InteractionType(str, Enum):
    """Types of interactive elements in the game"""
    COLLECT = "collect"
    DRAG_DROP = "drag_drop"
    MULTIPLE_CHOICE = "multiple_choice"
    VOICE = "voice"
    EXPLORE = "explore"
    BUILD = "build"
    SEQUENCE = "sequence"


class BloomLevel(str, Enum):
    """Bloom's Taxonomy levels for learning objectives"""
    REMEMBER = "Remember"
    UNDERSTAND = "Understand"
    APPLY = "Apply"
    ANALYZE = "Analyze"
    EVALUATE = "Evaluate"
    CREATE = "Create"


class Position(BaseModel):
    """3D position in Unity world space"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "x": 5.0,
                "y": 0.0,
                "z": 10.0
            }
        }


class GameObject(BaseModel):
    """
    Interactive game object in the scene.

    Represents NPCs, collectibles, obstacles, portals, and other
    interactive elements that children will engage with.
    """
    type: str = Field(
        ...,
        description="Object type: npc, collectible, obstacle, portal, decoration"
    )
    name: str = Field(..., description="Display name of the object")
    prefab_key: str = Field(
        ...,
        description="Unity Addressable asset key for instantiation"
    )
    position: Position = Field(default_factory=Position)
    interaction: Optional[InteractionType] = None
    dialogue: Optional[List[str]] = Field(
        None,
        description="Dialogue lines for NPCs or interactive text"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom data for specific object types"
    )
    xp_reward: int = Field(
        default=5,
        ge=0,
        description="Experience points awarded for interaction"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "npc",
                "name": "Professor Spark",
                "prefab_key": "characters/professor_spark",
                "position": {"x": 0, "y": 0, "z": 5},
                "interaction": "voice",
                "dialogue": [
                    "Welcome to the ocean adventure!",
                    "Can you help me find the treasure?"
                ],
                "xp_reward": 10
            }
        }


class Challenge(BaseModel):
    """
    Learning challenge or assessment checkpoint.

    Represents interactive questions, puzzles, or tasks that
    assess the child's understanding of learning objectives.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: InteractionType = Field(..., description="Type of interaction required")
    prompt: str = Field(..., description="Question or instruction text")
    correct_answer: Union[str, int, List[str]] = Field(
        ...,
        description="Correct answer(s) - can be string, number, or list"
    )
    choices: Optional[List[str]] = Field(
        None,
        description="Multiple choice options (if applicable)"
    )
    hint: Optional[str] = Field(
        None,
        description="Hint text to help struggling learners"
    )
    xp_reward: int = Field(
        default=10,
        ge=0,
        description="XP awarded for correct completion"
    )
    learning_objective_id: str = Field(
        ...,
        description="ID of the learning objective this challenge assesses"
    )
    difficulty_level: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Difficulty rating from 1 (easiest) to 5 (hardest)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "challenge-123",
                "type": "multiple_choice",
                "prompt": "Which ocean creature uses echolocation?",
                "correct_answer": "Dolphin",
                "choices": ["Dolphin", "Shark", "Octopus", "Starfish"],
                "hint": "It's a mammal that is very intelligent!",
                "xp_reward": 15,
                "learning_objective_id": "obj-456",
                "difficulty_level": 2
            }
        }


class Scene(BaseModel):
    """
    Individual scene in the lesson.

    A lesson consists of multiple scenes, each with its own
    environment, objects, and challenges.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Scene name/title")
    narration: str = Field(
        ...,
        description="Opening narration or story text for this scene"
    )
    environment_prefab: str = Field(
        ...,
        description="Unity prefab key for the environment"
    )
    objects: List[GameObject] = Field(
        default_factory=list,
        description="Interactive objects in this scene"
    )
    challenges: List[Challenge] = Field(
        default_factory=list,
        description="Learning challenges in this scene"
    )
    exit_condition: str = Field(
        ...,
        description="Condition to complete scene (e.g., 'collect_all', 'answer_challenges', 'reach_portal')"
    )
    estimated_duration_minutes: int = Field(
        default=5,
        ge=1,
        description="Expected time to complete this scene"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "scene-001",
                "name": "Coral Reef Discovery",
                "narration": "Welcome to the beautiful coral reef! Help us learn about ocean life.",
                "environment_prefab": "environments/coral_reef",
                "objects": [],
                "challenges": [],
                "exit_condition": "collect_all_fish",
                "estimated_duration_minutes": 7
            }
        }


class LearningObjective(BaseModel):
    """
    Specific learning goal aligned with curriculum.

    Maps to educational standards and Bloom's Taxonomy levels.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(..., description="Clear, measurable learning objective")
    bloom_level: BloomLevel = Field(
        ...,
        description="Bloom's Taxonomy cognitive level"
    )
    subject_area: str = Field(
        ...,
        description="Subject area (e.g., Math, Science, Language Arts)"
    )
    difficulty: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Overall difficulty rating"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "obj-001",
                "text": "Identify and classify different types of ocean creatures",
                "bloom_level": "Understand",
                "subject_area": "Science",
                "difficulty": 2
            }
        }


class MentorPersona(BaseModel):
    """
    AI mentor character configuration.

    Defines the personality and behavior of the AI guide.
    """
    name: str = Field(default="Professor Spark", description="Mentor's name")
    voice: str = Field(
        default="friendly_adult",
        description="Voice profile for text-to-speech"
    )
    personality: str = Field(
        default="encouraging",
        description="Personality traits (encouraging, playful, serious, etc.)"
    )
    avatar_prefab: str = Field(
        default="characters/professor_spark",
        description="Unity prefab for mentor character"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Captain Coral",
                "voice": "friendly_adult",
                "personality": "adventurous and encouraging",
                "avatar_prefab": "characters/captain_coral"
            }
        }


class DifficultyPolicy(BaseModel):
    """
    Adaptive difficulty configuration.

    Controls how the game adjusts difficulty based on performance.
    """
    adaptive_enabled: bool = Field(
        default=True,
        description="Enable adaptive difficulty adjustment"
    )
    success_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Success rate threshold to increase difficulty"
    )
    failure_threshold: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Success rate threshold to decrease difficulty"
    )
    adjustment_rate: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="How quickly difficulty adjusts (0-1)"
    )


class SceneSpec(BaseModel):
    """
    Complete specification for Unity to build an interactive learning world.

    This is the root model that contains all information needed to
    generate a playable lesson from a curriculum PDF.
    """
    lesson_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., description="Lesson title")
    theme: ThemeType = Field(..., description="Visual theme for the lesson")
    age_range: str = Field(
        ...,
        description="Target age range (e.g., '6-8', '9-12')"
    )
    estimated_duration_minutes: int = Field(
        ...,
        ge=1,
        description="Total estimated playtime"
    )
    learning_objectives: List[LearningObjective] = Field(
        ...,
        min_length=1,
        description="List of learning objectives"
    )
    scenes: List[Scene] = Field(
        ...,
        min_length=1,
        description="Ordered list of scenes in the lesson"
    )
    mentor_persona: MentorPersona = Field(
        default_factory=MentorPersona,
        description="AI mentor configuration"
    )
    difficulty_policy: DifficultyPolicy = Field(
        default_factory=DifficultyPolicy,
        description="Adaptive difficulty settings"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of creation"
    )
    curriculum_id: Optional[str] = Field(
        None,
        description="Reference to source curriculum document"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "lesson_id": "lesson-12345",
                "title": "Ocean Life Adventure",
                "theme": "ocean",
                "age_range": "6-8",
                "estimated_duration_minutes": 20,
                "learning_objectives": [],
                "scenes": [],
                "mentor_persona": {
                    "name": "Captain Coral",
                    "voice": "friendly_adult",
                    "personality": "adventurous"
                },
                "difficulty_policy": {
                    "adaptive_enabled": True
                },
                "created_at": "2024-01-01T00:00:00"
            }
        }
