"""
Real-time Dynamic Game Mechanic Generation Engine

Generates infinite adaptive game mechanics in real-time based on:
- Child behavior and engagement levels
- Learning progress and comprehension
- Cultural context and language
- Boredom detection and excitement injection

Supports streaming over WebSocket for immediate gameplay updates.
"""
import logging
import asyncio
import json
import uuid
from typing import Dict, List, AsyncGenerator, Optional
from datetime import datetime
from enum import Enum

from app.services.language_processor import LanguageProcessor

logger = logging.getLogger(__name__)


class MechanicType(str, Enum):
    """Types of game mechanics that can be dynamically generated"""
    CHASE = "chase"  # Character must chase/catch moving objects
    COLLECT = "collect"  # Gather items scattered in scene
    PUZZLE = "puzzle"  # Solve logic/matching puzzles
    BUILD = "build"  # Construct objects from parts
    EXPLORE = "explore"  # Navigate to discover areas
    QUIZ = "quiz"  # Answer questions in fun format
    SEQUENCE = "sequence"  # Remember and repeat patterns
    SORT = "sort"  # Categorize and organize items


class DifficultyLevel(str, Enum):
    """Adaptive difficulty levels"""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class EngagementLevel(str, Enum):
    """Child engagement states detected from behavior"""
    BORED = "bored"  # Low interaction, need excitement
    FRUSTRATED = "frustrated"  # High errors, need easier content
    ENGAGED = "engaged"  # Optimal learning state
    MASTERED = "mastered"  # Too easy, need challenge


