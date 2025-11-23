"""
Gemini Infographic Service for Visual Content Generation

Uses Google Gemini API to generate educational infographics from text insights.
Optimized for speed with parallel processing and caching.
"""

import asyncio
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class InfographicStyle(str, Enum):
    """Infographic visual styles"""
    COLORFUL = "colorful"
    MINIMAL = "minimal"
    PLAYFUL = "playful"
    SCIENTIFIC = "scientific"
    CARTOON = "cartoon"


class InfographicElement(BaseModel):
    """Single element in an infographic"""
    type: str  # text, icon, chart, diagram, image
    content: str
    position: Dict[str, float]  # x, y, width, height (0-1 normalized)
    style: Dict = Field(default_factory=dict)
    data: Optional[Dict] = None  # For charts/diagrams


class InfographicLayout(BaseModel):
    """Complete infographic layout specification"""
    title: str
    subtitle: Optional[str] = None
    elements: List[InfographicElement]
    background_color: str = "#FFFFFF"
    theme_color: str = "#4A90E2"
    style: InfographicStyle = InfographicStyle.COLORFUL
    metadata: Dict = Field(default_factory=dict)


class GeminiInfographicConfig(BaseModel):
    """Configuration for Gemini infographic service"""
    api_key: str
    api_url: str = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    timeout: int = 30
    max_retries: int = 3
    enable_cache: bool = True
    cache_ttl_hours: int = 12
    temperature: float = 0.7
    max_tokens: int = 2000


class GeminiInfographicService:
    """
    Professional infographic generation service using Gemini API.

    Features:
    - Text-to-infographic conversion
    - Multiple visual styles
    - Parallel generation of multiple infographics
    - Result caching
    - Optimized for educational content
    """

    def __init__(self, config: GeminiInfographicConfig):
        self.config = config
        self.cache: Dict[str, Tuple[InfographicLayout, datetime]] = {}
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def _generate_cache_key(self, text: str, options: Dict) -> str:
        """Generate cache key from text and options"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        options_hash = hashlib.md5(json.dumps(options, sort_keys=True).encode()).hexdigest()
        return f"infographic_{text_hash[:16]}_{options_hash[:8]}"

    def _get_cached_result(self, cache_key: str) -> Optional[InfographicLayout]:
        """Get cached infographic if valid"""
        if not self.config.enable_cache:
            return None

        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            age = datetime.now() - timestamp

            if age < timedelta(hours=self.config.cache_ttl_hours):
                logger.info(f"Infographic cache hit: {cache_key[:24]}...")
                return result
            else:
                del self.cache[cache_key]

        return None

    def _cache_result(self, cache_key: str, result: InfographicLayout):
        """Cache infographic result"""
        if self.config.enable_cache:
            self.cache[cache_key] = (result, datetime.now())
            logger.debug(f"Cached infographic: {cache_key[:24]}...")

    async def _call_gemini_api(self, prompt: str) -> Dict:
        """
        Call Gemini API with retry logic.

        Args:
            prompt: Generation prompt

        Returns:
            API response data
        """
        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
                "topP": 0.95,
                "topK": 40
            }
        }

        url = f"{self.config.api_url}?key={self.config.api_key}"

        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                if attempt == self.config.max_retries - 1:
                    logger.error(f"Gemini API failed after {self.config.max_retries} attempts: {e}")
                    raise

                wait_time = 2 ** attempt
                logger.warning(f"Gemini API attempt {attempt + 1} failed, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)

    def _build_infographic_prompt(
        self,
        text_insights: str,
        age_range: str = "6-10",
        style: InfographicStyle = InfographicStyle.COLORFUL,
        topic: Optional[str] = None
    ) -> str:
        """
        Build optimized prompt for infographic generation.

        Args:
            text_insights: Key insights from OCR text
            age_range: Target age range
            style: Visual style
            topic: Optional topic override

        Returns:
            Formatted prompt
        """
        return f"""You are an expert educational infographic designer for children aged {age_range}.

Generate a detailed infographic layout specification based on these key insights:

{text_insights}

Topic: {topic or "Auto-detected from insights"}
Visual Style: {style.value}

Output a JSON specification with this exact structure:
{{
  "title": "Engaging title for children",
  "subtitle": "Brief subtitle (optional)",
  "elements": [
    {{
      "type": "text|icon|chart|diagram|image",
      "content": "Element content or description",
      "position": {{"x": 0.0-1.0, "y": 0.0-1.0, "width": 0.0-1.0, "height": 0.0-1.0}},
      "style": {{"fontSize": "large|medium|small", "color": "#HEX", "iconName": "star|heart|..."}},
      "data": {{}} // For charts: {{labels: [], values: []}}
    }}
  ],
  "background_color": "#HEX",
  "theme_color": "#HEX"
}}

