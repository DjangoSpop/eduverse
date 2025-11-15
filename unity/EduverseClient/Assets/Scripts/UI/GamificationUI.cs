using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace Eduverse.UI
{
    /// <summary>
    /// Displays XP, level, and progress to the learner.
    /// </summary>
    public class GamificationUI : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private TextMeshProUGUI xpText;
        [SerializeField] private TextMeshProUGUI levelText;
        [SerializeField] private Slider xpProgressBar;
        [SerializeField] private GameObject levelUpEffect;

        [Header("XP Animation")]
        [SerializeField] private GameObject xpPopupPrefab;
        [SerializeField] private Transform xpPopupContainer;

        private int currentXP = 0;
        private int currentLevel = 1;
        private int xpToNextLevel = 100;

        private void Start()
        {
            UpdateUI();
        }

        /// <summary>
        /// Add XP and update UI.
        /// </summary>
        public void AddXP(int amount, string reason = "")
        {
            currentXP += amount;

            // Show XP popup
            ShowXPPopup(amount, reason);

            // Check for level up
            CheckLevelUp();

            // Update UI
            UpdateUI();

            Debug.Log($"[Gamification] +{amount} XP ({reason}). Total: {currentXP}");
        }

        /// <summary>
        /// Check if player leveled up.
        /// </summary>
        private void CheckLevelUp()
        {
            while (currentXP >= xpToNextLevel)
            {
                currentLevel++;
                currentXP -= xpToNextLevel;

                // Calculate next level requirement (exponential)
                xpToNextLevel = Mathf.RoundToInt(100 * Mathf.Pow(currentLevel, 1.5f));

                // Show level up effect
                ShowLevelUpEffect();

                Debug.Log($"[Gamification] LEVEL UP! Now level {currentLevel}");
            }
        }

        /// <summary>
        /// Update all UI elements.
        /// </summary>
        private void UpdateUI()
        {
            if (xpText != null)
                xpText.text = $"{currentXP} / {xpToNextLevel} XP";

            if (levelText != null)
                levelText.text = $"Level {currentLevel}";

            if (xpProgressBar != null)
            {
                float progress = (float)currentXP / xpToNextLevel;
                xpProgressBar.value = progress;
            }
        }

        /// <summary>
        /// Show floating XP popup.
        /// </summary>
        private void ShowXPPopup(int amount, string reason)
        {
            if (xpPopupPrefab == null || xpPopupContainer == null)
                return;

            GameObject popup = Instantiate(xpPopupPrefab, xpPopupContainer);
            var text = popup.GetComponentInChildren<TextMeshProUGUI>();

            if (text != null)
            {
                if (string.IsNullOrEmpty(reason))
                    text.text = $"+{amount} XP";
                else
                    text.text = $"+{amount} XP\n{reason}";
            }

            // Animate popup
            LeanTween.moveY(popup.GetComponent<RectTransform>(), 100f, 1.5f)
                .setEaseOutQuad();

            LeanTween.alphaCanvas(popup.GetComponent<CanvasGroup>(), 0f, 1.5f)
                .setDelay(0.5f)
                .setOnComplete(() => Destroy(popup));
        }

        /// <summary>
        /// Show level up celebration effect.
        /// </summary>
        private void ShowLevelUpEffect()
        {
            if (levelUpEffect != null)
            {
                GameObject effect = Instantiate(levelUpEffect, transform);
                Destroy(effect, 3f);
            }

            // Play sound
            // TODO: Add level up sound effect

            Debug.Log("🎉 LEVEL UP! 🎉");
        }

        /// <summary>
        /// Set XP and level from backend data.
        /// </summary>
        public void SetXPAndLevel(int xp, int level, int xpToNext)
        {
            currentXP = xp;
            currentLevel = level;
            xpToNextLevel = xpToNext;

            UpdateUI();
        }

        public int GetCurrentXP() => currentXP;
        public int GetCurrentLevel() => currentLevel;
    }
}
