"""
Learners API endpoints for managing learner profiles.

Handles learner profile creation, updates, and retrieval.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime

from app.storage import memory_store
from app.models.learner import (
    LearnerProfile,
    LearnerCreateRequest,
    LearnerUpdateRequest,
    LearnerResponse,
    PerformanceMetrics,
    StreakData
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/learners", tags=["learners"])


@router.post("/", response_model=LearnerResponse)
async def create_learner(request: LearnerCreateRequest):
    """
    Create a new learner profile.

    Args:
        request: Learner creation parameters

    Returns:
        Created learner profile

    Raises:
        400: Invalid input
    """
    logger.info(f"Creating learner profile: {request.name}")

    # Create learner profile
    learner = LearnerProfile(
        name=request.name,
        age=request.age,
        grade_level=request.grade_level,
        parent_email=request.parent_email
    )

    # Store learner
    memory_store.save_learner(learner.id, learner.model_dump())

    logger.info(f"Learner created: {learner.id}")

    # Return response
    return LearnerResponse(
        id=learner.id,
        name=learner.name,
        age=learner.age,
        grade_level=learner.grade_level,
        avatar_key=learner.avatar_key,
        performance=learner.performance,
        streak=learner.streak,
        created_at=learner.created_at,
        last_active=learner.last_active
    )


@router.get("/{learner_id}", response_model=LearnerProfile)
async def get_learner(learner_id: str):
    """
    Retrieve learner profile by ID.

    Args:
        learner_id: Learner identifier

    Returns:
        Complete learner profile

    Raises:
        404: Learner not found
    """
    logger.debug(f"Retrieving learner: {learner_id}")

    learner_data = memory_store.get_learner(learner_id)
    if not learner_data:
        raise HTTPException(
            status_code=404,
            detail=f"Learner not found: {learner_id}"
        )

    return LearnerProfile(**learner_data)


@router.patch("/{learner_id}", response_model=LearnerResponse)
async def update_learner(learner_id: str, request: LearnerUpdateRequest):
    """
    Update learner profile.

    Args:
        learner_id: Learner identifier
        request: Update parameters

    Returns:
        Updated learner profile

    Raises:
        404: Learner not found
    """
    logger.info(f"Updating learner: {learner_id}")

    # Retrieve learner
    learner_data = memory_store.get_learner(learner_id)
    if not learner_data:
        raise HTTPException(
            status_code=404,
            detail=f"Learner not found: {learner_id}"
        )

    learner = LearnerProfile(**learner_data)

    # Update fields
    if request.name is not None:
        learner.name = request.name

    if request.age is not None:
        learner.age = request.age

    if request.grade_level is not None:
        learner.grade_level = request.grade_level

    if request.avatar_key is not None:
        learner.avatar_key = request.avatar_key

    if request.preferences is not None:
        learner.preferences = request.preferences

    # Update last active
    learner.last_active = datetime.utcnow()

    # Store updated learner
    memory_store.update_session(learner.id, learner.model_dump())

    logger.info(f"Learner updated: {learner_id}")

    return LearnerResponse(
        id=learner.id,
        name=learner.name,
        age=learner.age,
        grade_level=learner.grade_level,
        avatar_key=learner.avatar_key,
        performance=learner.performance,
        streak=learner.streak,
        created_at=learner.created_at,
        last_active=learner.last_active
    )


@router.get("/", response_model=List[LearnerResponse])
async def list_learners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List all learners.

    Args:
        skip: Number of items to skip
        limit: Maximum items to return

    Returns:
        List of learner profiles
    """
    logger.debug(f"Listing learners (skip={skip}, limit={limit})")

    all_learners = memory_store.MemoryStore.list_all(memory_store.learner_store)

    # Sort by last active (most recent first)
    all_learners.sort(
        key=lambda x: x.get("last_active", ""),
        reverse=True
    )

    # Apply pagination
    paginated = all_learners[skip:skip + limit]

    # Convert to responses
    responses = []
    for learner_data in paginated:
        try:
            learner = LearnerProfile(**learner_data)
            response = LearnerResponse(
                id=learner.id,
                name=learner.name,
                age=learner.age,
                grade_level=learner.grade_level,
                avatar_key=learner.avatar_key,
                performance=learner.performance,
                streak=learner.streak,
                created_at=learner.created_at,
                last_active=learner.last_active
            )
            responses.append(response)
        except Exception as e:
            logger.warning(f"Failed to create response for learner: {str(e)}")
            continue

    return responses


@router.delete("/{learner_id}")
async def delete_learner(learner_id: str):
    """
    Delete a learner profile.

    Args:
        learner_id: Learner identifier

    Returns:
        Success message

    Raises:
        404: Learner not found
    """
    logger.info(f"Deleting learner: {learner_id}")

    deleted = memory_store.MemoryStore.delete(
        memory_store.learner_store,
        learner_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Learner not found: {learner_id}"
        )

    return {"message": "Learner deleted successfully", "id": learner_id}
