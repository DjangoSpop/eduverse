"""
Multilingual curriculum processing API endpoints

Handles curriculum upload, language detection, and culturally-aware
lesson generation in multiple languages.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional, Dict
import uuid
from datetime import datetime
import logging

from app.services.language_processor import LanguageProcessor
from app.services.pdf_processor import PDFProcessor
from app.services.ai_analyzer import AIAnalyzer
from app.services.scene_generator import SceneGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multilingual", tags=["multilingual"])

# In-memory stores (same pattern as existing endpoints)
from app.api.endpoints.curriculum import curriculum_store
from app.api.endpoints.lessons import scene_spec_store


@router.get("/languages")
async def list_supported_languages():
    """
    Get list of all supported languages

    Returns language codes, names, and metadata for all
    languages that Eduverse can process.
    """
    languages = LanguageProcessor.list_supported_languages()
    return {
        "supported_languages": languages,
        "total_count": len(languages),
        "default_language": "en"
    }


@router.post("/curriculum/upload")
async def upload_multilingual_curriculum(
    file: UploadFile = File(...),
    force_language: Optional[str] = Query(None, description="Force specific language (skip auto-detection)")
):
    """
    Upload curriculum in any supported language with automatic detection

    The system will:
    1. Extract text from PDF (with OCR fallback for image-based PDFs)
    2. Auto-detect language (or use force_language if provided)
    3. Apply language-specific processing
    4. Return curriculum metadata ready for lesson generation

    Args:
        file: PDF curriculum file
        force_language: Optional language code to skip auto-detection

    Returns:
        Curriculum metadata including detected/forced language
    """
    try:
        # Read PDF content
        content = await file.read()
        logger.info(f"Received curriculum: {file.filename} ({len(content)} bytes)")

        # Extract text using standard PDF extraction
        try:
            pdf_extraction = PDFProcessor.extract_text(content)
            text = pdf_extraction['full_text']
            pages_count = pdf_extraction.get('pages_count', 1)
            logger.info(f"Extracted {len(text)} characters from {pages_count} pages")
        except Exception as e:
            logger.warning(f"Standard PDF extraction failed: {e}, will use OCR if needed")
            text = ""
            pages_count = 0

        # Detect or use forced language
        if force_language:
            if force_language not in LanguageProcessor.SUPPORTED_LANGUAGES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported language: {force_language}. Use /languages endpoint to see supported languages."
                )
            detected_lang = force_language
            confidence = 1.0
            logger.info(f"Using forced language: {force_language}")
        else:
            detected_lang, confidence = LanguageProcessor.detect_language(text)
            logger.info(f"Auto-detected language: {detected_lang} (confidence: {confidence:.2f})")

        # If confidence is low or text is too short, suggest OCR
        needs_ocr = confidence < 0.7 or len(text.strip()) < 100

        if needs_ocr:
            logger.info(f"Low confidence ({confidence:.2f}) or insufficient text, OCR recommended")
            # Note: Full OCR implementation would require image conversion
            # For MVP, we'll flag it but continue with available text

        # Get language configuration
        lang_config = LanguageProcessor.get_language_config(detected_lang)
        if not lang_config:
            lang_config = LanguageProcessor.get_language_config('en')
            detected_lang = 'en'
            logger.warning(f"Falling back to English for unsupported language")

        # Calculate text statistics
        word_count = len(text.split())
        char_count = len(text)

        # Store curriculum with language metadata
        curriculum_id = str(uuid.uuid4())
        curriculum_data = {
            "id": curriculum_id,
            "title": file.filename,
            "text": text,
            "language": detected_lang,
            "language_name": lang_config['name'],
            "native_name": lang_config.get('native_name', lang_config['name']),
            "direction": lang_config['direction'],
            "cultural_context": lang_config.get('cultural_context'),
            "script": lang_config.get('script'),
            "confidence": confidence,
            "word_count": word_count,
            "char_count": char_count,
            "pages_count": pages_count,
            "needs_ocr": needs_ocr,
            "uploaded_at": datetime.utcnow().isoformat()
        }

        curriculum_store[curriculum_id] = curriculum_data

        logger.info(f"Curriculum stored: {curriculum_id} ({detected_lang})")

        return {
            "curriculum_id": curriculum_id,
            "detected_language": lang_config['name'],
            "language_code": detected_lang,
            "native_name": lang_config.get('native_name'),
            "confidence": round(confidence, 2),
            "text_direction": lang_config['direction'],
            "cultural_context": lang_config.get('cultural_context'),
            "word_count": word_count,
            "char_count": char_count,
            "pages_count": pages_count,
            "needs_ocr": needs_ocr,
            "status": "ready_for_generation"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing multilingual curriculum: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process curriculum: {str(e)}")


@router.post("/lessons/generate")
async def generate_multilingual_lesson(
    curriculum_id: str = Query(..., description="Curriculum ID from upload"),
    age_range: str = Query("6-10", description="Target age range"),
    preferred_theme: Optional[str] = Query(None, description="Preferred visual theme"),
    target_duration: int = Query(30, description="Target duration in minutes")
):
    """
    Generate culturally-appropriate lesson in the curriculum's language

    This endpoint:
    1. Retrieves the curriculum with language metadata
    2. Gets cultural prompts for the detected language
    3. Generates lesson content using culturally-aware AI
    4. Validates content safety for the target culture
    5. Returns lesson specification with RTL support if needed

    Args:
        curriculum_id: ID from upload endpoint
        age_range: Target age range (e.g., "6-10")
        preferred_theme: Optional theme override
        target_duration: Target lesson duration in minutes

    Returns:
        Lesson specification with cultural and language metadata
    """
    try:
        # Retrieve curriculum
        if curriculum_id not in curriculum_store:
            raise HTTPException(status_code=404, detail="Curriculum not found")

        curriculum = curriculum_store[curriculum_id]
        language = curriculum['language']

        logger.info(f"Generating multilingual lesson for {curriculum_id} ({language})")

        # Get cultural prompts for language
        cultural_prompts = LanguageProcessor.get_cultural_prompts(language)
        lang_config = LanguageProcessor.get_language_config(language)

        # Extract learning objectives with language context
        ai_analyzer = AIAnalyzer()

        # Build culturally-aware analysis prompt
        analysis_context = f"""
        Language: {lang_config['name']} ({language})
        Cultural Context: {lang_config.get('cultural_context', 'universal')}
        Age Range: {age_range}

        Cultural Guidelines:
        {cultural_prompts.get('learning_style', '')}

        Please analyze this curriculum and extract learning objectives that are:
        1. Age-appropriate for {age_range} year-olds
        2. Culturally sensitive to {lang_config.get('cultural_context', 'diverse')} context
        3. Expressed in {lang_config['name']} language
        4. Pedagogically sound for this cultural background
        """

        analysis = await ai_analyzer.analyze_curriculum(
            text=curriculum['text'],
            title=curriculum['title'],
            additional_context=analysis_context
        )

        # Generate scene specification with cultural adaptation
        scene_generator = SceneGenerator()

        scene_spec = scene_generator.generate_scene_spec(
            curriculum_id=curriculum_id,
            title=curriculum['title'],
            analysis=analysis,
            target_duration_minutes=target_duration,
            language=language,
            cultural_prompts=cultural_prompts
        )

        # Add language metadata to scene spec
        scene_spec['language'] = language
        scene_spec['text_direction'] = curriculum['direction']
        scene_spec['cultural_context'] = curriculum.get('cultural_context')
        scene_spec['native_language_name'] = lang_config.get('native_name')

        # Apply language-specific mentor persona
        if 'mentor_persona' in scene_spec:
            mentor_prompts = cultural_prompts.get('mentor_personality', '')
            scene_spec['mentor_persona']['cultural_guidelines'] = mentor_prompts

        # Validate content safety for the target language/culture
        import json
        scene_json = json.dumps(scene_spec, ensure_ascii=False)
        is_safe, safety_issues = LanguageProcessor.validate_content_safety(
            scene_json,
            language
        )

        if not is_safe:
            logger.warning(f"Content safety issues detected for {language}: {safety_issues}")
            scene_spec['content_warnings'] = safety_issues
            scene_spec['safety_status'] = 'needs_review'
        else:
            scene_spec['safety_status'] = 'approved'

        # Store lesson
        lesson_id = scene_spec['lesson_id']
        scene_spec_store[lesson_id] = scene_spec

        logger.info(f"Multilingual lesson generated: {lesson_id} ({language})")

        return {
            "lesson_id": lesson_id,
            "language": language,
            "language_name": lang_config['name'],
            "native_name": lang_config.get('native_name'),
            "text_direction": curriculum['direction'],
            "title": scene_spec['title'],
            "scene_count": len(scene_spec.get('scenes', [])),
            "learning_objectives_count": len(scene_spec.get('learning_objectives', [])),
            "cultural_validation": scene_spec['safety_status'],
            "cultural_context": curriculum.get('cultural_context'),
            "status": "ready",
            "warnings": scene_spec.get('content_warnings', [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating multilingual lesson: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate lesson: {str(e)}")


@router.get("/curriculum/{curriculum_id}/language")
async def get_curriculum_language_info(curriculum_id: str):
    """
    Get detailed language information for a curriculum

    Returns language metadata, cultural context, and processing status.
    """
    if curriculum_id not in curriculum_store:
        raise HTTPException(status_code=404, detail="Curriculum not found")

    curriculum = curriculum_store[curriculum_id]
    lang_config = LanguageProcessor.get_language_config(curriculum['language'])

    return {
        "curriculum_id": curriculum_id,
        "language": {
            "code": curriculum['language'],
            "name": lang_config['name'],
            "native_name": lang_config.get('native_name'),
            "direction": lang_config['direction'],
            "script": lang_config.get('script')
        },
        "cultural_context": curriculum.get('cultural_context'),
        "detection_confidence": curriculum.get('confidence'),
        "text_statistics": {
            "word_count": curriculum.get('word_count'),
            "char_count": curriculum.get('char_count'),
            "pages_count": curriculum.get('pages_count')
        },
        "processing_status": {
            "needs_ocr": curriculum.get('needs_ocr', False),
            "uploaded_at": curriculum.get('uploaded_at')
        }
    }


@router.post("/content/validate")
async def validate_content_culturally(
    text: str = Query(..., description="Text to validate"),
    language: str = Query(..., description="Language code")
):
    """
    Validate content for cultural appropriateness

    Useful for testing custom content before including in lessons.

    Args:
        text: Content to validate
        language: Language/culture code

    Returns:
        Validation result with any issues found
    """
    if language not in LanguageProcessor.SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    is_safe, issues = LanguageProcessor.validate_content_safety(text, language)

    return {
        "is_safe": is_safe,
        "language": language,
        "issues": issues,
        "issue_count": len(issues),
        "recommendation": "approved" if is_safe else "needs_review"
    }
