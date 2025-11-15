using UnityEngine;
using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;

namespace Eduverse.Streaming
{
    /// <summary>
    /// Dynamically spawns and manages game mechanics from streaming backend
    ///
    /// This is the core component that turns streamed mechanic JSON into
    /// actual gameplay experiences in the 3D world.
    ///
    /// Features:
    /// - Real-time mechanic instantiation
    /// - Performance tracking and reporting
    /// - Mechanic lifecycle management
    /// - Behavior analysis for engagement detection
    /// </summary>
    public class DynamicMechanicSpawner : MonoBehaviour
    {
        [Header("References")]
        [SerializeField] private StreamingWebSocketClient webSocketClient;
        [SerializeField] private Transform mechanicContainer;
        [SerializeField] private Canvas uiCanvas;

        [Header("Mechanic Prefabs")]
        [SerializeField] private GameObject chaseMechanicPrefab;
        [SerializeField] private GameObject collectMechanicPrefab;
        [SerializeField] private GameObject puzzleMechanicPrefab;
        [SerializeField] private GameObject buildMechanicPrefab;
        [SerializeField] private GameObject exploreMechanicPrefab;
        [SerializeField] private GameObject quizMechanicPrefab;
        [SerializeField] private GameObject sequenceMechanicPrefab;
        [SerializeField] private GameObject sortMechanicPrefab;

        [Header("UI Elements")]
        [SerializeField] private TextMeshProUGUI titleText;
        [SerializeField] private TextMeshProUGUI instructionText;
        [SerializeField] private TextMeshProUGUI objectiveText;
        [SerializeField] private GameObject feedbackPanel;

        [Header("Settings")]
        [SerializeField] private bool autoStartNext = true;
        [SerializeField] private float delayBetweenMechanics = 2f;
        [SerializeField] private int maxConcurrentMechanics = 1;

        // State
        private Queue<MechanicData> mechanicQueue = new Queue<MechanicData>();
        private MechanicData currentMechanic;
        private GameObject currentMechanicInstance;
        private float mechanicStartTime;
        private int errorCount;
        private bool isProcessingMechanic = false;

        // Events
        public event Action<MechanicData> OnMechanicStarted;
        public event Action<MechanicData, bool, float> OnMechanicCompleted;

        // Analytics
        private List<MechanicResult> completedMechanics = new List<MechanicResult>();

        private void Awake()
        {
            if (webSocketClient == null)
            {
                webSocketClient = GetComponent<StreamingWebSocketClient>();
            }

            if (mechanicContainer == null)
            {
                mechanicContainer = new GameObject("MechanicContainer").transform;
                mechanicContainer.SetParent(transform);
            }
        }

        private void OnEnable()
        {
            if (webSocketClient != null)
            {
                webSocketClient.OnMechanicReceived += EnqueueMechanic;
                webSocketClient.OnConnected += OnStreamingConnected;
                webSocketClient.OnDisconnected += OnStreamingDisconnected;
                webSocketClient.OnError += OnStreamingError;
            }
        }

        private void OnDisable()
        {
            if (webSocketClient != null)
            {
                webSocketClient.OnMechanicReceived -= EnqueueMechanic;
                webSocketClient.OnConnected -= OnStreamingConnected;
                webSocketClient.OnDisconnected -= OnStreamingDisconnected;
                webSocketClient.OnError -= OnStreamingError;
            }
        }

        private void OnStreamingConnected(string sessionId)
        {
            Debug.Log($"[MechanicSpawner] Connected to streaming session: {sessionId}");
            // Ready to receive mechanics
        }

        private void OnStreamingDisconnected()
        {
            Debug.Log("[MechanicSpawner] Streaming disconnected");
            // Clean up current mechanic if any
            if (currentMechanicInstance != null)
            {
                CompleteMechanic(false, Time.time - mechanicStartTime);
            }
        }

        private void OnStreamingError(string error)
        {
            Debug.LogError($"[MechanicSpawner] Streaming error: {error}");
        }

