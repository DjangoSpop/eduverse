"""
Animation Engine Service for Infographic Animation

Generates animation sequences for educational infographics.
Optimized for performance with pre-computed timelines and batching.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

from pydantic import BaseModel, Field

from app.services.gemini_infographic_service import InfographicLayout, InfographicElement

logger = logging.getLogger(__name__)


class AnimationType(str, Enum):
    """Animation effect types"""
    FADE_IN = "fadeIn"
    SLIDE_IN = "slideIn"
    SCALE_UP = "scaleUp"
    BOUNCE = "bounce"
    ROTATE = "rotate"
    PULSE = "pulse"
    DRAW = "draw"  # For diagrams/lines
    COUNT_UP = "countUp"  # For numbers
    TYPEWRITER = "typewriter"  # For text


class EasingFunction(str, Enum):
    """Easing functions for smooth animations"""
    LINEAR = "linear"
    EASE_IN = "easeIn"
    EASE_OUT = "easeOut"
    EASE_IN_OUT = "easeInOut"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


class AnimationKeyframe(BaseModel):
    """Single animation keyframe"""
    time: float  # Seconds from start
    properties: Dict[str, any]  # CSS-like properties
    easing: EasingFunction = EasingFunction.EASE_IN_OUT


class AnimationSequence(BaseModel):
    """Animation sequence for a single element"""
    element_id: int  # Index in infographic.elements
    type: AnimationType
    keyframes: List[AnimationKeyframe]
    duration: float  # Total duration in seconds
    delay: float = 0.0  # Delay before starting
    loop: bool = False
    metadata: Dict = Field(default_factory=dict)


class AnimatedInfographic(BaseModel):
    """Complete animated infographic specification"""
    infographic_id: str
    total_duration: float
    sequences: List[AnimationSequence]
    audio_cues: List[Dict] = Field(default_factory=list)  # Optional audio timings
    interaction_points: List[Dict] = Field(default_factory=list)  # Interactive moments
    metadata: Dict = Field(default_factory=dict)


class AnimationEngineConfig(BaseModel):
    """Configuration for animation engine"""
    max_duration: float = 30.0  # Max total animation duration
    default_element_duration: float = 0.8  # Default animation time per element
    stagger_delay: float = 0.15  # Delay between sequential animations
    enable_interactions: bool = True
    optimize_for_mobile: bool = True


class AnimationEngineService:
    """
    Professional animation engine for educational infographics.

    Features:
    - Intelligent animation choreography
    - Age-appropriate timing and effects
    - Parallel animation optimization
    - Mobile performance optimization
    - Interactive pause points
    """

    def __init__(self, config: AnimationEngineConfig):
        self.config = config

    def _choose_animation_for_element(
        self,
        element: InfographicElement,
        age_range: str = "6-10"
    ) -> AnimationType:
        """
        Choose appropriate animation type based on element type and age.

        Args:
            element: Infographic element
            age_range: Target age range

        Returns:
            Recommended animation type
        """
        # Younger children prefer more dynamic animations
        is_young = int(age_range.split('-')[0]) <= 7

        animation_map = {
            "text": AnimationType.TYPEWRITER if is_young else AnimationType.FADE_IN,
            "icon": AnimationType.BOUNCE if is_young else AnimationType.SCALE_UP,
            "chart": AnimationType.DRAW,
            "diagram": AnimationType.DRAW,
            "image": AnimationType.SLIDE_IN
        }

        return animation_map.get(element.type, AnimationType.FADE_IN)

    def _generate_keyframes(
        self,
        animation_type: AnimationType,
        element: InfographicElement,
        duration: float
    ) -> List[AnimationKeyframe]:
        """
        Generate keyframes for an animation type.

        Args:
            animation_type: Type of animation
            element: Target element
            duration: Animation duration

        Returns:
            List of keyframes
        """
        keyframes = []

        if animation_type == AnimationType.FADE_IN:
            keyframes = [
                AnimationKeyframe(
                    time=0.0,
                    properties={"opacity": 0},
                    easing=EasingFunction.EASE_IN
                ),
                AnimationKeyframe(
                    time=duration,
                    properties={"opacity": 1},
                    easing=EasingFunction.EASE_OUT
                )
            ]

        elif animation_type == AnimationType.SLIDE_IN:
            # Slide from left, right, top, or bottom based on position
            pos = element.position
            start_x = -1.0 if pos["x"] < 0.5 else 2.0
            keyframes = [
                AnimationKeyframe(
                    time=0.0,
                    properties={"x": start_x, "opacity": 0},
                    easing=EasingFunction.EASE_IN_OUT
                ),
                AnimationKeyframe(
                    time=duration,
                    properties={"x": pos["x"], "opacity": 1},
                    easing=EasingFunction.EASE_OUT
                )
            ]

        elif animation_type == AnimationType.SCALE_UP:
            keyframes = [
                AnimationKeyframe(
                    time=0.0,
                    properties={"scale": 0, "opacity": 0},
                    easing=EasingFunction.EASE_IN
                ),
                AnimationKeyframe(
                    time=duration * 0.7,
                    properties={"scale": 1.1, "opacity": 1},
                    easing=EasingFunction.ELASTIC
                ),
                AnimationKeyframe(
                    time=duration,
                    properties={"scale": 1.0},
                    easing=EasingFunction.EASE_OUT
                )
            ]

        elif animation_type == AnimationType.BOUNCE:
            keyframes = [
                AnimationKeyframe(time=0.0, properties={"y": -0.5, "opacity": 0}),
                AnimationKeyframe(time=duration * 0.4, properties={"y": element.position["y"], "opacity": 1}),
                AnimationKeyframe(time=duration * 0.6, properties={"y": element.position["y"] - 0.05}),
                AnimationKeyframe(time=duration * 0.8, properties={"y": element.position["y"]}),
                AnimationKeyframe(time=duration, properties={"y": element.position["y"]})
            ]

        elif animation_type == AnimationType.PULSE:
            keyframes = [
                AnimationKeyframe(time=0.0, properties={"scale": 1.0}),
                AnimationKeyframe(time=duration * 0.5, properties={"scale": 1.15}),
                AnimationKeyframe(time=duration, properties={"scale": 1.0})
            ]

        elif animation_type == AnimationType.DRAW:
            # For diagrams/charts
            keyframes = [
                AnimationKeyframe(
                    time=0.0,
                    properties={"strokeDashoffset": 1000, "opacity": 0.3},
                    easing=EasingFunction.LINEAR
                ),
                AnimationKeyframe(
                    time=duration,
                    properties={"strokeDashoffset": 0, "opacity": 1},
                    easing=EasingFunction.EASE_IN_OUT
                )
            ]

        elif animation_type == AnimationType.TYPEWRITER:
            # Text reveal
            content_length = len(element.content)
            keyframes = [
                AnimationKeyframe(
                    time=0.0,
                    properties={"characters_visible": 0}
                ),
                AnimationKeyframe(
                    time=duration,
                    properties={"characters_visible": content_length},
                    easing=EasingFunction.LINEAR
                )
            ]

        elif animation_type == AnimationType.COUNT_UP:
            # For numbers in charts
            if element.data and "value" in element.data:
                target_value = element.data["value"]
                keyframes = [
                    AnimationKeyframe(time=0.0, properties={"value": 0}),
                    AnimationKeyframe(
                        time=duration,
                        properties={"value": target_value},
                        easing=EasingFunction.EASE_OUT
                    )
                ]

        return keyframes

    async def generate_animation_async(
        self,
        infographic: InfographicLayout,
        age_range: str = "6-10",
        style_preference: str = "playful"
    ) -> AnimatedInfographic:
        """
        Generate complete animation sequence for an infographic.

        Args:
            infographic: Infographic layout
            age_range: Target age range
            style_preference: Animation style (playful, smooth, energetic)

        Returns:
            Animated infographic with all sequences
        """
        start_time = asyncio.get_event_loop().time()

        sequences = []
        current_time = 0.0

        # Determine animation strategy
        is_young = int(age_range.split('-')[0]) <= 7
        element_duration = self.config.default_element_duration * (1.2 if is_young else 1.0)
        stagger = self.config.stagger_delay

        # Special elements that should animate differently
        title_indices = []
        content_indices = []

        for i, element in enumerate(infographic.elements):
            if "title" in element.type.lower() or i == 0:
                title_indices.append(i)
            else:
                content_indices.append(i)

        # Animate title first
        for i in title_indices:
            element = infographic.elements[i]
            anim_type = AnimationType.SCALE_UP if is_young else AnimationType.FADE_IN

            sequence = AnimationSequence(
                element_id=i,
                type=anim_type,
                keyframes=self._generate_keyframes(anim_type, element, element_duration),
                duration=element_duration,
                delay=current_time,
                metadata={"priority": "high", "element_type": element.type}
            )
            sequences.append(sequence)

        current_time += element_duration + stagger * 2

        # Animate content elements with stagger
        for i in content_indices:
            element = infographic.elements[i]
            anim_type = self._choose_animation_for_element(element, age_range)

            # Charts/diagrams get more time
            duration = element_duration * (1.5 if element.type in ["chart", "diagram"] else 1.0)

            sequence = AnimationSequence(
                element_id=i,
                type=anim_type,
                keyframes=self._generate_keyframes(anim_type, element, duration),
                duration=duration,
                delay=current_time,
                metadata={"element_type": element.type}
            )
            sequences.append(sequence)

            current_time += stagger

        # Calculate total duration
        total_duration = max(
            (seq.delay + seq.duration for seq in sequences),
            default=0.0
        )

        # Add interaction points (pause moments for user engagement)
        interaction_points = []
        if self.config.enable_interactions and total_duration > 5.0:
            # Add mid-point interaction
            interaction_points.append({
                "time": total_duration * 0.5,
                "type": "tap_to_continue",
                "message": "Tap to continue!"
            })

        # Add audio cues (for future TTS integration)
        audio_cues = []
        for i, elem in enumerate(infographic.elements):
            if elem.type == "text" and len(elem.content) > 20:
                # Find corresponding sequence
                seq = next((s for s in sequences if s.element_id == i), None)
                if seq:
                    audio_cues.append({
                        "time": seq.delay,
                        "text": elem.content,
                        "duration": seq.duration
                    })

        processing_time = asyncio.get_event_loop().time() - start_time

        result = AnimatedInfographic(
            infographic_id=f"anim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            total_duration=min(total_duration, self.config.max_duration),
            sequences=sequences,
            audio_cues=audio_cues,
            interaction_points=interaction_points,
            metadata={
                "age_range": age_range,
                "style": style_preference,
                "element_count": len(infographic.elements),
                "sequence_count": len(sequences),
                "processing_time": processing_time,
                "optimized_for_mobile": self.config.optimize_for_mobile
            }
        )

        logger.info(f"Generated animation with {len(sequences)} sequences in {processing_time:.3f}s")

        return result

    def generate_animation(
        self,
        infographic: InfographicLayout,
        age_range: str = "6-10"
    ) -> AnimatedInfographic:
        """Synchronous wrapper for generate_animation_async"""
        return asyncio.run(self.generate_animation_async(infographic, age_range))


# Global instance
_animation_engine: Optional[AnimationEngineService] = None


def get_animation_engine() -> AnimationEngineService:
    """Get or create animation engine instance"""
    global _animation_engine

    if _animation_engine is None:
        config = AnimationEngineConfig(
            max_duration=30.0,
            default_element_duration=0.8,
            stagger_delay=0.15,
            enable_interactions=True,
            optimize_for_mobile=True
        )
        _animation_engine = AnimationEngineService(config)

    return _animation_engine
