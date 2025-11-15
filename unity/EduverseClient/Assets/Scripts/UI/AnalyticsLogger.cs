using UnityEngine;
using System;
using System.Collections.Generic;
// Firebase SDK imports (uncomment when Firebase SDK is installed)
// using Firebase;
// using Firebase.Analytics;
// using Firebase.Extensions;

namespace Eduverse.UI
{
    /// <summary>
    /// Handles analytics logging to Firebase Analytics and backend.
    /// Tracks player actions, progress, XP gains, badge unlocks, and session metrics.
    /// </summary>
    public class AnalyticsLogger : MonoBehaviour
    {
        [Header("Settings")]
        [SerializeField] private bool enableFirebaseAnalytics = true;
        [SerializeField] private bool enableBackendAnalytics = true;
        [SerializeField] private bool enableDebugLogs = true;

        [Header("Batch Settings")]
        [SerializeField] private int batchSize = 10; // Send events in batches
        [SerializeField] private float batchInterval = 30f; // Send every 30 seconds

        // Singleton instance
        private static AnalyticsLogger _instance;
        public static AnalyticsLogger Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = FindObjectOfType<AnalyticsLogger>();
                }
                return _instance;
            }
        }

        // Event batching
        private Queue<AnalyticsEvent> eventQueue = new Queue<AnalyticsEvent>();
        private float timeSinceLastBatch = 0f;

        // Session tracking
        private string currentSessionId;
        private DateTime sessionStartTime;
        private bool firebaseInitialized = false;

        private void Awake()
        {
            if (_instance != null && _instance != this)
            {
                Destroy(gameObject);
                return;
            }

            _instance = this;
            DontDestroyOnLoad(gameObject);

            InitializeFirebase();
        }

        private void Start()
        {
            LogAppOpen();
        }

        private void Update()
        {
            // Process event batches
            if (eventQueue.Count > 0)
            {
                timeSinceLastBatch += Time.deltaTime;

                if (timeSinceLastBatch >= batchInterval || eventQueue.Count >= batchSize)
                {
                    ProcessEventBatch();
                    timeSinceLastBatch = 0f;
                }
            }
        }

        #region Firebase Initialization

        /// <summary>
        /// Initialize Firebase Analytics.
        /// </summary>
        private void InitializeFirebase()
        {
            if (!enableFirebaseAnalytics)
            {
                if (enableDebugLogs)
                    Debug.Log("[AnalyticsLogger] Firebase Analytics disabled in settings");
                return;
            }

            // TODO: Uncomment when Firebase SDK is installed
            /*
            FirebaseApp.CheckAndFixDependenciesAsync().ContinueWithOnMainThread(task =>
            {
                if (task.Result == DependencyStatus.Available)
                {
                    firebaseInitialized = true;
                    FirebaseAnalytics.SetAnalyticsCollectionEnabled(true);

                    if (enableDebugLogs)
                        Debug.Log("[AnalyticsLogger] Firebase Analytics initialized successfully");
                }
                else
                {
                    Debug.LogError($"[AnalyticsLogger] Firebase initialization failed: {task.Result}");
                }
            });
            */

            // Placeholder for now
            firebaseInitialized = false;
            if (enableDebugLogs)
                Debug.Log("[AnalyticsLogger] Firebase SDK not installed. Install Firebase Unity SDK to enable analytics.");
        }

        #endregion

        #region Session Events

        /// <summary>
        /// Log app open event.
        /// </summary>
        public void LogAppOpen()
        {
            LogEvent("app_open", new Dictionary<string, object>
            {
                { "platform", Application.platform.ToString() },
                { "unity_version", Application.unityVersion },
                { "app_version", Application.version }
            });
        }

        /// <summary>
        /// Log session start.
        /// </summary>
        public void LogSessionStart(string sessionId, string learnerId, string lessonId)
        {
            currentSessionId = sessionId;
            sessionStartTime = DateTime.UtcNow;

            LogEvent("session_start", new Dictionary<string, object>
            {
                { "session_id", sessionId },
                { "learner_id", learnerId },
                { "lesson_id", lessonId },
                { "timestamp", sessionStartTime.ToString("o") }
            });

            if (enableDebugLogs)
                Debug.Log($"[AnalyticsLogger] Session started: {sessionId}");
        }

        /// <summary>
        /// Log session end.
        /// </summary>
        public void LogSessionEnd(string sessionId, float completionPercentage, int totalXP, int challengesCompleted)
        {
            TimeSpan sessionDuration = DateTime.UtcNow - sessionStartTime;

            LogEvent("session_end", new Dictionary<string, object>
            {
                { "session_id", sessionId },
                { "duration_seconds", (int)sessionDuration.TotalSeconds },
                { "completion_percentage", completionPercentage },
                { "total_xp", totalXP },
                { "challenges_completed", challengesCompleted },
                { "timestamp", DateTime.UtcNow.ToString("o") }
            });

            if (enableDebugLogs)
                Debug.Log($"[AnalyticsLogger] Session ended: {sessionId}, Duration: {sessionDuration.TotalMinutes:F2} min");
        }

        #endregion

        #region Gameplay Events

        /// <summary>
        /// Log XP gained event.
        /// </summary>
        public void LogXPGained(int amount, string reason, int totalXP)
        {
            LogEvent("xp_gained", new Dictionary<string, object>
            {
                { "amount", amount },
                { "reason", reason },
                { "total_xp", totalXP },
                { "session_id", currentSessionId }
            });
        }

        /// <summary>
        /// Log level up event.
        /// </summary>
        public void LogLevelUp(int newLevel, int totalXP)
        {
            LogEvent("level_up", new Dictionary<string, object>
            {
                { "new_level", newLevel },
                { "total_xp", totalXP },
                { "session_id", currentSessionId }
            });

            if (enableDebugLogs)
                Debug.Log($"[AnalyticsLogger] Level up! New level: {newLevel}");
        }

        /// <summary>
        /// Log badge unlocked event.
        /// </summary>
        public void LogBadgeUnlocked(string badgeId, string badgeName)
        {
            LogEvent("badge_unlocked", new Dictionary<string, object>
            {
                { "badge_id", badgeId },
                { "badge_name", badgeName },
                { "session_id", currentSessionId }
            });

            if (enableDebugLogs)
                Debug.Log($"[AnalyticsLogger] Badge unlocked: {badgeName}");
        }

        /// <summary>
        /// Log collectible collected event.
        /// </summary>
        public void LogCollectibleCollected(string collectibleId, string collectibleType, int xpAwarded)
        {
            LogEvent("collectible_collected", new Dictionary<string, object>
            {
                { "collectible_id", collectibleId },
                { "collectible_type", collectibleType },
                { "xp_awarded", xpAwarded },
                { "session_id", currentSessionId }
            });
        }

        /// <summary>
        /// Log NPC interaction event.
        /// </summary>
        public void LogNPCInteraction(string npcId, string npcName, string dialogueId)
        {
            LogEvent("npc_interaction", new Dictionary<string, object>
            {
                { "npc_id", npcId },
                { "npc_name", npcName },
                { "dialogue_id", dialogueId },
                { "session_id", currentSessionId }
            });
        }

        /// <summary>
        /// Log challenge started event.
        /// </summary>
        public void LogChallengeStarted(string challengeId, string challengeType, int difficulty)
        {
            LogEvent("challenge_started", new Dictionary<string, object>
            {
                { "challenge_id", challengeId },
                { "challenge_type", challengeType },
                { "difficulty", difficulty },
                { "session_id", currentSessionId }
            });
        }

        /// <summary>
        /// Log challenge completed event.
        /// </summary>
        public void LogChallengeCompleted(string challengeId, bool success, int attempts, float timeTaken, int xpAwarded)
        {
            LogEvent("challenge_completed", new Dictionary<string, object>
            {
                { "challenge_id", challengeId },
                { "success", success },
                { "attempts", attempts },
                { "time_taken_seconds", timeTaken },
                { "xp_awarded", xpAwarded },
                { "session_id", currentSessionId }
            });
        }

        /// <summary>
        /// Log quiz answer event.
        /// </summary>
        public void LogQuizAnswer(string challengeId, int questionIndex, bool correct, float responseTime)
        {
            LogEvent("quiz_answer", new Dictionary<string, object>
            {
                { "challenge_id", challengeId },
                { "question_index", questionIndex },
                { "correct", correct },
                { "response_time_seconds", responseTime },
                { "session_id", currentSessionId }
            });
        }

        /// <summary>
        /// Log curiosity change event.
        /// </summary>
        public void LogCuriosityChanged(float newValue, float delta, string trigger)
        {
            LogEvent("curiosity_changed", new Dictionary<string, object>
            {
                { "new_value", newValue },
                { "delta", delta },
                { "trigger", trigger },
                { "session_id", currentSessionId }
            });
        }

        #endregion

        #region Scene Events

        /// <summary>
        /// Log scene loaded event.
        /// </summary>
        public void LogSceneLoaded(string sceneId, string sceneName, string theme)
        {
            LogEvent("scene_loaded", new Dictionary<string, object>
            {
                { "scene_id", sceneId },
                { "scene_name", sceneName },
                { "theme", theme },
                { "session_id", currentSessionId }
            });
        }

        /// <summary>
        /// Log scene completed event.
        /// </summary>
        public void LogSceneCompleted(string sceneId, float completionPercentage, float timeSpent)
        {
            LogEvent("scene_completed", new Dictionary<string, object>
            {
                { "scene_id", sceneId },
                { "completion_percentage", completionPercentage },
                { "time_spent_seconds", timeSpent },
                { "session_id", currentSessionId }
            });
        }

        #endregion

        #region Loading Events

        /// <summary>
        /// Log loading stage changed event.
        /// </summary>
        public void LogLoadingStageChanged(string stageName, int stageIndex, float progress)
        {
            LogEvent("loading_stage_changed", new Dictionary<string, object>
            {
                { "stage_name", stageName },
                { "stage_index", stageIndex },
                { "progress", progress },
                { "session_id", currentSessionId }
            });
        }

        /// <summary>
        /// Log loading completed event.
        /// </summary>
        public void LogLoadingCompleted(float totalLoadTime, string lessonId)
        {
            LogEvent("loading_completed", new Dictionary<string, object>
            {
                { "total_load_time_seconds", totalLoadTime },
                { "lesson_id", lessonId },
                { "session_id", currentSessionId }
            });

            if (enableDebugLogs)
                Debug.Log($"[AnalyticsLogger] Loading completed in {totalLoadTime:F2}s");
        }

        #endregion

        #region Error Events

        /// <summary>
        /// Log error event.
        /// </summary>
        public void LogError(string errorType, string errorMessage, string stackTrace = "")
        {
            LogEvent("error_occurred", new Dictionary<string, object>
            {
                { "error_type", errorType },
                { "error_message", errorMessage },
                { "stack_trace", stackTrace },
                { "session_id", currentSessionId },
                { "timestamp", DateTime.UtcNow.ToString("o") }
            });

            Debug.LogError($"[AnalyticsLogger] Error logged: {errorType} - {errorMessage}");
        }

        #endregion

        #region Core Analytics Functions

        /// <summary>
        /// Log a custom event with parameters.
        /// </summary>
        public void LogEvent(string eventName, Dictionary<string, object> parameters = null)
        {
            // Create analytics event
            AnalyticsEvent analyticsEvent = new AnalyticsEvent
            {
                eventName = eventName,
                parameters = parameters ?? new Dictionary<string, object>(),
                timestamp = DateTime.UtcNow
            };

            // Add to queue for batching
            eventQueue.Enqueue(analyticsEvent);

            // Log to Firebase immediately for critical events
            if (ShouldLogImmediately(eventName))
            {
                LogToFirebase(analyticsEvent);
            }

            // Debug log
            if (enableDebugLogs)
            {
                string paramsStr = parameters != null ? string.Join(", ", parameters) : "none";
                Debug.Log($"[AnalyticsLogger] Event: {eventName}, Params: {paramsStr}");
            }
        }

        /// <summary>
        /// Check if event should be logged immediately (not batched).
        /// </summary>
        private bool ShouldLogImmediately(string eventName)
        {
            return eventName == "session_start" ||
                   eventName == "session_end" ||
                   eventName == "error_occurred" ||
                   eventName == "level_up" ||
                   eventName == "badge_unlocked";
        }

        /// <summary>
        /// Process queued events as a batch.
        /// </summary>
        private void ProcessEventBatch()
        {
            if (eventQueue.Count == 0) return;

            List<AnalyticsEvent> batch = new List<AnalyticsEvent>();

            while (eventQueue.Count > 0 && batch.Count < batchSize)
            {
                batch.Add(eventQueue.Dequeue());
            }

            // Send to Firebase
            if (enableFirebaseAnalytics)
            {
                foreach (var evt in batch)
                {
                    LogToFirebase(evt);
                }
            }

            // Send to backend
            if (enableBackendAnalytics)
            {
                SendBatchToBackend(batch);
            }

            if (enableDebugLogs)
                Debug.Log($"[AnalyticsLogger] Processed batch of {batch.Count} events");
        }

        /// <summary>
        /// Log event to Firebase Analytics.
        /// </summary>
        private void LogToFirebase(AnalyticsEvent evt)
        {
            if (!firebaseInitialized || !enableFirebaseAnalytics)
                return;

            // TODO: Uncomment when Firebase SDK is installed
            /*
            Parameter[] firebaseParams = new Parameter[evt.parameters.Count];
            int index = 0;
            foreach (var param in evt.parameters)
            {
                if (param.Value is string strValue)
                {
                    firebaseParams[index] = new Parameter(param.Key, strValue);
                }
                else if (param.Value is int intValue)
                {
                    firebaseParams[index] = new Parameter(param.Key, intValue);
                }
                else if (param.Value is long longValue)
                {
                    firebaseParams[index] = new Parameter(param.Key, longValue);
                }
                else if (param.Value is double doubleValue)
                {
                    firebaseParams[index] = new Parameter(param.Key, doubleValue);
                }
                else if (param.Value is float floatValue)
                {
                    firebaseParams[index] = new Parameter(param.Key, floatValue);
                }
                else if (param.Value is bool boolValue)
                {
                    firebaseParams[index] = new Parameter(param.Key, boolValue ? 1 : 0);
                }
                else
                {
                    firebaseParams[index] = new Parameter(param.Key, param.Value.ToString());
                }
                index++;
            }

            FirebaseAnalytics.LogEvent(evt.eventName, firebaseParams);
            */
        }

        /// <summary>
        /// Send event batch to backend API.
        /// </summary>
        private void SendBatchToBackend(List<AnalyticsEvent> batch)
        {
            // TODO: Implement backend batch sending via APIClient
            // This would send events to the backend's /api/sessions/events endpoint

            if (Core.APIClient.Instance != null && !string.IsNullOrEmpty(currentSessionId))
            {
                foreach (var evt in batch)
                {
                    // Convert to backend format and send
                    // StartCoroutine(Core.APIClient.Instance.LogEvent(...));
                }
            }
        }

        #endregion

        #region User Properties

        /// <summary>
        /// Set user property (persists across sessions).
        /// </summary>
        public void SetUserProperty(string propertyName, string value)
        {
            if (!firebaseInitialized || !enableFirebaseAnalytics)
                return;

            // TODO: Uncomment when Firebase SDK is installed
            // FirebaseAnalytics.SetUserProperty(propertyName, value);

            if (enableDebugLogs)
                Debug.Log($"[AnalyticsLogger] User property set: {propertyName} = {value}");
        }

        /// <summary>
        /// Set user ID for analytics.
        /// </summary>
        public void SetUserId(string userId)
        {
            if (!firebaseInitialized || !enableFirebaseAnalytics)
                return;

            // TODO: Uncomment when Firebase SDK is installed
            // FirebaseAnalytics.SetUserId(userId);

            if (enableDebugLogs)
                Debug.Log($"[AnalyticsLogger] User ID set: {userId}");
        }

        #endregion

        private void OnApplicationQuit()
        {
            // Flush any remaining events
            if (eventQueue.Count > 0)
            {
                ProcessEventBatch();
            }
        }

        private void OnApplicationPause(bool pause)
        {
            if (pause)
            {
                // Flush events when app is paused
                if (eventQueue.Count > 0)
                {
                    ProcessEventBatch();
                }
            }
        }
    }

    #region Data Structures

    [Serializable]
    public class AnalyticsEvent
    {
        public string eventName;
        public Dictionary<string, object> parameters;
        public DateTime timestamp;
    }

    #endregion
}
