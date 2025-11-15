using UnityEngine;
using TMPro;
using System.Collections.Generic;

namespace Eduverse.Localization
{
    /// <summary>
    /// Component that automatically localizes text based on current language
    ///
    /// Usage:
    /// 1. Attach to GameObject with TextMeshProUGUI
    /// 2. Set localizationKey (e.g., "mentor.greeting")
    /// 3. Text will automatically update when language changes
    /// </summary>
    [RequireComponent(typeof(TextMeshProUGUI))]
    public class LocalizedText : MonoBehaviour
    {
        [Header("Localization")]
        [Tooltip("Key for looking up translated text (e.g., 'mentor.greeting')")]
        public string localizationKey;

        [Header("Fallback")]
        [Tooltip("Text to show if translation not found")]
        public string fallbackText = "";

        private TextMeshProUGUI textComponent;

        // Static translation database (in production, load from JSON/server)
        private static Dictionary<string, Dictionary<string, string>> translations = new Dictionary<string, Dictionary<string, string>>
        {
            // Mentor greetings
            {
                "mentor.greeting",
                new Dictionary<string, string>
                {
                    { "en", "Hello! Ready to learn?" },
                    { "ar", "مرحباً! هل أنت مستعد للتعلم؟" },
                    { "fr", "Bonjour! Prêt à apprendre?" },
                    { "es", "¡Hola! ¿Listo para aprender?" },
                    { "zh", "你好!准备好学习了吗?" }
                }
            },

            // Challenge feedback
            {
                "challenge.correct",
                new Dictionary<string, string>
                {
                    { "en", "Great job! ✨" },
                    { "ar", "أحسنت! ✨" },
                    { "fr", "Excellent travail! ✨" },
                    { "es", "¡Buen trabajo! ✨" },
                    { "zh", "做得好! ✨" }
                }
            },
            {
                "challenge.incorrect",
                new Dictionary<string, string>
                {
                    { "en", "Nice try! Let's learn from this." },
                    { "ar", "محاولة جيدة! دعنا نتعلم من هذا." },
                    { "fr", "Bon essai! Apprenons de cela." },
                    { "es", "¡Buen intento! Aprendamos de esto." },
                    { "zh", "不错的尝试!让我们从中学习。" }
                }
            },
            {
                "challenge.hint",
                new Dictionary<string, string>
                {
                    { "en", "💡 Hint: Try thinking about..." },
                    { "ar", "💡 تلميح: حاول التفكير في..." },
                    { "fr", "💡 Indice: Essayez de penser à..." },
                    { "es", "💡 Pista: Intenta pensar en..." },
                    { "zh", "💡 提示:试着想想..." }
                }
            },

            // UI labels
            {
                "ui.continue",
                new Dictionary<string, string>
                {
                    { "en", "Continue" },
                    { "ar", "متابعة" },
                    { "fr", "Continuer" },
                    { "es", "Continuar" },
                    { "zh", "继续" }
                }
            },
            {
                "ui.start",
                new Dictionary<string, string>
                {
                    { "en", "Start" },
                    { "ar", "ابدأ" },
                    { "fr", "Commencer" },
                    { "es", "Comenzar" },
                    { "zh", "开始" }
                }
            },
            {
                "ui.next",
                new Dictionary<string, string>
                {
                    { "en", "Next" },
                    { "ar", "التالي" },
                    { "fr", "Suivant" },
                    { "es", "Siguiente" },
                    { "zh", "下一个" }
                }
            },
            {
                "ui.back",
                new Dictionary<string, string>
                {
                    { "en", "Back" },
                    { "ar", "رجوع" },
                    { "fr": "Retour" },
                    { "es", "Atrás" },
                    { "zh", "返回" }
                }
            },

            // XP and rewards
            {
                "xp.earned",
                new Dictionary<string, string>
                {
                    { "en", "+{0} XP" },
                    { "ar", "+{0} نقطة خبرة" },
                    { "fr", "+{0} XP" },
                    { "es", "+{0} XP" },
                    { "zh", "+{0} 经验值" }
                }
            },
            {
                "level.up",
                new Dictionary<string, string>
                {
                    { "en", "Level Up! 🎉" },
                    { "ar", "ترقية المستوى! 🎉" },
                    { "fr", "Niveau supérieur! 🎉" },
                    { "es", "¡Subir de nivel! 🎉" },
                    { "zh", "升级! 🎉" }
                }
            },

            // Loading messages
            {
                "loading.analyzing",
                new Dictionary<string, string>
                {
                    { "en", "📚 Reading your lesson..." },
                    { "ar", "📚 قراءة درسك..." },
                    { "fr", "📚 Lecture de votre leçon..." },
                    { "es", "📚 Leyendo tu lección..." },
                    { "zh", "📚 正在阅读您的课程..." }
                }
            },
            {
                "loading.building",
                new Dictionary<string, string>
                {
                    { "en", "🌍 Creating your 3D world..." },
                    { "ar", "🌍 إنشاء عالمك ثلاثي الأبعاد..." },
                    { "fr", "🌍 Création de votre monde 3D..." },
                    { "es", "🌍 Creando tu mundo 3D..." },
                    { "zh", "🌍 正在创建您的3D世界..." }
                }
            },

            // Encouragement
            {
                "encouragement.keep_going",
                new Dictionary<string, string>
                {
                    { "en", "You're doing great! Keep going! 💪" },
                    { "ar", "أنت تقوم بعمل رائع! استمر! 💪" },
                    { "fr", "Vous vous débrouillez très bien! Continuez! 💪" },
                    { "es", "¡Lo estás haciendo genial! ¡Sigue así! 💪" },
                    { "zh", "你做得很好!继续! 💪" }
                }
            },
            {
                "encouragement.excellent",
                new Dictionary<string, string>
                {
                    { "en", "Excellent work! ✨" },
                    { "ar", "عمل ممتاز! ✨" },
                    { "fr", "Excellent travail! ✨" },
                    { "es", "¡Excelente trabajo! ✨" },
                    { "zh", "优秀的工作! ✨" }
                }
            }
        };

