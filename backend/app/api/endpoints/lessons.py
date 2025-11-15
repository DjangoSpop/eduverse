"""
Lessons API endpoints for generating and retrieving interactive lessons.

Handles lesson generation from curricula and lesson retrieval for Unity.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.scene_generator import SceneGenerator
from app.storage import memory_store
from app.models.scene_spec import SceneSpec, ThemeType
from app.models.curriculum import Curriculum
from app.core.logging import get_logger
from app.utils.validators import validate_age_range, validate_duration

logger = get_logger(__name__)

router = APIRouter(prefix="/lessons", tags=["lessons"])


class LessonGenerationRequest(BaseModel):
    """Request to generate a new lesson"""
    curriculum_id: str = Field(..., description="Source curriculum ID")
    age_range: Optional[str] = Field(
        None,
        description="Target age range (e.g., '6-8'). Uses curriculum recommendation if not provided."
    )
    preferred_theme: Optional[ThemeType] = Field(
        None,
        description="Preferred visual theme. Uses AI recommendation if not provided."
    )
    target_duration_minutes: int = Field(
        default=20,
        ge=5,
        le=120,
        description="Target lesson duration in minutes"
    )
    title_override: Optional[str] = Field(
        None,
        description="Override lesson title"
    )


class LessonGenerationResponse(BaseModel):
    """Response from lesson generation"""
    lesson_id: str
    title: str
    theme: str
    scene_count: int
    estimated_duration_minutes: int
    learning_objectives_count: int
    status: str
    message: str


class LessonSummary(BaseModel):
    """Summary of a lesson for listing"""
    lesson_id: str
    title: str
    theme: str
    age_range: str
    estimated_duration_minutes: int
    scene_count: int
    learning_objectives_count: int
    created_at: datetime
    curriculum_id: Optional[str]


@router.post("/generate", response_model=LessonGenerationResponse)
async def generate_lesson(request: LessonGenerationRequest):
    """
    Generate an interactive lesson from a curriculum.

    This endpoint:
    1. Retrieves the curriculum and its AI analysis
    2. Uses SceneGenerator to create a complete SceneSpec
    3. Stores the lesson for Unity to fetch
    4. Returns lesson metadata

    The complete SceneSpec can then be retrieved via GET /lessons/{lesson_id}

    Args:
        request: Lesson generation parameters

    Returns:
        LessonGenerationResponse with lesson metadata

    Raises:
        404: Curriculum not found
        400: Invalid parameters or curriculum not analyzed
        500: Generation failed
    """
    logger.info(f"Starting lesson generation for curriculum: {request.curriculum_id}")

    # Validate inputs
    if request.age_range:
        validate_age_range(request.age_range)

    validate_duration(request.target_duration_minutes)

    # Retrieve curriculum
    curriculum_data = memory_store.get_curriculum(request.curriculum_id)

    if not curriculum_data:
        raise HTTPException(
            status_code=404,
            detail=f"Curriculum not found: {request.curriculum_id}"
        )

    curriculum = Curriculum(**curriculum_data)

    # Check if curriculum has been analyzed
    if not curriculum.ai_analysis:
        raise HTTPException(
            status_code=400,
            detail="Curriculum must be analyzed before generating lessons. "
                   "Please call POST /curriculum/analyze first."
        )

    # Prepare analysis data
    analysis_dict = curriculum.ai_analysis.model_dump()

    # Override theme if requested
    if request.preferred_theme:
        analysis_dict["narrative_theme"] = request.preferred_theme.value
        logger.info(f"Using requested theme: {request.preferred_theme.value}")

    # Override age range if requested
    age_range = request.age_range or analysis_dict.get("recommended_age_range", "6-10")

    # Determine title
    title = request.title_override or curriculum.title

    # Generate scene spec
    try:
        generator = SceneGenerator()

        scene_spec = generator.generate_scene_spec(
            curriculum_id=curriculum.id,
            title=title,
            analysis=analysis_dict,
            target_duration_minutes=request.target_duration_minutes,
            age_range=age_range
        )

        # Store lesson
        memory_store.save_lesson(scene_spec.lesson_id, scene_spec.model_dump())

        logger.info(
            f"Lesson generated successfully: {scene_spec.lesson_id} "
            f"({len(scene_spec.scenes)} scenes, {len(scene_spec.learning_objectives)} objectives)"
        )

        return LessonGenerationResponse(
            lesson_id=scene_spec.lesson_id,
            title=scene_spec.title,
            theme=scene_spec.theme.value,
            scene_count=len(scene_spec.scenes),
            estimated_duration_minutes=scene_spec.estimated_duration_minutes,
            learning_objectives_count=len(scene_spec.learning_objectives),
            status="ready",
            message="Lesson generated successfully and ready for Unity"
        )

    except Exception as e:
        logger.error(f"Lesson generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate lesson: {str(e)}"
        )


@router.get("/{lesson_id}", response_model=SceneSpec)
async def get_lesson(lesson_id: str):
    """
    Retrieve complete SceneSpec for Unity.

    Unity calls this endpoint to get the full specification
    for building the interactive 3D world.

    Args:
        lesson_id: Lesson identifier

    Returns:
        Complete SceneSpec with scenes, objectives, and challenges

    Raises:
        404: Lesson not found
    """
    logger.debug(f"Retrieving lesson: {lesson_id}")

    lesson_data = memory_store.get_lesson(lesson_id)

    if not lesson_data:
        raise HTTPException(
            status_code=404,
            detail=f"Lesson not found: {lesson_id}"
        )

    return SceneSpec(**lesson_data)


@router.get("/", response_model=List[LessonSummary])
async def list_lessons(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max items to return"),
    theme: Optional[ThemeType] = Query(None, description="Filter by theme"),
    curriculum_id: Optional[str] = Query(None, description="Filter by curriculum ID")
):
    """
    List all lessons with optional filters.

    Args:
        skip: Number of items to skip (pagination)
        limit: Maximum items to return
        theme: Optional theme filter
        curriculum_id: Optional curriculum filter

    Returns:
        List of lesson summaries
    """
    logger.debug(
        f"Listing lessons (skip={skip}, limit={limit}, theme={theme}, "
        f"curriculum_id={curriculum_id})"
    )

    all_lessons = memory_store.MemoryStore.list_all(memory_store.lesson_store)

    # Apply filters
    if theme:
        all_lessons = [
            lesson for lesson in all_lessons
            if lesson.get("theme") == theme.value
        ]

    if curriculum_id:
        all_lessons = [
            lesson for lesson in all_lessons
            if lesson.get("curriculum_id") == curriculum_id
        ]

    # Sort by creation time (most recent first)
    all_lessons.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )

    # Apply pagination
    paginated = all_lessons[skip:skip + limit]

    # Convert to summaries
    summaries = []
    for lesson_data in paginated:
        try:
            lesson = SceneSpec(**lesson_data)
            summary = LessonSummary(
                lesson_id=lesson.lesson_id,
                title=lesson.title,
                theme=lesson.theme.value,
                age_range=lesson.age_range,
                estimated_duration_minutes=lesson.estimated_duration_minutes,
                scene_count=len(lesson.scenes),
                learning_objectives_count=len(lesson.learning_objectives),
                created_at=lesson.created_at,
                curriculum_id=lesson.curriculum_id
            )
            summaries.append(summary)
        except Exception as e:
            logger.warning(f"Failed to create summary for lesson: {str(e)}")
            continue

    return summaries


@router.delete("/{lesson_id}")
async def delete_lesson(lesson_id: str):
    """
    Delete a lesson.

    Args:
        lesson_id: Lesson identifier

    Returns:
        Success message

    Raises:
        404: Lesson not found
    """
    logger.info(f"Deleting lesson: {lesson_id}")

    deleted = memory_store.MemoryStore.delete(
        memory_store.lesson_store,
        lesson_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Lesson not found: {lesson_id}"
        )

    return {"message": "Lesson deleted successfully", "id": lesson_id}


@router.get("/{lesson_id}/preview")
async def get_lesson_preview(lesson_id: str):
    """
    Get a preview of lesson content.

    Returns a simplified view of the lesson for quick inspection.

    Args:
        lesson_id: Lesson identifier

    Returns:
        Lesson preview with key information

    Raises:
        404: Lesson not found
    """
    logger.debug(f"Retrieving lesson preview: {lesson_id}")

    lesson_data = memory_store.get_lesson(lesson_id)

    if not lesson_data:
        raise HTTPException(
            status_code=404,
            detail=f"Lesson not found: {lesson_id}"
        )

    lesson = SceneSpec(**lesson_data)

    # Build preview
    preview = {
        "lesson_id": lesson.lesson_id,
        "title": lesson.title,
        "theme": lesson.theme.value,
        "age_range": lesson.age_range,
        "estimated_duration_minutes": lesson.estimated_duration_minutes,
        "mentor": {
            "name": lesson.mentor_persona.name,
            "personality": lesson.mentor_persona.personality
        },
        "learning_objectives": [
            {
                "text": obj.text,
                "subject": obj.subject_area,
                "bloom_level": obj.bloom_level.value
            }
            for obj in lesson.learning_objectives
        ],
        "scenes": [
            {
                "name": scene.name,
                "narration": scene.narration,
                "objects_count": len(scene.objects),
                "challenges_count": len(scene.challenges),
                "estimated_duration": scene.estimated_duration_minutes
            }
            for scene in lesson.scenes
        ],
        "total_challenges": sum(len(scene.challenges) for scene in lesson.scenes),
        "total_xp_available": sum(
            sum(challenge.xp_reward for challenge in scene.challenges) +
            sum(obj.xp_reward for obj in scene.objects)
            for scene in lesson.scenes
        )
    }

    return preview
