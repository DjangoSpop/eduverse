"""
Pilot Testing Analytics Service

Collects and analyzes data from pilot program with 20 students
to measure learning effectiveness and system performance.

Key Metrics:
- Learning gain (pre/post test comparison)
- Engagement levels and session duration
- System performance (FPS, load times, errors)
- User satisfaction (NPS scores)
- Cultural appropriateness validation
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import statistics
import csv
import io

logger = logging.getLogger(__name__)


@dataclass
class PilotParticipant:
    """Individual pilot program participant"""
    participant_id: str
    age: int
    grade_level: int
    language: str
    school: str
    pre_test_score: float = 0.0
    post_test_score: float = 0.0
    enrolled_at: str = ""
    completed_at: Optional[str] = None


@dataclass
class SessionMetrics:
    """Metrics for a single learning session"""
    session_id: str
    participant_id: str
    curriculum_id: str
    language: str
    started_at: str
    ended_at: Optional[str] = None
    duration_seconds: float = 0.0

    # Engagement metrics
    mechanics_completed: int = 0
    mechanics_successful: int = 0
    average_time_per_mechanic: float = 0.0
    error_count: int = 0
    help_requests: int = 0

    # Performance metrics
    average_fps: float = 0.0
    min_fps: float = 0.0
    memory_usage_mb: float = 0.0
    load_time_seconds: float = 0.0
    crash_count: int = 0

    # Behavior metrics
    engagement_states: Dict[str, float] = None  # Time in each state
    final_difficulty: str = ""
    xp_earned: int = 0
    badges_earned: int = 0


@dataclass
class SatisfactionSurvey:
    """Post-session satisfaction survey"""
    participant_id: str
    session_id: str
    timestamp: str

    # Ratings (1-5 scale)
    fun_rating: int = 0
    learning_rating: int = 0
    difficulty_rating: int = 0
    would_recommend: int = 0  # NPS: 1-10

    # Open feedback
    liked_most: str = ""
    liked_least: str = ""
    suggestions: str = ""


class PilotAnalyticsService:
    """
    Service for collecting and analyzing pilot program data
    """

    def __init__(self):
        """Initialize pilot analytics service"""
        self.participants: Dict[str, PilotParticipant] = {}
        self.sessions: List[SessionMetrics] = []
        self.surveys: List[SatisfactionSurvey] = []

        logger.info("Pilot Analytics Service initialized")

    def enroll_participant(
        self,
        participant_id: str,
        age: int,
        grade_level: int,
        language: str,
        school: str,
        pre_test_score: float
    ) -> PilotParticipant:
        """
        Enroll a new participant in the pilot program

        Args:
            participant_id: Unique participant identifier
            age: Student age
            grade_level: Current grade level
            language: Primary language
            school: School name
            pre_test_score: Pre-test baseline score (0-100)

        Returns:
            PilotParticipant object
        """
        participant = PilotParticipant(
            participant_id=participant_id,
            age=age,
            grade_level=grade_level,
            language=language,
            school=school,
            pre_test_score=pre_test_score,
            enrolled_at=datetime.utcnow().isoformat()
        )

        self.participants[participant_id] = participant

        logger.info(f"Enrolled participant {participant_id} (age {age}, {language})")

        return participant

    def record_session(self, session_data: Dict) -> SessionMetrics:
        """
        Record a completed learning session

        Args:
            session_data: Session metrics dictionary

        Returns:
            SessionMetrics object
        """
        # Convert engagement_states dict if needed
        if 'engagement_states' not in session_data:
            session_data['engagement_states'] = {}

        session = SessionMetrics(**session_data)
        self.sessions.append(session)

        logger.info(f"Recorded session {session.session_id} for participant {session.participant_id}")

        return session

    def record_survey(self, survey_data: Dict) -> SatisfactionSurvey:
        """
        Record post-session satisfaction survey

        Args:
            survey_data: Survey responses

        Returns:
            SatisfactionSurvey object
        """
        survey = SatisfactionSurvey(**survey_data)
        self.surveys.append(survey)

        logger.info(f"Recorded survey from participant {survey.participant_id}")

        return survey

    def complete_participant(
        self,
        participant_id: str,
        post_test_score: float
    ):
        """
        Mark participant as completed with post-test score

        Args:
            participant_id: Participant ID
            post_test_score: Post-test score (0-100)
        """
        if participant_id not in self.participants:
            logger.error(f"Participant {participant_id} not found")
            return

        participant = self.participants[participant_id]
        participant.post_test_score = post_test_score
        participant.completed_at = datetime.utcnow().isoformat()

        # Calculate learning gain
        gain = post_test_score - participant.pre_test_score
        gain_percentage = (gain / participant.pre_test_score) * 100 if participant.pre_test_score > 0 else 0

        logger.info(
            f"Participant {participant_id} completed: "
            f"pre={participant.pre_test_score}, post={post_test_score}, "
            f"gain={gain_percentage:.1f}%"
        )

    def get_participant_summary(self, participant_id: str) -> Optional[Dict]:
        """
        Get comprehensive summary for a participant

        Args:
            participant_id: Participant ID

        Returns:
            Summary dictionary
        """
        if participant_id not in self.participants:
            logger.warning(f"Participant {participant_id} not found")
            return None

        participant = self.participants[participant_id]

        # Get participant's sessions
        participant_sessions = [s for s in self.sessions if s.participant_id == participant_id]

        # Get participant's surveys
        participant_surveys = [s for s in self.surveys if s.participant_id == participant_id]

        # Calculate aggregate metrics
        total_sessions = len(participant_sessions)
        total_duration = sum(s.duration_seconds for s in participant_sessions)
        total_mechanics = sum(s.mechanics_completed for s in participant_sessions)
        success_rate = 0.0

        if total_mechanics > 0:
            total_successful = sum(s.mechanics_successful for s in participant_sessions)
            success_rate = total_successful / total_mechanics

        # Calculate learning gain
        learning_gain = participant.post_test_score - participant.pre_test_score if participant.post_test_score > 0 else 0
        learning_gain_percentage = (learning_gain / participant.pre_test_score * 100) if participant.pre_test_score > 0 else 0

        # Calculate average satisfaction
        avg_nps = 0.0
        if participant_surveys:
            avg_nps = statistics.mean([s.would_recommend for s in participant_surveys])

        return {
            'participant': asdict(participant),
            'sessions': {
                'total_count': total_sessions,
                'total_duration_hours': total_duration / 3600,
                'total_mechanics': total_mechanics,
                'success_rate': success_rate
            },
            'learning_outcomes': {
                'pre_test_score': participant.pre_test_score,
                'post_test_score': participant.post_test_score,
                'learning_gain': learning_gain,
                'learning_gain_percentage': learning_gain_percentage
            },
            'satisfaction': {
                'average_nps': avg_nps,
                'survey_count': len(participant_surveys)
            }
        }

    def get_pilot_summary(self) -> Dict:
        """
        Get comprehensive summary of entire pilot program

        Returns:
            Pilot program summary with all key metrics
        """
        total_participants = len(self.participants)
        completed_participants = len([p for p in self.participants.values() if p.completed_at])

        # Learning outcomes
        learning_gains = []
        for p in self.participants.values():
            if p.post_test_score > 0:
                gain = ((p.post_test_score - p.pre_test_score) / p.pre_test_score) * 100
                learning_gains.append(gain)

        avg_learning_gain = statistics.mean(learning_gains) if learning_gains else 0

        # Session metrics
        total_sessions = len(self.sessions)
        total_duration = sum(s.duration_seconds for s in self.sessions) / 3600  # Convert to hours
        avg_session_duration = statistics.mean([s.duration_seconds / 60 for s in self.sessions]) if self.sessions else 0

        # Performance metrics
        avg_fps = statistics.mean([s.average_fps for s in self.sessions if s.average_fps > 0]) if self.sessions else 0
        total_crashes = sum(s.crash_count for s in self.sessions)

        # Engagement metrics
        total_mechanics = sum(s.mechanics_completed for s in self.sessions)
        successful_mechanics = sum(s.mechanics_successful for s in self.sessions)
        overall_success_rate = successful_mechanics / total_mechanics if total_mechanics > 0 else 0

        # Satisfaction metrics (NPS)
        nps_scores = [s.would_recommend for s in self.surveys]
        promoters = len([s for s in nps_scores if s >= 9])
        detractors = len([s for s in nps_scores if s <= 6])
        nps = ((promoters - detractors) / len(nps_scores) * 100) if nps_scores else 0

        # Language breakdown
        language_breakdown = {}
        for p in self.participants.values():
            language_breakdown[p.language] = language_breakdown.get(p.language, 0) + 1

        return {
            'program_overview': {
                'total_participants': total_participants,
                'completed_participants': completed_participants,
                'completion_rate': completed_participants / total_participants if total_participants > 0 else 0,
                'total_sessions': total_sessions,
                'total_hours': total_duration,
                'language_breakdown': language_breakdown
            },
            'learning_outcomes': {
                'average_learning_gain_percentage': avg_learning_gain,
                'target_gain_percentage': 40.0,  # Target: 40%+ improvement
                'target_met': avg_learning_gain >= 40.0,
                'participants_with_data': len(learning_gains)
            },
            'engagement': {
                'total_mechanics_completed': total_mechanics,
                'overall_success_rate': overall_success_rate,
                'average_session_minutes': avg_session_duration,
                'target_session_minutes': 30,
                'target_met': avg_session_duration >= 30
            },
            'performance': {
                'average_fps': avg_fps,
                'target_fps': 50,
                'target_met': avg_fps >= 50,
                'total_crashes': total_crashes,
                'crash_rate': total_crashes / total_sessions if total_sessions > 0 else 0
            },
            'satisfaction': {
                'nps_score': nps,
                'target_nps': 40,
                'target_met': nps >= 40,
                'survey_count': len(self.surveys),
                'response_rate': len(self.surveys) / total_sessions if total_sessions > 0 else 0
            }
        }

    def export_to_csv(self) -> str:
        """
        Export all pilot data to CSV format

        Returns:
            CSV string with all data
        """
        output = io.StringIO()

        # Export participants
        output.write("=== PARTICIPANTS ===\n")
        if self.participants:
            writer = csv.DictWriter(
                output,
                fieldnames=['participant_id', 'age', 'grade_level', 'language', 'school',
                           'pre_test_score', 'post_test_score', 'learning_gain_percentage',
                           'enrolled_at', 'completed_at']
            )
            writer.writeheader()

            for p in self.participants.values():
                row = asdict(p)
                if p.post_test_score > 0:
                    row['learning_gain_percentage'] = ((p.post_test_score - p.pre_test_score) / p.pre_test_score) * 100
                else:
                    row['learning_gain_percentage'] = 0
                writer.writerow(row)

        output.write("\n=== SESSIONS ===\n")
        if self.sessions:
            writer = csv.DictWriter(
                output,
                fieldnames=['session_id', 'participant_id', 'curriculum_id', 'language',
                           'duration_seconds', 'mechanics_completed', 'mechanics_successful',
                           'success_rate', 'average_fps', 'crash_count']
            )
            writer.writeheader()

            for s in self.sessions:
                row = {
                    'session_id': s.session_id,
                    'participant_id': s.participant_id,
                    'curriculum_id': s.curriculum_id,
                    'language': s.language,
                    'duration_seconds': s.duration_seconds,
                    'mechanics_completed': s.mechanics_completed,
                    'mechanics_successful': s.mechanics_successful,
                    'success_rate': s.mechanics_successful / s.mechanics_completed if s.mechanics_completed > 0 else 0,
                    'average_fps': s.average_fps,
                    'crash_count': s.crash_count
                }
                writer.writerow(row)

        output.write("\n=== SURVEYS ===\n")
        if self.surveys:
            writer = csv.DictWriter(
                output,
                fieldnames=['participant_id', 'session_id', 'fun_rating', 'learning_rating',
                           'difficulty_rating', 'would_recommend', 'liked_most', 'liked_least']
            )
            writer.writeheader()

            for s in self.surveys:
                writer.writerow(asdict(s))

        csv_content = output.getvalue()
        output.close()

        return csv_content

    def get_recommendations(self) -> List[str]:
        """
        Generate recommendations based on pilot data

        Returns:
            List of actionable recommendations
        """
        recommendations = []
        summary = self.get_pilot_summary()

        # Learning outcomes
        if not summary['learning_outcomes']['target_met']:
            recommendations.append(
                f"⚠️ Learning gain ({summary['learning_outcomes']['average_learning_gain_percentage']:.1f}%) "
                f"is below target (40%). Consider improving content difficulty adaptation."
            )
        else:
            recommendations.append(
                f"✅ Learning gain target met ({summary['learning_outcomes']['average_learning_gain_percentage']:.1f}%)"
            )

        # Engagement
        if not summary['engagement']['target_met']:
            recommendations.append(
                f"⚠️ Session duration ({summary['engagement']['average_session_minutes']:.1f} min) "
                f"is below target (30 min). Consider adding more engaging mechanics."
            )
        else:
            recommendations.append(
                f"✅ Session duration target met ({summary['engagement']['average_session_minutes']:.1f} min)"
            )

        # Performance
        if not summary['performance']['target_met']:
            recommendations.append(
                f"⚠️ Average FPS ({summary['performance']['average_fps']:.1f}) "
                f"is below target (50). Optimize assets and enable LOD system."
            )
        else:
            recommendations.append(
                f"✅ Performance target met ({summary['performance']['average_fps']:.1f} FPS)"
            )

        # Satisfaction
        if not summary['satisfaction']['target_met']:
            recommendations.append(
                f"⚠️ NPS score ({summary['satisfaction']['nps_score']:.0f}) "
                f"is below target (40). Collect qualitative feedback to identify issues."
            )
        else:
            recommendations.append(
                f"✅ Satisfaction target met (NPS: {summary['satisfaction']['nps_score']:.0f})"
            )

        # Crash rate
        if summary['performance']['crash_rate'] > 0.05:  # More than 5% crash rate
            recommendations.append(
                f"🔴 CRITICAL: High crash rate ({summary['performance']['crash_rate']:.1%}). "
                f"Prioritize stability fixes."
            )

        return recommendations


# Global pilot analytics instance
pilot_analytics = PilotAnalyticsService()
