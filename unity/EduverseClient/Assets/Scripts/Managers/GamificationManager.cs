using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System;
using System.Collections.Generic;
using DG.Tweening;

namespace Eduverse.Managers
{
    /// <summary>
    /// Manages XP, badges, curiosity bar, and rewards.
    /// Integrates with GameCoordinator and AnalyticsLogger for tracking.
    /// </summary>
    public class GamificationManager : MonoBehaviour
    {
        [Header("XP and Level Settings")]
        [SerializeField] private int currentXP = 0;
        [SerializeField] private int currentLevel = 1;
        [SerializeField] private int[] xpThresholds = { 100, 250, 500, 1000, 2000, 5000 }; // XP needed for each level

        [Header("Curiosity Bar Settings")]
        [SerializeField] private float curiosityValue = 0f; // 0-1 scale
        [SerializeField] private float curiosityDecayRate = 0.05f; // Per second
        [SerializeField] private float curiosityGainOnInteraction = 0.15f;
        [SerializeField] private float curiosityGainOnSuccess = 0.25f;

        [Header("UI References")]
        [SerializeField] private Slider curiosityBar;
        [SerializeField] private Image curiosityBarFill;
        [SerializeField] private TextMeshProUGUI xpText;
        [SerializeField] private TextMeshProUGUI levelText;
        [SerializeField] private Slider xpProgressBar;
        [SerializeField] private GameObject badgePopupPrefab;
        [SerializeField] private Transform badgePopupParent;
        [SerializeField] private GameObject xpPopupPrefab;
        [SerializeField] private Transform xpPopupParent;

        [Header("Curiosity Bar Colors")]
        [SerializeField] private Color lowCuriosityColor = new Color(0.8f, 0.2f, 0.2f); // Red
        [SerializeField] private Color mediumCuriosityColor = new Color(1f, 0.8f, 0.2f); // Yellow
        [SerializeField] private Color highCuriosityColor = new Color(0.2f, 1f, 0.2f); // Green

        [Header("Audio")]
        [SerializeField] private AudioSource audioSource;
        [SerializeField] private AudioClip xpGainSound;
        [SerializeField] private AudioClip levelUpSound;
        [SerializeField] private AudioClip badgeUnlockSound;
        [SerializeField] private AudioClip curiosityBoostSound;

        // Badge tracking
        private HashSet<string> unlockedBadges = new HashSet<string>();
        private Dictionary<string, BadgeDefinition> badgeDefinitions = new Dictionary<string, BadgeDefinition>();

