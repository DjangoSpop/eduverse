"""
In-memory storage for MVP.

Simple dictionary-based storage for development and testing.
In production, this would be replaced with a proper database.
"""

from typing import Dict, List, Optional
from threading import Lock
import logging

from app.core.logging import get_logger

logger = get_logger(__name__)

# Thread-safe storage dictionaries
_storage_lock = Lock()

# Storage containers
curriculum_store: Dict[str, Dict] = {}
lesson_store: Dict[str, Dict] = {}
learner_store: Dict[str, Dict] = {}
session_store: Dict[str, Dict] = {}
gamification_store: Dict[str, Dict] = {}


class MemoryStore:
    """
    Thread-safe in-memory storage manager.

    Provides CRUD operations for all entity types with
    thread safety for concurrent access.
    """

    @staticmethod
    def create(store: Dict, entity_id: str, data: Dict) -> Dict:
        """
        Create a new entity in the store.

        Args:
            store: Storage dictionary to use
            entity_id: Unique identifier
            data: Entity data

        Returns:
            Dict: Created entity data
        """
        with _storage_lock:
            if entity_id in store:
                logger.warning(f"Entity {entity_id} already exists, overwriting")

            store[entity_id] = data
            logger.debug(f"Created entity: {entity_id}")
            return data

    @staticmethod
    def read(store: Dict, entity_id: str) -> Optional[Dict]:
        """
        Read an entity from the store.

        Args:
            store: Storage dictionary to use
            entity_id: Entity identifier

        Returns:
            Optional[Dict]: Entity data if found, None otherwise
        """
        with _storage_lock:
            data = store.get(entity_id)
            if data:
                logger.debug(f"Retrieved entity: {entity_id}")
            else:
                logger.debug(f"Entity not found: {entity_id}")
            return data

    @staticmethod
    def update(store: Dict, entity_id: str, data: Dict) -> Optional[Dict]:
        """
        Update an existing entity.

        Args:
            store: Storage dictionary to use
            entity_id: Entity identifier
            data: Updated entity data

        Returns:
            Optional[Dict]: Updated data if entity exists, None otherwise
        """
        with _storage_lock:
            if entity_id not in store:
                logger.warning(f"Cannot update non-existent entity: {entity_id}")
                return None

            store[entity_id] = data
            logger.debug(f"Updated entity: {entity_id}")
            return data

    @staticmethod
    def delete(store: Dict, entity_id: str) -> bool:
        """
        Delete an entity from the store.

        Args:
            store: Storage dictionary to use
            entity_id: Entity identifier

        Returns:
            bool: True if deleted, False if not found
        """
        with _storage_lock:
            if entity_id in store:
                del store[entity_id]
                logger.debug(f"Deleted entity: {entity_id}")
                return True
            else:
                logger.debug(f"Entity not found for deletion: {entity_id}")
                return False

    @staticmethod
    def list_all(store: Dict) -> List[Dict]:
        """
        List all entities in the store.

        Args:
            store: Storage dictionary to use

        Returns:
            List[Dict]: List of all entities
        """
        with _storage_lock:
            entities = list(store.values())
            logger.debug(f"Retrieved {len(entities)} entities")
            return entities

    @staticmethod
    def find_by(
        store: Dict,
        field: str,
        value: any
    ) -> List[Dict]:
        """
        Find entities by field value.

        Args:
            store: Storage dictionary to use
            field: Field name to search
            value: Value to match

        Returns:
            List[Dict]: Matching entities
        """
        with _storage_lock:
            matches = [
                entity for entity in store.values()
                if entity.get(field) == value
            ]
            logger.debug(f"Found {len(matches)} entities where {field}={value}")
            return matches

    @staticmethod
    def count(store: Dict) -> int:
        """
        Get count of entities in store.

        Args:
            store: Storage dictionary to use

        Returns:
            int: Number of entities
        """
        with _storage_lock:
            return len(store)

    @staticmethod
    def clear_all_stores() -> None:
        """
        Clear all storage (useful for testing).

        WARNING: This deletes all data!
        """
        with _storage_lock:
            global curriculum_store, lesson_store, learner_store, session_store, gamification_store

            curriculum_store.clear()
            lesson_store.clear()
            learner_store.clear()
            session_store.clear()
            gamification_store.clear()

            logger.warning("All storage cleared!")

    @staticmethod
    def get_storage_stats() -> Dict:
        """
        Get statistics about current storage usage.

        Returns:
            Dict: Storage statistics
        """
        with _storage_lock:
            return {
                "curriculum_count": len(curriculum_store),
                "lesson_count": len(lesson_store),
                "learner_count": len(learner_store),
                "session_count": len(session_store),
                "gamification_count": len(gamification_store),
                "total_entities": (
                    len(curriculum_store) +
                    len(lesson_store) +
                    len(learner_store) +
                    len(session_store) +
                    len(gamification_store)
                )
            }


# Convenience functions for common operations

def get_curriculum(curriculum_id: str) -> Optional[Dict]:
    """Get curriculum by ID"""
    return MemoryStore.read(curriculum_store, curriculum_id)


def save_curriculum(curriculum_id: str, data: Dict) -> Dict:
    """Save curriculum"""
    return MemoryStore.create(curriculum_store, curriculum_id, data)


def get_lesson(lesson_id: str) -> Optional[Dict]:
    """Get lesson by ID"""
    return MemoryStore.read(lesson_store, lesson_id)


def save_lesson(lesson_id: str, data: Dict) -> Dict:
    """Save lesson"""
    return MemoryStore.create(lesson_store, lesson_id, data)


def get_learner(learner_id: str) -> Optional[Dict]:
    """Get learner by ID"""
    return MemoryStore.read(learner_store, learner_id)


def save_learner(learner_id: str, data: Dict) -> Dict:
    """Save learner"""
    return MemoryStore.create(learner_store, learner_id, data)


def get_session(session_id: str) -> Optional[Dict]:
    """Get session by ID"""
    return MemoryStore.read(session_store, session_id)


def save_session(session_id: str, data: Dict) -> Dict:
    """Save session"""
    return MemoryStore.create(session_store, session_id, data)


def update_session(session_id: str, data: Dict) -> Optional[Dict]:
    """Update session"""
    return MemoryStore.update(session_store, session_id, data)


def get_learner_sessions(learner_id: str) -> List[Dict]:
    """Get all sessions for a learner"""
    return MemoryStore.find_by(session_store, "learner_id", learner_id)


def get_storage_stats() -> Dict:
    """Get storage statistics"""
    return MemoryStore.get_storage_stats()
