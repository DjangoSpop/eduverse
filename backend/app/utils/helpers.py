"""
General utility helper functions.

Common utility functions used across the application.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid
import hashlib


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique identifier.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        str: Unique identifier
    """
    unique_id = str(uuid.uuid4())

    if prefix:
        return f"{prefix}-{unique_id}"

    return unique_id


def calculate_success_rate(
    completed: int,
    attempted: int
) -> float:
    """
    Calculate success rate.

    Args:
        completed: Number of successful attempts
        attempted: Total number of attempts

    Returns:
        float: Success rate (0.0 to 1.0)
    """
    if attempted == 0:
        return 0.0

    return min(1.0, completed / attempted)


def calculate_xp_for_level(level: int) -> int:
    """
    Calculate total XP required to reach a level.

    Uses exponential progression: XP = 100 * level^1.5

    Args:
        level: Target level

    Returns:
        int: Total XP required
    """
    if level <= 1:
        return 0

    return int(100 * (level ** 1.5))


def get_level_from_xp(xp: int) -> int:
    """
    Calculate level from total XP.

    Args:
        xp: Total XP earned

    Returns:
        int: Current level
    """
    level = 1

    while calculate_xp_for_level(level + 1) <= xp:
        level += 1

    return level


def calculate_xp_to_next_level(current_xp: int, current_level: int) -> int:
    """
    Calculate XP needed for next level.

    Args:
        current_xp: Current total XP
        current_level: Current level

    Returns:
        int: XP needed for next level
    """
    next_level_xp = calculate_xp_for_level(current_level + 1)
    return max(0, next_level_xp - current_xp)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        str: Formatted duration (e.g., "5m 30s")
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes}m {remaining_seconds}s"
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes > 0:
        return f"{hours}h {remaining_minutes}m"
    return f"{hours}h"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def calculate_streak(
    last_activity: datetime,
    current_streak: int
) -> int:
    """
    Calculate current learning streak.

    Streak continues if activity was yesterday or today.

    Args:
        last_activity: Last activity timestamp
        current_streak: Current streak count

    Returns:
        int: Updated streak count
    """
    now = datetime.utcnow()
    today = now.date()
    last_date = last_activity.date()

    # Same day - maintain streak
    if last_date == today:
        return current_streak

    # Yesterday - increment streak
    elif last_date == today - timedelta(days=1):
        return current_streak + 1

    # Older - reset streak
    else:
        return 1


def hash_string(value: str) -> str:
    """
    Create a hash of a string value.

    Args:
        value: String to hash

    Returns:
        str: SHA256 hash
    """
    return hashlib.sha256(value.encode()).hexdigest()


def percentage_to_float(percentage: float) -> float:
    """
    Normalize percentage to 0.0-1.0 range.

    Args:
        percentage: Percentage value (0-100 or 0-1)

    Returns:
        float: Normalized value (0.0-1.0)
    """
    if percentage > 1.0:
        return min(1.0, percentage / 100.0)

    return min(1.0, max(0.0, percentage))


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Merge two dictionaries, with dict2 values taking precedence.

    Args:
        dict1: Base dictionary
        dict2: Override dictionary

    Returns:
        Dict: Merged dictionary
    """
    result = dict1.copy()
    result.update(dict2)
    return result


def batch_list(items: List, batch_size: int) -> List[List]:
    """
    Split a list into batches.

    Args:
        items: List to batch
        batch_size: Size of each batch

    Returns:
        List[List]: List of batches
    """
    batches = []

    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])

    return batches
