"""
Scene generator service for creating Unity SceneSpecs.

Transforms AI curriculum analysis into complete, playable
3D learning experiences.
"""

from typing import Dict, List, Optional
import uuid
import logging

from app.models.scene_spec import (
    SceneSpec,
    Scene,
    GameObject,
    Challenge,
    LearningObjective,
    MentorPersona,
    DifficultyPolicy,
    Position,
    ThemeType,
    InteractionType,
    BloomLevel
)
from app.models.curriculum import AIAnalysisResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class SceneGenerator:
    """
    Service for generating interactive scene specifications.

    Converts AI-analyzed curriculum into structured SceneSpec
    objects that Unity can use to build 3D worlds.
    """

    # Theme-specific environment prefabs
    THEME_ENVIRONMENTS = {
        "ocean": ["environments/coral_reef", "environments/underwater_cave", "environments/ocean_surface"],
        "space": ["environments/space_station", "environments/asteroid_field", "environments/moon_base"],
        "jungle": ["environments/rainforest", "environments/jungle_clearing", "environments/tree_canopy"],
        "city": ["environments/city_plaza", "environments/park", "environments/museum"],
        "lab": ["environments/science_lab", "environments/experiment_room", "environments/observation_deck"],
        "fantasy": ["environments/magic_forest", "environments/castle_courtyard", "environments/enchanted_garden"]
    }

    # Theme-specific mentor personas
    THEME_MENTORS = {
        "ocean": {"name": "Captain Coral", "voice": "friendly_adult", "personality": "adventurous and curious"},
        "space": {"name": "Commander Nova", "voice": "friendly_adult", "personality": "smart and encouraging"},
        "jungle": {"name": "Explorer Jade", "voice": "friendly_adult", "personality": "brave and enthusiastic"},
        "city": {"name": "Professor Urban", "voice": "friendly_adult", "personality": "wise and patient"},
        "lab": {"name": "Dr. Discovery", "voice": "friendly_adult", "personality": "curious and methodical"},
        "fantasy": {"name": "Wizard Spark", "voice": "friendly_adult", "personality": "magical and playful"}
    }

    def __init__(self):
        """Initialize the scene generator"""
        logger.info("Scene Generator initialized")

    def generate_scene_spec(
        self,
        curriculum_id: str,
        title: str,
        analysis: Dict,
        target_duration_minutes: int = 20,
        age_range: Optional[str] = None
    ) -> SceneSpec:
        """
        Generate a complete SceneSpec from curriculum analysis.

        Args:
            curriculum_id: Source curriculum ID
            title: Lesson title
            analysis: AI analysis results
            target_duration_minutes: Desired lesson duration
            age_range: Optional age range override

        Returns:
            SceneSpec: Complete specification for Unity

        Raises:
            ValueError: If analysis is invalid
        """
        logger.info(f"Generating scene spec for: {title}")

        # Extract theme
        theme = self._normalize_theme(analysis.get("narrative_theme", "ocean"))

        # Use analysis age range or provided override
        age_range = age_range or analysis.get("recommended_age_range", "6-10")

        # Generate learning objectives
        learning_objectives = self._generate_learning_objectives(
            analysis.get("learning_objectives", [])
        )

        # Generate scenes based on concepts and gamification ideas
        scenes = self._generate_scenes(
            analysis.get("key_concepts", []),
            analysis.get("gamification_ideas", []),
            analysis.get("assessment_checkpoints", []),
            learning_objectives,
            theme,
            target_duration_minutes
        )

        # Create mentor persona
        mentor_persona = self._create_mentor_persona(theme)

        # Create difficulty policy
        difficulty_policy = DifficultyPolicy()

        # Build complete SceneSpec
        scene_spec = SceneSpec(
            lesson_id=str(uuid.uuid4()),
            curriculum_id=curriculum_id,
            title=title,
            theme=ThemeType(theme),
            age_range=age_range,
            estimated_duration_minutes=target_duration_minutes,
            learning_objectives=learning_objectives,
            scenes=scenes,
            mentor_persona=mentor_persona,
            difficulty_policy=difficulty_policy
        )

        logger.info(
            f"Scene spec generated: {len(scenes)} scenes, "
            f"{len(learning_objectives)} objectives"
        )

        return scene_spec

    def _normalize_theme(self, theme: str) -> str:
        """
        Normalize theme to valid ThemeType.

        Args:
            theme: Theme string from AI

        Returns:
            str: Valid theme name
        """
        theme = theme.lower().strip()

        # Map common variations
        theme_mapping = {
            "underwater": "ocean",
            "sea": "ocean",
            "outer space": "space",
            "cosmos": "space",
            "forest": "jungle",
            "rainforest": "jungle",
            "urban": "city",
            "town": "city",
            "laboratory": "lab",
            "science": "lab",
            "magic": "fantasy",
            "medieval": "fantasy"
        }

        theme = theme_mapping.get(theme, theme)

        # Validate against ThemeType
        valid_themes = ["ocean", "space", "jungle", "city", "lab", "fantasy"]
        if theme not in valid_themes:
            logger.warning(f"Invalid theme '{theme}', defaulting to 'ocean'")
            theme = "ocean"

        return theme

    def _generate_learning_objectives(
        self,
        objectives_data: List[Dict]
    ) -> List[LearningObjective]:
        """
        Convert AI objectives to LearningObjective models.

        Args:
            objectives_data: List of objective dicts from AI

        Returns:
            List[LearningObjective]: Validated learning objectives
        """
        objectives = []

        for obj_data in objectives_data:
            try:
                # Normalize Bloom level
                bloom_level = obj_data.get("bloom_level", "Understand")
                if bloom_level not in [level.value for level in BloomLevel]:
                    bloom_level = "Understand"

                objective = LearningObjective(
                    id=str(uuid.uuid4()),
                    text=obj_data.get("text", ""),
                    bloom_level=BloomLevel(bloom_level),
                    subject_area=obj_data.get("subject_area", "General"),
                    difficulty=3
                )
                objectives.append(objective)

            except Exception as e:
                logger.warning(f"Failed to create learning objective: {str(e)}")
                continue

        # Ensure at least one objective
        if not objectives:
            logger.warning("No valid objectives, creating default")
            objectives.append(
                LearningObjective(
                    text="Complete the learning adventure",
                    bloom_level=BloomLevel.UNDERSTAND,
                    subject_area="General",
                    difficulty=3
                )
            )

        return objectives

    def _generate_scenes(
        self,
        key_concepts: List[str],
        gamification_ideas: List[Dict],
        assessment_checkpoints: List[Dict],
        learning_objectives: List[LearningObjective],
        theme: str,
        target_duration: int
    ) -> List[Scene]:
        """
        Generate interactive scenes from curriculum concepts.

        Args:
            key_concepts: List of key concepts to cover
            gamification_ideas: Gamification mechanics from AI
            assessment_checkpoints: Assessment points from AI
            learning_objectives: Learning objectives
            theme: Visual theme
            target_duration: Target duration in minutes

        Returns:
            List[Scene]: Generated scenes
        """
        scenes = []

        # Determine number of scenes based on duration
        # Aim for 5-7 minutes per scene
        num_scenes = max(2, min(5, target_duration // 6))

        # Get environment prefabs for this theme
        env_prefabs = self.THEME_ENVIRONMENTS.get(theme, self.THEME_ENVIRONMENTS["ocean"])

        # Distribute concepts across scenes
        concepts_per_scene = max(1, len(key_concepts) // num_scenes)

        for scene_idx in range(num_scenes):
            # Select concepts for this scene
            start_idx = scene_idx * concepts_per_scene
            end_idx = start_idx + concepts_per_scene
            scene_concepts = key_concepts[start_idx:end_idx]

            # Skip empty scenes
            if not scene_concepts:
                continue

            # Create scene
            scene = self._create_scene(
                scene_idx,
                scene_concepts,
                gamification_ideas,
                assessment_checkpoints,
                learning_objectives,
                theme,
                env_prefabs[scene_idx % len(env_prefabs)]
            )

            scenes.append(scene)

        # Ensure at least 2 scenes
        if len(scenes) < 2:
            logger.warning("Generated fewer than 2 scenes, adding default scene")
            scenes.append(self._create_default_scene(theme, env_prefabs[0]))

        return scenes

    def _create_scene(
        self,
        scene_idx: int,
        concepts: List[str],
        gamification_ideas: List[Dict],
        assessments: List[Dict],
        objectives: List[LearningObjective],
        theme: str,
        env_prefab: str
    ) -> Scene:
        """Create a single scene with objects and challenges"""

        scene_name = f"Scene {scene_idx + 1}: {concepts[0] if concepts else 'Adventure'}"

        # Create narration
        narration = self._create_narration(scene_idx, concepts, theme)

        # Create game objects
        objects = self._create_game_objects(concepts, gamification_ideas, theme)

        # Create challenges
        challenges = self._create_challenges(concepts, assessments, objectives)

        # Determine exit condition
        exit_condition = "complete_all_challenges" if challenges else "explore_area"

        scene = Scene(
            id=str(uuid.uuid4()),
            name=scene_name,
            narration=narration,
            environment_prefab=env_prefab,
            objects=objects,
            challenges=challenges,
            exit_condition=exit_condition,
            estimated_duration_minutes=5 + len(challenges)
        )

        return scene

    def _create_narration(
        self,
        scene_idx: int,
        concepts: List[str],
        theme: str
    ) -> str:
        """Create engaging narration for a scene"""

        if scene_idx == 0:
            return f"Welcome to your adventure! Today we'll explore {', '.join(concepts[:2])} together. Let's get started!"
        else:
            return f"Great job! Now let's learn about {concepts[0] if concepts else 'the next topic'}. Are you ready?"

    def _create_game_objects(
        self,
        concepts: List[str],
        gamification_ideas: List[Dict],
        theme: str
    ) -> List[GameObject]:
        """Create interactive game objects for the scene"""

        objects = []

        # Add mentor NPC
        mentor_data = self.THEME_MENTORS.get(theme, self.THEME_MENTORS["ocean"])
        mentor_obj = GameObject(
            type="npc",
            name=mentor_data["name"],
            prefab_key=f"characters/{theme}_mentor",
            position=Position(x=0, y=0, z=3),
            interaction=InteractionType.VOICE,
            dialogue=[
                f"Hello! I'm {mentor_data['name']}!",
                "I'll help you learn today!",
                "Click on objects to interact with them."
            ],
            xp_reward=10
        )
        objects.append(mentor_obj)

        # Add collectibles based on concepts (2-4 per scene)
        for i, concept in enumerate(concepts[:3]):
            collectible = GameObject(
                type="collectible",
                name=f"{concept} Token",
                prefab_key=f"collectibles/{theme}_token",
                position=Position(x=2 * (i - 1), y=0.5, z=5 + i),
                interaction=InteractionType.COLLECT,
                metadata={"concept": concept},
                xp_reward=5
            )
            objects.append(collectible)

        return objects

    def _create_challenges(
        self,
        concepts: List[str],
        assessments: List[Dict],
        objectives: List[LearningObjective]
    ) -> List[Challenge]:
        """Create learning challenges for the scene"""

        challenges = []

        # Create 1-2 challenges per scene
        for i, concept in enumerate(concepts[:2]):
            # Find matching assessment if available
            assessment = next(
                (a for a in assessments if concept.lower() in a.get("after_concept", "").lower()),
                None
            )

            if assessment:
                challenge = self._create_challenge_from_assessment(
                    assessment,
                    objectives,
                    concept
                )
            else:
                challenge = self._create_default_challenge(concept, objectives)

            challenges.append(challenge)

        return challenges

    def _create_challenge_from_assessment(
        self,
        assessment: Dict,
        objectives: List[LearningObjective],
        concept: str
    ) -> Challenge:
        """Create a challenge from an assessment checkpoint"""

        question_type = assessment.get("question_type", "multiple_choice")

        # Map question type to interaction type
        interaction_map = {
            "multiple_choice": InteractionType.MULTIPLE_CHOICE,
            "voice": InteractionType.VOICE,
            "ordering": InteractionType.SEQUENCE,
            "drag_drop": InteractionType.DRAG_DROP
        }

        interaction_type = interaction_map.get(
            question_type,
            InteractionType.MULTIPLE_CHOICE
        )

        # Get related objective
        objective_id = objectives[0].id if objectives else str(uuid.uuid4())

        challenge = Challenge(
            id=str(uuid.uuid4()),
            type=interaction_type,
            prompt=assessment.get("sample_question", f"What did you learn about {concept}?"),
            correct_answer="Correct",  # Placeholder - would be filled by detailed generation
            choices=["Correct", "Incorrect", "Maybe", "Not sure"] if interaction_type == InteractionType.MULTIPLE_CHOICE else None,
            hint=f"Think about what we learned about {concept}",
            xp_reward=15,
            learning_objective_id=objective_id,
            difficulty_level=3
        )

        return challenge

    def _create_default_challenge(
        self,
        concept: str,
        objectives: List[LearningObjective]
    ) -> Challenge:
        """Create a default challenge for a concept"""

        objective_id = objectives[0].id if objectives else str(uuid.uuid4())

        challenge = Challenge(
            id=str(uuid.uuid4()),
            type=InteractionType.MULTIPLE_CHOICE,
            prompt=f"What is an important fact about {concept}?",
            correct_answer="It's an important concept!",
            choices=[
                "It's an important concept!",
                "It's not relevant",
                "It's too difficult",
                "It's optional"
            ],
            hint=f"Think about what we just learned about {concept}",
            xp_reward=10,
            learning_objective_id=objective_id,
            difficulty_level=2
        )

        return challenge

    def _create_mentor_persona(self, theme: str) -> MentorPersona:
        """Create themed mentor persona"""

        mentor_data = self.THEME_MENTORS.get(theme, self.THEME_MENTORS["ocean"])

        return MentorPersona(
            name=mentor_data["name"],
            voice=mentor_data["voice"],
            personality=mentor_data["personality"],
            avatar_prefab=f"characters/{theme}_mentor"
        )

    def _create_default_scene(self, theme: str, env_prefab: str) -> Scene:
        """Create a default fallback scene"""

        return Scene(
            id=str(uuid.uuid4()),
            name="Welcome Scene",
            narration="Welcome to your learning adventure! Let's explore together.",
            environment_prefab=env_prefab,
            objects=[],
            challenges=[],
            exit_condition="explore_area",
            estimated_duration_minutes=5
        )
