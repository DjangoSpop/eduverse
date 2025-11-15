"""
WebSocket endpoints for real-time game mechanic streaming

Enables Unity clients to receive infinite adaptive game mechanics
in real-time based on child behavior and learning progress.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from typing import Optional, Dict, List
import logging
import json
import asyncio

from app.services.streaming_game_engine import (
    StreamingGameEngine,
    DifficultyLevel,
    EngagementLevel
)
from app.api.endpoints.curriculum import curriculum_store
from app.api.endpoints.lessons import scene_spec_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streaming", tags=["streaming"])

# Global streaming engine instance
streaming_engine = StreamingGameEngine()

# Track active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


@router.post("/session/start")
async def start_streaming_session(
    learner_id: str = Query(..., description="Learner ID"),
    curriculum_id: str = Query(..., description="Curriculum ID"),
    language: str = Query("en", description="Language code"),
    initial_difficulty: DifficultyLevel = Query(DifficultyLevel.MEDIUM, description="Starting difficulty")
):
    """
    Start a new streaming game session

    Creates a session that can stream infinite mechanics via WebSocket.

    Returns:
        session_id and connection details
    """
    # Validate curriculum exists
    if curriculum_id not in curriculum_store:
        raise HTTPException(status_code=404, detail="Curriculum not found")

    # Create session
    session_id = streaming_engine.create_session(
        learner_id=learner_id,
        curriculum_id=curriculum_id,
        language=language,
        initial_difficulty=initial_difficulty
    )

    curriculum = curriculum_store[curriculum_id]

    return {
        "session_id": session_id,
        "learner_id": learner_id,
        "curriculum_id": curriculum_id,
        "language": language,
        "initial_difficulty": initial_difficulty,
        "websocket_endpoint": f"/streaming/ws/{session_id}",
        "status": "ready",
        "curriculum_title": curriculum.get('title', 'Unknown')
    }


@router.websocket("/ws/{session_id}")
async def websocket_mechanic_stream(
    websocket: WebSocket,
    session_id: str,
    lesson_id: Optional[str] = None
):
    """
    WebSocket endpoint for streaming mechanics

    Unity connects here to receive real-time game mechanics.

    Flow:
    1. Client connects with session_id
    2. Server streams mechanics indefinitely
    3. Client sends performance updates
    4. Server adapts difficulty and engagement
    5. Continues until client disconnects

    Message formats:
    - Server -> Client: {"type": "mechanic", "data": {...}}
    - Client -> Server: {"type": "performance", "data": {...}}
    """
    await websocket.accept()
    active_connections[session_id] = websocket

    logger.info(f"WebSocket connected for session {session_id}")

    # Get session info
    session = streaming_engine.get_session_stats(session_id)
    if not session:
        await websocket.send_json({
            "type": "error",
            "message": f"Session {session_id} not found"
        })
        await websocket.close()
        return

    # Get learning objectives from lesson or curriculum
    learning_objectives = []
    if lesson_id and lesson_id in scene_spec_store:
        lesson = scene_spec_store[lesson_id]
        learning_objectives = lesson.get('learning_objectives', [])
    else:
        # Fallback to curriculum-based objectives
        curriculum_id = session['curriculum_id']
        if curriculum_id in curriculum_store:
            curriculum = curriculum_store[curriculum_id]
            # Extract key topics as objectives
            learning_objectives = [
                "Practice reading comprehension",
                "Develop problem-solving skills",
                "Build mathematical reasoning",
                "Enhance memory and recall"
            ]

    try:
        # Create tasks for streaming and receiving
        stream_task = asyncio.create_task(
            stream_mechanics_to_client(websocket, session_id, learning_objectives)
        )
        receive_task = asyncio.create_task(
            receive_performance_updates(websocket, session_id)
        )

        # Run both tasks concurrently
        await asyncio.gather(stream_task, receive_task)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}", exc_info=True)

    finally:
        # Clean up connection
        if session_id in active_connections:
            del active_connections[session_id]

        # Get final stats
        final_stats = streaming_engine.terminate_session(session_id)
        logger.info(f"Session {session_id} ended: {final_stats}")


async def stream_mechanics_to_client(
    websocket: WebSocket,
    session_id: str,
    learning_objectives: List[str]
):
    """
    Stream mechanics to Unity client continuously

    Args:
        websocket: WebSocket connection
        session_id: Session ID
        learning_objectives: Learning goals for content generation
    """
    try:
        # Stream mechanics indefinitely
        async for mechanic in streaming_engine.stream_mechanics(
            session_id=session_id,
            learning_objectives=learning_objectives,
            context={}
        ):
            # Send mechanic to client
            message = {
                "type": "mechanic",
                "data": mechanic
            }

            await websocket.send_json(message)

            logger.debug(f"Sent {mechanic['type']} mechanic to session {session_id}")

            # Wait for client to request next mechanic
            # (controlled by receive_performance_updates)
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from mechanic stream: {session_id}")

    except Exception as e:
        logger.error(f"Error streaming mechanics to {session_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Streaming error: {str(e)}"
            })
        except:
            pass


async def receive_performance_updates(
    websocket: WebSocket,
    session_id: str
):
    """
    Receive performance updates from Unity client

    Client sends updates when mechanics are completed,
    which triggers difficulty adaptation and engagement detection.

    Expected message format:
    {
        "type": "performance",
        "mechanic_id": "...",
        "success": true/false,
        "time_taken": 45.2,
        "errors": 2,
        "score": 0.85
    }
    """
    try:
        while True:
            # Wait for client message
            message = await websocket.receive_text()

            try:
                data = json.loads(message)

                if data.get('type') == 'performance':
                    # Update session with performance data
                    streaming_engine.update_session_performance(
                        session_id=session_id,
                        mechanic_id=data.get('mechanic_id'),
                        success=data.get('success', False),
                        time_taken=data.get('time_taken', 0.0),
                        errors=data.get('errors', 0)
                    )

                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "ack",
                        "message": "Performance updated"
                    })

                    logger.debug(f"Updated performance for session {session_id}")

                elif data.get('type') == 'request_next':
                    # Client requesting next mechanic (stream will continue)
                    logger.debug(f"Client requested next mechanic: {session_id}")

                elif data.get('type') == 'ping':
                    # Heartbeat
                    await websocket.send_json({"type": "pong"})

                else:
                    logger.warning(f"Unknown message type from {session_id}: {data.get('type')}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {session_id}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from performance updates: {session_id}")

    except Exception as e:
        logger.error(f"Error receiving performance updates from {session_id}: {e}", exc_info=True)


@router.get("/session/{session_id}/stats")
async def get_session_stats(session_id: str):
    """
    Get current session statistics

    Useful for monitoring and debugging streaming sessions.
    """
    stats = streaming_engine.get_session_stats(session_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "stats": stats,
        "is_active": session_id in active_connections
    }


@router.post("/session/{session_id}/terminate")
async def terminate_session(session_id: str):
    """
    Manually terminate a streaming session

    Returns final statistics and closes WebSocket if active.
    """
    # Close WebSocket if active
    if session_id in active_connections:
        try:
            ws = active_connections[session_id]
            await ws.send_json({
                "type": "terminate",
                "message": "Session terminated by server"
            })
            await ws.close()
            del active_connections[session_id]
        except Exception as e:
            logger.error(f"Error closing WebSocket for {session_id}: {e}")

    # Get final stats
    final_stats = streaming_engine.terminate_session(session_id)

    if not final_stats:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "status": "terminated",
        "final_stats": final_stats
    }


@router.post("/session/{session_id}/difficulty")
async def update_difficulty(
    session_id: str,
    difficulty: DifficultyLevel = Query(..., description="New difficulty level")
):
    """
    Manually override difficulty level

    Useful for testing or teacher intervention.
    """
    session = streaming_engine.get_session_stats(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session['current_difficulty'] = difficulty

    return {
        "session_id": session_id,
        "new_difficulty": difficulty,
        "message": "Difficulty updated successfully"
    }


@router.get("/active-sessions")
async def list_active_sessions():
    """
    List all active streaming sessions

    Useful for monitoring and administration.
    """
    sessions = []

    for session_id, ws in active_connections.items():
        stats = streaming_engine.get_session_stats(session_id)
        if stats:
            sessions.append({
                "session_id": session_id,
                "learner_id": stats.get('learner_id'),
                "mechanics_generated": stats.get('mechanics_generated'),
                "current_difficulty": stats.get('current_difficulty'),
                "engagement_level": stats.get('engagement_level'),
                "started_at": stats.get('started_at')
            })

    return {
        "active_session_count": len(sessions),
        "sessions": sessions
    }
