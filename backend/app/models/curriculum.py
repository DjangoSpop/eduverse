"""
Curriculum data models for PDF uploads and text extraction.

Models for handling curriculum documents, their metadata,
and AI analysis results.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class PageContent(BaseModel):
    """Content from a single page of the curriculum PDF"""
    page: int = Field(..., ge=1, description="Page number (1-indexed)")
    text: str = Field(..., description="Extracted text content")
    char_count: int = Field(..., ge=0, description="Character count")


class CurriculumMetadata(BaseModel):
    """Metadata about the curriculum document"""
    page_count: int = Field(..., ge=1, description="Total number of pages")
    word_count: int = Field(..., ge=0, description="Total word count")
    char_count: int = Field(..., ge=0, description="Total character count")
    file_size_bytes: int = Field(..., ge=0, description="Original file size")
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Upload timestamp"
    )


class GamificationIdea(BaseModel):
    """Suggested gamification mechanic for a concept"""
    concept: str = Field(..., description="Educational concept to gamify")
    mechanic: str = Field(
        ...,
        description="Game mechanic (collect, build, explore, puzzle, etc.)"
    )
    description: str = Field(..., description="How to implement the gamification")


class AssessmentCheckpoint(BaseModel):
    """Suggested assessment point in the lesson"""
    after_concept: str = Field(..., description="Concept to assess")
    question_type: str = Field(
        ...,
        description="Type of question (multiple_choice, voice, ordering, etc.)"
    )
    sample_question: str = Field(..., description="Example assessment question")


class AIAnalysisResult(BaseModel):
    """
    Result of AI curriculum analysis.

    Contains extracted learning objectives, concepts, and pedagogical insights.
    """
    learning_objectives: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Extracted learning objectives with Bloom levels"
    )
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Main concepts covered"
    )
    recommended_age_range: str = Field(
        ...,
        description="Suggested age range (e.g., '6-8', '9-12')"
    )
    difficulty_estimate: int = Field(
        ...,
        ge=1,
        le=5,
        description="Overall difficulty (1-5)"
    )
    engagement_hooks: List[str] = Field(
        default_factory=list,
        description="Elements that would engage children"
    )
    gamification_ideas: List[GamificationIdea] = Field(
        default_factory=list,
        description="Suggested gamification mechanics"
    )
    narrative_theme: str = Field(
        ...,
        description="Recommended visual theme"
    )
    theme_reasoning: str = Field(
        ...,
        description="Why this theme fits the content"
    )
    assessment_checkpoints: List[AssessmentCheckpoint] = Field(
        default_factory=list,
        description="Suggested assessment points"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analysis timestamp"
    )


class Curriculum(BaseModel):
    """
    Complete curriculum document with content and metadata.

    Represents an uploaded PDF curriculum with all extracted
    information and AI analysis.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., description="Curriculum title")
    filename: str = Field(..., description="Original filename")
    full_text: str = Field(..., description="Complete extracted text")
    pages: List[PageContent] = Field(
        default_factory=list,
        description="Page-by-page content"
    )
    metadata: CurriculumMetadata = Field(..., description="Document metadata")
    ai_analysis: Optional[AIAnalysisResult] = Field(
        None,
        description="AI analysis results (populated after analysis)"
    )
    status: str = Field(
        default="uploaded",
        description="Processing status: uploaded, analyzing, analyzed, error"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "curr-12345",
                "title": "Grade 2 Ocean Science",
                "filename": "ocean_science_grade2.pdf",
                "full_text": "Ocean creatures are fascinating...",
                "pages": [],
                "metadata": {
                    "page_count": 5,
                    "word_count": 1200,
                    "char_count": 6500,
                    "file_size_bytes": 245000
                },
                "status": "uploaded"
            }
        }


class CurriculumUploadResponse(BaseModel):
    """Response from curriculum upload endpoint"""
    curriculum_id: str = Field(..., description="Unique curriculum identifier")
    title: str = Field(..., description="Curriculum title")
    page_count: int = Field(..., description="Number of pages")
    word_count: int = Field(..., description="Total words")
    extracted_text_preview: str = Field(
        ...,
        description="First 200 characters preview"
    )
    status: str = Field(..., description="Processing status")

    class Config:
        json_schema_extra = {
            "example": {
                "curriculum_id": "curr-12345",
                "title": "Ocean Science",
                "page_count": 5,
                "word_count": 1200,
                "extracted_text_preview": "Ocean creatures are amazing...",
                "status": "ready_for_generation"
            }
        }


class CurriculumAnalysisRequest(BaseModel):
    """Request to analyze a curriculum"""
    curriculum_id: str = Field(..., description="ID of curriculum to analyze")
    force_reanalysis: bool = Field(
        default=False,
        description="Force reanalysis even if already analyzed"
    )


class CurriculumAnalysisResponse(BaseModel):
    """Response from curriculum analysis endpoint"""
    curriculum_id: str = Field(..., description="Curriculum ID")
    status: str = Field(..., description="Analysis status")
    analysis: Optional[AIAnalysisResult] = Field(
        None,
        description="Analysis results (if complete)"
    )
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "curriculum_id": "curr-12345",
                "status": "completed",
                "analysis": {},
                "message": "Analysis completed successfully"
            }
        }
