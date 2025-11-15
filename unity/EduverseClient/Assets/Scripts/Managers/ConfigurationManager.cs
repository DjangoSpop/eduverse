using UnityEngine;

namespace Eduverse.Managers
{
    /// <summary>
    /// Manages game configuration and settings.
    /// Stores learner ID, backend URL, and other configuration.
    /// </summary>
    public class ConfigurationManager : MonoBehaviour
    {
        [Header("Backend Configuration")]
        [SerializeField] private string backendURL = "http://localhost:8000";
        [SerializeField] private bool useLocalBackend = true;
        [SerializeField] private string productionURL = "https://api.eduverse.com";

        [Header("Learner Configuration")]
        [SerializeField] private string defaultLearnerId = "test-learner-123";
        [SerializeField] private string currentLearnerId;

        [Header("Lesson Configuration")]
        [SerializeField] private string defaultLessonId = "test-lesson-456";
        [SerializeField] private string currentLessonId;

        [Header("Debug Settings")]
        [SerializeField] private bool enableDebugLogs = true;
        [SerializeField] private bool mockAPIResponses = false;

        private static ConfigurationManager _instance;
        public static ConfigurationManager Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = FindObjectOfType<ConfigurationManager>();

                    if (_instance == null)
                    {
                        GameObject go = new GameObject("ConfigurationManager");
                        _instance = go.AddComponent<ConfigurationManager>();
                        DontDestroyOnLoad(go);
                    }
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

            Initialize();
        }

        private void Initialize()
        {
            // Set initial values
            if (string.IsNullOrEmpty(currentLearnerId))
                currentLearnerId = defaultLearnerId;

            if (string.IsNullOrEmpty(currentLessonId))
                currentLessonId = defaultLessonId;

            // Configure API client
            ConfigureAPIClient();

            Debug.Log("[Configuration] Initialized");
            Debug.Log($"[Configuration] Backend URL: {GetBackendURL()}");
            Debug.Log($"[Configuration] Learner ID: {currentLearnerId}");
        }

        private void ConfigureAPIClient()
        {
            string url = GetBackendURL();

            var apiClient = Core.APIClient.Instance;
            if (apiClient != null)
            {
                apiClient.SetBaseURL(url);
            }
        }

        #region Public Interface

        public string GetBackendURL()
        {
            return useLocalBackend ? backendURL : productionURL;
        }

        public void SetBackendURL(string url, bool isLocal = false)
        {
            if (isLocal)
            {
                backendURL = url;
                useLocalBackend = true;
            }
            else
            {
                productionURL = url;
                useLocalBackend = false;
            }

            ConfigureAPIClient();
        }

        public string GetLearnerId()
        {
            return currentLearnerId;
        }

        public void SetLearnerId(string id)
        {
            currentLearnerId = id;
            PlayerPrefs.SetString("LearnerId", id);
            PlayerPrefs.Save();

            Debug.Log($"[Configuration] Learner ID set to: {id}");
        }

        public string GetLessonId()
        {
            return currentLessonId;
        }

        public void SetLessonId(string id)
        {
            currentLessonId = id;
            Debug.Log($"[Configuration] Lesson ID set to: {id}");
        }

        public bool IsDebugEnabled()
        {
            return enableDebugLogs;
        }

        public bool IsMockMode()
        {
            return mockAPIResponses;
        }

        #endregion

        #region PlayerPrefs Integration

        /// <summary>
        /// Load settings from PlayerPrefs.
        /// </summary>
        public void LoadSettings()
        {
            if (PlayerPrefs.HasKey("LearnerId"))
            {
                currentLearnerId = PlayerPrefs.GetString("LearnerId");
            }

            if (PlayerPrefs.HasKey("BackendURL"))
            {
                backendURL = PlayerPrefs.GetString("BackendURL");
            }

            if (PlayerPrefs.HasKey("UseLocalBackend"))
            {
                useLocalBackend = PlayerPrefs.GetInt("UseLocalBackend") == 1;
            }

            ConfigureAPIClient();

            Debug.Log("[Configuration] Settings loaded from PlayerPrefs");
        }

        /// <summary>
        /// Save settings to PlayerPrefs.
        /// </summary>
        public void SaveSettings()
        {
            PlayerPrefs.SetString("LearnerId", currentLearnerId);
            PlayerPrefs.SetString("BackendURL", backendURL);
            PlayerPrefs.SetInt("UseLocalBackend", useLocalBackend ? 1 : 0);
            PlayerPrefs.Save();

            Debug.Log("[Configuration] Settings saved to PlayerPrefs");
        }

        #endregion
    }
}
