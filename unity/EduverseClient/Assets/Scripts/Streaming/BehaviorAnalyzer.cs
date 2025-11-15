using UnityEngine;
using System;
using System.Collections.Generic;
using System.Linq;

namespace Eduverse.Streaming
{
    /// <summary>
    /// Analyzes child behavior patterns to detect engagement levels
    ///
    /// Tracks interactions, response times, and error patterns to identify:
    /// - Boredom (slow responses, distraction)
    /// - Frustration (high errors, giving up)
    /// - Mastery (fast, accurate responses)
    /// - Optimal engagement
    ///
    /// This data is used by the backend to adapt difficulty and content.
    /// </summary>
    public class BehaviorAnalyzer : MonoBehaviour
    {
        [Header("Tracking Settings")]
        [SerializeField] private float inactivityThreshold = 15f;  // Seconds of no input = bored
        [SerializeField] private float fastResponseThreshold = 5f;  // Very fast = mastered
        [SerializeField] private int errorThreshold = 3;  // Errors before frustration
        [SerializeField] private int windowSize = 10;  // Number of interactions to analyze

        [Header("Input Tracking")]
        [SerializeField] private bool trackMouseMovement = true;
        [SerializeField] private bool trackTouchInput = true;
        [SerializeField] private bool trackKeyboard = false;

        // State tracking
        private float lastInteractionTime;
        private Vector2 lastMousePosition;
        private float totalIdleTime;
        private int consecutiveErrors;

        // Interaction history
        private Queue<InteractionEvent> recentInteractions = new Queue<InteractionEvent>();
        private List<BehaviorMetric> behaviorHistory = new List<BehaviorMetric>();

        // Current metrics
        private BehaviorMetric currentMetrics = new BehaviorMetric();

        // Events
        public event Action<EngagementState> OnEngagementChanged;
        public event Action<BehaviorMetric> OnMetricsUpdated;

        // Properties
        public EngagementState CurrentEngagement { get; private set; } = EngagementState.Engaged;
        public float IdleTime => Time.time - lastInteractionTime;
        public BehaviorMetric CurrentMetrics => currentMetrics;

        private void Start()
        {
            lastInteractionTime = Time.time;
            lastMousePosition = Input.mousePosition;
        }

        private void Update()
        {
            // Track input activity
            TrackInputActivity();

            // Update idle time
            float idleTime = Time.time - lastInteractionTime;
            if (idleTime > inactivityThreshold)
            {
                totalIdleTime += Time.deltaTime;
            }

            // Analyze engagement every second
            if (Time.frameCount % 60 == 0)
            {
                AnalyzeEngagement();
            }
        }

        /// <summary>
        /// Track various input methods
        /// </summary>
        private void TrackInputActivity()
        {
            bool hadInteraction = false;

            // Mouse/cursor movement
            if (trackMouseMovement)
            {
                Vector2 currentMousePos = Input.mousePosition;
                if (Vector2.Distance(currentMousePos, lastMousePosition) > 5f)
                {
                    hadInteraction = true;
                    lastMousePosition = currentMousePos;
                }
            }

            // Mouse clicks
            if (Input.GetMouseButtonDown(0) || Input.GetMouseButtonDown(1))
            {
                hadInteraction = true;
                RecordInteraction(InteractionType.Click);
            }

            // Touch input (mobile)
            if (trackTouchInput && Input.touchCount > 0)
            {
                hadInteraction = true;
                RecordInteraction(InteractionType.Touch);
            }

            // Keyboard input
            if (trackKeyboard && Input.anyKeyDown)
            {
                hadInteraction = true;
                RecordInteraction(InteractionType.KeyPress);
            }

            // Update last interaction time
            if (hadInteraction)
            {
                lastInteractionTime = Time.time;
                totalIdleTime = 0f;  // Reset idle accumulator
            }
        }

        /// <summary>
        /// Record an interaction event
        /// </summary>
        public void RecordInteraction(InteractionType type)
        {
            var interaction = new InteractionEvent
            {
                type = type,
                timestamp = Time.time,
                timeSinceLastInteraction = Time.time - lastInteractionTime
            };

            recentInteractions.Enqueue(interaction);

            // Keep only recent interactions
            while (recentInteractions.Count > windowSize)
            {
                recentInteractions.Dequeue();
            }

            // Update metrics
            UpdateMetrics();
        }

