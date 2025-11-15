"""
Pytest configuration and fixtures.

Provides common test fixtures and setup for all tests.
"""

import pytest
from fastapi.testclient import TestClient
import io
from PyPDF2 import PdfWriter

from main import app
from app.storage import memory_store


@pytest.fixture(scope="function")
def client():
    """
    FastAPI test client.

    Provides a client for testing API endpoints.
    """
    return TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def reset_storage():
    """
    Reset storage before each test.

    Ensures tests start with clean state.
    """
    memory_store.MemoryStore.clear_all_stores()
    yield
    memory_store.MemoryStore.clear_all_stores()


@pytest.fixture
def sample_pdf_bytes():
    """
    Create a simple PDF for testing.

    Returns:
        bytes: PDF file bytes
    """
    # Create a simple PDF with PyPDF2
    pdf_writer = PdfWriter()

    # Note: In a real test, you'd create actual pages with content
    # For now, we'll return a minimal valid PDF structure
    # In practice, you'd want to use a real sample PDF file

    output = io.BytesIO()
    pdf_writer.write(output)
    output.seek(0)

    return output.read()


@pytest.fixture
def sample_curriculum_data():
    """
    Sample curriculum data for testing.

    Returns:
        dict: Curriculum data
    """
    return {
        "id": "test-curriculum-123",
        "title": "Test Ocean Science",
        "filename": "ocean_science.pdf",
        "full_text": "Ocean creatures are fascinating. Dolphins use echolocation. Sharks are amazing hunters.",
        "pages": [
            {
                "page": 1,
                "text": "Ocean creatures are fascinating.",
                "char_count": 30
            }
        ],
        "metadata": {
            "page_count": 1,
            "word_count": 10,
            "char_count": 100,
            "file_size_bytes": 1024,
            "uploaded_at": "2024-01-01T00:00:00"
        },
        "status": "uploaded"
    }


@pytest.fixture
def sample_analysis_result():
    """
    Sample AI analysis result for testing.

    Returns:
        dict: Analysis result
    """
    return {
        "learning_objectives": [
            {
                "text": "Understand ocean ecosystems",
                "bloom_level": "Understand",
                "subject_area": "Science"
            }
        ],
        "key_concepts": ["ocean", "marine life", "ecosystems"],
        "recommended_age_range": "6-8",
        "difficulty_estimate": 2,
        "engagement_hooks": ["Colorful fish", "Ocean sounds"],
        "gamification_ideas": [
            {
                "concept": "ocean creatures",
                "mechanic": "collect",
                "description": "Collect different types of fish"
            }
        ],
        "narrative_theme": "ocean",
        "theme_reasoning": "Ocean theme fits marine biology content",
        "assessment_checkpoints": [
            {
                "after_concept": "dolphins",
                "question_type": "multiple_choice",
                "sample_question": "How do dolphins find food?"
            }
        ],
        "analyzed_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_learner_data():
    """
    Sample learner data for testing.

    Returns:
        dict: Learner data
    """
    return {
        "name": "Test Learner",
        "age": 7,
        "grade_level": "Grade 2"
    }
