"""
DeepSeek OCR Service for PDF Data Extraction

High-performance OCR service with caching and parallel processing.
Extracts text, tables, diagrams, and metadata from PDF documents.
"""

import asyncio
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OCRResult(BaseModel):
    """OCR extraction result"""
    text: str
    tables: List[Dict] = Field(default_factory=list)
    diagrams: List[Dict] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)
    confidence: float = 0.0
    processing_time: float = 0.0
    page_count: int = 0


class DeepSeekOCRConfig(BaseModel):
    """Configuration for DeepSeek OCR"""
    api_key: str
    api_url: str = "https://api.deepseek.com/v1/ocr"
    timeout: int = 60
    max_retries: int = 3
    enable_cache: bool = True
    cache_ttl_hours: int = 24
    max_concurrent_requests: int = 5


class DeepSeekOCRService:
    """
    Professional OCR service with DeepSeek integration.

    Features:
    - Parallel page processing
    - Result caching with TTL
    - Automatic retry with exponential backoff
    - Connection pooling
    - Structured data extraction (tables, diagrams)
    """

    def __init__(self, config: DeepSeekOCRConfig):
        self.config = config
        self.cache: Dict[str, Tuple[OCRResult, datetime]] = {}
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            limits=httpx.Limits(
                max_connections=config.max_concurrent_requests,
                max_keepalive_connections=config.max_concurrent_requests
            )
        )
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def _generate_cache_key(self, pdf_content: bytes, options: Dict) -> str:
        """Generate cache key from PDF content and options"""
        content_hash = hashlib.sha256(pdf_content).hexdigest()
        options_hash = hashlib.md5(json.dumps(options, sort_keys=True).encode()).hexdigest()
        return f"ocr_{content_hash}_{options_hash}"

    def _get_cached_result(self, cache_key: str) -> Optional[OCRResult]:
        """Get cached OCR result if valid"""
        if not self.config.enable_cache:
            return None

        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            age = datetime.now() - timestamp

            if age < timedelta(hours=self.config.cache_ttl_hours):
                logger.info(f"Cache hit for {cache_key[:16]}... (age: {age.seconds}s)")
                return result
            else:
                # Remove expired entry
                del self.cache[cache_key]

        return None

    def _cache_result(self, cache_key: str, result: OCRResult):
        """Cache OCR result"""
        if self.config.enable_cache:
            self.cache[cache_key] = (result, datetime.now())
            logger.debug(f"Cached result for {cache_key[:16]}...")

    async def _extract_page_async(
        self,
        page_data: bytes,
        page_num: int,
        extract_tables: bool = True,
        extract_diagrams: bool = True
    ) -> Dict:
        """
        Extract OCR data from a single page asynchronously.

        Args:
            page_data: Image data for the page
            page_num: Page number
            extract_tables: Extract table structures
            extract_diagrams: Extract diagram metadata

        Returns:
            Dict with extracted data
        """
        async with self._semaphore:
            start_time = asyncio.get_event_loop().time()

            try:
                # Prepare request
                files = {"image": ("page.png", page_data, "image/png")}
                data = {
                    "extract_tables": extract_tables,
                    "extract_diagrams": extract_diagrams,
                    "language": "auto",
                    "output_format": "json"
                }
                headers = {"Authorization": f"Bearer {self.config.api_key}"}

                # Make request with retry logic
                for attempt in range(self.config.max_retries):
                    try:
                        response = await self.client.post(
                            self.config.api_url,
                            files=files,
                            data=data,
                            headers=headers
                        )
                        response.raise_for_status()
                        break
                    except httpx.HTTPError as e:
                        if attempt == self.config.max_retries - 1:
                            raise
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"OCR attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)

                result = response.json()
                processing_time = asyncio.get_event_loop().time() - start_time

                logger.info(f"Page {page_num} processed in {processing_time:.2f}s")

                return {
                    "page_num": page_num,
                    "text": result.get("text", ""),
                    "tables": result.get("tables", []),
                    "diagrams": result.get("diagrams", []),
                    "confidence": result.get("confidence", 0.0),
                    "processing_time": processing_time
                }

            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
                return {
                    "page_num": page_num,
                    "text": "",
                    "tables": [],
                    "diagrams": [],
                    "confidence": 0.0,
                    "error": str(e)
                }

    async def extract_from_pdf_async(
        self,
        pdf_path: Path,
        extract_tables: bool = True,
        extract_diagrams: bool = True,
        parallel_pages: bool = True
    ) -> OCRResult:
        """
        Extract text and structured data from PDF using DeepSeek OCR.

        Args:
            pdf_path: Path to PDF file
            extract_tables: Extract table structures
            extract_diagrams: Extract diagram metadata
            parallel_pages: Process pages in parallel

        Returns:
            OCRResult with extracted data
        """
        start_time = asyncio.get_event_loop().time()

        # Read PDF content
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()

        # Check cache
        options = {
            "extract_tables": extract_tables,
            "extract_diagrams": extract_diagrams
        }
        cache_key = self._generate_cache_key(pdf_content, options)

        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        # Convert PDF to images (using pdf2image or similar)
        # For now, simulate with placeholder
        page_images = await self._convert_pdf_to_images(pdf_content)

        # Process pages
        if parallel_pages:
            # Parallel processing for speed
            tasks = [
                self._extract_page_async(img, i + 1, extract_tables, extract_diagrams)
                for i, img in enumerate(page_images)
            ]
            page_results = await asyncio.gather(*tasks)
        else:
            # Sequential processing
            page_results = []
            for i, img in enumerate(page_images):
                result = await self._extract_page_async(img, i + 1, extract_tables, extract_diagrams)
                page_results.append(result)

        # Combine results
        all_text = "\n\n".join(r["text"] for r in page_results if r.get("text"))
        all_tables = [t for r in page_results for t in r.get("tables", [])]
        all_diagrams = [d for r in page_results for d in r.get("diagrams", [])]
        avg_confidence = sum(r.get("confidence", 0) for r in page_results) / len(page_results) if page_results else 0

        total_time = asyncio.get_event_loop().time() - start_time

        result = OCRResult(
            text=all_text,
            tables=all_tables,
            diagrams=all_diagrams,
            metadata={
                "source": str(pdf_path),
                "extraction_method": "deepseek_ocr",
                "timestamp": datetime.now().isoformat(),
                "pages_processed": len(page_results)
            },
            confidence=avg_confidence,
            processing_time=total_time,
            page_count=len(page_images)
        )

        # Cache result
        self._cache_result(cache_key, result)

        logger.info(f"PDF processed: {len(page_images)} pages in {total_time:.2f}s (avg: {total_time/len(page_images):.2f}s/page)")

        return result

    async def _convert_pdf_to_images(self, pdf_content: bytes) -> List[bytes]:
        """
        Convert PDF to images for OCR processing.

        Note: This is a placeholder. In production, use pdf2image or similar.
        """
        # TODO: Implement actual PDF to image conversion
        # For now, return placeholder
        logger.warning("Using placeholder PDF conversion - implement pdf2image integration")
        return [b"placeholder_image_data"]

    def extract_from_pdf(
        self,
        pdf_path: Path,
        extract_tables: bool = True,
        extract_diagrams: bool = True
    ) -> OCRResult:
        """
        Synchronous wrapper for extract_from_pdf_async.

        Args:
            pdf_path: Path to PDF file
            extract_tables: Extract table structures
            extract_diagrams: Extract diagram metadata

        Returns:
            OCRResult with extracted data
        """
        return asyncio.run(self.extract_from_pdf_async(
            pdf_path,
            extract_tables,
            extract_diagrams
        ))


# Global instance (initialized with settings)
_deepseek_service: Optional[DeepSeekOCRService] = None


def get_deepseek_service() -> DeepSeekOCRService:
    """Get or create DeepSeek OCR service instance"""
    global _deepseek_service

    if _deepseek_service is None:
        # TODO: Load from settings
        config = DeepSeekOCRConfig(
            api_key="your-deepseek-api-key",  # Load from env
            enable_cache=True,
            max_concurrent_requests=5
        )
        _deepseek_service = DeepSeekOCRService(config)

    return _deepseek_service
