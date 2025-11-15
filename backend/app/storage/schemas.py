"""
Storage schemas and data transformation utilities.

Handles conversion between Pydantic models and storage dictionaries.
"""

from typing import Dict, Any
from datetime import datetime
import json


def model_to_dict(model: Any) -> Dict:
    """
    Convert a Pydantic model to a dictionary suitable for storage.

    Args:
        model: Pydantic model instance

    Returns:
        Dict: Serializable dictionary
    """
    # Use Pydantic's model_dump method with proper serialization
    return json.loads(model.model_dump_json())


def ensure_serializable(data: Dict) -> Dict:
    """
    Ensure all values in dictionary are JSON serializable.

    Converts datetime objects to ISO format strings.

    Args:
        data: Dictionary to process

    Returns:
        Dict: Serializable dictionary
    """
    result = {}

    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = ensure_serializable(value)
        elif isinstance(value, list):
            result[key] = [
                ensure_serializable(item) if isinstance(item, dict)
                else item.isoformat() if isinstance(item, datetime)
                else item
                for item in value
            ]
        else:
            result[key] = value

    return result