        // Singleton instance
        private static GamificationManager _instance;
        public static GamificationManager Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = FindObjectOfType<GamificationManager>();
                }
                return _instance;
            }
        }

        // Events
        public event Action<int> OnXPGained;
        public event Action<int> OnLevelUp;
        public event Action<string> OnBadgeUnlocked;
        public event Action<float> OnCuriosityChanged;

        private void Awake()
        {
            if (_instance != null && _instance != this)
            {
                Destroy(gameObject);
                return;
            }

            _instance = this;
            DontDestroyOnLoad(gameObject);

            InitializeBadges();
            LoadProgress();
        }

        private void Start()
        {
            UpdateUI();
        }

        private void Update()
        {
            // Decay curiosity over time
            if (curiosityValue > 0f)
            {
                curiosityValue = Mathf.Max(0f, curiosityValue - curiosityDecayRate * Time.deltaTime);
                UpdateCuriosityBar();
            }
        }

        #region Badge System

        /// <summary>
        /// Initialize all badge definitions.
        /// </summary>
        private void InitializeBadges()
        {
            badgeDefinitions.Clear();

            // Starter badges
            AddBadge("first_steps", "First Steps", "Complete your first interaction", 0, BadgeType.Interaction);
            AddBadge("explorer", "Explorer", "Earn 50 XP", 50, BadgeType.XP);
            AddBadge("adventurer", "Adventurer", "Earn 200 XP", 200, BadgeType.XP);
            AddBadge("scholar", "Scholar", "Earn 500 XP", 500, BadgeType.XP);
            AddBadge("master", "Master", "Earn 1000 XP", 1000, BadgeType.XP);

            // Challenge badges
            AddBadge("quiz_master", "Quiz Master", "Answer 10 quiz questions correctly", 10, BadgeType.QuizSuccess);
            AddBadge("perfect_score", "Perfect Score", "Get 5 challenges with 100% accuracy", 5, BadgeType.PerfectChallenge);
            AddBadge("curious_mind", "Curious Mind", "Keep curiosity bar at 80%+ for 5 minutes", 300, BadgeType.CuriosityTime);

            // Collection badges
            AddBadge("collector", "Collector", "Collect 20 items", 20, BadgeType.Collectibles);
            AddBadge("treasure_hunter", "Treasure Hunter", "Collect 50 items", 50, BadgeType.Collectibles);

            // Social/NPC badges
            AddBadge("friendly", "Friendly", "Talk to 5 different NPCs", 5, BadgeType.NPCInteraction);
            AddBadge("socialite", "Socialite", "Talk to 15 different NPCs", 15, BadgeType.NPCInteraction);

            Debug.Log($"[GamificationManager] Initialized {badgeDefinitions.Count} badge definitions");
        }

        private void AddBadge(string id, string name, string description, int requirement, BadgeType type)
        {
            badgeDefinitions[id] = new BadgeDefinition
            {
                id = id,
                name = name,
                description = description,
                requirement = requirement,
                type = type
            };
        }

        /// <summary>
        /// Check if a badge should be unlocked based on current stats.
        /// </summary>
        private void CheckBadgeUnlocks(BadgeType type, int currentValue)
        {
            foreach (var badge in badgeDefinitions.Values)
            {
                if (badge.type == type && !unlockedBadges.Contains(badge.id))
                {
                    if (currentValue >= badge.requirement)
                    {
                        UnlockBadge(badge.id);
                    }
                }
            }
        }

        /// <summary>
        /// Unlock a specific badge.
        /// </summary>
        public void UnlockBadge(string badgeId)
        {
            if (unlockedBadges.Contains(badgeId))
            {
                Debug.LogWarning($"[GamificationManager] Badge already unlocked: {badgeId}");
                return;
            }

            if (!badgeDefinitions.ContainsKey(badgeId))
            {
                Debug.LogError($"[GamificationManager] Badge not found: {badgeId}");
                return;
            }

            unlockedBadges.Add(badgeId);
            BadgeDefinition badge = badgeDefinitions[badgeId];

            Debug.Log($"[GamificationManager] Badge unlocked: {badge.name}");

            // Show popup
            ShowBadgePopup(badge);

            // Play sound
            if (audioSource != null && badgeUnlockSound != null)
            {
                audioSource.PlayOneShot(badgeUnlockSound);
            }

            // Fire event
            OnBadgeUnlocked?.Invoke(badgeId);

            // Log to analytics
            if (UI.AnalyticsLogger.Instance != null)
            {
                UI.AnalyticsLogger.Instance.LogBadgeUnlocked(badgeId, badge.name);
            }

            SaveProgress();
        }

        /// <summary>
        /// Show animated badge popup.
        /// </summary>
        private void ShowBadgePopup(BadgeDefinition badge)
        {
            if (badgePopupPrefab == null || badgePopupParent == null)
            {
                Debug.LogWarning("[GamificationManager] Badge popup prefab or parent not assigned");
                return;
            }

            GameObject popup = Instantiate(badgePopupPrefab, badgePopupParent);
            BadgePopup popupComponent = popup.GetComponent<BadgePopup>();

            if (popupComponent != null)
            {
                popupComponent.Show(badge.name, badge.description);
            }
            else
            {
                // Fallback: Basic popup animation
                popup.transform.localScale = Vector3.zero;
                popup.transform.DOScale(1f, 0.5f).SetEase(Ease.OutBounce);

                // Auto-destroy after 4 seconds
                Destroy(popup, 4f);
            }
        }

        #endregion

        #region XP and Leveling

        /// <summary>
        /// Award XP to the player.
        /// </summary>
        public void AwardXP(int amount, string reason = "")
        {
            if (amount <= 0) return;

            int previousXP = currentXP;
            int previousLevel = currentLevel;

            currentXP += amount;

            Debug.Log($"[GamificationManager] Awarded {amount} XP for: {reason}. Total XP: {currentXP}");

            // Check for level up
            CheckLevelUp();

            // Check for XP-based badges
            CheckBadgeUnlocks(BadgeType.XP, currentXP);

            // Show XP popup
            ShowXPPopup(amount);

            // Update UI
            UpdateUI();

            // Play sound
            if (audioSource != null && xpGainSound != null)
            {
                audioSource.PlayOneShot(xpGainSound);
            }

            // Fire event
            OnXPGained?.Invoke(amount);

            // Log to analytics
            if (UI.AnalyticsLogger.Instance != null)
            {
                UI.AnalyticsLogger.Instance.LogXPGained(amount, reason, currentXP);
            }

            SaveProgress();
        }

        /// <summary>
        /// Check if player should level up.
        /// </summary>
        private void CheckLevelUp()
        {
            int previousLevel = currentLevel;

            while (currentLevel < xpThresholds.Length && currentXP >= xpThresholds[currentLevel - 1])
            {
                currentLevel++;
                Debug.Log($"[GamificationManager] Level up! Now level {currentLevel}");

                // Play level up sound
                if (audioSource != null && levelUpSound != null)
                {
                    audioSource.PlayOneShot(levelUpSound);
                }

                // Fire event
                OnLevelUp?.Invoke(currentLevel);

                // Log to analytics
                if (UI.AnalyticsLogger.Instance != null)
                {
                    UI.AnalyticsLogger.Instance.LogLevelUp(currentLevel, currentXP);
                }

                // Show level up effect
                ShowLevelUpEffect();
            }

            if (currentLevel > previousLevel)
            {
                SaveProgress();
            }
        }

        /// <summary>
        /// Show XP gain popup animation.
        /// </summary>
        private void ShowXPPopup(int amount)
        {
            if (xpPopupPrefab == null || xpPopupParent == null)
            {
                return;
            }

            GameObject popup = Instantiate(xpPopupPrefab, xpPopupParent);
            TextMeshProUGUI popupText = popup.GetComponentInChildren<TextMeshProUGUI>();

            if (popupText != null)
            {
                popupText.text = $"+{amount} XP";
            }

            // Animate popup
            RectTransform rectTransform = popup.GetComponent<RectTransform>();
            if (rectTransform != null)
            {
                Vector3 startPos = rectTransform.anchoredPosition;
                rectTransform.DOAnchorPos(startPos + new Vector3(0, 100, 0), 1f).SetEase(Ease.OutQuad);
                popup.GetComponent<CanvasGroup>()?.DOFade(0f, 1f).SetDelay(0.5f);
            }

            Destroy(popup, 1.5f);
        }

        /// <summary>
        /// Show level up visual effect.
        /// </summary>
        private void ShowLevelUpEffect()
        {
            if (levelText != null)
            {
                levelText.transform.DOScale(1.3f, 0.3f).SetEase(Ease.OutBounce).OnComplete(() =>
                {
                    levelText.transform.DOScale(1f, 0.3f);
                });

                levelText.DOColor(Color.yellow, 0.3f).OnComplete(() =>
                {
                    levelText.DOColor(Color.white, 0.3f);
                });
            }
        }

        /// <summary>
        /// Get XP needed for next level.
        /// </summary>
        public int GetXPForNextLevel()
        {
            if (currentLevel >= xpThresholds.Length)
            {
                return -1; // Max level reached
            }
            return xpThresholds[currentLevel - 1];
        }

        /// <summary>
        /// Get XP progress as 0-1 value for current level.
        /// </summary>
        public float GetXPProgress()
        {
            if (currentLevel >= xpThresholds.Length)
            {
                return 1f; // Max level
            }

            int previousThreshold = currentLevel > 1 ? xpThresholds[currentLevel - 2] : 0;
            int nextThreshold = xpThresholds[currentLevel - 1];
            int xpInCurrentLevel = currentXP - previousThreshold;
            int xpNeededForLevel = nextThreshold - previousThreshold;

            return Mathf.Clamp01((float)xpInCurrentLevel / xpNeededForLevel);
        }

        #endregion

        #region Curiosity Bar

        /// <summary>
        /// Increase curiosity on interaction.
        /// </summary>
        public void OnInteraction()
        {
            IncreaseCuriosity(curiosityGainOnInteraction);
        }

        /// <summary>
        /// Increase curiosity on successful challenge.
        /// </summary>
        public void OnSuccessfulChallenge()
        {
            IncreaseCuriosity(curiosityGainOnSuccess);

            // Play boost sound
            if (audioSource != null && curiosityBoostSound != null)
            {
                audioSource.PlayOneShot(curiosityBoostSound);
            }
        }

        /// <summary>
        /// Increase curiosity value.
        /// </summary>
        private void IncreaseCuriosity(float amount)
        {
            float previousValue = curiosityValue;
            curiosityValue = Mathf.Clamp01(curiosityValue + amount);

            if (curiosityValue > previousValue)
            {
                UpdateCuriosityBar();

                // Fire event
                OnCuriosityChanged?.Invoke(curiosityValue);

                // Animate bar fill
                if (curiosityBarFill != null)
                {
                    curiosityBarFill.transform.DOScale(1.1f, 0.2f).SetEase(Ease.OutQuad).OnComplete(() =>
                    {
                        curiosityBarFill.transform.DOScale(1f, 0.2f);
                    });
                }

                Debug.Log($"[GamificationManager] Curiosity increased to {curiosityValue:F2}");
            }
        }

        /// <summary>
        /// Update curiosity bar UI.
        /// </summary>
        private void UpdateCuriosityBar()
        {
            if (curiosityBar != null)
            {
                curiosityBar.value = curiosityValue;
            }

            if (curiosityBarFill != null)
            {
                // Color based on value
                if (curiosityValue < 0.33f)
                {
                    curiosityBarFill.color = lowCuriosityColor;
                }
                else if (curiosityValue < 0.66f)
                {
                    curiosityBarFill.color = mediumCuriosityColor;
                }
                else
                {
                    curiosityBarFill.color = highCuriosityColor;
                }
            }
        }

        /// <summary>
        /// Get current curiosity value (0-1).
        /// </summary>
        public float GetCuriosityValue()
        {
            return curiosityValue;
        }

        #endregion

        #region Statistics Tracking

        // Track various stats for badge unlocking
        private int quizSuccessCount = 0;
        private int perfectChallengeCount = 0;
        private int collectiblesCount = 0;
        private HashSet<string> npcInteractions = new HashSet<string>();
        private float highCuriosityTime = 0f;

        /// <summary>
        /// Track quiz success for badges.
        /// </summary>
        public void OnQuizSuccess()
        {
            quizSuccessCount++;
            CheckBadgeUnlocks(BadgeType.QuizSuccess, quizSuccessCount);
        }

        /// <summary>
        /// Track perfect challenge completion.
        /// </summary>
        public void OnPerfectChallenge()
        {
            perfectChallengeCount++;
            CheckBadgeUnlocks(BadgeType.PerfectChallenge, perfectChallengeCount);
        }

        /// <summary>
        /// Track collectible pickup.
        /// </summary>
        public void OnCollectibleCollected()
        {
            collectiblesCount++;
            CheckBadgeUnlocks(BadgeType.Collectibles, collectiblesCount);

            // Also check first interaction badge
            if (collectiblesCount == 1)
            {
                UnlockBadge("first_steps");
            }
        }

        /// <summary>
        /// Track NPC interaction.
        /// </summary>
        public void OnNPCInteraction(string npcId)
        {
            if (!npcInteractions.Contains(npcId))
            {
                npcInteractions.Add(npcId);
                CheckBadgeUnlocks(BadgeType.NPCInteraction, npcInteractions.Count);

                // Also check first interaction badge
                if (npcInteractions.Count == 1)
                {
                    UnlockBadge("first_steps");
                }
            }
        }

        #endregion

        #region UI Updates

        /// <summary>
        /// Update all UI elements.
        /// </summary>
        private void UpdateUI()
        {
            // Update XP text
            if (xpText != null)
            {
                int nextLevelXP = GetXPForNextLevel();
                if (nextLevelXP > 0)
                {
                    xpText.text = $"{currentXP} / {nextLevelXP} XP";
                }
                else
                {
                    xpText.text = $"{currentXP} XP (Max Level)";
                }
            }

            // Update level text
            if (levelText != null)
            {
                levelText.text = $"Level {currentLevel}";
            }

            // Update XP progress bar
            if (xpProgressBar != null)
            {
                xpProgressBar.value = GetXPProgress();
            }

            // Update curiosity bar
            UpdateCuriosityBar();
        }

        #endregion

        #region Persistence

        /// <summary>
        /// Save progress to PlayerPrefs.
        /// </summary>
        private void SaveProgress()
        {
            PlayerPrefs.SetInt("CurrentXP", currentXP);
            PlayerPrefs.SetInt("CurrentLevel", currentLevel);
            PlayerPrefs.SetFloat("CuriosityValue", curiosityValue);
            PlayerPrefs.SetInt("QuizSuccessCount", quizSuccessCount);
            PlayerPrefs.SetInt("PerfectChallengeCount", perfectChallengeCount);
            PlayerPrefs.SetInt("CollectiblesCount", collectiblesCount);

            // Save unlocked badges as comma-separated string
            PlayerPrefs.SetString("UnlockedBadges", string.Join(",", unlockedBadges));

            PlayerPrefs.Save();
        }

        /// <summary>
        /// Load progress from PlayerPrefs.
        /// </summary>
        private void LoadProgress()
        {
            currentXP = PlayerPrefs.GetInt("CurrentXP", 0);
            currentLevel = PlayerPrefs.GetInt("CurrentLevel", 1);
            curiosityValue = PlayerPrefs.GetFloat("CuriosityValue", 0f);
            quizSuccessCount = PlayerPrefs.GetInt("QuizSuccessCount", 0);
            perfectChallengeCount = PlayerPrefs.GetInt("PerfectChallengeCount", 0);
            collectiblesCount = PlayerPrefs.GetInt("CollectiblesCount", 0);

            // Load unlocked badges
            string badgesString = PlayerPrefs.GetString("UnlockedBadges", "");
            if (!string.IsNullOrEmpty(badgesString))
            {
                string[] badges = badgesString.Split(',');
                foreach (string badge in badges)
                {
                    if (!string.IsNullOrEmpty(badge))
                    {
                        unlockedBadges.Add(badge);
                    }
                }
            }

            Debug.Log($"[GamificationManager] Progress loaded: Level {currentLevel}, {currentXP} XP, {unlockedBadges.Count} badges");
        }

        /// <summary>
        /// Reset all progress (for testing).
        /// </summary>
        public void ResetProgress()
        {
            currentXP = 0;
            currentLevel = 1;
            curiosityValue = 0f;
            quizSuccessCount = 0;
            perfectChallengeCount = 0;
            collectiblesCount = 0;
            npcInteractions.Clear();
            unlockedBadges.Clear();

            PlayerPrefs.DeleteAll();
            PlayerPrefs.Save();

            UpdateUI();

            Debug.Log("[GamificationManager] Progress reset");
        }

        #endregion

        #region Public Getters

        public int GetCurrentXP() => currentXP;
        public int GetCurrentLevel() => currentLevel;
        public bool IsBadgeUnlocked(string badgeId) => unlockedBadges.Contains(badgeId);
        public int GetUnlockedBadgeCount() => unlockedBadges.Count;
        public HashSet<string> GetUnlockedBadges() => new HashSet<string>(unlockedBadges);

        #endregion
    }

    #region Data Structures

    [Serializable]
    public class BadgeDefinition
    {
        public string id;
        public string name;
        public string description;
        public int requirement;
        public BadgeType type;
    }

    public enum BadgeType
    {
        XP,
        QuizSuccess,
        PerfectChallenge,
        Collectibles,
        NPCInteraction,
        CuriosityTime,
        Interaction
    }

    #endregion
}
