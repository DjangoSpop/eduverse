"""
WebSocket endpoints for real-time game mechanic streaming

Enables Unity client to receive dynamically generated game mechanics
in real-time based on child behavior and progress.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging
import json

from app.services.streaming_engine import streaming_engine
from app.api.endpoints.lessons import scene_spec_store
from app.api.endpoints.learners import learner_profiles

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streaming", tags=["streaming"])


@router.websocket("/ws/mechanics")
async def mechanics_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time game mechanic streaming

    Client sends:
    {
        "child_id": "unique_child_id",
        "lesson_id": "lesson_id",
        "language": "ar" or "en",
        "age": 8,
        "name": "Ahmed" (optional)
    }

    Server streams:
    {
        "type": "mechanic_token",
        "token": "partial JSON string"
    }
    OR
    {
        "type": "mechanic_complete",
        "full_mechanic": "complete JSON object"
    }
    OR
    {
        "type": "encouragement",
        "message": "励message in child's language"
    }

    Client continuously sends progress updates:
    {
        "idle_seconds": 45,
        "error_streak": 2,
        "correct_streak": 0,
        "hints_used": 3,
        "avg_response_time": 8.5,
        "exploration_count": 5,
        "time_in_scene": 180
    }
    """
    await websocket.accept()
    logger.info("[Streaming] WebSocket connection accepted")

    try:
        # Receive initial connection data from client
        init_data = await websocket.receive_json()

        child_id = init_data.get('child_id')
        lesson_id = init_data.get('lesson_id')
        language = init_data.get('language', 'en')
        age = init_data.get('age', 8)
        name = init_data.get('name', 'friend')

        if not child_id:
            await websocket.send_json({
                'type': 'error',
                'message': 'child_id is required'
            })
            await websocket.close()
            return

        logger.info(f"[Streaming] Stream initiated for child_id={child_id}, lesson_id={lesson_id}, language={language}")

        # Build child profile
        child_profile = {
            'child_id': child_id,
            'language': language,
            'age': age,
            'name': name
        }

        # Get learner profile if exists
        if child_id in learner_profiles:
            stored_profile = learner_profiles[child_id]
            child_profile.update({
                'name': stored_profile.get('name', name),
                'age': stored_profile.get('age', age),
                'preferred_language': stored_profile.get('preferred_language', language)
            })

        # Build lesson context
        lesson_context = {
            'topic': 'general learning',
            'theme': 'ocean',
            'learning_objectives': []
        }

        if lesson_id and lesson_id in scene_spec_store:
            lesson = scene_spec_store[lesson_id]
            lesson_context.update({
                'topic': lesson.get('title', 'learning'),
                'theme': lesson.get('theme', 'ocean'),
                'learning_objectives': lesson.get('learning_objectives', [])
            })

        # Send confirmation
        await websocket.send_json({
            'type': 'connected',
            'message': 'Streaming engine ready',
            'child_id': child_id,
            'language': language
        })

        # Start streaming engine
        await streaming_engine.start_mechanic_stream(
            websocket=websocket,
            child_profile=child_profile,
            lesson_context=lesson_context
        )

    except WebSocketDisconnect:
        logger.info(f"[Streaming] Client disconnected")
    except json.JSONDecodeError as e:
        logger.error(f"[Streaming] Invalid JSON from client: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': 'Invalid JSON format'
            })
        except:
            pass
    except Exception as e:
        logger.error(f"[Streaming] WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info("[Streaming] WebSocket connection closed")


@router.get("/stats")
async def get_streaming_stats(
    session_id: Optional[str] = Query(None, description="Session ID to get stats for")
):
    """
    Get statistics for active streaming sessions

    Args:
        session_id: Optional session ID, if not provided returns all active streams

    Returns:
        Stream statistics
    """
    if session_id:
        stats = streaming_engine.get_stream_stats(session_id)
        if not stats:
            return {
                "error": "Session not found or stream not active",
                "session_id": session_id
            }
        return stats
    else:
        active_streams = streaming_engine.get_all_active_streams()
        return {
            "active_streams_count": len(active_streams),
            "session_ids": active_streams
        }


@router.post("/test-mechanic")
async def test_mechanic_generation(
    language: str = Query("en", description="Language code"),
    mechanic_type: str = Query("exciting_chase", description="Mechanic type"),
    age: int = Query(8, description="Child age"),
    topic: str = Query("ocean animals", description="Learning topic")
):
    """
    Test mechanic generation without WebSocket connection

    Useful for testing the streaming engine's output

    Args:
        language: Target language
        mechanic_type: Type of mechanic to generate
        age: Child's age
        topic: Learning topic

    Returns:
        Generated mechanic JSON
    """
    from app.services.streaming_engine import StreamingGameEngine

    engine = StreamingGameEngine()

    child_profile = {
        'child_id': 'test',
        'language': language,
        'age': age,
        'name': 'TestChild'
    }

    lesson_context = {
        'topic': topic,
        'theme': 'ocean',
        'learning_objectives': []
    }

    behavior = {
        'recommended_mechanic_type': mechanic_type,
        'boredom_detected': False,
        'frustration_detected': False,
        'mastery_detected': False,
        'needs_encouragement': False,
        'error_streak': 0,
        'correct_streak': 0
    }

    # Collect streamed tokens
    full_mechanic = ""
    async for token in engine._generate_mechanic_stream(
        child_profile=child_profile,
        lesson_context=lesson_context,
        behavior=behavior
    ):
        full_mechanic += token

    try:
        mechanic_json = json.loads(full_mechanic)
        return {
            "status": "success",
            "mechanic": mechanic_json,
            "language": language,
            "mechanic_type": mechanic_type
        }
    except json.JSONDecodeError as e:
        logger.error(f"[Test] Failed to parse generated mechanic: {e}")
        return {
            "status": "error",
            "message": "Generated invalid JSON",
            "raw_output": full_mechanic[:500],  # First 500 chars for debugging
            "error": str(e)
        }
