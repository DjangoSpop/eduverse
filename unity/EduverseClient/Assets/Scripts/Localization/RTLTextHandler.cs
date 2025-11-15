using UnityEngine;
using TMPro;
using System.Text;
using System.Text.RegularExpressions;
using System.Collections.Generic;

namespace Eduverse.Localization
{
    /// <summary>
    /// Handles Right-to-Left text rendering for Arabic, Hebrew, and other RTL languages
    ///
    /// Features:
    /// - Automatic RTL detection and configuration
    /// - Mixed RTL/LTR text handling (e.g., Arabic with English numbers)
    /// - TextMeshPro RTL support
    /// - Character normalization for proper display
    /// </summary>
    public class RTLTextHandler : MonoBehaviour
    {
        private static readonly string[] RTL_LANGUAGES = { "ar", "he", "fa", "ur" };  // Arabic, Hebrew, Persian, Urdu

        /// <summary>
        /// Check if a language code represents a right-to-left language
        /// </summary>
        public static bool IsRTLLanguage(string languageCode)
        {
            if (string.IsNullOrEmpty(languageCode))
                return false;

            return System.Array.IndexOf(RTL_LANGUAGES, languageCode.ToLower()) >= 0;
        }

        /// <summary>
        /// Configure TextMeshPro component for RTL display
        /// </summary>
        public static void ConfigureRTL(TextMeshProUGUI textComponent, string languageCode)
        {
            if (textComponent == null)
            {
                Debug.LogWarning("[RTLTextHandler] Null TextMeshPro component");
                return;
            }

            if (IsRTLLanguage(languageCode))
            {
                // Enable RTL rendering
                textComponent.isRightToLeftText = true;

                // Set appropriate alignment
                textComponent.alignment = TextAlignmentOptions.Right;

                // Adjust line spacing for RTL languages
                if (languageCode == "ar")
                {
                    // Arabic needs extra space for diacritics (tashkeel)
                    textComponent.lineSpacing = 1.2f;
                    textComponent.characterSpacing = 0.5f;
                }
                else if (languageCode == "he")
                {
                    // Hebrew spacing
                    textComponent.lineSpacing = 1.1f;
                    textComponent.characterSpacing = 0.3f;
                }

                // Force mesh update
                textComponent.ForceMeshUpdate();

                Debug.Log($"[RTLTextHandler] Configured RTL for {languageCode}");
            }
            else
            {
                // LTR configuration
                textComponent.isRightToLeftText = false;
                textComponent.alignment = TextAlignmentOptions.Left;
                textComponent.lineSpacing = 1.0f;
                textComponent.characterSpacing = 0f;
            }
        }

        /// <summary>
        /// Process mixed RTL/LTR text (e.g., Arabic with English numbers or Latin characters)
        /// </summary>
        public static string ProcessMixedText(string text, string languageCode)
        {
            if (string.IsNullOrEmpty(text))
                return text;

            if (!IsRTLLanguage(languageCode))
                return text;

            // Handle Arabic numerals vs Western numerals
            if (languageCode == "ar")
            {
                // Convert Western numerals to Arabic-Indic numerals
                text = ConvertToArabicNumerals(text);
            }

            // Additional processing can be added here
            return text;
        }

        /// <summary>
        /// Convert Western numerals (0-9) to Arabic-Indic numerals (٠-٩)
        /// </summary>
        private static string ConvertToArabicNumerals(string text)
        {
            if (string.IsNullOrEmpty(text))
                return text;

            char[] westernNumerals = { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9' };
            char[] arabicNumerals = { '٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩' };

            StringBuilder result = new StringBuilder(text);
            for (int i = 0; i < westernNumerals.Length; i++)
            {
                result.Replace(westernNumerals[i], arabicNumerals[i]);
            }

            return result.ToString();
        }

        /// <summary>
        /// Normalize Arabic text for proper display
        /// Removes problematic characters and normalizes variations
        /// </summary>
        public static string NormalizeArabicText(string text)
        {
            if (string.IsNullOrEmpty(text))
                return text;

            // Remove tatweel (elongation character)
            text = text.Replace('\u0640', '\0');

            // Normalize alif variations
            text = text.Replace('\u0649', '\u064A');  // alif maksura → yaa
            text = text.Replace('\u0623', '\u0627');  // alif with hamza above → alif
            text = text.Replace('\u0625', '\u0627');  // alif with hamza below → alif

            // Remove zero-width characters
            text = text.Replace('\u200B', '\0');  // zero width space
            text = text.Replace('\u200C', '\0');  // zero width non-joiner
            text = text.Replace('\u200D', '\0');  // zero width joiner

            // Remove null characters created above
            text = text.Replace("\0", "");

            return text;
        }

        /// <summary>
        /// Get proper text direction for UI layout
        /// </summary>
        public static TextDirection GetTextDirection(string languageCode)
        {
            return IsRTLLanguage(languageCode) ? TextDirection.RightToLeft : TextDirection.LeftToRight;
        }

        /// <summary>
        /// Reverse string for RTL display (fallback for non-TextMeshPro texts)
        /// </summary>
        public static string ReverseForRTL(string text)
        {
            if (string.IsNullOrEmpty(text))
                return text;

            char[] arr = text.ToCharArray();
            System.Array.Reverse(arr);
            return new string(arr);
        }
    }

    /// <summary>
    /// Text direction enum
    /// </summary>
    public enum TextDirection
    {
        LeftToRight,
        RightToLeft
    }
}
