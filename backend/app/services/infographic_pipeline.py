"""
Infographic Pipeline Orchestrator

Professional pipeline that orchestrates:
1. DeepSeek OCR (PDF → Text insights)
2. Gemini Infographic Generation (Text → Visual layout)
3. Animation Engine (Layout → Animated sequence)

Optimized for speed with parallel processing, caching, and streaming.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

from pydantic import BaseModel, Field

from app.services.deepseek_ocr_service import (
    DeepSeekOCRService,
    DeepSeekOCRConfig,
    OCRResult,
    get_deepseek_service
)
from app.services.gemini_infographic_service import (
    GeminiInfographicService,
    GeminiInfographicConfig,
    InfographicLayout,
    InfographicStyle,
    get_gemini_service
)
from app.services.animation_engine_service import (
    AnimationEngineService,
    AnimationEngineConfig,
    AnimatedInfographic,
    get_animation_engine
)

logger = logging.getLogger(__name__)


class PipelineConfig(BaseModel):
    """Configuration for infographic pipeline"""
    enable_parallel_processing: bool = True
    enable_streaming: bool = True
    max_concurrent_infographics: int = 3
    cache_intermediate_results: bool = True
    auto_select_key_insights: bool = True
    max_insights_length: int = 1000


class PipelineStage(str):
    """Pipeline processing stages"""
    OCR = "ocr"
    INSIGHT_EXTRACTION = "insight_extraction"
    INFOGRAPHIC_GENERATION = "infographic_generation"
    ANIMATION = "animation"
    COMPLETE = "complete"


class PipelineProgress(BaseModel):
    """Real-time pipeline progress"""
    stage: str
    progress: float  # 0.0 to 1.0
    message: str
    estimated_time_remaining: float = 0.0


class InfographicPipelineResult(BaseModel):
    """Complete pipeline result"""
    ocr_result: OCRResult
    key_insights: str
    infographic: InfographicLayout
    animation: AnimatedInfographic
    metadata: Dict = Field(default_factory=dict)
    total_processing_time: float = 0.0


class InfographicPipeline:
    """
    Professional pipeline for PDF → Animated Infographic conversion.

    Performance Optimizations:
    - Parallel OCR page processing
    - Concurrent infographic generation
    - Streaming progress updates
    - Multi-level caching (OCR, infographics, animations)
    - Intelligent batching
    - Connection pooling across all services
    """

    def __init__(
        self,
        config: PipelineConfig,
        ocr_service: Optional[DeepSeekOCRService] = None,
        gemini_service: Optional[GeminiInfographicService] = None,
        animation_engine: Optional[AnimationEngineService] = None
    ):
        self.config = config
        self.ocr_service = ocr_service or get_deepseek_service()
        self.gemini_service = gemini_service or get_gemini_service()
        self.animation_engine = animation_engine or get_animation_engine()

        # Progress tracking
        self._progress_callbacks = []

    def add_progress_callback(self, callback):
        """Add callback for progress updates"""
        self._progress_callbacks.append(callback)

    async def _notify_progress(self, stage: str, progress: float, message: str):
        """Notify all progress callbacks"""
        progress_update = PipelineProgress(
            stage=stage,
            progress=progress,
            message=message
        )

        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress_update)
                else:
                    callback(progress_update)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def _extract_key_insights(self, ocr_result: OCRResult, max_length: int = 1000) -> str:
        """
        Extract key insights from OCR text using intelligent summarization.

        Args:
            ocr_result: OCR extraction result
            max_length: Maximum insight length

        Returns:
            Condensed key insights
        """
        text = ocr_result.text

        # Extract important sentences (simple heuristic)
        # In production, use NLP/LLM for better extraction
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        # Priority scoring
        scored_sentences = []
        for sent in sentences:
            score = 0

            # Longer sentences often have more info
            if 50 < len(sent) < 200:
                score += 2

            # Contains numbers (data points)
            if any(char.isdigit() for char in sent):
                score += 3

            # Contains key educational words
            key_words = ['learn', 'important', 'key', 'main', 'because', 'therefore', 'result']
            if any(word in sent.lower() for word in key_words):
                score += 2

            # Near a table or diagram
            # (would check position in actual implementation)

            scored_sentences.append((score, sent))

        # Sort by score and take top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])

        insights = []
        total_length = 0

        for score, sent in scored_sentences:
            if total_length + len(sent) <= max_length:
                insights.append(sent)
                total_length += len(sent)
            else:
                break

        result = '. '.join(insights) + '.'

        # Include table summaries if available
        if ocr_result.tables:
            table_summary = f"\n\nData Tables: {len(ocr_result.tables)} tables with key data points."
            if total_length + len(table_summary) <= max_length:
                result += table_summary

        logger.info(f"Extracted {len(insights)} key insights ({len(result)} chars) from {len(sentences)} sentences")

        return result

    async def process_pdf_async(
        self,
        pdf_path: Path,
        age_range: str = "6-10",
        style: InfographicStyle = InfographicStyle.COLORFUL,
        topic: Optional[str] = None,
        generate_variations: int = 1
    ) -> List[InfographicPipelineResult]:
        """
        Process PDF through complete pipeline with optimizations.

        Args:
            pdf_path: Path to PDF file
            age_range: Target age range
            style: Infographic style
            topic: Optional topic override
            generate_variations: Number of infographic variations

        Returns:
            List of pipeline results (one per variation)
        """
        start_time = asyncio.get_event_loop().time()
        results = []

        try:
            # Stage 1: OCR Extraction (20% of progress)
            await self._notify_progress(PipelineStage.OCR, 0.0, "Starting OCR extraction...")

            ocr_result = await self.ocr_service.extract_from_pdf_async(
                pdf_path,
                extract_tables=True,
                extract_diagrams=True,
                parallel_pages=self.config.enable_parallel_processing
            )

            await self._notify_progress(PipelineStage.OCR, 0.2, f"OCR complete: {ocr_result.page_count} pages")

            # Stage 2: Insight Extraction (30% of progress)
            await self._notify_progress(
                PipelineStage.INSIGHT_EXTRACTION,
                0.3,
                "Extracting key insights..."
            )

            if self.config.auto_select_key_insights:
                key_insights = self._extract_key_insights(
                    ocr_result,
                    max_length=self.config.max_insights_length
                )
            else:
                key_insights = ocr_result.text[:self.config.max_insights_length]

            await self._notify_progress(
                PipelineStage.INSIGHT_EXTRACTION,
                0.4,
                f"Insights extracted: {len(key_insights)} chars"
            )

            # Stage 3: Infographic Generation (60% of progress)
            await self._notify_progress(
                PipelineStage.INFOGRAPHIC_GENERATION,
                0.5,
                f"Generating {generate_variations} infographic(s)..."
            )

            if generate_variations > 1 and self.config.enable_parallel_processing:
                # Parallel generation
                infographics = await self.gemini_service.generate_multiple_infographics_async(
                    key_insights,
                    variations=generate_variations,
                    age_range=age_range
                )
            else:
                # Sequential generation
                infographics = []
                for i in range(generate_variations):
                    infographic = await self.gemini_service.generate_infographic_async(
                        key_insights,
                        age_range=age_range,
                        style=style,
                        topic=topic
                    )
                    infographics.append(infographic)

                    await self._notify_progress(
                        PipelineStage.INFOGRAPHIC_GENERATION,
                        0.5 + (0.1 * (i + 1) / generate_variations),
                        f"Generated infographic {i + 1}/{generate_variations}"
                    )

            await self._notify_progress(
                PipelineStage.INFOGRAPHIC_GENERATION,
                0.7,
                f"Infographics complete: {len(infographics)} created"
            )

            # Stage 4: Animation Generation (90% of progress)
            await self._notify_progress(
                PipelineStage.ANIMATION,
                0.8,
                "Generating animations..."
            )

            if self.config.enable_parallel_processing:
                # Parallel animation generation
                animation_tasks = [
                    self.animation_engine.generate_animation_async(infographic, age_range)
                    for infographic in infographics
                ]
                animations = await asyncio.gather(*animation_tasks)
            else:
                # Sequential animation
                animations = []
                for i, infographic in enumerate(infographics):
                    animation = await self.animation_engine.generate_animation_async(
                        infographic,
                        age_range
                    )
                    animations.append(animation)

                    await self._notify_progress(
                        PipelineStage.ANIMATION,
                        0.8 + (0.1 * (i + 1) / len(infographics)),
                        f"Animated {i + 1}/{len(infographics)}"
                    )

            # Combine results
            total_time = asyncio.get_event_loop().time() - start_time

            for i, (infographic, animation) in enumerate(zip(infographics, animations)):
                result = InfographicPipelineResult(
                    ocr_result=ocr_result,
                    key_insights=key_insights,
                    infographic=infographic,
                    animation=animation,
                    total_processing_time=total_time,
                    metadata={
                        "pdf_path": str(pdf_path),
                        "variation_index": i,
                        "total_variations": len(infographics),
                        "age_range": age_range,
                        "style": style.value,
                        "processing_breakdown": {
                            "ocr_time": ocr_result.processing_time,
                            "infographic_time": infographic.metadata.get("processing_time", 0),
                            "animation_time": animation.metadata.get("processing_time", 0),
                            "total_time": total_time
                        },
                        "optimizations_enabled": {
                            "parallel_processing": self.config.enable_parallel_processing,
                            "caching": self.config.cache_intermediate_results,
                            "streaming": self.config.enable_streaming
                        }
                    }
                )
                results.append(result)

            await self._notify_progress(
                PipelineStage.COMPLETE,
                1.0,
                f"Complete! Generated {len(results)} animated infographic(s) in {total_time:.2f}s"
            )

            logger.info(
                f"Pipeline complete: {len(results)} results in {total_time:.2f}s "
                f"(OCR: {ocr_result.processing_time:.2f}s, "
                f"avg infographic: {sum(i.metadata.get('processing_time', 0) for i in infographics)/len(infographics):.2f}s, "
                f"avg animation: {sum(a.metadata.get('processing_time', 0) for a in animations)/len(animations):.2f}s)"
            )

            return results

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            await self._notify_progress("error", 0.0, f"Error: {str(e)}")
            raise

    def process_pdf(
        self,
        pdf_path: Path,
        age_range: str = "6-10",
        style: InfographicStyle = InfographicStyle.COLORFUL
    ) -> InfographicPipelineResult:
        """Synchronous wrapper for process_pdf_async"""
        results = asyncio.run(self.process_pdf_async(pdf_path, age_range, style))
        return results[0] if results else None

    async def process_batch_async(
        self,
        pdf_paths: List[Path],
        age_range: str = "6-10",
        max_concurrent: Optional[int] = None
    ) -> List[InfographicPipelineResult]:
        """
        Process multiple PDFs with intelligent batching.

        Args:
            pdf_paths: List of PDF paths
            age_range: Target age range
            max_concurrent: Maximum concurrent processing

        Returns:
            List of all results
        """
        max_concurrent = max_concurrent or self.config.max_concurrent_infographics

        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(path):
            async with semaphore:
                logger.info(f"Processing batch item: {path}")
                batch_results = await self.process_pdf_async(path, age_range)
                return batch_results

        tasks = [process_with_semaphore(path) for path in pdf_paths]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        for batch in batch_results:
            if isinstance(batch, list):
                results.extend(batch)
            elif isinstance(batch, Exception):
                logger.error(f"Batch item failed: {batch}")

        logger.info(f"Batch processing complete: {len(results)} total results from {len(pdf_paths)} PDFs")

        return results


# Global pipeline instance
_pipeline: Optional[InfographicPipeline] = None


def get_pipeline() -> InfographicPipeline:
    """Get or create pipeline instance"""
    global _pipeline

    if _pipeline is None:
        config = PipelineConfig(
            enable_parallel_processing=True,
            enable_streaming=True,
            max_concurrent_infographics=3,
            cache_intermediate_results=True,
            auto_select_key_insights=True
        )
        _pipeline = InfographicPipeline(config)

    return _pipeline
