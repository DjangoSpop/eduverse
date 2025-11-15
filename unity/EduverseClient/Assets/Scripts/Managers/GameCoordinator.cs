using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Eduverse.Data;
using Eduverse.UI;
using Eduverse.Managers;

namespace Eduverse.Core
{
    /// <summary>
    /// Main game coordinator that manages gameplay flow and integration.
    /// Coordinates between LessonLoader, UI, and backend tracking.
    /// Integrates with GamificationManager and AnalyticsLogger for Sprint 4 features.
    /// </summary>
    public class GameCoordinator : MonoBehaviour
    {
        [Header("References")]
        [SerializeField] private GamificationUI gamificationUI;
        [SerializeField] private ChallengeUI challengeUI;

        [Header("Sprint 4 Integration")]
        [SerializeField] private bool useGamificationManager = true;
        [SerializeField] private bool useAnalyticsLogger = true;

        // Current lesson data
        private SceneSpecification currentLesson;
        private string currentSessionId;
        private string currentLearnerId;
        private int currentSceneIndex = 0;

        // Session tracking
        private int totalXPEarned = 0;
        private int challengesAttempted = 0;
        private int challengesCompleted = 0;
        private List<string> collectiblesCollected = new List<string>();
        private System.DateTime sessionStartTime;

        // Sprint 4 component references
        private GamificationManager gamificationManager;
        private AnalyticsLogger analyticsLogger;

        private void Awake()
        {
            // Find UI if not assigned
            if (gamificationUI == null)
                gamificationUI = FindObjectOfType<GamificationUI>();

            if (challengeUI == null)
                challengeUI = FindObjectOfType<ChallengeUI>();

            // Sprint 4: Get references to new managers
            if (useGamificationManager)
                gamificationManager = GamificationManager.Instance;

            if (useAnalyticsLogger)
                analyticsLogger = AnalyticsLogger.Instance;
        }

        #region Lesson Management

        /// <summary>
        /// Called by LessonLoader when lesson is loaded.
        /// </summary>
        public void OnLessonLoaded(SceneSpecification lesson, string sessionId, string learnerId = "")
        {
            currentLesson = lesson;
            currentSessionId = sessionId;
            currentLearnerId = learnerId;
            currentSceneIndex = 0;
            sessionStartTime = System.DateTime.UtcNow;

            Debug.Log($"[GameCoordinator] Lesson loaded: {lesson.title}");
            Debug.Log($"[GameCoordinator] Session ID: {sessionId}");
            Debug.Log($"[GameCoordinator] Scenes: {lesson.scenes.Count}");
            Debug.Log($"[GameCoordinator] Learning Objectives: {lesson.learning_objectives.Count}");

            // Sprint 4: Log session start to analytics
            if (analyticsLogger != null)
            {
                analyticsLogger.LogSessionStart(sessionId, learnerId, lesson.lesson_id);
                analyticsLogger.SetUserId(learnerId);
                analyticsLogger.SetUserProperty("current_lesson", lesson.lesson_id);
                analyticsLogger.SetUserProperty("lesson_theme", lesson.theme);
            }

            // Log lesson start event
            LogEvent("lesson_started", new Dictionary<string, object>
            {
                { "lesson_id", lesson.lesson_id },
                { "lesson_title", lesson.title },
                { "theme", lesson.theme }
            });

            // Show current scene challenges
            ShowSceneChallenges();
        }

        #endregion

        #region Challenge Management

        /// <summary>
        /// Show challenges for current scene.
        /// </summary>
        private void ShowSceneChallenges()
        {
            if (currentLesson == null || currentSceneIndex >= currentLesson.scenes.Count)
                return;

            var currentScene = currentLesson.scenes[currentSceneIndex];

            if (currentScene.challenges != null && currentScene.challenges.Count > 0)
            {
                Debug.Log($"[GameCoordinator] Scene has {currentScene.challenges.Count} challenges");

                // Show first challenge after a delay
                StartCoroutine(ShowChallengeAfterDelay(currentScene.challenges[0], 3f));
            }
            else
            {
                Debug.Log("[GameCoordinator] No challenges in this scene");
            }
        }