        /// <summary>
        /// Enqueue received mechanic for processing
        /// </summary>
        private void EnqueueMechanic(MechanicData mechanic)
        {
            Debug.Log($"[MechanicSpawner] Enqueued {mechanic.type} mechanic: {mechanic.title}");
            mechanicQueue.Enqueue(mechanic);

            // Start processing if not already
            if (!isProcessingMechanic && autoStartNext)
            {
                StartCoroutine(ProcessNextMechanic());
            }
        }

        /// <summary>
        /// Process next mechanic from queue
        /// </summary>
        public IEnumerator ProcessNextMechanic()
        {
            if (mechanicQueue.Count == 0)
            {
                Debug.Log("[MechanicSpawner] No mechanics in queue");
                isProcessingMechanic = false;
                yield break;
            }

            if (isProcessingMechanic)
            {
                Debug.Log("[MechanicSpawner] Already processing a mechanic");
                yield break;
            }

            isProcessingMechanic = true;

            // Wait for previous mechanic cleanup
            yield return new WaitForSeconds(delayBetweenMechanics);

            // Get next mechanic
            currentMechanic = mechanicQueue.Dequeue();

            Debug.Log($"[MechanicSpawner] Starting {currentMechanic.type}: {currentMechanic.title}");

            // Display mechanic info
            UpdateUI(currentMechanic);

            // Spawn mechanic in world
            yield return StartCoroutine(SpawnMechanic(currentMechanic));

            // Track start time
            mechanicStartTime = Time.time;
            errorCount = 0;

            // Fire event
            OnMechanicStarted?.Invoke(currentMechanic);
        }

        /// <summary>
        /// Spawn mechanic instance in 3D world
        /// </summary>
        private IEnumerator SpawnMechanic(MechanicData mechanic)
        {
            // Clean up previous mechanic
            if (currentMechanicInstance != null)
            {
                Destroy(currentMechanicInstance);
            }

            // Select prefab based on type
            GameObject prefab = GetPrefabForType(mechanic.type);

            if (prefab == null)
            {
                Debug.LogError($"[MechanicSpawner] No prefab found for type: {mechanic.type}");
                CompleteMechanic(false, 0);
                yield break;
            }

            // Instantiate mechanic
            currentMechanicInstance = Instantiate(prefab, mechanicContainer);

            // Configure mechanic with data
            ConfigureMechanic(currentMechanicInstance, mechanic);

            // Play spawn animation
            if (mechanic.spawn_config.spawn_immediately)
            {
                yield return StartCoroutine(PlaySpawnAnimation(
                    currentMechanicInstance,
                    mechanic.spawn_config.spawn_animation,
                    mechanic.spawn_config.spawn_duration
                ));
            }

            Debug.Log($"[MechanicSpawner] Spawned {mechanic.type} mechanic");
        }

        /// <summary>
        /// Get prefab for mechanic type
        /// </summary>
        private GameObject GetPrefabForType(string mechanicType)
        {
            switch (mechanicType.ToLower())
            {
                case "chase": return chaseMechanicPrefab;
                case "collect": return collectMechanicPrefab;
                case "puzzle": return puzzleMechanicPrefab;
                case "build": return buildMechanicPrefab;
                case "explore": return exploreMechanicPrefab;
                case "quiz": return quizMechanicPrefab;
                case "sequence": return sequenceMechanicPrefab;
                case "sort": return sortMechanicPrefab;
                default:
                    Debug.LogWarning($"[MechanicSpawner] Unknown mechanic type: {mechanicType}");
                    return collectMechanicPrefab; // Fallback
            }
        }