        /// <summary>
        /// Record a correct response
        /// </summary>
        public void RecordSuccess(float responseTime)
        {
            consecutiveErrors = 0;  // Reset error streak

            currentMetrics.successCount++;
            currentMetrics.totalResponses++;
            currentMetrics.totalResponseTime += responseTime;

            RecordInteraction(InteractionType.Success);

            Debug.Log($"[BehaviorAnalyzer] Success recorded (response time: {responseTime:F2}s)");
        }

        /// <summary>
        /// Record an error/mistake
        /// </summary>
        public void RecordError(float responseTime = 0f)
        {
            consecutiveErrors++;

            currentMetrics.errorCount++;
            currentMetrics.totalResponses++;

            if (responseTime > 0)
            {
                currentMetrics.totalResponseTime += responseTime;
            }

            RecordInteraction(InteractionType.Error);

            Debug.Log($"[BehaviorAnalyzer] Error recorded (consecutive: {consecutiveErrors})");

            // Check for frustration
            if (consecutiveErrors >= errorThreshold)
            {
                UpdateEngagement(EngagementState.Frustrated);
            }
        }

        /// <summary>
        /// Record when child asks for help/hint
        /// </summary>
        public void RecordHelpRequest()
        {
            currentMetrics.helpRequestCount++;

            RecordInteraction(InteractionType.HelpRequest);

            Debug.Log("[BehaviorAnalyzer] Help requested");
        }

        /// <summary>
        /// Record when child takes a break/pauses
        /// </summary>
        public void RecordPause()
        {
            currentMetrics.pauseCount++;

            RecordInteraction(InteractionType.Pause);

            Debug.Log("[BehaviorAnalyzer] Pause detected");
        }

        /// <summary>
        /// Update behavior metrics
        /// </summary>
        private void UpdateMetrics()
        {
            if (recentInteractions.Count == 0) return;

            // Calculate average response time
            if (currentMetrics.totalResponses > 0)
            {
                currentMetrics.averageResponseTime = currentMetrics.totalResponseTime / currentMetrics.totalResponses;
            }

            // Calculate success rate
            if (currentMetrics.totalResponses > 0)
            {
                currentMetrics.successRate = (float)currentMetrics.successCount / currentMetrics.totalResponses;
            }

            // Calculate interaction rate (interactions per minute)
            var recentArray = recentInteractions.ToArray();
            if (recentArray.Length > 1)
            {
                float timeSpan = recentArray[recentArray.Length - 1].timestamp - recentArray[0].timestamp;
                if (timeSpan > 0)
                {
                    currentMetrics.interactionRate = (recentArray.Length / timeSpan) * 60f;
                }
            }

            // Update idle percentage
            float totalTime = Time.time;
            currentMetrics.idlePercentage = totalIdleTime / totalTime;

            // Fire metrics updated event
            OnMetricsUpdated?.Invoke(currentMetrics);
        }

        /// <summary>
        /// Analyze current behavior and determine engagement state
        /// </summary>
        private void AnalyzeEngagement()
        {
            EngagementState newState = EngagementState.Engaged;  // Default

            // Check for boredom indicators
            if (IdleTime > inactivityThreshold)
            {
                newState = EngagementState.Bored;
            }
            // Check for frustration indicators
            else if (consecutiveErrors >= errorThreshold || currentMetrics.successRate < 0.3f)
            {
                newState = EngagementState.Frustrated;
            }
            // Check for mastery indicators
            else if (currentMetrics.successRate > 0.9f &&
                     currentMetrics.averageResponseTime < fastResponseThreshold &&
                     currentMetrics.totalResponses >= 5)
            {
                newState = EngagementState.Mastered;
            }
            // Check for distraction (low interaction rate despite activity)
            else if (currentMetrics.interactionRate < 10f && IdleTime < inactivityThreshold)
            {
                newState = EngagementState.Distracted;
            }
            // Otherwise, engaged!
            else
            {
                newState = EngagementState.Engaged;
            }

            // Update state if changed
            if (newState != CurrentEngagement)
            {
                UpdateEngagement(newState);
            }
        }