        /// <summary>
        /// Show a challenge after a delay.
        /// </summary>
        private IEnumerator ShowChallengeAfterDelay(Challenge challenge, float delay)
        {
            yield return new WaitForSeconds(delay);

            if (challengeUI != null)
            {
                challengeUI.ShowChallenge(challenge, OnChallengeCompleted);
            }
            else
            {
                Debug.LogWarning("[GameCoordinator] ChallengeUI not found!");
            }
        }

        /// <summary>
        /// Called when a challenge is completed.
        /// </summary>
        private void OnChallengeCompleted(bool success)
        {
            challengesAttempted++;

            if (success)
            {
                challengesCompleted++;

                // Get current challenge from scene
                var currentScene = currentLesson.scenes[currentSceneIndex];
                var challenge = currentScene.challenges[0]; // TODO: Track which challenge

                // Award XP
                AwardXP(challenge.xp_reward, "Challenge completed");

                // Sprint 4: Increase curiosity on success
                if (gamificationManager != null)
                {
                    gamificationManager.OnSuccessfulChallenge();
                    gamificationManager.OnQuizSuccess();

                    // Check for perfect challenge (100% accuracy)
                    if (challengesCompleted == challengesAttempted)
                    {
                        gamificationManager.OnPerfectChallenge();
                    }
                }

                // Sprint 4: Log to analytics
                if (analyticsLogger != null)
                {
                    analyticsLogger.LogChallengeCompleted(challenge.id, true, 1, 0f, challenge.xp_reward);
                }

                // Log event
                LogEvent("challenge_completed", new Dictionary<string, object>
                {
                    { "challenge_id", challenge.id },
                    { "success", true },
                    { "attempts", 1 },
                    { "xp_earned", challenge.xp_reward }
                }, true, challenge.xp_reward);
            }
            else
            {
                // Sprint 4: Log to analytics
                if (analyticsLogger != null)
                {
                    var currentScene = currentLesson.scenes[currentSceneIndex];
                    var challenge = currentScene.challenges[0];
                    analyticsLogger.LogChallengeCompleted(challenge.id, false, 1, 0f, 0);
                }

                // Log failed attempt
                LogEvent("challenge_failed", new Dictionary<string, object>
                {
                    { "challenge_id", "unknown" },
                    { "attempts", 1 }
                });
            }

            Debug.Log($"[GameCoordinator] Challenge completed: {success}");
        }

        #endregion

        #region Object Interaction

        /// <summary>
        /// Called when a collectible is collected.
        /// </summary>
        public void OnCollectibleCollected(GameObjectData collectible)
        {
            collectiblesCollected.Add(collectible.name);

            // Award XP
            AwardXP(collectible.xp_reward, $"Collected {collectible.name}");

            // Sprint 4: Track collectible in gamification system
            if (gamificationManager != null)
            {
                gamificationManager.OnCollectibleCollected();
                gamificationManager.OnInteraction(); // Also increase curiosity
            }

            // Sprint 4: Log to analytics
            if (analyticsLogger != null)
            {
                analyticsLogger.LogCollectibleCollected(collectible.id, collectible.type, collectible.xp_reward);
            }

            // Log event
            LogEvent("collectible_collected", new Dictionary<string, object>
            {
                { "object_name", collectible.name },
                { "xp_earned", collectible.xp_reward }
            }, true, collectible.xp_reward);

            Debug.Log($"[GameCoordinator] Collectible collected: {collectible.name}");
        }

        /// <summary>
        /// Called when portal is activated.
        /// </summary>
        public void OnPortalActivated()
        {
            Debug.Log("[GameCoordinator] Portal activated - moving to next scene");

            currentSceneIndex++;

            if (currentSceneIndex < currentLesson.scenes.Count)
            {
                // Load next scene
                Debug.Log($"[GameCoordinator] Loading scene {currentSceneIndex + 1}/{currentLesson.scenes.Count}");

                // TODO: Tell LessonLoader to load next scene
                ShowSceneChallenges();
            }
            else
            {
                // Lesson complete
                OnLessonComplete();
            }
        }

