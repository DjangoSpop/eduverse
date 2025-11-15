using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
// using Newtonsoft.Json;  // Commented out - using Unity's JsonUtility instead
using Eduverse.Data;

namespace Eduverse.Core
{
    /// <summary>
    /// API Client for communicating with Eduverse backend.
    /// Handles all HTTP requests and JSON serialization.
    /// </summary>
    public class APIClient : MonoBehaviour
    {
        [Header("Backend Configuration")]
        [SerializeField] private string baseURL = "http://localhost:8000";
        [SerializeField] private int timeoutSeconds = 30;
        [SerializeField] private bool logRequests = true;

        private static APIClient _instance;
        public static APIClient Instance
        {
            get
            {
                if (_instance == null)
                {
                    GameObject go = new GameObject("APIClient");
                    _instance = go.AddComponent<APIClient>();
                    DontDestroyOnLoad(go);
                }
                return _instance;
            }
        }

        private void Awake()
        {
            if (_instance != null && _instance != this)
            {
                Destroy(gameObject);
                return;
            }

            _instance = this;
            DontDestroyOnLoad(gameObject);
        }

        #region GET Requests

        /// <summary>
        /// Perform GET request and deserialize response.
        /// </summary>
        public IEnumerator Get<T>(string endpoint, Action<T> onSuccess, Action<string> onError)
        {
            string url = $"{baseURL}{endpoint}";

            if (logRequests)
                Debug.Log($"[API] GET {url}");

            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                request.timeout = timeoutSeconds;
                request.SetRequestHeader("Accept", "application/json");

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        string json = request.downloadHandler.text;

                        if (logRequests)
                            Debug.Log($"[API] Response: {json.Substring(0, Mathf.Min(200, json.Length))}...");

                        T data = JsonUtility.FromJson<T>(json);
                        onSuccess?.Invoke(data);
                    }
                    catch (Exception e)
                    {
                        Debug.LogError($"[API] JSON Parse Error: {e.Message}");
                        onError?.Invoke($"Failed to parse response: {e.Message}");
                    }
                }
                else
                {
                    string error = $"{request.error} - {request.downloadHandler.text}";
                    Debug.LogError($"[API] Request Failed: {error}");
                    onError?.Invoke(error);
                }
            }
        }

        #endregion

        #region POST Requests

        /// <summary>
        /// Perform POST request with JSON body.
        /// </summary>
        public IEnumerator Post<TRequest, TResponse>(
            string endpoint,
            TRequest data,
            Action<TResponse> onSuccess,
            Action<string> onError)
        {
            string url = $"{baseURL}{endpoint}";
            string json = JsonUtility.ToJson(data);

            if (logRequests)
                Debug.Log($"[API] POST {url}\nBody: {json}");

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.SetRequestHeader("Accept", "application/json");
                request.timeout = timeoutSeconds;

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        string responseJson = request.downloadHandler.text;

                        if (logRequests)
                            Debug.Log($"[API] Response: {responseJson}");

                        TResponse response = JsonUtility.FromJson<TResponse>(responseJson);
                        onSuccess?.Invoke(response);
                    }
                    catch (Exception e)
                    {
                        Debug.LogError($"[API] JSON Parse Error: {e.Message}");
                        onError?.Invoke($"Failed to parse response: {e.Message}");
                    }
                }
                else
                {
                    string error = $"{request.error} - {request.downloadHandler.text}";
                    Debug.LogError($"[API] Request Failed: {error}");
                    onError?.Invoke(error);
                }
            }
        }

        /// <summary>
        /// POST without expecting a response body (returns simple message).
        /// </summary>
        public IEnumerator PostSimple<TRequest>(
            string endpoint,
            TRequest data,
            Action onSuccess,
            Action<string> onError)
        {
            string url = $"{baseURL}{endpoint}";
            string json = JsonUtility.ToJson(data);

            if (logRequests)
                Debug.Log($"[API] POST {url}\nBody: {json}");

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.timeout = timeoutSeconds;

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    if (logRequests)
                        Debug.Log($"[API] Request successful");

                    onSuccess?.Invoke();
                }
                else
                {
                    string error = $"{request.error} - {request.downloadHandler.text}";
                    Debug.LogError($"[API] Request Failed: {error}");
                    onError?.Invoke(error);
                }
            }
        }

        #endregion

        #region Lesson Endpoints

        /// <summary>
        /// Fetch complete lesson specification.
        /// This is the main endpoint Unity calls to get the world data.
        /// </summary>
        public IEnumerator GetLesson(string lessonId, Action<SceneSpecification> onSuccess, Action<string> onError)
        {
            yield return Get($"/api/lessons/{lessonId}", onSuccess, onError);
        }

        /// <summary>
        /// Get lesson preview (lighter weight).
        /// </summary>
        public IEnumerator GetLessonPreview(string lessonId, Action<object> onSuccess, Action<string> onError)
        {
            yield return Get($"/api/lessons/{lessonId}/preview", onSuccess, onError);
        }

        #endregion

        #region Session Endpoints

        /// <summary>
        /// Start a new learning session.
        /// Call this when the child begins playing a lesson.
        /// </summary>
        public IEnumerator StartSession(
            string learnerId,
            string lessonId,
            Action<SessionStartResponse> onSuccess,
            Action<string> onError)
        {
            var request = new SessionStartRequest
            {
                learner_id = learnerId,
                lesson_id = lessonId,
                device_info = new System.Collections.Generic.Dictionary<string, string>
                {
                    { "platform", Application.platform.ToString() },
                    { "device_model", SystemInfo.deviceModel },
                    { "os", SystemInfo.operatingSystem }
                }
            };

            yield return Post("/api/sessions/start", request, onSuccess, onError);
        }

        /// <summary>
        /// Log an event during gameplay.
        /// </summary>
        public IEnumerator LogEvent(
            string sessionId,
            string eventType,
            System.Collections.Generic.Dictionary<string, object> eventData,
            bool success,
            int xpEarned,
            Action onSuccess,
            Action<string> onError)
        {
            var request = new SessionEventRequest
            {
                session_id = sessionId,
                event_type = eventType,
                event_data = eventData,
                success = success,
                xp_earned = xpEarned
            };

            yield return PostSimple("/api/sessions/event", request, onSuccess, onError);
        }

        /// <summary>
        /// End the learning session.
        /// Call when child finishes or quits the lesson.
        /// </summary>
        public IEnumerator EndSession(
            string sessionId,
            float completionPercentage,
            string status,
            Action onSuccess,
            Action<string> onError)
        {
            var request = new SessionEndRequest
            {
                session_id = sessionId,
                completion_percentage = completionPercentage,
                status = status
            };

            yield return PostSimple("/api/sessions/end", request, onSuccess, onError);
        }

        #endregion

        #region Learner Endpoints

        /// <summary>
        /// Get learner profile.
        /// </summary>
        public IEnumerator GetLearner(string learnerId, Action<LearnerProfile> onSuccess, Action<string> onError)
        {
            yield return Get($"/api/learners/{learnerId}", onSuccess, onError);
        }

        #endregion

        #region Configuration

        public void SetBaseURL(string url)
        {
            baseURL = url;
            Debug.Log($"[API] Base URL set to: {baseURL}");
        }

        public string GetBaseURL()
        {
            return baseURL;
        }

        #endregion
    }
}
