using UnityEngine;
using UnityEngine.Networking;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

#if !UNITY_WEBGL || UNITY_EDITOR
using NativeWebSocket;
#endif

namespace Eduverse.Streaming
{
    /// <summary>
    /// WebSocket client for real-time game mechanic streaming
    ///
    /// Connects to backend streaming engine and receives infinite
    /// adaptive game mechanics based on child behavior.
    ///
    /// Features:
    /// - Automatic reconnection
    /// - Performance tracking and reporting
    /// - Heartbeat/ping-pong keep-alive
    /// - Error handling and recovery
    /// </summary>
    public class StreamingWebSocketClient : MonoBehaviour
    {
        [Header("Connection Settings")]
        [SerializeField] private string backendHost = "localhost";
        [SerializeField] private int backendPort = 8000;
        [SerializeField] private bool useSSL = false;

        [Header("Session Configuration")]
        [SerializeField] private string learnerId;
        [SerializeField] private string curriculumId;
        [SerializeField] private string language = "en";
        [SerializeField] private string initialDifficulty = "medium";

        [Header("Connection Management")]
        [SerializeField] private bool autoReconnect = true;
        [SerializeField] private float reconnectDelay = 3f;
        [SerializeField] private int maxReconnectAttempts = 5;
        [SerializeField] private float heartbeatInterval = 10f;

        // Connection state
        private string sessionId;
        private WebSocket websocket;
        private bool isConnecting = false;
        private int reconnectAttempts = 0;
        private float lastHeartbeat;

        // Events
        public event Action<string> OnConnected;
        public event Action OnDisconnected;
        public event Action<MechanicData> OnMechanicReceived;
        public event Action<string> OnError;
        public event Action<string> OnAcknowledgment;

        // Status
        public bool IsConnected => websocket != null && websocket.State == WebSocketState.Open;
        public string SessionId => sessionId;
        public ConnectionStatus Status { get; private set; } = ConnectionStatus.Disconnected;

        private void Update()
        {
#if !UNITY_WEBGL || UNITY_EDITOR
            // Process WebSocket messages
            if (websocket != null)
            {
                websocket.DispatchMessageQueue();
            }
#endif

            // Send periodic heartbeat
            if (IsConnected && Time.time - lastHeartbeat > heartbeatInterval)
            {
                SendHeartbeat();
            }
        }

        /// <summary>
        /// Initialize and start streaming session
        /// </summary>
        public void StartStreamingSession(string learnerId, string curriculumId, string language = "en")
        {
            this.learnerId = learnerId;
            this.curriculumId = curriculumId;
            this.language = language;

            StartCoroutine(InitializeSession());
        }

