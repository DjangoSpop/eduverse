"""
PDF processing service for text extraction and validation.

Handles PDF file validation and text extraction using PyPDF2.
"""

import PyPDF2
import io
from typing import Dict, List
from fastapi import HTTPException
import logging

from app.core.logging import get_logger

logger = get_logger(__name__)


class PDFProcessor:
    """Service for processing curriculum PDFs"""

    @staticmethod
    def validate_pdf(pdf_bytes: bytes) -> bool:
        """
        Validate that the file is a readable PDF.

        Args:
            pdf_bytes: Raw PDF file bytes

        Returns:
            bool: True if valid PDF, False otherwise
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Check that we can read at least the number of pages
            _ = len(pdf_reader.pages)

            logger.info("PDF validation successful")
            return True

        except Exception as e:
            logger.warning(f"PDF validation failed: {str(e)}")
            return False

    @staticmethod
    def extract_text(pdf_bytes: bytes) -> Dict:
        """
        Extract full text content from PDF.

        Extracts text page by page and compiles metadata about
        the document including page count, word count, etc.

        Args:
            pdf_bytes: Raw PDF file bytes

        Returns:
            Dictionary containing:
                - full_text: Complete extracted text
                - pages: List of PageContent dicts
                - metadata: Document metadata

        Raises:
            HTTPException: If PDF processing fails
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            logger.info(f"Processing PDF with {len(pdf_reader.pages)} pages")

            full_text = ""
            page_texts = []

            # Extract text from each page
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()

                    # Clean up the text
                    page_text = page_text.strip()

                    page_texts.append({
                        "page": page_num + 1,
                        "text": page_text,
                        "char_count": len(page_text)
                    })

                    full_text += page_text + "\n\n"

                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                    # Continue with other pages even if one fails
                    page_texts.append({
                        "page": page_num + 1,
                        "text": "",
                        "char_count": 0
                    })

            # Calculate metadata
            word_count = len(full_text.split())
            char_count = len(full_text)

            metadata = {
                "page_count": len(pdf_reader.pages),
                "word_count": word_count,
                "char_count": char_count
            }

            logger.info(
                f"PDF processing complete: {metadata['page_count']} pages, "
                f"{metadata['word_count']} words"
            )

            return {
                "full_text": full_text,
                "pages": page_texts,
                "metadata": metadata
            }

        except PyPDF2.errors.PdfReadError as e:
            logger.error(f"PDF read error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or corrupted PDF file: {str(e)}"
            )
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process PDF: {str(e)}"
            )

    @staticmethod
    def extract_metadata(pdf_bytes: bytes) -> Dict:
        """
        Extract PDF metadata without extracting text.

        Useful for quick validation and preview.

        Args:
            pdf_bytes: Raw PDF file bytes

        Returns:
            Dictionary with metadata (page_count, etc.)

        Raises:
            HTTPException: If PDF processing fails
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            metadata = {
                "page_count": len(pdf_reader.pages)
            }

            # Try to get PDF info if available
            if pdf_reader.metadata:
                try:
                    metadata["title"] = pdf_reader.metadata.get("/Title", "")
                    metadata["author"] = pdf_reader.metadata.get("/Author", "")
                    metadata["subject"] = pdf_reader.metadata.get("/Subject", "")
                except:
                    pass

            return metadata

        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract PDF metadata: {str(e)}"
            )

    @staticmethod
    def validate_size(file_size_bytes: int, max_size_mb: int = 10) -> bool:
        """
        Validate that PDF file size is within limits.

        Args:
            file_size_bytes: File size in bytes
            max_size_mb: Maximum allowed size in megabytes

        Returns:
            bool: True if size is acceptable

        Raises:
            HTTPException: If file is too large
        """
        max_bytes = max_size_mb * 1024 * 1024

        if file_size_bytes > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {max_size_mb}MB"
            )

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize uploaded filename for safe storage.

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename
        """
        # Remove path components
        filename = filename.split("/")[-1].split("\\")[-1]

        # Remove dangerous characters
        dangerous_chars = ['..', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            filename = filename.replace(char, '')

        # Limit length
        if len(filename) > 255:
            filename = filename[:255]

        return filename
