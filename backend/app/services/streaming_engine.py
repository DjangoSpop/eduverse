"""
Real-time adaptive game mechanic generation engine

Generates infinite, personalized game content via WebSocket streaming
based on real-time analysis of child behavior and progress.

Features:
- Boredom detection (idle time, repetitive actions)
- Frustration detection (error streaks, hint usage)
- Mastery detection (quick correct answers, exploration)
- Dynamic difficulty adjustment
- Cultural personalization
- Real-time encouragement
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.services.language_processor import LanguageProcessor

logger = logging.getLogger(__name__)


class StreamingGameEngine:
    """
    Generates game mechanics in real-time via WebSocket streaming

    Prevents boredom by injecting new content when:
    - Child is idle for 30+ seconds
    - Child has mastered current content (3+ correct streak)
    - 5 minutes have elapsed in same scene
    - Frustration detected (2+ errors with hints)
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.active_streams: Dict[str, Dict] = {}  # session_id -> stream_state

    async def start_mechanic_stream(
        self,
        websocket,
        child_profile: Dict,
        lesson_context: Dict
    ):
        """
        Main streaming loop for a child's session

        Args:
            websocket: FastAPI WebSocket connection
            child_profile: Child metadata (id, age, language, etc.)
            lesson_context: Current lesson data (topic, theme, objectives)
        """
        session_id = child_profile.get('child_id', 'unknown')

        # Initialize stream state
        self.active_streams[session_id] = {
            'child_profile': child_profile,
            'lesson_context': lesson_context,
            'mechanics_generated': 0,
            'boredom_score': 0.0,
            'last_mechanic_time': datetime.utcnow(),
            'behavior_history': []
        }

        logger.info(f"[StreamingEngine] Started stream for {session_id}")

        try:
            while True:
                # Receive progress updates from Unity
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=60.0  # 60 second timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"[StreamingEngine] Timeout for {session_id}")
                    break

                # Analyze child behavior
                behavior_analysis = self._analyze_behavior(session_id, data)

                # Store in history
                self.active_streams[session_id]['behavior_history'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'analysis': behavior_analysis
                })

                # Decide if new mechanic needed
                if self._should_generate_new_mechanic(session_id, behavior_analysis):
                    logger.info(f"[StreamingEngine] Generating new mechanic for {session_id}")

                    # Generate and stream new mechanic
                    full_json = ""
                    async for token in self._generate_mechanic_stream(
                        child_profile=child_profile,
                        lesson_context=lesson_context,
                        behavior=behavior_analysis
                    ):
                        full_json += token
                        # Stream token to Unity
                        await websocket.send_json({
                            'type': 'mechanic_token',
                            'token': token
                        })

                    # Send completion signal
                    await websocket.send_json({
                        'type': 'mechanic_complete',
                        'full_mechanic': full_json
                    })

                    self.active_streams[session_id]['mechanics_generated'] += 1
                    self.active_streams[session_id]['last_mechanic_time'] = datetime.utcnow()

                # Send periodic encouragement
                if behavior_analysis.get('needs_encouragement'):
                    encouragement = await self._generate_encouragement(
                        child_profile,
                        behavior_analysis
                    )
                    await websocket.send_json({
                        'type': 'encouragement',
                        'message': encouragement
                    })

        except Exception as e:
            logger.error(f"[StreamingEngine] Error for session {session_id}: {e}", exc_info=True)
        finally:
            # Cleanup
            if session_id in self.active_streams:
                del self.active_streams[session_id]
            logger.info(f"[StreamingEngine] Stream ended for {session_id}")

    def _analyze_behavior(self, session_id: str, progress_data: Dict) -> Dict:
        """
        Analyze child behavior to detect boredom, frustration, or mastery

        Signals:
        - Boredom: Long idle time (30s+), low exploration, repetitive actions
        - Frustration: Multiple errors (2+ streak), hint usage (2+), slow response
        - Mastery: Quick correct answers (<5s), high correct streak (3+), high exploration

        Args:
            session_id: Session identifier
            progress_data: Real-time progress from Unity

        Returns:
            Behavior analysis dict with flags and metrics
        """
        analysis = {
            # Raw metrics
            'idle_seconds': progress_data.get('idle_seconds', 0),
            'error_streak': progress_data.get('error_streak', 0),
            'correct_streak': progress_data.get('correct_streak', 0),
            'hints_used': progress_data.get('hints_used', 0),
            'avg_response_time': progress_data.get('avg_response_time', 0),
            'exploration_count': progress_data.get('exploration_count', 0),
            'time_in_scene': progress_data.get('time_in_scene', 0),

            # Flags
            'needs_encouragement': False,
            'boredom_detected': False,
            'frustration_detected': False,
            'mastery_detected': False,

            # Recommendations
            'recommended_mechanic_type': 'exploratory_quest'  # default
        }

        # Boredom detection
        if analysis['idle_seconds'] > 30:
            analysis['boredom_detected'] = True
            analysis['recommended_mechanic_type'] = 'exciting_chase'
            logger.info(f"[Behavior] Boredom detected for {session_id} (idle {analysis['idle_seconds']}s)")

        elif analysis['exploration_count'] < 2 and analysis['time_in_scene'] > 120:
            analysis['boredom_detected'] = True
            analysis['recommended_mechanic_type'] = 'exciting_chase'
            logger.info(f"[Behavior] Low exploration detected for {session_id}")

        # Frustration detection
        if analysis['error_streak'] >= 2 and analysis['hints_used'] >= 2:
            analysis['frustration_detected'] = True
            analysis['needs_encouragement'] = True
            analysis['recommended_mechanic_type'] = 'supportive_helper'
            logger.info(f"[Behavior] Frustration detected for {session_id}")

        elif analysis['error_streak'] >= 3:
            analysis['frustration_detected'] = True
            analysis['needs_encouragement'] = True
            analysis['recommended_mechanic_type'] = 'supportive_helper'

        # Mastery detection
        if analysis['correct_streak'] >= 3 and analysis['avg_response_time'] < 5:
            analysis['mastery_detected'] = True
            analysis['recommended_mechanic_type'] = 'advanced_puzzle'
            logger.info(f"[Behavior] Mastery detected for {session_id}")

        elif analysis['correct_streak'] >= 5:
            analysis['mastery_detected'] = True
            analysis['recommended_mechanic_type'] = 'advanced_puzzle'

        return analysis

    def _should_generate_new_mechanic(self, session_id: str, behavior: Dict) -> bool:
        """
        Decide if a new game mechanic should be generated

        Generate new content if:
        1. Child is bored (idle or low exploration)
        2. Child has mastered current content (high correct streak)
        3. 5 minutes have elapsed since last mechanic
        4. Child is frustrated and needs easier content

        Args:
            session_id: Session identifier
            behavior: Behavior analysis from _analyze_behavior

        Returns:
            True if new mechanic should be generated
        """
        stream_state = self.active_streams.get(session_id, {})

        # Check time since last mechanic
        last_mechanic_time = stream_state.get('last_mechanic_time')
        if last_mechanic_time:
            time_since_last = (datetime.utcnow() - last_mechanic_time).total_seconds()
            if time_since_last > 300:  # 5 minutes
                logger.info(f"[Streaming] 5 minutes elapsed for {session_id}, generating new mechanic")
                return True

        # Check behavior flags
        if behavior['boredom_detected']:
            logger.info(f"[Streaming] Boredom detected for {session_id}, generating exciting mechanic")
            return True

        if behavior['mastery_detected']:
            logger.info(f"[Streaming] Mastery detected for {session_id}, increasing difficulty")
            return True

        if behavior['frustration_detected']:
            logger.info(f"[Streaming] Frustration detected for {session_id}, providing support")
            return True

        return False

    async def _generate_mechanic_stream(
        self,
        child_profile: Dict,
        lesson_context: Dict,
        behavior: Dict
    ) -> AsyncGenerator[str, None]:
        """
        Stream generation of new game mechanic using Claude AI

        Returns JSON tokens that Unity can parse and execute in real-time

        Args:
            child_profile: Child metadata
            lesson_context: Lesson data
            behavior: Current behavior analysis

        Yields:
            JSON string tokens
        """
        language = child_profile.get('language', 'en')
        age = child_profile.get('age', 8)
        mechanic_type = behavior['recommended_mechanic_type']

        # Get cultural context
        cultural_context = LanguageProcessor.get_cultural_prompts(language)
        cultural_guidelines = cultural_context.get('gamification', '')

        # Build AI prompt for mechanic generation
        prompt = self._build_mechanic_prompt(
            language=language,
            age=age,
            mechanic_type=mechanic_type,
            lesson_context=lesson_context,
            cultural_guidelines=cultural_guidelines
        )

        logger.info(f"[StreamingEngine] Generating {mechanic_type} mechanic in {language}")

        # Stream from Claude AI
        try:
            async with self.client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                temperature=0.9,  # High creativity for varied content
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"[StreamingEngine] AI generation error: {e}", exc_info=True)
            # Yield fallback mechanic
            fallback = self._get_fallback_mechanic(mechanic_type, language)
            yield json.dumps(fallback, ensure_ascii=False)

    def _build_mechanic_prompt(
        self,
        language: str,
        age: int,
        mechanic_type: str,
        lesson_context: Dict,
        cultural_guidelines: str
    ) -> str:
        """
        Build AI prompt for generating game mechanic

        Args:
            language: Target language code
            age: Child's age
            mechanic_type: Type of mechanic to generate
            lesson_context: Current lesson data
            cultural_guidelines: Cultural adaptation guidelines

        Returns:
            Prompt string for Claude AI
        """
        topic = lesson_context.get('topic', 'learning')
        theme = lesson_context.get('theme', 'ocean')

        # Language-specific instructions
        lang_config = LanguageProcessor.get_language_config(language)
        lang_name = lang_config.get('name', 'English') if lang_config else 'English'

        # Mechanic type descriptions
        mechanic_descriptions = {
            'exciting_chase': f"Fast-paced chase game where child follows or catches a moving object. HIGH ENERGY.",
            'supportive_helper': f"Gentle, guided activity with step-by-step hints. EASY and SUPPORTIVE.",
            'advanced_puzzle': f"Challenging puzzle or problem-solving activity. MORE DIFFICULT.",
            'exploratory_quest': f"Open exploration with discovery elements. MODERATE difficulty."
        }

        mechanic_desc = mechanic_descriptions.get(mechanic_type, mechanic_descriptions['exploratory_quest'])

        prompt = f"""You are an expert educational game designer creating content for a {age}-year-old child learning about "{topic}".

Language: {lang_name} ({language})
Theme: {theme}
Mechanic Type: {mechanic_type}
Description: {mechanic_desc}

Cultural Guidelines:
{cultural_guidelines}

Generate a COMPLETE game mechanic as a JSON object with this EXACT structure:

{{
  "type": "{mechanic_type}",
  "name": "Short catchy name in {lang_name}",
  "description": "What the child does (in {lang_name})",
  "prefab_key": "unity_prefab_name (e.g., CollectibleCoin, ChasingAnimal, PuzzleBlock)",
  "dialogue": "AI mentor introduction in {lang_name} (encouraging, age-appropriate)",
  "learning_objective": "What this teaches about {topic}",
  "difficulty": 1-5 (1=easiest, 5=hardest),
  "estimated_duration": 60-180 (seconds),
  "reward_xp": 10-50 (based on difficulty),
  "instructions": [
    "Step 1 in {lang_name}",
    "Step 2 in {lang_name}",
    "Step 3 in {lang_name}"
  ],
  "success_feedback": "Celebration message in {lang_name}",
  "retry_hint": "Helpful hint in {lang_name}",
  "spawn_position": {{
    "x": -10 to 10,
    "y": 0 to 5,
    "z": -10 to 10
  }}
}}

CRITICAL REQUIREMENTS:
1. Use ONLY {lang_name} for all text fields
2. Make it EXCITING and AGE-APPROPRIATE for {age}-year-olds
3. Follow cultural guidelines above
4. Respond with ONLY valid JSON, no explanation text
5. Ensure it teaches about "{topic}"

Generate the mechanic NOW:"""

        return prompt

    async def _generate_encouragement(
        self,
        child_profile: Dict,
        behavior: Dict
    ) -> str:
        """
        Generate personalized encouragement message

        Args:
            child_profile: Child metadata
            behavior: Current behavior analysis

        Returns:
            Encouragement message in child's language
        """
        language = child_profile.get('language', 'en')
        name = child_profile.get('name', 'friend')

        # Pre-defined encouragements by language
        encouragements = {
            'ar': [
                f"أحسنت يا {name}! استمر في المحاولة 💪",
                f"رائع! أنت تتعلم بسرعة يا {name} ✨",
                f"ما شاء الله! محاولة ممتازة يا {name} 🌟",
                f"ممتاز! أنت تبلي بلاءً حسناً 🎯"
            ],
            'en': [
                f"Great effort, {name}! Keep going! 💪",
                f"Awesome job, {name}! You're learning so fast! ✨",
                f"Fantastic, {name}! You're doing amazing! 🌟",
                f"Nice work! You've got this! 🎯"
            ],
            'fr': [
                f"Excellent effort, {name}! Continue! 💪",
                f"Superbe, {name}! Tu apprends vite! ✨",
                f"Fantastique, {name}! C'est génial! 🌟"
            ],
            'es': [
                f"¡Gran esfuerzo, {name}! ¡Sigue así! 💪",
                f"¡Increíble, {name}! ¡Aprendes rápido! ✨",
                f"¡Fantástico, {name}! ¡Lo estás haciendo genial! 🌟"
            ],
            'zh': [
                f"很好, {name}! 继续努力! 💪",
                f"太棒了, {name}! 你学得很快! ✨",
                f"非常好, {name}! 你做得很棒! 🌟"
            ]
        }

        lang_encouragements = encouragements.get(language, encouragements['en'])

        # Select based on error streak (cycle through)
        index = behavior.get('error_streak', 0) % len(lang_encouragements)
        return lang_encouragements[index]

    def _get_fallback_mechanic(self, mechanic_type: str, language: str) -> Dict:
        """
        Get a fallback mechanic if AI generation fails

        Args:
            mechanic_type: Type of mechanic
            language: Target language

        Returns:
            Fallback mechanic dict
        """
        fallbacks = {
            'exciting_chase': {
                'type': 'exciting_chase',
                'name': 'Chase the Star!' if language == 'en' else 'اصطد النجمة!',
                'description': 'Tap the moving star!' if language == 'en' else 'اضغط على النجمة المتحركة!',
                'prefab_key': 'CollectibleStar',
                'dialogue': 'Can you catch the star?' if language == 'en' else 'هل يمكنك الإمساك بالنجمة؟',
                'learning_objective': 'Hand-eye coordination',
                'difficulty': 2,
                'estimated_duration': 60,
                'reward_xp': 20,
                'instructions': ['Tap the moving star', 'Collect 5 stars'] if language == 'en' else ['اضغط على النجمة', 'اجمع 5 نجوم'],
                'success_feedback': 'Amazing!' if language == 'en' else 'رائع!',
                'retry_hint': 'Try to predict where it will move' if language == 'en' else 'حاول توقع أين ستتحرك',
                'spawn_position': {'x': 0, 'y': 2, 'z': 5}
            }
        }

        return fallbacks.get(mechanic_type, fallbacks['exciting_chase'])

    def get_stream_stats(self, session_id: str) -> Optional[Dict]:
        """
        Get statistics for an active stream

        Args:
            session_id: Session identifier

        Returns:
            Stream statistics or None if not found
        """
        if session_id not in self.active_streams:
            return None

        stream = self.active_streams[session_id]
        return {
            'session_id': session_id,
            'mechanics_generated': stream.get('mechanics_generated', 0),
            'behavior_samples': len(stream.get('behavior_history', [])),
            'last_mechanic_time': stream.get('last_mechanic_time').isoformat() if stream.get('last_mechanic_time') else None
        }

    def get_all_active_streams(self) -> List[str]:
        """Get list of all active stream session IDs"""
        return list(self.active_streams.keys())


# Global instance
streaming_engine = StreamingGameEngine()
