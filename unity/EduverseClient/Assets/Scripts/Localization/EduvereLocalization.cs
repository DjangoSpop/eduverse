using UnityEngine;
using TMPro;
using System.Collections.Generic;
using System.Linq;

namespace Eduverse.Localization
{
    /// <summary>
    /// Localization manager for Eduverse
    ///
    /// Handles:
    /// - Language switching
    /// - RTL/LTR text configuration
    /// - Font management per language
    /// - Translation loading
    /// - UI layout adjustments
    /// </summary>
    public class EduvereLocalization : MonoBehaviour
    {
        [System.Serializable]
        public class LanguageData
        {
            public string code;  // e.g., "ar", "en"
            public string name;  // e.g., "العربية", "English"
            public string direction;  // "rtl" or "ltr"
            public TMP_FontAsset customFont;  // Language-specific font
            public string culturalContext;  // e.g., "middle_eastern", "western"
        }

        [Header("Supported Languages")]
        public List<LanguageData> supportedLanguages = new List<LanguageData>();

        [Header("Default Language")]
        public string defaultLanguage = "en";

        [Header("Debug")]
        public bool enableDebugLogs = true;

        private string currentLanguage;
        private Dictionary<string, LanguageData> languageMap = new Dictionary<string, LanguageData>();

        // Singleton instance
        private static EduvereLocalization _instance;
        public static EduvereLocalization Instance
        {
            get
            {
                if (_instance == null)
                {
                    GameObject go = new GameObject("EduvereLocalization");
                    _instance = go.AddComponent<EduvereLocalization>();
                    DontDestroyOnLoad(go);
                }
                return _instance;
            }
        }

        // Events
        public event System.Action<string> OnLanguageChanged;

        private void Awake()
        {
            if (_instance != null && _instance != this)
            {
                Destroy(gameObject);
                return;
            }

            _instance = this;
            DontDestroyOnLoad(gameObject);

            InitializeLanguages();
        }

        private void Start()
        {
            // Load saved language preference or use default
            string savedLanguage = PlayerPrefs.GetString("PreferredLanguage", defaultLanguage);
            SetLanguage(savedLanguage);
        }

        /// <summary>
        /// Initialize language map from configured languages
        /// </summary>
        private void InitializeLanguages()
        {
            languageMap.Clear();

            foreach (var lang in supportedLanguages)
            {
                if (!languageMap.ContainsKey(lang.code))
                {
                    languageMap[lang.code] = lang;
                }
            }

            // Ensure default languages exist
            if (!languageMap.ContainsKey("en"))
            {
                languageMap["en"] = new LanguageData
                {
                    code = "en",
                    name = "English",
                    direction = "ltr",
                    culturalContext = "western"
                };
            }

            if (!languageMap.ContainsKey("ar"))
            {
                languageMap["ar"] = new LanguageData
                {
                    code = "ar",
                    name = "العربية",
                    direction = "rtl",
                    culturalContext = "middle_eastern"
                };
            }

            if (enableDebugLogs)
                Debug.Log($"[EduvereLocalization] Initialized {languageMap.Count} languages");
        }

        /// <summary>
        /// Set current language and update all UI
        /// </summary>
        public void SetLanguage(string languageCode)
        {
            if (string.IsNullOrEmpty(languageCode))
            {
                Debug.LogWarning("[EduvereLocalization] Invalid language code");
                return;
            }

            if (!languageMap.ContainsKey(languageCode))
            {
                Debug.LogWarning($"[EduvereLocalization] Unsupported language: {languageCode}, falling back to {defaultLanguage}");
                languageCode = defaultLanguage;
            }

            currentLanguage = languageCode;

            // Save preference
            PlayerPrefs.SetString("PreferredLanguage", languageCode);
            PlayerPrefs.Save();

            // Update all text components in scene
            UpdateAllText(languageCode);

            // Apply language-specific fonts
            ApplyLanguageFonts(languageCode);

            // Notify listeners
            OnLanguageChanged?.Invoke(languageCode);

            if (enableDebugLogs)
                Debug.Log($"[EduvereLocalization] Language set to: {languageCode}");
        }

        /// <summary>
        /// Update all TextMeshPro components in the scene
        /// </summary>
        private void UpdateAllText(string languageCode)
        {
            TextMeshProUGUI[] allText = FindObjectsOfType<TextMeshProUGUI>(true); // Include inactive

            foreach (var tmp in allText)
            {
                RTLTextHandler.ConfigureRTL(tmp, languageCode);
            }

            if (enableDebugLogs)
                Debug.Log($"[EduvereLocalization] Updated {allText.Length} text components");
        }

        /// <summary>
        /// Apply language-specific fonts to all text components
        /// </summary>
        private void ApplyLanguageFonts(string languageCode)
        {
            if (!languageMap.ContainsKey(languageCode))
                return;

            LanguageData langData = languageMap[languageCode];

            if (langData.customFont != null)
            {
                TextMeshProUGUI[] allText = FindObjectsOfType<TextMeshProUGUI>(true);

                foreach (var tmp in allText)
                {
                    // Only apply font if component doesn't have a specific font assigned
                    // (Allow per-component font overrides)
                    if (tmp.font == null || tmp.font.name.Contains("Default"))
                    {
                        tmp.font = langData.customFont;
                    }
                }

                if (enableDebugLogs)
                    Debug.Log($"[EduvereLocalization] Applied {langData.customFont.name} font");
            }
        }

        /// <summary>
        /// Get current language code
        /// </summary>
        public string GetCurrentLanguage()
        {
            return currentLanguage ?? defaultLanguage;
        }

        /// <summary>
        /// Check if current language is RTL
        /// </summary>
        public bool IsRTL()
        {
            return RTLTextHandler.IsRTLLanguage(GetCurrentLanguage());
        }

        /// <summary>
        /// Get current language data
        /// </summary>
        public LanguageData GetCurrentLanguageData()
        {
            string lang = GetCurrentLanguage();
            return languageMap.ContainsKey(lang) ? languageMap[lang] : null;
        }

        /// <summary>
        /// Get all supported languages
        /// </summary>
        public List<LanguageData> GetSupportedLanguages()
        {
            return languageMap.Values.ToList();
        }

        /// <summary>
        /// Check if a language is supported
        /// </summary>
        public bool IsLanguageSupported(string languageCode)
        {
            return languageMap.ContainsKey(languageCode);
        }

        /// <summary>
        /// Get localized text direction
        /// </summary>
        public TextDirection GetTextDirection()
        {
            return RTLTextHandler.GetTextDirection(GetCurrentLanguage());
        }

        /// <summary>
        /// Register a new language at runtime
        /// </summary>
        public void RegisterLanguage(LanguageData languageData)
        {
            if (languageData == null || string.IsNullOrEmpty(languageData.code))
            {
                Debug.LogWarning("[EduvereLocalization] Invalid language data");
                return;
            }

            if (languageMap.ContainsKey(languageData.code))
            {
                Debug.LogWarning($"[EduvereLocalization] Language {languageData.code} already registered, updating...");
            }

            languageMap[languageData.code] = languageData;
            supportedLanguages.Add(languageData);

            if (enableDebugLogs)
                Debug.Log($"[EduvereLocalization] Registered language: {languageData.code}");
        }
    }
}