class StreamingGameEngine:
    """
    Generates dynamic game mechanics in real-time based on child behavior

    This engine analyzes child engagement and learning progress to create
    an infinite stream of culturally-appropriate, adaptive game content.
    """

    def __init__(self):
        """Initialize the streaming game engine"""
        self.active_sessions: Dict[str, Dict] = {}
        self.mechanic_history: Dict[str, List[Dict]] = {}

    def create_session(
        self,
        learner_id: str,
        curriculum_id: str,
        language: str = 'en',
        initial_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    ) -> str:
        """
        Create a new streaming game session

        Args:
            learner_id: ID of the child learner
            curriculum_id: Curriculum being studied
            language: Language code
            initial_difficulty: Starting difficulty level

        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())

        self.active_sessions[session_id] = {
            'session_id': session_id,
            'learner_id': learner_id,
            'curriculum_id': curriculum_id,
            'language': language,
            'cultural_context': LanguageProcessor.get_language_config(language).get('cultural_context', 'universal'),
            'current_difficulty': initial_difficulty,
            'engagement_level': EngagementLevel.ENGAGED,
            'mechanics_generated': 0,
            'success_rate': 0.0,
            'average_time_per_mechanic': 0.0,
            'consecutive_successes': 0,
            'consecutive_failures': 0,
            'started_at': datetime.utcnow().isoformat(),
            'last_mechanic_at': None
        }

        self.mechanic_history[session_id] = []

        logger.info(f"Created streaming session {session_id} for learner {learner_id}")
        return session_id

    async def stream_mechanics(
        self,
        session_id: str,
        learning_objectives: List[str],
        context: Optional[Dict] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream infinite game mechanics for a session

        This is the main streaming endpoint that yields mechanics indefinitely
        until the session is terminated by the client.

        Args:
            session_id: Active session ID
            learning_objectives: List of learning goals
            context: Additional context (theme, scene type, etc.)

        Yields:
            Dict: Mechanic specification ready for Unity instantiation
        """
        if session_id not in self.active_sessions:
            logger.error(f"Session {session_id} not found")
            return

        session = self.active_sessions[session_id]
        logger.info(f"Starting mechanic stream for session {session_id}")

        context = context or {}
        mechanic_count = 0

        while True:
            try:
                # Generate next mechanic based on current state
                mechanic = await self._generate_mechanic_stream(
                    session=session,
                    learning_objectives=learning_objectives,
                    context=context,
                    mechanic_index=mechanic_count
                )

                # Track generation
                session['mechanics_generated'] += 1
                session['last_mechanic_at'] = datetime.utcnow().isoformat()
                self.mechanic_history[session_id].append(mechanic)

                mechanic_count += 1

                yield mechanic

                # Small delay to prevent overwhelming client
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error generating mechanic for session {session_id}: {e}", exc_info=True)
                # Yield error mechanic
                yield {
                    'type': 'error',
                    'message': 'Failed to generate mechanic',
                    'session_id': session_id
                }
                await asyncio.sleep(2)  # Wait before retry

    async def _generate_mechanic_stream(
        self,
        session: Dict,
        learning_objectives: List[str],
        context: Dict,
        mechanic_index: int
    ) -> Dict:
        """
        Generate a single mechanic specification

        This is where the magic happens - analyzing engagement, selecting
        appropriate mechanics, and generating culturally-aware content.

        Args:
            session: Session state
            learning_objectives: Learning goals
            context: Additional context
            mechanic_index: Index of this mechanic in stream

        Returns:
            Complete mechanic specification
        """
        # Detect engagement level and adjust difficulty
        engagement = session['engagement_level']
        current_difficulty = session['current_difficulty']
        language = session['language']
        cultural_context = session['cultural_context']

        # Select mechanic type based on engagement
        mechanic_type = self._select_mechanic_type(
            engagement=engagement,
            previous_mechanics=self.mechanic_history[session['session_id']][-5:],  # Last 5
            learning_objectives=learning_objectives
        )

        # Get cultural prompts for content generation
        cultural_prompts = LanguageProcessor.get_cultural_prompts(language)

        # Build mechanic specification
        mechanic = {
            'mechanic_id': str(uuid.uuid4()),
            'session_id': session['session_id'],
            'type': mechanic_type,
            'index': mechanic_index,
            'difficulty': current_difficulty,
            'language': language,
            'cultural_context': cultural_context,
            'generated_at': datetime.utcnow().isoformat(),

            # Core mechanic configuration
            'title': self._generate_title(mechanic_type, language, learning_objectives),
            'instruction': self._generate_instruction(mechanic_type, language, cultural_prompts),
            'learning_objective': learning_objectives[mechanic_index % len(learning_objectives)],

            # Mechanic-specific parameters
            'parameters': self._generate_mechanic_parameters(
                mechanic_type=mechanic_type,
                difficulty=current_difficulty,
                language=language,
                cultural_context=cultural_context
            ),

            # Unity instantiation data
            'spawn_config': self._generate_spawn_config(mechanic_type, current_difficulty),

            # Success criteria
            'success_criteria': self._generate_success_criteria(mechanic_type, current_difficulty),

            # Rewards and feedback
            'rewards': self._generate_rewards(current_difficulty),
            'feedback': self._generate_feedback_messages(language, cultural_prompts),

            # Analytics tracking
            'expected_duration_seconds': self._estimate_duration(mechanic_type, current_difficulty),
            'metadata': {
                'engagement_level': engagement,
                'success_rate': session['success_rate'],
                'consecutive_successes': session['consecutive_successes']
            }
        }

        logger.info(f"Generated {mechanic_type} mechanic for session {session['session_id']}")

        return mechanic

    def _select_mechanic_type(
        self,
        engagement: EngagementLevel,
        previous_mechanics: List[Dict],
        learning_objectives: List[str]
    ) -> MechanicType:
        """
        Intelligently select next mechanic type based on engagement

        Uses boredom detection and variety algorithms to keep children engaged.
        """
        # Avoid repeating same mechanic too often
        if previous_mechanics:
            recent_types = [m['type'] for m in previous_mechanics]

            # If last 3 were same type, force variety
            if len(set(recent_types[-3:])) == 1:
                excluded_type = recent_types[-1]
                available_types = [t for t in MechanicType if t != excluded_type]
            else:
                available_types = list(MechanicType)
        else:
            available_types = list(MechanicType)

        # Select based on engagement level
        if engagement == EngagementLevel.BORED:
            # Inject exciting mechanics: chase, collect (fast-paced)
            exciting_types = [MechanicType.CHASE, MechanicType.COLLECT, MechanicType.EXPLORE]
            candidates = [t for t in exciting_types if t in available_types]
            return candidates[0] if candidates else available_types[0]

        elif engagement == EngagementLevel.FRUSTRATED:
            # Provide easier, more intuitive mechanics
            easy_types = [MechanicType.COLLECT, MechanicType.QUIZ, MechanicType.SORT]
            candidates = [t for t in easy_types if t in available_types]
            return candidates[0] if candidates else available_types[0]

        elif engagement == EngagementLevel.MASTERED:
            # Increase challenge: puzzle, build, sequence (cognitive)
            challenging_types = [MechanicType.PUZZLE, MechanicType.BUILD, MechanicType.SEQUENCE]
            candidates = [t for t in challenging_types if t in available_types]
            return candidates[0] if candidates else available_types[0]

        else:  # ENGAGED - optimal state
            # Balanced variety
            import random
            return random.choice(available_types)

    def _generate_title(
        self,
        mechanic_type: MechanicType,
        language: str,
        learning_objectives: List[str]
    ) -> str:
        """Generate culturally-appropriate title for mechanic"""

        # Title templates by language
        titles = {
            'ar': {
                MechanicType.CHASE: 'اِلْحَق وامْسِك',
                MechanicType.COLLECT: 'اِجْمَع الكنوز',
                MechanicType.PUZZLE: 'حَلّ اللُغز',
                MechanicType.BUILD: 'ابْنِ المشروع',
                MechanicType.EXPLORE: 'اِكْتَشِف المكان',
                MechanicType.QUIZ: 'أَجِب على السؤال',
                MechanicType.SEQUENCE: 'تَذَكَّر التسلسل',
                MechanicType.SORT: 'رَتِّب العناصر'
            },
            'en': {
                MechanicType.CHASE: 'Catch the Items',
                MechanicType.COLLECT: 'Collect the Treasures',
                MechanicType.PUZZLE: 'Solve the Puzzle',
                MechanicType.BUILD: 'Build the Project',
                MechanicType.EXPLORE: 'Explore the Area',
                MechanicType.QUIZ: 'Answer the Question',
                MechanicType.SEQUENCE: 'Remember the Pattern',
                MechanicType.SORT: 'Sort the Items'
            }
        }

        lang_titles = titles.get(language, titles['en'])
        return lang_titles.get(mechanic_type, f'{mechanic_type} Challenge')

    def _generate_instruction(
        self,
        mechanic_type: MechanicType,
        language: str,
        cultural_prompts: Dict
    ) -> str:
        """Generate instruction text with cultural sensitivity"""

        instructions = {
            'ar': {
                MechanicType.CHASE: 'الْحَق الأشياء المتحركة واجمعها قبل أن تختفي!',
                MechanicType.COLLECT: 'اجمع جميع العناصر المطلوبة من المكان',
                MechanicType.PUZZLE: 'ضع القطع في الأماكن الصحيحة لحل اللغز',
                MechanicType.BUILD: 'اِستخدم المواد لبناء الشيء الموجود في الصورة',
                MechanicType.EXPLORE: 'اِستكشف المكان واعثر على الكنوز المخفية',
                MechanicType.QUIZ: 'اِختر الإجابة الصحيحة من الخيارات',
                MechanicType.SEQUENCE: 'تابع التسلسل وكرره بنفس الترتيب',
                MechanicType.SORT: 'رتّب العناصر في المجموعات الصحيحة'
            },
            'en': {
                MechanicType.CHASE: 'Chase and catch the moving items before they disappear!',
                MechanicType.COLLECT: 'Collect all the required items from the scene',
                MechanicType.PUZZLE: 'Place the pieces in the correct positions to solve the puzzle',
                MechanicType.BUILD: 'Use the materials to build the object shown in the picture',
                MechanicType.EXPLORE: 'Explore the area and find the hidden treasures',
                MechanicType.QUIZ: 'Choose the correct answer from the options',
                MechanicType.SEQUENCE: 'Watch the sequence and repeat it in the same order',
                MechanicType.SORT: 'Sort the items into the correct groups'
            }
        }

        lang_instructions = instructions.get(language, instructions['en'])
        return lang_instructions.get(mechanic_type, f'Complete the {mechanic_type} challenge')

    def _generate_mechanic_parameters(
        self,
        mechanic_type: MechanicType,
        difficulty: DifficultyLevel,
        language: str,
        cultural_context: str
    ) -> Dict:
        """
        Generate mechanic-specific parameters tuned to difficulty

        This determines how the mechanic actually works (speed, count, time, etc.)
        """
        # Difficulty multipliers
        difficulty_config = {
            DifficultyLevel.VERY_EASY: {'speed': 0.5, 'count': 3, 'time': 60},
            DifficultyLevel.EASY: {'speed': 0.7, 'count': 5, 'time': 45},
            DifficultyLevel.MEDIUM: {'speed': 1.0, 'count': 7, 'time': 30},
            DifficultyLevel.HARD: {'speed': 1.3, 'count': 10, 'time': 25},
            DifficultyLevel.VERY_HARD: {'speed': 1.5, 'count': 12, 'time': 20}
        }

        config = difficulty_config[difficulty]

        if mechanic_type == MechanicType.CHASE:
            return {
                'target_count': config['count'],
                'target_speed': config['speed'] * 3.0,  # Units per second
                'spawn_interval': 2.0 / config['speed'],  # Faster spawning at higher difficulty
                'max_active_targets': min(config['count'], 5),
                'target_lifetime': 8.0 / config['speed'],  # Disappear faster at higher difficulty
                'catch_radius': 2.0 / config['speed']  # Smaller radius = harder
            }

        elif mechanic_type == MechanicType.COLLECT:
            return {
                'item_count': config['count'],
                'scatter_radius': 15.0 * config['speed'],  # Wider area at higher difficulty
                'item_size': 1.0 / config['speed'],  # Smaller items = harder
                'time_limit': config['time'],
                'distractor_count': int(config['count'] * 0.5)  # Wrong items to avoid
            }

        elif mechanic_type == MechanicType.PUZZLE:
            return {
                'piece_count': config['count'],
                'grid_size': int(2 + config['count'] / 3),  # 2x2 to 5x5
                'rotation_allowed': difficulty in [DifficultyLevel.HARD, DifficultyLevel.VERY_HARD],
                'snap_tolerance': 1.0 / config['speed'],  # Tighter snap = harder
                'show_preview': difficulty in [DifficultyLevel.VERY_EASY, DifficultyLevel.EASY],
                'time_limit': config['time']
            }

        elif mechanic_type == MechanicType.BUILD:
            return {
                'part_count': config['count'],
                'construction_steps': int(config['count'] / 2),
                'show_blueprint': difficulty in [DifficultyLevel.VERY_EASY, DifficultyLevel.EASY],
                'snap_assist': difficulty != DifficultyLevel.VERY_HARD,
                'time_limit': config['time'],
                'allow_mistakes': 3 - int(config['speed'])
            }

        elif mechanic_type == MechanicType.EXPLORE:
            return {
                'area_size': 20.0 * config['speed'],
                'hidden_item_count': config['count'],
                'reveal_radius': 3.0 / config['speed'],
                'time_limit': config['time'],
                'obstacles': int(config['count'] * 0.3),
                'show_minimap': difficulty in [DifficultyLevel.VERY_EASY, DifficultyLevel.EASY]
            }

        elif mechanic_type == MechanicType.QUIZ:
            return {
                'question_count': 1,
                'option_count': 2 + int(config['speed']),  # More options = harder
                'time_per_question': config['time'] / max(1, config['count']),
                'show_hints': difficulty == DifficultyLevel.VERY_EASY,
                'allow_retries': difficulty in [DifficultyLevel.VERY_EASY, DifficultyLevel.EASY]
            }

        elif mechanic_type == MechanicType.SEQUENCE:
            return {
                'sequence_length': config['count'],
                'display_speed': 1.0 / config['speed'],  # Faster display = harder to remember
                'repeat_count': 1,
                'visual_and_audio': True,
                'time_to_reproduce': config['time']
            }

        elif mechanic_type == MechanicType.SORT:
            return {
                'item_count': config['count'],
                'category_count': 2 + int(config['speed'] / 0.5),  # 2-5 categories
                'time_limit': config['time'],
                'show_category_labels': difficulty != DifficultyLevel.VERY_HARD,
                'allow_mistakes': 3 - int(config['speed'])
            }

        else:
            return {'difficulty': difficulty}

    def _generate_spawn_config(self, mechanic_type: MechanicType, difficulty: DifficultyLevel) -> Dict:
        """
        Generate Unity spawn configuration (positions, prefabs, animations)
        """
        return {
            'spawn_immediately': True,
            'spawn_animation': 'FadeIn',
            'spawn_duration': 0.5,
            'spawn_positions': 'procedural',  # Unity will generate based on type
            'parent_transform': 'MechanicContainer',
            'z_layer': 0.0
        }

    def _generate_success_criteria(self, mechanic_type: MechanicType, difficulty: DifficultyLevel) -> Dict:
        """Define what constitutes success for this mechanic"""

        base_criteria = {
            'type': 'completion',
            'min_score': 0.7 if difficulty in [DifficultyLevel.HARD, DifficultyLevel.VERY_HARD] else 0.6,
            'allow_hints': difficulty in [DifficultyLevel.VERY_EASY, DifficultyLevel.EASY],
            'max_attempts': 3 if difficulty == DifficultyLevel.VERY_EASY else 1
        }

        if mechanic_type in [MechanicType.CHASE, MechanicType.COLLECT]:
            base_criteria['min_items_collected'] = '100%' if difficulty == DifficultyLevel.VERY_HARD else '80%'

        elif mechanic_type == MechanicType.PUZZLE:
            base_criteria['min_pieces_correct'] = '100%' if difficulty == DifficultyLevel.VERY_HARD else '90%'

        return base_criteria

    def _generate_rewards(self, difficulty: DifficultyLevel) -> Dict:
        """Generate XP and rewards based on difficulty"""

        xp_values = {
            DifficultyLevel.VERY_EASY: 10,
            DifficultyLevel.EASY: 25,
            DifficultyLevel.MEDIUM: 50,
            DifficultyLevel.HARD: 100,
            DifficultyLevel.VERY_HARD: 200
        }

        return {
            'xp': xp_values[difficulty],
            'stars': 1 if difficulty in [DifficultyLevel.VERY_EASY, DifficultyLevel.EASY] else 3,
            'coins': xp_values[difficulty] // 10,
            'badge': difficulty in [DifficultyLevel.HARD, DifficultyLevel.VERY_HARD]
        }

    def _generate_feedback_messages(self, language: str, cultural_prompts: Dict) -> Dict:
        """
        Generate culturally-appropriate feedback messages

        Uses cultural prompts to ensure messages are appropriate
        """
        if language == 'ar':
            return {
                'success': ['أحسنت!', 'ممتاز!', 'ما شاء الله!', 'رائع!'],
                'failure': ['حاول مرة أخرى', 'يمكنك فعلها!', 'لا تستسلم', 'تعلم من الخطأ'],
                'hint': ['جرّب هذا', 'فكّر في...', 'تذكّر أن...'],
                'encouragement': ['أنت قريب جداً!', 'تقدّم رائع!', 'استمر!']
            }
        else:  # English and others
            return {
                'success': ['Great job!', 'Excellent!', 'Well done!', 'Awesome!'],
                'failure': ['Try again!', 'You can do it!', 'Learn from this', 'Almost there!'],
                'hint': ['Try this', 'Think about...', 'Remember that...'],
                'encouragement': ['You\'re so close!', 'Great progress!', 'Keep going!']
            }

    def _estimate_duration(self, mechanic_type: MechanicType, difficulty: DifficultyLevel) -> int:
        """Estimate expected completion time in seconds"""

        base_times = {
            MechanicType.CHASE: 30,
            MechanicType.COLLECT: 45,
            MechanicType.PUZZLE: 60,
            MechanicType.BUILD: 90,
            MechanicType.EXPLORE: 120,
            MechanicType.QUIZ: 20,
            MechanicType.SEQUENCE: 40,
            MechanicType.SORT: 50
        }

        difficulty_multipliers = {
            DifficultyLevel.VERY_EASY: 0.7,
            DifficultyLevel.EASY: 0.85,
            DifficultyLevel.MEDIUM: 1.0,
            DifficultyLevel.HARD: 1.2,
            DifficultyLevel.VERY_HARD: 1.5
        }

        return int(base_times.get(mechanic_type, 60) * difficulty_multipliers[difficulty])

    def update_session_performance(
        self,
        session_id: str,
        mechanic_id: str,
        success: bool,
        time_taken: float,
        errors: int = 0
    ):
        """
        Update session with performance data to adapt difficulty and engagement detection

        Args:
            session_id: Session ID
            mechanic_id: Completed mechanic ID
            success: Whether mechanic was completed successfully
            time_taken: Time in seconds
            errors: Number of errors made
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found for update")
            return

        session = self.active_sessions[session_id]

        # Update success tracking
        if success:
            session['consecutive_successes'] += 1
            session['consecutive_failures'] = 0
        else:
            session['consecutive_failures'] += 1
            session['consecutive_successes'] = 0

        # Update success rate (exponential moving average)
        alpha = 0.2
        session['success_rate'] = alpha * (1.0 if success else 0.0) + (1 - alpha) * session['success_rate']

        # Update average time
        session['average_time_per_mechanic'] = (
            alpha * time_taken + (1 - alpha) * session['average_time_per_mechanic']
        )

        # Detect engagement level
        session['engagement_level'] = self._detect_engagement(
            success_rate=session['success_rate'],
            consecutive_successes=session['consecutive_successes'],
            consecutive_failures=session['consecutive_failures'],
            average_time=session['average_time_per_mechanic'],
            errors=errors
        )

        # Adapt difficulty
        session['current_difficulty'] = self._adapt_difficulty(
            current_difficulty=session['current_difficulty'],
            engagement=session['engagement_level'],
            success_rate=session['success_rate']
        )

        logger.info(
            f"Session {session_id} updated: "
            f"success_rate={session['success_rate']:.2f}, "
            f"engagement={session['engagement_level']}, "
            f"difficulty={session['current_difficulty']}"
        )

    def _detect_engagement(
        self,
        success_rate: float,
        consecutive_successes: int,
        consecutive_failures: int,
        average_time: float,
        errors: int
    ) -> EngagementLevel:
        """
        Detect child's engagement level from behavior patterns

        This is the boredom detection algorithm
        """
        # Frustrated: High failure rate or many errors
        if consecutive_failures >= 3 or success_rate < 0.4 or errors >= 5:
            return EngagementLevel.FRUSTRATED

        # Mastered: Very high success with fast completion
        if consecutive_successes >= 5 and success_rate > 0.9 and average_time < 20:
            return EngagementLevel.MASTERED

        # Bored: Success but taking too long (distracted)
        if success_rate > 0.7 and average_time > 90:
            return EngagementLevel.BORED

        # Engaged: Optimal state
        return EngagementLevel.ENGAGED

    def _adapt_difficulty(
        self,
        current_difficulty: DifficultyLevel,
        engagement: EngagementLevel,
        success_rate: float
    ) -> DifficultyLevel:
        """
        Adapt difficulty based on engagement and performance

        Implements adaptive difficulty algorithm
        """
        difficulties = [
            DifficultyLevel.VERY_EASY,
            DifficultyLevel.EASY,
            DifficultyLevel.MEDIUM,
            DifficultyLevel.HARD,
            DifficultyLevel.VERY_HARD
        ]

        current_index = difficulties.index(current_difficulty)

        # Adjust based on engagement
        if engagement == EngagementLevel.FRUSTRATED:
            # Decrease difficulty
            new_index = max(0, current_index - 1)
        elif engagement == EngagementLevel.MASTERED:
            # Increase difficulty
            new_index = min(len(difficulties) - 1, current_index + 1)
        elif engagement == EngagementLevel.BORED:
            # Slight increase to re-engage
            new_index = min(len(difficulties) - 1, current_index + 1)
        else:
            # Maintain current difficulty
            new_index = current_index

        return difficulties[new_index]

    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """Get current session statistics"""
        return self.active_sessions.get(session_id)

    def terminate_session(self, session_id: str) -> Dict:
        """
        Terminate a streaming session and return final statistics
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found for termination")
            return {}

        session = self.active_sessions[session_id]
        mechanics = self.mechanic_history.get(session_id, [])

        final_stats = {
            'session_id': session_id,
            'learner_id': session['learner_id'],
            'total_mechanics': session['mechanics_generated'],
            'success_rate': session['success_rate'],
            'final_difficulty': session['current_difficulty'],
            'final_engagement': session['engagement_level'],
            'duration_seconds': (
                datetime.utcnow() - datetime.fromisoformat(session['started_at'])
            ).total_seconds(),
            'mechanics_breakdown': {
                mechanic_type: len([m for m in mechanics if m['type'] == mechanic_type])
                for mechanic_type in MechanicType
            }
        }

        # Clean up
        del self.active_sessions[session_id]
        del self.mechanic_history[session_id]

        logger.info(f"Session {session_id} terminated with {final_stats['total_mechanics']} mechanics")

        return final_stats
