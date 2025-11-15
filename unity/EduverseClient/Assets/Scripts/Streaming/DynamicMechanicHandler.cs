using UnityEngine;
using UnityEngine.Networking;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using TMPro;

namespace Eduverse.Streaming
{
    /// <summary>
    /// Handles real-time game mechanic streaming from backend
    /// Simplified version without WebSocket dependencies - uses UnityWebRequest for now
    ///
    /// Features:
    /// - Behavior tracking and reporting
    /// - Dynamic mechanic reception
    /// - Automatic spawning of new content
    /// - Encouragement display
    /// </summary>
    public class DynamicMechanicHandler : MonoBehaviour
    {
        [Header("Configuration")]
        public string backendURL = "http://localhost:8000";
        public float behaviorUpdateInterval = 5f;  // Send updates every 5 seconds

        [Header("Child Profile")]
        public string childId = "test_child";
        public string language = "en";
        public int age = 8;
        public string childName = "friend";

        [Header("References")]
        public TextMeshProUGUI mentorDialogue;
        public Transform spawnParent;

        [Header("Behavior Tracking")]
        public float idleThreshold = 30f;  // Seconds before boredom

        // Behavior metrics
        private float lastInteractionTime;
        private int errorStreak = 0;
        private int correctStreak = 0;
        private int hintsUsed = 0;
        private List<float> responseTimes = new List<float>();
        private int explorationCount = 0;
        private float sceneStartTime;

        // Streaming state
        private bool isPolling = false;
        private int mechanicsReceived = 0;

        // Events
        public event Action<DynamicMechanic> OnNewMechanicReceived;
        public event Action<string> OnEncouragementReceived;

        private void Start()
        {
            lastInteractionTime = Time.time;
            sceneStartTime = Time.time;

            // Start polling for mechanics (simplified approach without WebSocket)
            StartCoroutine(PollForMechanics());
        }

        /// <summary>
        /// Poll backend for new mechanics based on behavior
        /// Simplified alternative to WebSocket streaming
        /// </summary>
        private IEnumerator PollForMechanics()
        {
            isPolling = true;

            while (isPolling)
            {
                yield return new WaitForSeconds(behaviorUpdateInterval);

                // Analyze current behavior
                var behaviorData = GetCurrentBehavior();

                // Check if we should request a new mechanic
                if (ShouldRequestMechanic(behaviorData))
                {
                    yield return RequestNewMechanic(behaviorData);
                }
            }
        }

        /// <summary>
        /// Get current behavior metrics
        /// </summary>
        private Dictionary<string, object> GetCurrentBehavior()
        {
            float idleSeconds = Time.time - lastInteractionTime;
            float timeInScene = Time.time - sceneStartTime;
            float avgResponseTime = responseTimes.Count > 0
                ? CalculateAverage(responseTimes)
                : 0f;

            return new Dictionary<string, object>
            {
                { "idle_seconds", idleSeconds },
                { "error_streak", errorStreak },
                { "correct_streak", correctStreak },
                { "hints_used", hintsUsed },
                { "avg_response_time", avgResponseTime },
                { "exploration_count", explorationCount },
                { "time_in_scene", timeInScene }
            };
        }

        /// <summary>
        /// Check if we should request a new mechanic
        /// </summary>
        private bool ShouldRequestMechanic(Dictionary<string, object> behavior)
        {
            float idleSeconds = (float)behavior["idle_seconds"];
            int errorStreak = (int)behavior["error_streak"];
            int correctStreak = (int)behavior["correct_streak"];
            float timeInScene = (float)behavior["time_in_scene"];

            // Boredom detection
            if (idleSeconds > idleThreshold)
            {
                Debug.Log("[DynamicMechanic] Boredom detected, requesting new mechanic");
                return true;
            }

            // Mastery detection
            if (correctStreak >= 3)
            {
                Debug.Log("[DynamicMechanic] Mastery detected, requesting harder content");
                return true;
            }

            // Time-based refresh
            if (timeInScene > 300 && mechanicsReceived == 0)  // 5 minutes
            {
                Debug.Log("[DynamicMechanic] Time for fresh content");
                return true;
            }

            return false;
        }

