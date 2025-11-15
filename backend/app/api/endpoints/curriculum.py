"""
Curriculum API endpoints for PDF upload and management.

Handles curriculum document uploads, text extraction, and AI analysis.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from typing import List, Optional
import uuid
from datetime import datetime

from app.services.pdf_processor import PDFProcessor
from app.services.ai_analyzer import AIAnalyzer
from app.storage import memory_store
from app.models.curriculum import (
    CurriculumUploadResponse,
    CurriculumAnalysisRequest,
    CurriculumAnalysisResponse,
    Curriculum,
    CurriculumMetadata,
    AIAnalysisResult
)
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.post("/upload", response_model=CurriculumUploadResponse)
async def upload_curriculum(
    file: UploadFile = File(...),
    title: Optional[str] = None
):
    """
    Upload a curriculum PDF for processing.

    This endpoint:
    1. Validates the PDF file
    2. Extracts text content from all pages
    3. Stores the curriculum for later analysis
    4. Returns a curriculum ID for generating lessons

    Args:
        file: PDF file (max 10MB)
        title: Optional custom title (defaults to filename)

    Returns:
        CurriculumUploadResponse with curriculum ID and preview

    Raises:
        400: Invalid file format or corrupted PDF
        413: File too large
        500: Processing error
    """
    logger.info(f"Curriculum upload started: {file.filename}")

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a PDF document."
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    PDFProcessor.validate_size(file_size, settings.max_upload_size_mb)

    # Validate PDF format
    if not PDFProcessor.validate_pdf(content):
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted PDF file. Please ensure the file is a valid PDF."
        )

    # Extract text and metadata
    try:
        extraction_result = PDFProcessor.extract_text(content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during PDF extraction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extract text from PDF"
        )

    # Generate curriculum ID
    curriculum_id = str(uuid.uuid4())

    # Determine title
    if not title:
        title = PDFProcessor.sanitize_filename(file.filename)
        title = title.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()

    # Create metadata
    metadata = CurriculumMetadata(
        page_count=extraction_result["metadata"]["page_count"],
        word_count=extraction_result["metadata"]["word_count"],
        char_count=extraction_result["metadata"]["char_count"],
        file_size_bytes=file_size,
        uploaded_at=datetime.utcnow()
    )

    # Create curriculum object
    curriculum = Curriculum(
        id=curriculum_id,
        title=title,
        filename=file.filename,
        full_text=extraction_result["full_text"],
        pages=extraction_result["pages"],
        metadata=metadata,
        status="uploaded"
    )

    # Store curriculum
    memory_store.save_curriculum(curriculum_id, curriculum.model_dump())

    logger.info(
        f"Curriculum uploaded successfully: {curriculum_id} "
        f"({metadata.page_count} pages, {metadata.word_count} words)"
    )

    # Return response
    return CurriculumUploadResponse(
        curriculum_id=curriculum_id,
        title=title,
        page_count=metadata.page_count,
        word_count=metadata.word_count,
        extracted_text_preview=extraction_result["full_text"][:200] + "...",
        status="ready_for_generation"
    )


@router.post("/analyze", response_model=CurriculumAnalysisResponse)
async def analyze_curriculum(request: CurriculumAnalysisRequest):
    """
    Analyze curriculum content using AI.

    Uses Claude to perform deep semantic analysis of the curriculum,
    extracting learning objectives, concepts, and pedagogical insights.

    Args:
        request: Analysis request with curriculum ID

    Returns:
        CurriculumAnalysisResponse with analysis results

    Raises:
        404: Curriculum not found
        500: Analysis failed
    """
    logger.info(f"Starting curriculum analysis: {request.curriculum_id}")

    # Retrieve curriculum
    curriculum_data = memory_store.get_curriculum(request.curriculum_id)

    if not curriculum_data:
        raise HTTPException(
            status_code=404,
            detail=f"Curriculum not found: {request.curriculum_id}"
        )

    curriculum = Curriculum(**curriculum_data)

    # Check if already analyzed
    if curriculum.ai_analysis and not request.force_reanalysis:
        logger.info(f"Using existing analysis for: {request.curriculum_id}")
        return CurriculumAnalysisResponse(
            curriculum_id=curriculum.id,
            status="completed",
            analysis=curriculum.ai_analysis,
            message="Analysis already completed (use force_reanalysis=true to reanalyze)"
        )

    # Update status
    curriculum.status = "analyzing"
    memory_store.save_curriculum(curriculum.id, curriculum.model_dump())

    # Perform AI analysis
    try:
        analyzer = AIAnalyzer()
        analysis_result = await analyzer.analyze_curriculum(
            text=curriculum.full_text,
            title=curriculum.title
        )

        # Create AIAnalysisResult
        ai_analysis = AIAnalysisResult(
            **analysis_result,
            analyzed_at=datetime.utcnow()
        )

        # Update curriculum with analysis
        curriculum.ai_analysis = ai_analysis
        curriculum.status = "analyzed"
        memory_store.save_curriculum(curriculum.id, curriculum.model_dump())

        logger.info(f"Analysis completed for: {curriculum.id}")

        return CurriculumAnalysisResponse(
            curriculum_id=curriculum.id,
            status="completed",
            analysis=ai_analysis,
            message="Analysis completed successfully"
        )

    except HTTPException:
        # Update status on error
        curriculum.status = "error"
        memory_store.save_curriculum(curriculum.id, curriculum.model_dump())
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        curriculum.status = "error"
        memory_store.save_curriculum(curriculum.id, curriculum.model_dump())

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/{curriculum_id}", response_model=Curriculum)
async def get_curriculum(curriculum_id: str):
    """
    Retrieve curriculum by ID.

    Args:
        curriculum_id: Curriculum identifier

    Returns:
        Complete curriculum with text and analysis

    Raises:
        404: Curriculum not found
    """
    logger.debug(f"Retrieving curriculum: {curriculum_id}")

    curriculum_data = memory_store.get_curriculum(curriculum_id)

    if not curriculum_data:
        raise HTTPException(
            status_code=404,
            detail=f"Curriculum not found: {curriculum_id}"
        )

    return Curriculum(**curriculum_data)


@router.get("/", response_model=List[Curriculum])
async def list_curricula(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max items to return")
):
    """
    List all curricula.

    Args:
        skip: Number of items to skip (pagination)
        limit: Maximum items to return

    Returns:
        List of curricula
    """
    logger.debug(f"Listing curricula (skip={skip}, limit={limit})")

    all_curricula = memory_store.MemoryStore.list_all(memory_store.curriculum_store)

    # Sort by upload time (most recent first)
    all_curricula.sort(
        key=lambda x: x.get("metadata", {}).get("uploaded_at", ""),
        reverse=True
    )

    # Apply pagination
    paginated = all_curricula[skip:skip + limit]

    return [Curriculum(**c) for c in paginated]


@router.delete("/{curriculum_id}")
async def delete_curriculum(curriculum_id: str):
    """
    Delete a curriculum.

    Args:
        curriculum_id: Curriculum identifier

    Returns:
        Success message

    Raises:
        404: Curriculum not found
    """
    logger.info(f"Deleting curriculum: {curriculum_id}")

    deleted = memory_store.MemoryStore.delete(
        memory_store.curriculum_store,
        curriculum_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Curriculum not found: {curriculum_id}"
        )

    return {"message": "Curriculum deleted successfully", "id": curriculum_id}