        private void Awake()
        {
            textComponent = GetComponent<TextMeshProUGUI>();

            if (string.IsNullOrEmpty(fallbackText))
            {
                fallbackText = textComponent.text;
            }
        }

        private void OnEnable()
        {
            // Subscribe to language changes
            if (EduvereLocalization.Instance != null)
            {
                EduvereLocalization.Instance.OnLanguageChanged += OnLanguageChanged;
            }

            // Update text immediately
            UpdateLanguage(EduvereLocalization.Instance?.GetCurrentLanguage() ?? "en");
        }

        private void OnDisable()
        {
            // Unsubscribe from language changes
            if (EduvereLocalization.Instance != null)
            {
                EduvereLocalization.Instance.OnLanguageChanged -= OnLanguageChanged;
            }
        }

        private void OnLanguageChanged(string newLanguage)
        {
            UpdateLanguage(newLanguage);
        }

        /// <summary>
        /// Update text for the specified language
        /// </summary>
        public void UpdateLanguage(string languageCode)
        {
            if (textComponent == null || string.IsNullOrEmpty(localizationKey))
                return;

            string localizedText = GetLocalizedText(localizationKey, languageCode);

            if (!string.IsNullOrEmpty(localizedText))
            {
                // Apply localized text with RTL processing
                textComponent.text = RTLTextHandler.ProcessMixedText(localizedText, languageCode);

                // Configure RTL if needed
                RTLTextHandler.ConfigureRTL(textComponent, languageCode);
            }
            else
            {
                // Use fallback
                textComponent.text = fallbackText;
            }
        }

        /// <summary>
        /// Get localized text for a specific key and language
        /// </summary>
        public static string GetLocalizedText(string key, string languageCode)
        {
            if (string.IsNullOrEmpty(key) || string.IsNullOrEmpty(languageCode))
                return null;

            if (translations.ContainsKey(key))
            {
                var languageDict = translations[key];
                if (languageDict.ContainsKey(languageCode))
                {
                    return languageDict[languageCode];
                }
                else if (languageDict.ContainsKey("en"))
                {
                    // Fallback to English
                    Debug.LogWarning($"[LocalizedText] No translation for '{key}' in {languageCode}, using English");
                    return languageDict["en"];
                }
            }

            Debug.LogWarning($"[LocalizedText] No translation found for key: {key}");
            return null;
        }

        /// <summary>
        /// Add a new translation at runtime
        /// </summary>
        public static void AddTranslation(string key, string languageCode, string text)
        {
            if (!translations.ContainsKey(key))
            {
                translations[key] = new Dictionary<string, string>();
            }

            translations[key][languageCode] = text;
        }

        /// <summary>
        /// Format localized text with parameters (e.g., "+{0} XP")
        /// </summary>
        public static string GetFormattedText(string key, string languageCode, params object[] args)
        {
            string template = GetLocalizedText(key, languageCode);
            if (string.IsNullOrEmpty(template))
                return null;

            try
            {
                return string.Format(template, args);
            }
            catch
            {
                Debug.LogError($"[LocalizedText] Format error for key: {key}");
                return template;
            }
        }

        /// <summary>
        /// Set text with formatting parameters
        /// </summary>
        public void SetFormattedText(params object[] args)
        {
            if (textComponent == null || string.IsNullOrEmpty(localizationKey))
                return;

            string languageCode = EduvereLocalization.Instance?.GetCurrentLanguage() ?? "en";
            string formattedText = GetFormattedText(localizationKey, languageCode, args);

            if (!string.IsNullOrEmpty(formattedText))
            {
                textComponent.text = RTLTextHandler.ProcessMixedText(formattedText, languageCode);
                RTLTextHandler.ConfigureRTL(textComponent, languageCode);
            }
        }
    }
}