Guidelines:
1. Use 4-6 elements maximum (children have short attention spans)
2. Prefer icons and diagrams over text
3. Use bright, engaging colors for {style.value} style
4. Make text large and readable
5. Include at least one interactive element (chart/diagram)
6. Layout should be balanced and visually appealing
7. All text should be simple (grade {age_range.split('-')[0]} reading level)

Output ONLY the JSON, no explanations."""

    async def generate_infographic_async(
        self,
        text_insights: str,
        age_range: str = "6-10",
        style: InfographicStyle = InfographicStyle.COLORFUL,
        topic: Optional[str] = None
    ) -> InfographicLayout:
        """
        Generate infographic layout from text insights.

        Args:
            text_insights: Key insights from OCR/text
            age_range: Target age range
            style: Visual style
            topic: Optional topic

        Returns:
            InfographicLayout specification
        """
        start_time = asyncio.get_event_loop().time()

        # Check cache
        options = {"age_range": age_range, "style": style.value, "topic": topic}
        cache_key = self._generate_cache_key(text_insights, options)

        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        # Build prompt
        prompt = self._build_infographic_prompt(text_insights, age_range, style, topic)

        try:
            # Call Gemini API
            response = await self._call_gemini_api(prompt)

            # Extract JSON from response
            raw_text = response["candidates"][0]["content"]["parts"][0]["text"]

            # Parse JSON (handle markdown code blocks)
            json_text = raw_text
            if "```json" in raw_text:
                json_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                json_text = raw_text.split("```")[1].split("```")[0].strip()

            infographic_data = json.loads(json_text)

            # Create InfographicLayout
            result = InfographicLayout(
                title=infographic_data["title"],
                subtitle=infographic_data.get("subtitle"),
                elements=[InfographicElement(**elem) for elem in infographic_data["elements"]],
                background_color=infographic_data.get("background_color", "#FFFFFF"),
                theme_color=infographic_data.get("theme_color", "#4A90E2"),
                style=style,
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "age_range": age_range,
                    "topic": topic,
                    "processing_time": asyncio.get_event_loop().time() - start_time
                }
            )

            # Cache result
            self._cache_result(cache_key, result)

            logger.info(f"Generated infographic '{result.title}' in {result.metadata['processing_time']:.2f}s")

            return result

        except Exception as e:
            logger.error(f"Error generating infographic: {e}")
            # Return fallback infographic
            return self._create_fallback_infographic(text_insights, age_range)

    def _create_fallback_infographic(self, text: str, age_range: str) -> InfographicLayout:
        """Create simple fallback infographic on error"""
        return InfographicLayout(
            title="Learning Summary",
            subtitle="Key Points",
            elements=[
                InfographicElement(
                    type="text",
                    content=text[:200] + "..." if len(text) > 200 else text,
                    position={"x": 0.1, "y": 0.3, "width": 0.8, "height": 0.4},
                    style={"fontSize": "large", "color": "#333333"}
                )
            ],
            metadata={
                "fallback": True,
                "age_range": age_range
            }
        )

    async def generate_multiple_infographics_async(
        self,
        text_insights: str,
        variations: int = 3,
        age_range: str = "6-10"
    ) -> List[InfographicLayout]:
        """
        Generate multiple infographic variations in parallel.

        Args:
            text_insights: Source text
            variations: Number of variations
            age_range: Target age range

        Returns:
            List of infographic layouts
        """
        styles = [InfographicStyle.COLORFUL, InfographicStyle.PLAYFUL, InfographicStyle.CARTOON]

        tasks = [
            self.generate_infographic_async(
                text_insights,
                age_range=age_range,
                style=styles[i % len(styles)]
            )
            for i in range(variations)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        infographics = [r for r in results if isinstance(r, InfographicLayout)]

        logger.info(f"Generated {len(infographics)} infographic variations")

        return infographics

    def generate_infographic(
        self,
        text_insights: str,
        age_range: str = "6-10",
        style: InfographicStyle = InfographicStyle.COLORFUL
    ) -> InfographicLayout:
        """
        Synchronous wrapper for generate_infographic_async.
        """
        return asyncio.run(self.generate_infographic_async(text_insights, age_range, style))


# Global instance
_gemini_service: Optional[GeminiInfographicService] = None


def get_gemini_service() -> GeminiInfographicService:
    """Get or create Gemini infographic service instance"""
    global _gemini_service

    if _gemini_service is None:
        config = GeminiInfographicConfig(
            api_key="your-gemini-api-key",  # Load from env
            enable_cache=True,
            temperature=0.7
        )
        _gemini_service = GeminiInfographicService(config)

    return _gemini_service
