"""
Input validation utilities.

Custom validators for API inputs beyond Pydantic's built-in validation.
"""

from typing import Optional
from fastapi import HTTPException
import re


def validate_age_range(age_range: str) -> bool:
    """
    Validate age range format.

    Expected format: "6-8" or "9-12"

    Args:
        age_range: Age range string

    Returns:
        bool: True if valid

    Raises:
        HTTPException: If format is invalid
    """
    pattern = r'^\d{1,2}-\d{1,2}$'

    if not re.match(pattern, age_range):
        raise HTTPException(
            status_code=400,
            detail="Invalid age range format. Expected format: '6-8' or '9-12'"
        )

    # Parse and validate range
    try:
        start, end = map(int, age_range.split('-'))

        if start < 4 or end > 18:
            raise HTTPException(
                status_code=400,
                detail="Age range must be between 4 and 18"
            )

        if start >= end:
            raise HTTPException(
                status_code=400,
                detail="Start age must be less than end age"
            )

        return True

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid age range format"
        )


def validate_difficulty(difficulty: int) -> bool:
    """
    Validate difficulty level.

    Args:
        difficulty: Difficulty level (1-5)

    Returns:
        bool: True if valid

    Raises:
        HTTPException: If out of range
    """
    if difficulty < 1 or difficulty > 5:
        raise HTTPException(
            status_code=400,
            detail="Difficulty must be between 1 and 5"
        )

    return True


def validate_duration(duration_minutes: int) -> bool:
    """
    Validate lesson duration.

    Args:
        duration_minutes: Duration in minutes

    Returns:
        bool: True if valid

    Raises:
        HTTPException: If out of range
    """
    if duration_minutes < 5:
        raise HTTPException(
            status_code=400,
            detail="Duration must be at least 5 minutes"
        )

    if duration_minutes > 120:
        raise HTTPException(
            status_code=400,
            detail="Duration cannot exceed 120 minutes (2 hours)"
        )

    return True


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user-provided text.

    Args:
        text: Text to sanitize
        max_length: Optional maximum length

    Returns:
        str: Sanitized text
    """
    # Strip whitespace
    text = text.strip()

    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')

    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text
