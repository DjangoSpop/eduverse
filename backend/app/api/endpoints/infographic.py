"""
Infographic API Endpoints

Professional API for PDF → Animated Infographic pipeline.
Supports real-time progress streaming and batch processing.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from pathlib import Path
import tempfile
import asyncio
import uuid
import logging

from app.services.infographic_pipeline import (
    InfographicPipeline,
    PipelineConfig,
    InfographicPipelineResult,
    PipelineProgress,
    get_pipeline
)
from app.services.gemini_infographic_service import InfographicStyle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/infographic", tags=["infographic"])

# Active WebSocket connections for progress streaming
active_connections: dict[str, WebSocket] = {}


@router.post("/generate")
async def generate_infographic_from_pdf(
    file: UploadFile = File(...),
    age_range: str = Query("6-10", description="Target age range"),
    style: InfographicStyle = Query(InfographicStyle.COLORFUL, description="Visual style"),
    topic: Optional[str] = Query(None, description="Optional topic override"),
    variations: int = Query(1, ge=1, le=5, description="Number of variations to generate")
):
    """
    Generate animated infographic(s) from PDF curriculum.

    Process:
    1. Extract text from PDF using DeepSeek OCR
    2. Extract key learning insights
    3. Generate infographic layout(s) using Gemini
    4. Create animation sequences

    Returns complete animated infographic ready for Unity rendering.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)

        logger.info(f"Processing PDF: {file.filename} ({len(content)} bytes)")

        # Get pipeline
        pipeline = get_pipeline()

        # Process PDF
        results = await pipeline.process_pdf_async(
            tmp_path,
            age_range=age_range,
            style=style,
            topic=topic,
            generate_variations=variations
        )

        # Clean up temp file
        tmp_path.unlink()

        # Return results
        response_data = {
            "status": "success",
            "results_count": len(results),
            "results": [
                {
                    "infographic_id": result.animation.infographic_id,
                    "title": result.infographic.title,
                    "subtitle": result.infographic.subtitle,
                    "element_count": len(result.infographic.elements),
                    "animation_duration": result.animation.total_duration,
                    "sequence_count": len(result.animation.sequences),
                    "processing_time": result.total_processing_time,
                    "infographic": result.infographic.model_dump(),
                    "animation": result.animation.model_dump(),
                    "metadata": result.metadata
                }
                for result in results
            ],
            "ocr_summary": {
                "page_count": results[0].ocr_result.page_count,
                "confidence": results[0].ocr_result.confidence,
                "tables_found": len(results[0].ocr_result.tables),
                "diagrams_found": len(results[0].ocr_result.diagrams)
            },
            "key_insights": results[0].key_insights
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Error generating infographic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/generate")
async def generate_infographic_with_progress(websocket: WebSocket):
    """
    Generate infographic with real-time progress updates via WebSocket.

    Client sends:
    {
        "pdf_base64": "...",
        "age_range": "6-10",
        "style": "colorful",
        "topic": "ocean animals"
    }

    Server streams:
    {
        "type": "progress",
        "stage": "ocr|insight_extraction|infographic_generation|animation",
        "progress": 0.0-1.0,
        "message": "..."
    }

    Final message:
    {
        "type": "complete",
        "result": { /* InfographicPipelineResult */ }
    }
    """
    await websocket.accept()

    session_id = str(uuid.uuid4())
    active_connections[session_id] = websocket

    try:
        # Receive initial request
        request_data = await websocket.receive_json()

        age_range = request_data.get("age_range", "6-10")
        style_str = request_data.get("style", "colorful")
        style = InfographicStyle(style_str)
        topic = request_data.get("topic")
        pdf_base64 = request_data.get("pdf_base64")

        if not pdf_base64:
            await websocket.send_json({
                "type": "error",
                "message": "Missing pdf_base64 in request"
            })
            return

        # Decode PDF
        import base64
        pdf_content = base64.b64decode(pdf_base64)

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_content)
            tmp_path = Path(tmp_file.name)

        # Create pipeline with progress callback
        pipeline = get_pipeline()

        async def progress_callback(progress: PipelineProgress):
            """Stream progress to WebSocket"""
            try:
                await websocket.send_json({
                    "type": "progress",
                    "stage": progress.stage,
                    "progress": progress.progress,
                    "message": progress.message
                })
            except Exception as e:
                logger.error(f"Error sending progress: {e}")

        pipeline.add_progress_callback(progress_callback)

        # Process PDF
        results = await pipeline.process_pdf_async(
            tmp_path,
            age_range=age_range,
            style=style,
            topic=topic
        )

        # Clean up
        tmp_path.unlink()

        # Send completion
        await websocket.send_json({
            "type": "complete",
            "result": {
                "infographic": results[0].infographic.model_dump(),
                "animation": results[0].animation.model_dump(),
                "processing_time": results[0].total_processing_time
            }
        })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        if session_id in active_connections:
            del active_connections[session_id]


@router.post("/batch")
async def generate_batch_infographics(
    files: List[UploadFile] = File(...),
    age_range: str = Query("6-10"),
    max_concurrent: int = Query(3, ge=1, le=10)
):
    """
    Generate infographics from multiple PDFs in parallel.

    Processes up to max_concurrent PDFs simultaneously for maximum speed.
    """
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 PDFs per batch")

    try:
        # Save all files temporarily
        tmp_paths = []
        for file in files:
            if not file.filename.endswith('.pdf'):
                continue

            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_paths.append(Path(tmp_file.name))

        logger.info(f"Processing batch of {len(tmp_paths)} PDFs")

        # Get pipeline
        pipeline = get_pipeline()

        # Process batch
        results = await pipeline.process_batch_async(
            tmp_paths,
            age_range=age_range,
            max_concurrent=max_concurrent
        )

        # Clean up temp files
        for path in tmp_paths:
            path.unlink()

        # Return summary
        return {
            "status": "success",
            "total_processed": len(results),
            "results": [
                {
                    "infographic_id": r.animation.infographic_id,
                    "title": r.infographic.title,
                    "processing_time": r.total_processing_time
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Batch processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_pipeline_stats():
    """
    Get pipeline performance statistics.
    """
    pipeline = get_pipeline()

    # Get cache stats
    ocr_cache_size = len(pipeline.ocr_service.cache)
    gemini_cache_size = len(pipeline.gemini_service.cache)

    return {
        "status": "operational",
        "active_connections": len(active_connections),
        "cache_stats": {
            "ocr_cache_entries": ocr_cache_size,
            "infographic_cache_entries": gemini_cache_size
        },
        "configuration": {
            "parallel_processing_enabled": pipeline.config.enable_parallel_processing,
            "streaming_enabled": pipeline.config.enable_streaming,
            "max_concurrent_infographics": pipeline.config.max_concurrent_infographics
        }
    }


@router.get("/styles")
async def list_available_styles():
    """
    List all available infographic styles.
    """
    return {
        "styles": [
            {
                "name": style.value,
                "description": f"{style.value.title()} visual style",
                "recommended_ages": "6-10" if style != InfographicStyle.SCIENTIFIC else "8-12"
            }
            for style in InfographicStyle
        ]
    }