        /// <summary>
        /// Update engagement state
        /// </summary>
        private void UpdateEngagement(EngagementState newState)
        {
            if (newState == CurrentEngagement) return;

            EngagementState previousState = CurrentEngagement;
            CurrentEngagement = newState;

            Debug.Log($"[BehaviorAnalyzer] Engagement changed: {previousState} → {newState}");

            // Fire event
            OnEngagementChanged?.Invoke(newState);

            // Record state change in history
            behaviorHistory.Add(new BehaviorMetric(currentMetrics)
            {
                engagementState = newState,
                timestamp = Time.time
            });
        }

        /// <summary>
        /// Reset metrics (e.g., for new session)
        /// </summary>
        public void ResetMetrics()
        {
            currentMetrics = new BehaviorMetric();
            consecutiveErrors = 0;
            totalIdleTime = 0f;
            lastInteractionTime = Time.time;
            recentInteractions.Clear();

            Debug.Log("[BehaviorAnalyzer] Metrics reset");
        }

        /// <summary>
        /// Get engagement summary for analytics
        /// </summary>
        public EngagementSummary GetEngagementSummary()
        {
            var summary = new EngagementSummary
            {
                currentState = CurrentEngagement,
                currentMetrics = currentMetrics,
                totalSessionTime = Time.time,
                idleTimePercentage = currentMetrics.idlePercentage,
                stateHistory = new Dictionary<EngagementState, float>()
            };

            // Calculate time in each state
            foreach (EngagementState state in Enum.GetValues(typeof(EngagementState)))
            {
                summary.stateHistory[state] = 0f;
            }

            for (int i = 0; i < behaviorHistory.Count - 1; i++)
            {
                var current = behaviorHistory[i];
                var next = behaviorHistory[i + 1];
                float duration = next.timestamp - current.timestamp;

                summary.stateHistory[current.engagementState] += duration;
            }

            // Add current state duration
            if (behaviorHistory.Count > 0)
            {
                var last = behaviorHistory[behaviorHistory.Count - 1];
                summary.stateHistory[last.engagementState] += Time.time - last.timestamp;
            }

            return summary;
        }

        /// <summary>
        /// Export metrics for backend reporting
        /// </summary>
        public string ExportMetricsJSON()
        {
            return JsonUtility.ToJson(currentMetrics, true);
        }
    }

    // Data structures

    [Serializable]
    public class InteractionEvent
    {
        public InteractionType type;
        public float timestamp;
        public float timeSinceLastInteraction;
    }

    public enum InteractionType
    {
        Click,
        Touch,
        KeyPress,
        Success,
        Error,
        HelpRequest,
        Pause
    }

    [Serializable]
    public class BehaviorMetric
    {
        public int totalResponses;
        public int successCount;
        public int errorCount;
        public int helpRequestCount;
        public int pauseCount;

        public float totalResponseTime;
        public float averageResponseTime;
        public float successRate;
        public float interactionRate;  // Interactions per minute
        public float idlePercentage;

        public EngagementState engagementState;
        public float timestamp;

        // Copy constructor
        public BehaviorMetric() { }

        public BehaviorMetric(BehaviorMetric other)
        {
            totalResponses = other.totalResponses;
            successCount = other.successCount;
            errorCount = other.errorCount;
            helpRequestCount = other.helpRequestCount;
            pauseCount = other.pauseCount;
            totalResponseTime = other.totalResponseTime;
            averageResponseTime = other.averageResponseTime;
            successRate = other.successRate;
            interactionRate = other.interactionRate;
            idlePercentage = other.idlePercentage;
            engagementState = other.engagementState;
            timestamp = other.timestamp;
        }
    }

    public enum EngagementState
    {
        Bored,          // Low activity, long idle times
        Frustrated,     // High errors, many help requests
        Distracted,     // Inconsistent interaction patterns
        Engaged,        // Optimal learning state
        Mastered        // High success, fast responses
    }

    [Serializable]
    public class EngagementSummary
    {
        public EngagementState currentState;
        public BehaviorMetric currentMetrics;
        public float totalSessionTime;
        public float idleTimePercentage;
        public Dictionary<EngagementState, float> stateHistory;  // Time spent in each state
    }
}
