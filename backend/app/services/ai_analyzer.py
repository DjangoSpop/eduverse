"""
AI analyzer service using Claude for curriculum analysis.

Uses Anthropic's Claude to perform deep semantic analysis of
curriculum content and extract learning insights.
"""

import anthropic
import json
from typing import Dict, Optional
from fastapi import HTTPException
import logging

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIAnalyzer:
    """
    Service for AI-powered curriculum analysis.

    Uses Claude to analyze curriculum content and extract:
    - Learning objectives (aligned with Bloom's taxonomy)
    - Key concepts
    - Difficulty level
    - Engagement opportunities
    - Gamification ideas
    - Narrative themes
    """

    def __init__(self):
        """Initialize the AI analyzer with Claude client"""
        try:
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            logger.info("AI Analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Analyzer: {str(e)}")
            raise

    async def analyze_curriculum(
        self,
        text: str,
        title: str,
        age_range: Optional[str] = None
    ) -> Dict:
        """
        Perform comprehensive curriculum analysis.

        Analyzes curriculum content to extract structured learning insights
        that will be used to generate interactive lessons.

        Args:
            text: Curriculum text content
            title: Curriculum title
            age_range: Optional target age range

        Returns:
            Dictionary containing analysis results with keys:
                - learning_objectives
                - key_concepts
                - recommended_age_range
                - difficulty_estimate
                - engagement_hooks
                - gamification_ideas
                - narrative_theme
                - theme_reasoning
                - assessment_checkpoints

        Raises:
            HTTPException: If analysis fails
        """
        logger.info(f"Starting AI analysis of curriculum: {title}")

        # Truncate text if too long (Claude has token limits)
        max_chars = 8000
        text_to_analyze = text[:max_chars]
        if len(text) > max_chars:
            logger.warning(f"Text truncated from {len(text)} to {max_chars} characters")

        # Build the analysis prompt
        prompt = self._build_analysis_prompt(text_to_analyze, title, age_range)

        try:
            # Call Claude API
            message = self.client.messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.anthropic_max_tokens,
                temperature=settings.ai_temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract response text
            response_text = message.content[0].text
            logger.debug(f"Received AI response: {response_text[:200]}...")

            # Parse JSON from response
            analysis = self._extract_json_from_response(response_text)

            # Validate analysis structure
            self._validate_analysis(analysis)

            logger.info(f"AI analysis completed successfully for: {title}")
            return analysis

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"AI service error: {str(e)}"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="AI returned invalid response format"
            )
        except Exception as e:
            logger.error(f"Unexpected error during AI analysis: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}"
            )

    def _build_analysis_prompt(
        self,
        text: str,
        title: str,
        age_range: Optional[str]
    ) -> str:
        """
        Build the analysis prompt for Claude.

        Args:
            text: Curriculum text
            title: Curriculum title
            age_range: Optional age range

        Returns:
            str: Complete prompt
        """
        age_context = f"\nTarget Age Range: {age_range}" if age_range else ""

        prompt = f"""You are an expert educational designer and curriculum analyst specializing in children's education.

Analyze this curriculum document and extract structured learning insights that will be used to create an interactive 3D learning game for children.

Curriculum Title: {title}{age_context}

Content:
{text}

Provide comprehensive analysis in valid JSON format with these keys:

{{
  "learning_objectives": [
    {{
      "text": "Specific measurable learning objective",
      "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create",
      "subject_area": "Math|Science|Language Arts|Social Studies|Art|etc"
    }}
  ],
  "key_concepts": ["concept1", "concept2", "concept3"],
  "recommended_age_range": "6-8|9-12|13-15",
  "difficulty_estimate": 1-5,
  "engagement_hooks": [
    "Elements that would interest and engage children of this age",
    "Interactive opportunities",
    "Fun facts or surprising information"
  ],
  "gamification_ideas": [
    {{
      "concept": "specific curriculum topic",
      "mechanic": "collect|build|explore|puzzle|sequence|drag_drop",
      "description": "How to turn this concept into a game mechanic"
    }}
  ],
  "narrative_theme": "ocean|space|jungle|city|lab|fantasy",
  "theme_reasoning": "Why this theme best fits the curriculum content and target age",
  "assessment_checkpoints": [
    {{
      "after_concept": "concept name to assess",
      "question_type": "multiple_choice|voice|ordering|drag_drop",
      "sample_question": "Example assessment question"
    }}
  ]
}}

Important guidelines:
1. Create 3-5 learning objectives that are specific and measurable
2. Identify 5-10 key concepts
3. Suggest a theme that will excite children and fit the content
4. Provide 3-5 concrete gamification ideas
5. Include 3-5 assessment checkpoints
6. Be creative but pedagogically sound

Respond with ONLY the JSON object, no additional text before or after."""

        return prompt

    def _extract_json_from_response(self, response_text: str) -> Dict:
        """
        Extract and parse JSON from Claude's response.

        Claude sometimes includes explanatory text before/after JSON,
        so we need to extract just the JSON portion.

        Args:
            response_text: Raw response from Claude

        Returns:
            Dict: Parsed JSON object

        Raises:
            json.JSONDecodeError: If JSON cannot be parsed
        """
        # Try to find JSON object in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            # No JSON found, try parsing entire response
            return json.loads(response_text)

        json_str = response_text[json_start:json_end]
        return json.loads(json_str)

    def _validate_analysis(self, analysis: Dict) -> None:
        """
        Validate that analysis contains required fields.

        Args:
            analysis: Analysis dictionary to validate

        Raises:
            HTTPException: If validation fails
        """
        required_fields = [
            "learning_objectives",
            "key_concepts",
            "recommended_age_range",
            "difficulty_estimate",
            "engagement_hooks",
            "gamification_ideas",
            "narrative_theme",
            "theme_reasoning",
            "assessment_checkpoints"
        ]

        missing_fields = [
            field for field in required_fields
            if field not in analysis
        ]

        if missing_fields:
            logger.error(f"Analysis missing required fields: {missing_fields}")
            raise HTTPException(
                status_code=500,
                detail=f"Incomplete analysis: missing {', '.join(missing_fields)}"
            )

        # Validate learning objectives structure
        if not isinstance(analysis["learning_objectives"], list):
            raise HTTPException(
                status_code=500,
                detail="learning_objectives must be a list"
            )

        if len(analysis["learning_objectives"]) == 0:
            raise HTTPException(
                status_code=500,
                detail="At least one learning objective is required"
            )

        # Validate difficulty is in range
        difficulty = analysis.get("difficulty_estimate", 0)
        if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
            logger.warning(f"Invalid difficulty {difficulty}, defaulting to 3")
            analysis["difficulty_estimate"] = 3

        logger.debug("Analysis validation passed")