        private IEnumerator InitializeSession()
        {
            Status = ConnectionStatus.Initializing;
            Debug.Log($"[StreamingWS] Initializing session for learner {learnerId}");

            // Create session via REST API
            string protocol = useSSL ? "https" : "http";
            string url = $"{protocol}://{backendHost}:{backendPort}/api/streaming/session/start" +
                         $"?learner_id={learnerId}" +
                         $"&curriculum_id={curriculumId}" +
                         $"&language={language}" +
                         $"&initial_difficulty={initialDifficulty}";

            using (UnityWebRequest request = UnityWebRequest.Post(url, ""))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseText = request.downloadHandler.text;
                    var response = JsonConvert.DeserializeObject<SessionStartResponse>(responseText);

                    sessionId = response.session_id;
                    Debug.Log($"[StreamingWS] Session created: {sessionId}");

                    // Connect WebSocket
                    ConnectWebSocket();
                }
                else
                {
                    Debug.LogError($"[StreamingWS] Failed to create session: {request.error}");
                    Status = ConnectionStatus.Error;
                    OnError?.Invoke($"Session creation failed: {request.error}");
                }
            }
        }

        private async void ConnectWebSocket()
        {
            if (isConnecting || IsConnected)
            {
                Debug.LogWarning("[StreamingWS] Already connecting or connected");
                return;
            }

            isConnecting = true;
            Status = ConnectionStatus.Connecting;

            try
            {
                // Build WebSocket URL
                string wsProtocol = useSSL ? "wss" : "ws";
                string wsUrl = $"{wsProtocol}://{backendHost}:{backendPort}/api/streaming/ws/{sessionId}";

                Debug.Log($"[StreamingWS] Connecting to {wsUrl}");

#if !UNITY_WEBGL || UNITY_EDITOR
                websocket = new WebSocket(wsUrl);

                // Event handlers
                websocket.OnOpen += OnWebSocketOpen;
                websocket.OnMessage += OnWebSocketMessage;
                websocket.OnError += OnWebSocketError;
                websocket.OnClose += OnWebSocketClose;

                // Connect
                await websocket.Connect();
#else
                Debug.LogError("[StreamingWS] WebGL WebSocket support requires different implementation");
                Status = ConnectionStatus.Error;
                isConnecting = false;
#endif
            }
            catch (Exception e)
            {
                Debug.LogError($"[StreamingWS] Connection error: {e.Message}");
                Status = ConnectionStatus.Error;
                isConnecting = false;
                OnError?.Invoke($"Connection failed: {e.Message}");

                // Attempt reconnection
                if (autoReconnect && reconnectAttempts < maxReconnectAttempts)
                {
                    StartCoroutine(AttemptReconnect());
                }
            }
        }

        private void OnWebSocketOpen()
        {
            Debug.Log($"[StreamingWS] Connected to session {sessionId}");
            Status = ConnectionStatus.Connected;
            isConnecting = false;
            reconnectAttempts = 0;
            lastHeartbeat = Time.time;

            OnConnected?.Invoke(sessionId);
        }

        private void OnWebSocketMessage(byte[] data)
        {
            try
            {
                string json = Encoding.UTF8.GetString(data);
                var message = JObject.Parse(json);

                string messageType = message["type"]?.ToString();

                switch (messageType)
                {
                    case "mechanic":
                        HandleMechanicMessage(message["data"]);
                        break;

                    case "ack":
                        string ackMsg = message["message"]?.ToString();
                        Debug.Log($"[StreamingWS] Acknowledgment: {ackMsg}");
                        OnAcknowledgment?.Invoke(ackMsg);
                        break;

                    case "pong":
                        // Heartbeat response
                        lastHeartbeat = Time.time;
                        break;

                    case "error":
                        string errorMsg = message["message"]?.ToString();
                        Debug.LogError($"[StreamingWS] Server error: {errorMsg}");
                        OnError?.Invoke(errorMsg);
                        break;

                    case "terminate":
                        string terminateMsg = message["message"]?.ToString();
                        Debug.LogWarning($"[StreamingWS] Session terminated: {terminateMsg}");
                        Disconnect();
                        break;

                    default:
                        Debug.LogWarning($"[StreamingWS] Unknown message type: {messageType}");
                        break;
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[StreamingWS] Error parsing message: {e.Message}");
                OnError?.Invoke($"Message parsing error: {e.Message}");
            }
        }

        private void HandleMechanicMessage(JToken mechanicData)
        {
            try
            {
                var mechanic = mechanicData.ToObject<MechanicData>();
                Debug.Log($"[StreamingWS] Received mechanic: {mechanic.type} (difficulty: {mechanic.difficulty})");

                OnMechanicReceived?.Invoke(mechanic);
            }
            catch (Exception e)
            {
                Debug.LogError($"[StreamingWS] Error deserializing mechanic: {e.Message}");
                OnError?.Invoke($"Mechanic parsing error: {e.Message}");
            }
        }

        private void OnWebSocketError(string error)
        {
            Debug.LogError($"[StreamingWS] WebSocket error: {error}");
            Status = ConnectionStatus.Error;
            OnError?.Invoke(error);
        }

        private void OnWebSocketClose(WebSocketCloseCode code)
        {
            Debug.Log($"[StreamingWS] WebSocket closed: {code}");
            Status = ConnectionStatus.Disconnected;
            OnDisconnected?.Invoke();

            // Attempt reconnection if not intentional disconnect
            if (autoReconnect && code != WebSocketCloseCode.Normal && reconnectAttempts < maxReconnectAttempts)
            {
                StartCoroutine(AttemptReconnect());
            }
        }

        /// <summary>
        /// Send performance data for completed mechanic
        /// </summary>
        public async void ReportPerformance(string mechanicId, bool success, float timeTaken, int errors = 0, float score = 0f)
        {
            if (!IsConnected)
            {
                Debug.LogWarning("[StreamingWS] Cannot report performance - not connected");
                return;
            }

            var performanceData = new
            {
                type = "performance",
                mechanic_id = mechanicId,
                success = success,
                time_taken = timeTaken,
                errors = errors,
                score = score
            };

            string json = JsonConvert.SerializeObject(performanceData);

            try
            {
#if !UNITY_WEBGL || UNITY_EDITOR
                await websocket.SendText(json);
                Debug.Log($"[StreamingWS] Sent performance data for {mechanicId}");
#endif
            }
            catch (Exception e)
            {
                Debug.LogError($"[StreamingWS] Failed to send performance: {e.Message}");
                OnError?.Invoke($"Performance send failed: {e.Message}");
            }
        }

        /// <summary>
        /// Request next mechanic (optional - streaming is automatic)
        /// </summary>
        public async void RequestNextMechanic()
        {
            if (!IsConnected)
            {
                Debug.LogWarning("[StreamingWS] Cannot request mechanic - not connected");
                return;
            }

            var request = new { type = "request_next" };
            string json = JsonConvert.SerializeObject(request);

            try
            {
#if !UNITY_WEBGL || UNITY_EDITOR
                await websocket.SendText(json);
#endif
            }
            catch (Exception e)
            {
                Debug.LogError($"[StreamingWS] Failed to request next: {e.Message}");
            }
        }

        private async void SendHeartbeat()
        {
            if (!IsConnected) return;

            var ping = new { type = "ping" };
            string json = JsonConvert.SerializeObject(ping);

            try
            {
#if !UNITY_WEBGL || UNITY_EDITOR
                await websocket.SendText(json);
                lastHeartbeat = Time.time;
#endif
            }
            catch (Exception e)
            {
                Debug.LogError($"[StreamingWS] Heartbeat failed: {e.Message}");
            }
        }

        private IEnumerator AttemptReconnect()
        {
            reconnectAttempts++;
            Debug.Log($"[StreamingWS] Attempting reconnect ({reconnectAttempts}/{maxReconnectAttempts})...");

            yield return new WaitForSeconds(reconnectDelay);

            ConnectWebSocket();
        }

        public async void Disconnect()
        {
            if (websocket != null && IsConnected)
            {
                Debug.Log("[StreamingWS] Disconnecting...");

#if !UNITY_WEBGL || UNITY_EDITOR
                await websocket.Close();
#endif
            }

            Status = ConnectionStatus.Disconnected;
            websocket = null;
        }

        private async void OnApplicationQuit()
        {
            if (websocket != null)
            {
#if !UNITY_WEBGL || UNITY_EDITOR
                await websocket.Close();
#endif
            }
        }

        private void OnDestroy()
        {
            Disconnect();
        }
    }

    // Data structures
    [Serializable]
    public class SessionStartResponse
    {
        public string session_id;
        public string learner_id;
        public string curriculum_id;
        public string language;
        public string initial_difficulty;
        public string websocket_endpoint;
        public string status;
    }

    [Serializable]
    public class MechanicData
    {
        public string mechanic_id;
        public string session_id;
        public string type;  // chase, collect, puzzle, build, etc.
        public int index;
        public string difficulty;
        public string language;
        public string cultural_context;
        public string generated_at;

        // Core mechanic info
        public string title;
        public string instruction;
        public string learning_objective;

        // Configuration
        public MechanicParameters parameters;
        public SpawnConfig spawn_config;
        public SuccessCriteria success_criteria;
        public Rewards rewards;
        public FeedbackMessages feedback;

        public int expected_duration_seconds;
        public MechanicMetadata metadata;
    }

    [Serializable]
    public class MechanicParameters
    {
        // Common parameters (varies by mechanic type)
        public int target_count;
        public int item_count;
        public int piece_count;
        public float target_speed;
        public float spawn_interval;
        public int time_limit;
        public float scatter_radius;
        public bool show_preview;
        public bool rotation_allowed;
        public int max_active_targets;
        public float catch_radius;
        public int distractor_count;
    }

    [Serializable]
    public class SpawnConfig
    {
        public bool spawn_immediately;
        public string spawn_animation;
        public float spawn_duration;
        public string spawn_positions;
        public string parent_transform;
        public float z_layer;
    }

    [Serializable]
    public class SuccessCriteria
    {
        public string type;
        public float min_score;
        public bool allow_hints;
        public int max_attempts;
        public string min_items_collected;
        public string min_pieces_correct;
    }

    [Serializable]
    public class Rewards
    {
        public int xp;
        public int stars;
        public int coins;
        public bool badge;
    }

    [Serializable]
    public class FeedbackMessages
    {
        public string[] success;
        public string[] failure;
        public string[] hint;
        public string[] encouragement;
    }

    [Serializable]
    public class MechanicMetadata
    {
        public string engagement_level;
        public float success_rate;
        public int consecutive_successes;
    }

    public enum ConnectionStatus
    {
        Disconnected,
        Initializing,
        Connecting,
        Connected,
        Error
    }
}