        /// <summary>
        /// Configure mechanic instance with parameters
        /// </summary>
        private void ConfigureMechanic(GameObject mechanicInstance, MechanicData mechanic)
        {
            // Try to find mechanic controller component
            var controller = mechanicInstance.GetComponent<IMechanicController>();

            if (controller != null)
            {
                controller.Initialize(mechanic);
                controller.OnCompleted += (success) => CompleteMechanic(success, Time.time - mechanicStartTime);
                controller.OnError += () => errorCount++;
            }
            else
            {
                Debug.LogWarning($"[MechanicSpawner] No IMechanicController found on {mechanic.type} prefab");

                // Fallback: Configure common components
                ConfigureMechanicFallback(mechanicInstance, mechanic);
            }
        }

        /// <summary>
        /// Fallback configuration for mechanics without controller
        /// </summary>
        private void ConfigureMechanicFallback(GameObject mechanicInstance, MechanicData mechanic)
        {
            // This would be implemented based on your specific mechanic structure
            // For example, setting up chase targets, collect items, etc.

            Debug.Log($"[MechanicSpawner] Using fallback configuration for {mechanic.type}");

            // Example: Set up a simple timer-based completion
            StartCoroutine(AutoCompleteMechanic(mechanic.expected_duration_seconds));
        }

        private IEnumerator AutoCompleteMechanic(int duration)
        {
            yield return new WaitForSeconds(duration);

            // Auto-complete with moderate success
            CompleteMechanic(true, duration);
        }

        /// <summary>
        /// Play spawn animation
        /// </summary>
        private IEnumerator PlaySpawnAnimation(GameObject instance, string animationType, float duration)
        {
            if (animationType == "FadeIn")
            {
                // Fade in animation
                var renderers = instance.GetComponentsInChildren<Renderer>();
                float elapsed = 0f;

                while (elapsed < duration)
                {
                    float alpha = Mathf.Lerp(0f, 1f, elapsed / duration);

                    foreach (var renderer in renderers)
                    {
                        foreach (var material in renderer.materials)
                        {
                            if (material.HasProperty("_Color"))
                            {
                                Color color = material.color;
                                color.a = alpha;
                                material.color = color;
                            }
                        }
                    }

                    elapsed += Time.deltaTime;
                    yield return null;
                }
            }
            else
            {
                // Simple delay
                yield return new WaitForSeconds(duration);
            }
        }

        /// <summary>
        /// Complete current mechanic and report performance
        /// </summary>
        public void CompleteMechanic(bool success, float timeTaken)
        {
            if (currentMechanic == null)
            {
                Debug.LogWarning("[MechanicSpawner] No current mechanic to complete");
                return;
            }

            Debug.Log($"[MechanicSpawner] Completed {currentMechanic.type}: " +
                      $"success={success}, time={timeTaken:F1}s, errors={errorCount}");

            // Calculate score
            float score = CalculateScore(success, timeTaken, errorCount, currentMechanic);

            // Report performance to backend
            webSocketClient.ReportPerformance(
                mechanicId: currentMechanic.mechanic_id,
                success: success,
                timeTaken: timeTaken,
                errors: errorCount,
                score: score
            );

            // Store result
            completedMechanics.Add(new MechanicResult
            {
                mechanicId = currentMechanic.mechanic_id,
                type = currentMechanic.type,
                success = success,
                timeTaken = timeTaken,
                errors = errorCount,
                score = score,
                timestamp = DateTime.Now
            });

            // Fire event
            OnMechanicCompleted?.Invoke(currentMechanic, success, timeTaken);

            // Show feedback
            ShowFeedback(success, currentMechanic.feedback);

            // Clean up
            if (currentMechanicInstance != null)
            {
                Destroy(currentMechanicInstance);
                currentMechanicInstance = null;
            }

            currentMechanic = null;
            isProcessingMechanic = false;

            // Process next mechanic if auto-start enabled
            if (autoStartNext && mechanicQueue.Count > 0)
            {
                StartCoroutine(ProcessNextMechanic());
            }
        }