        /// <summary>
        /// Request a new mechanic from backend
        /// </summary>
        private IEnumerator RequestNewMechanic(Dictionary<string, object> behavior)
        {
            string mechanicType = DetermineMechanicType(behavior);

            string url = $"{backendURL}/api/streaming/test-mechanic" +
                        $"?language={language}" +
                        $"&mechanic_type={mechanicType}" +
                        $"&age={age}" +
                        $"&topic=learning";

            Debug.Log($"[DynamicMechanic] Requesting {mechanicType} mechanic from {url}");

            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                request.SetRequestHeader("Content-Type", "application/json");

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        string json = request.downloadHandler.text;
                        var response = JsonUtility.FromJson<MechanicResponse>(json);

                        if (response != null && response.status == "success")
                        {
                            HandleNewMechanic(response.mechanic);
                        }
                        else
                        {
                            Debug.LogWarning($"[DynamicMechanic] Mechanic generation failed");
                        }
                    }
                    catch (Exception e)
                    {
                        Debug.LogError($"[DynamicMechanic] Parse error: {e.Message}");
                    }
                }
                else
                {
                    Debug.LogError($"[DynamicMechanic] Request failed: {request.error}");
                }
            }
        }

        /// <summary>
        /// Determine what type of mechanic to request based on behavior
        /// </summary>
        private string DetermineMechanicType(Dictionary<string, object> behavior)
        {
            int errorStreak = (int)behavior["error_streak"];
            int correctStreak = (int)behavior["correct_streak"];
            float idleSeconds = (float)behavior["idle_seconds"];

            if (idleSeconds > idleThreshold)
                return "exciting_chase";
            else if (errorStreak >= 2)
                return "supportive_helper";
            else if (correctStreak >= 3)
                return "advanced_puzzle";
            else
                return "exploratory_quest";
        }

        /// <summary>
        /// Handle a newly received mechanic
        /// </summary>
        private void HandleNewMechanic(DynamicMechanic mechanic)
        {
            Debug.Log($"[DynamicMechanic] Received: {mechanic.name}");

            mechanicsReceived++;

            // Show mentor dialogue
            if (mentorDialogue != null && !string.IsNullOrEmpty(mechanic.dialogue))
            {
                mentorDialogue.text = mechanic.dialogue;
            }

            // Spawn mechanic in game world
            StartCoroutine(SpawnMechanic(mechanic));

            // Fire event
            OnNewMechanicReceived?.Invoke(mechanic);

            // Reset boredom timer
            RecordInteraction();
        }

        /// <summary>
        /// Spawn the mechanic in the game world
        /// </summary>
        private IEnumerator SpawnMechanic(DynamicMechanic mechanic)
        {
            // Try to load prefab from Resources
            GameObject prefab = Resources.Load<GameObject>($"Prefabs/{mechanic.prefab_key}");

            if (prefab == null)
            {
                // Create simple placeholder
                prefab = GameObject.CreatePrimitive(PrimitiveType.Cube);
                prefab.name = mechanic.prefab_key;
                Debug.LogWarning($"[DynamicMechanic] Prefab not found: {mechanic.prefab_key}, using cube");
            }

            // Spawn at specified position
            Vector3 spawnPos = new Vector3(
                mechanic.spawn_position.x,
                mechanic.spawn_position.y,
                mechanic.spawn_position.z
            );

            GameObject instance = Instantiate(prefab, spawnPos, Quaternion.identity, spawnParent);
            instance.name = mechanic.name;

            // Add a simple interaction component
            var interactable = instance.AddComponent<SimpleMechanicInteraction>();
            interactable.mechanic = mechanic;
            interactable.handler = this;

            Debug.Log($"[DynamicMechanic] Spawned {mechanic.name} at {spawnPos}");

            yield return null;
        }

        /// <summary>
        /// Record an interaction (resets boredom timer)
        /// </summary>
        public void RecordInteraction()
        {
            lastInteractionTime = Time.time;
        }

        /// <summary>
        /// Record a correct answer
        /// </summary>
        public void RecordCorrectAnswer(float responseTime)
        {
            correctStreak++;
            errorStreak = 0;
            responseTimes.Add(responseTime);
            RecordInteraction();

            Debug.Log($"[DynamicMechanic] Correct! Streak: {correctStreak}");
        }

        /// <summary>
        /// Record an error
        /// </summary>
        public void RecordError()
        {
            errorStreak++;
            correctStreak = 0;
            RecordInteraction();

            Debug.Log($"[DynamicMechanic] Error. Streak: {errorStreak}");
        }

        /// <summary>
        /// Record hint usage
        /// </summary>
        public void RecordHintUsed()
        {
            hintsUsed++;
        }

        /// <summary>
        /// Record exploration
        /// </summary>
        public void RecordExploration()
        {
            explorationCount++;
            RecordInteraction();
        }

        private float CalculateAverage(List<float> values)
        {
            if (values.Count == 0) return 0f;
            float sum = 0f;
            foreach (float val in values)
                sum += val;
            return sum / values.Count;
        }

        private void OnDestroy()
        {
            isPolling = false;
        }
    }

    /// <summary>
    /// Simple interaction component for spawned mechanics
    /// </summary>
    public class SimpleMechanicInteraction : MonoBehaviour
    {
        public DynamicMechanic mechanic;
        public DynamicMechanicHandler handler;

        private void OnMouseDown()
        {
            // Simple click interaction
            if (handler != null)
            {
                handler.RecordInteraction();
                handler.RecordCorrectAnswer(1.0f);

                // Show success feedback
                Debug.Log(mechanic.success_feedback);

                // Destroy after interaction (simple approach)
                Destroy(gameObject, 0.5f);
            }
        }
    }

    // Data models (using Unity's JsonUtility which requires [Serializable])
    [Serializable]
    public class MechanicResponse
    {
        public string status;
        public DynamicMechanic mechanic;
        public string language;
        public string mechanic_type;
    }

    [Serializable]
    public class DynamicMechanic
    {
        public string type;
        public string name;
        public string description;
        public string prefab_key;
        public string dialogue;
        public string learning_objective;
        public int difficulty;
        public int estimated_duration;
        public int reward_xp;
        public string[] instructions;
        public string success_feedback;
        public string retry_hint;
        public SpawnPosition spawn_position;
    }

    [Serializable]
    public class SpawnPosition
    {
        public float x;
        public float y;
        public float z;
    }
}
