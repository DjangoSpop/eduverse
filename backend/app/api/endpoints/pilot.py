"""
Pilot Program Analytics API Endpoints

Endpoints for managing pilot program participants and collecting analytics data.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Optional
from pydantic import BaseModel
import logging

from app.services.pilot_analytics import pilot_analytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pilot", tags=["pilot"])


# Request models
class EnrollParticipantRequest(BaseModel):
    participant_id: str
    age: int
    grade_level: int
    language: str
    school: str
    pre_test_score: float


class RecordSessionRequest(BaseModel):
    session_id: str
    participant_id: str
    curriculum_id: str
    language: str
    started_at: str
    ended_at: Optional[str] = None
    duration_seconds: float = 0.0
    mechanics_completed: int = 0
    mechanics_successful: int = 0
    average_time_per_mechanic: float = 0.0
    error_count: int = 0
    help_requests: int = 0
    average_fps: float = 0.0
    min_fps: float = 0.0
    memory_usage_mb: float = 0.0
    load_time_seconds: float = 0.0
    crash_count: int = 0
    final_difficulty: str = ""
    xp_earned: int = 0
    badges_earned: int = 0


class RecordSurveyRequest(BaseModel):
    participant_id: str
    session_id: str
    timestamp: str
    fun_rating: int
    learning_rating: int
    difficulty_rating: int
    would_recommend: int
    liked_most: str = ""
    liked_least: str = ""
    suggestions: str = ""


class CompleteParticipantRequest(BaseModel):
    post_test_score: float


# Endpoints

@router.post("/participants/enroll")
async def enroll_participant(request: EnrollParticipantRequest):
    """
    Enroll a new participant in the pilot program

    Records baseline pre-test score and participant information.
    """
    try:
        participant = pilot_analytics.enroll_participant(
            participant_id=request.participant_id,
            age=request.age,
            grade_level=request.grade_level,
            language=request.language,
            school=request.school,
            pre_test_score=request.pre_test_score
        )

        return {
            "status": "enrolled",
            "participant_id": participant.participant_id,
            "enrolled_at": participant.enrolled_at,
            "message": f"Participant {participant.participant_id} enrolled successfully"
        }

    except Exception as e:
        logger.error(f"Error enrolling participant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to enroll participant: {str(e)}")


@router.post("/participants/{participant_id}/complete")
async def complete_participant(participant_id: str, request: CompleteParticipantRequest):
    """
    Mark participant as completed with post-test score

    Calculates learning gain based on pre/post test comparison.
    """
    try:
        pilot_analytics.complete_participant(
            participant_id=participant_id,
            post_test_score=request.post_test_score
        )

        # Get summary with learning gain
        summary = pilot_analytics.get_participant_summary(participant_id)

        if not summary:
            raise HTTPException(status_code=404, detail="Participant not found")

        return {
            "status": "completed",
            "participant_id": participant_id,
            "learning_outcomes": summary['learning_outcomes'],
            "message": f"Participant {participant_id} completed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing participant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to complete participant: {str(e)}")


@router.get("/participants/{participant_id}")
async def get_participant_summary(participant_id: str):
    """
    Get comprehensive summary for a participant

    Returns all sessions, learning outcomes, and satisfaction data.
    """
    summary = pilot_analytics.get_participant_summary(participant_id)

    if not summary:
        raise HTTPException(status_code=404, detail="Participant not found")

    return summary


@router.post("/sessions/record")
async def record_session(request: RecordSessionRequest):
    """
    Record a completed learning session

    Captures engagement, performance, and behavior metrics.
    """
    try:
        session = pilot_analytics.record_session(request.dict())

        return {
            "status": "recorded",
            "session_id": session.session_id,
            "participant_id": session.participant_id,
            "message": "Session recorded successfully"
        }

    except Exception as e:
        logger.error(f"Error recording session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to record session: {str(e)}")


@router.post("/surveys/record")
async def record_survey(request: RecordSurveyRequest):
    """
    Record post-session satisfaction survey

    Captures NPS score and qualitative feedback.
    """
    try:
        survey = pilot_analytics.record_survey(request.dict())

        return {
            "status": "recorded",
            "participant_id": survey.participant_id,
            "session_id": survey.session_id,
            "nps_score": survey.would_recommend,
            "message": "Survey recorded successfully"
        }

    except Exception as e:
        logger.error(f"Error recording survey: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to record survey: {str(e)}")


@router.get("/summary")
async def get_pilot_summary():
    """
    Get comprehensive summary of entire pilot program

    Returns all key metrics, targets, and performance indicators.
    """
    summary = pilot_analytics.get_pilot_summary()

    return summary


@router.get("/recommendations")
async def get_recommendations():
    """
    Get actionable recommendations based on pilot data

    Analyzes metrics and provides specific improvement suggestions.
    """
    recommendations = pilot_analytics.get_recommendations()

    return {
        "recommendations": recommendations,
        "total_count": len(recommendations)
    }


@router.get("/export/csv")
async def export_data_csv():
    """
    Export all pilot data to CSV format

    Downloads comprehensive CSV with participants, sessions, and surveys.
    """
    try:
        csv_content = pilot_analytics.export_to_csv()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=eduverse_pilot_data.csv"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")


@router.get("/stats")
async def get_pilot_stats():
    """
    Get quick statistics overview

    Returns key numbers for dashboard display.
    """
    summary = pilot_analytics.get_pilot_summary()

    return {
        "participants": {
            "total": summary['program_overview']['total_participants'],
            "completed": summary['program_overview']['completed_participants']
        },
        "sessions": {
            "total": summary['program_overview']['total_sessions'],
            "total_hours": summary['program_overview']['total_hours']
        },
        "learning_gain": {
            "average": summary['learning_outcomes']['average_learning_gain_percentage'],
            "target_met": summary['learning_outcomes']['target_met']
        },
        "nps_score": {
            "score": summary['satisfaction']['nps_score'],
            "target_met": summary['satisfaction']['target_met']
        },
        "performance": {
            "average_fps": summary['performance']['average_fps'],
            "target_met": summary['performance']['target_met']
        }
    }