        #endregion

        #region XP and Gamification

        /// <summary>
        /// Award XP to the learner.
        /// </summary>
        public void AwardXP(int amount, string reason = "")
        {
            totalXPEarned += amount;

            // Sprint 4: Award XP through GamificationManager
            if (gamificationManager != null)
            {
                gamificationManager.AwardXP(amount, reason);
            }
            // Fallback to old UI system if GamificationManager not available
            else if (gamificationUI != null)
            {
                gamificationUI.AddXP(amount, reason);
            }

            Debug.Log($"[GameCoordinator] +{amount} XP ({reason}). Total: {totalXPEarned}");
        }

        /// <summary>
        /// Called when an NPC is interacted with.
        /// </summary>
        public void OnNPCInteraction(string npcId, string npcName, string dialogueId)
        {
            // Sprint 4: Track NPC interaction
            if (gamificationManager != null)
            {
                gamificationManager.OnNPCInteraction(npcId);
                gamificationManager.OnInteraction(); // Increase curiosity
            }

            // Sprint 4: Log to analytics
            if (analyticsLogger != null)
            {
                analyticsLogger.LogNPCInteraction(npcId, npcName, dialogueId);
            }

            Debug.Log($"[GameCoordinator] NPC interaction: {npcName}");
        }

        #endregion

        #region Session Events

        /// <summary>
        /// Log an event to the backend.
        /// </summary>
        private void LogEvent(
            string eventType,
            Dictionary<string, object> eventData,
            bool success = false,
            int xpEarned = 0)
        {
            if (string.IsNullOrEmpty(currentSessionId))
            {
                Debug.LogWarning("[GameCoordinator] No active session - event not logged");
                return;
            }

            StartCoroutine(
                APIClient.Instance.LogEvent(
                    currentSessionId,
                    eventType,
                    eventData,
                    success,
                    xpEarned,
                    () => Debug.Log($"[GameCoordinator] Event logged: {eventType}"),
                    (error) => Debug.LogWarning($"[GameCoordinator] Failed to log event: {error}")
                )
            );
        }

        /// <summary>
        /// Called when lesson is completed.
        /// </summary>
        private void OnLessonComplete()
        {
            Debug.Log("[GameCoordinator] 🎉 LESSON COMPLETE! 🎉");

            // Calculate completion percentage
            float completionPercentage = 1.0f;

            // Sprint 4: Log session end to analytics
            if (analyticsLogger != null)
            {
                analyticsLogger.LogSessionEnd(currentSessionId, completionPercentage, totalXPEarned, challengesCompleted);
            }

            // End session
            if (!string.IsNullOrEmpty(currentSessionId))
            {
                StartCoroutine(
                    APIClient.Instance.EndSession(
                        currentSessionId,
                        completionPercentage,
                        "completed",
                        () => Debug.Log("[GameCoordinator] Session ended successfully"),
                        (error) => Debug.LogWarning($"[GameCoordinator] Failed to end session: {error}")
                    )
                );
            }

            // Show completion screen
            ShowCompletionScreen();
        }

        /// <summary>
        /// Show lesson completion screen.
        /// </summary>
        private void ShowCompletionScreen()
        {
            Debug.Log("=== LESSON COMPLETE ===");
            Debug.Log($"Total XP Earned: {totalXPEarned}");
            Debug.Log($"Challenges Completed: {challengesCompleted}/{challengesAttempted}");
            Debug.Log($"Collectibles: {collectiblesCollected.Count}");
            Debug.Log("======================");

            // TODO: Show completion UI with stats
        }

        #endregion

        #region Public Getters

        public SceneSpecification GetCurrentLesson() => currentLesson;
        public string GetSessionId() => currentSessionId;
        public int GetTotalXP() => totalXPEarned;
        public float GetSuccessRate()
        {
            if (challengesAttempted == 0)
                return 0f;
            return (float)challengesCompleted / challengesAttempted;
        }

        #endregion
    }
}