        /// <summary>
        /// Calculate performance score
        /// </summary>
        private float CalculateScore(bool success, float timeTaken, int errors, MechanicData mechanic)
        {
            if (!success) return 0f;

            float baseScore = 1.0f;

            // Time bonus (faster = better, up to 50% of expected time)
            float expectedTime = mechanic.expected_duration_seconds;
            float timeRatio = timeTaken / expectedTime;
            float timeBonus = Mathf.Clamp01(1.5f - timeRatio) * 0.3f;

            // Error penalty
            float errorPenalty = errors * 0.1f;

            float finalScore = Mathf.Clamp01(baseScore + timeBonus - errorPenalty);

            return finalScore;
        }

        /// <summary>
        /// Update UI with mechanic info
        /// </summary>
        private void UpdateUI(MechanicData mechanic)
        {
            if (titleText != null)
            {
                titleText.text = mechanic.title;

                // Apply RTL if needed
                if (mechanic.language == "ar" || mechanic.language == "he")
                {
                    Localization.RTLTextHandler.ConfigureRTL(titleText, mechanic.language);
                }
            }

            if (instructionText != null)
            {
                instructionText.text = mechanic.instruction;

                if (mechanic.language == "ar" || mechanic.language == "he")
                {
                    Localization.RTLTextHandler.ConfigureRTL(instructionText, mechanic.language);
                }
            }

            if (objectiveText != null)
            {
                objectiveText.text = mechanic.learning_objective;
            }
        }

        /// <summary>
        /// Show feedback after mechanic completion
        /// </summary>
        private void ShowFeedback(bool success, FeedbackMessages feedback)
        {
            if (feedbackPanel == null) return;

            // Select random message
            string[] messages = success ? feedback.success : feedback.failure;
            string message = messages[UnityEngine.Random.Range(0, messages.Length)];

            // Display feedback (implement your own UI system here)
            Debug.Log($"[Feedback] {message}");

            StartCoroutine(ShowFeedbackCoroutine(message));
        }

        private IEnumerator ShowFeedbackCoroutine(string message)
        {
            feedbackPanel.SetActive(true);

            // Update feedback text
            var feedbackText = feedbackPanel.GetComponentInChildren<TextMeshProUGUI>();
            if (feedbackText != null)
            {
                feedbackText.text = message;
            }

            // Show for 2 seconds
            yield return new WaitForSeconds(2f);

            feedbackPanel.SetActive(false);
        }

        /// <summary>
        /// Get analytics summary
        /// </summary>
        public MechanicAnalytics GetAnalytics()
        {
            int totalCompleted = completedMechanics.Count;
            int totalSuccess = completedMechanics.FindAll(m => m.success).Count;
            float avgTime = 0f;
            float avgScore = 0f;

            if (totalCompleted > 0)
            {
                foreach (var result in completedMechanics)
                {
                    avgTime += result.timeTaken;
                    avgScore += result.score;
                }
                avgTime /= totalCompleted;
                avgScore /= totalCompleted;
            }

            return new MechanicAnalytics
            {
                totalMechanics = totalCompleted,
                successfulMechanics = totalSuccess,
                successRate = totalCompleted > 0 ? (float)totalSuccess / totalCompleted : 0f,
                averageTimePerMechanic = avgTime,
                averageScore = avgScore,
                results = completedMechanics
            };
        }

        /// <summary>
        /// Manually trigger error (for testing/gameplay)
        /// </summary>
        public void RegisterError()
        {
            errorCount++;
            Debug.Log($"[MechanicSpawner] Error registered. Total: {errorCount}");
        }
    }

    // Interface for mechanic controllers
    public interface IMechanicController
    {
        void Initialize(MechanicData data);
        event Action<bool> OnCompleted;
        event Action OnError;
    }

    // Analytics data structures
    [Serializable]
    public class MechanicResult
    {
        public string mechanicId;
        public string type;
        public bool success;
        public float timeTaken;
        public int errors;
        public float score;
        public DateTime timestamp;
    }

    [Serializable]
    public class MechanicAnalytics
    {
        public int totalMechanics;
        public int successfulMechanics;
        public float successRate;
        public float averageTimePerMechanic;
        public float averageScore;
        public List<MechanicResult> results;
    }
}
