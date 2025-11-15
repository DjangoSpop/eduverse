using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace Eduverse.UI
{
    /// <summary>
    /// Loading screen with progress bar and stage indicators.
    /// </summary>
    public class LoadingScreen : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private GameObject loadingPanel;
        [SerializeField] private TextMeshProUGUI loadingText;
        [SerializeField] private Slider progressBar;
        [SerializeField] private TextMeshProUGUI progressPercentage;
        [SerializeField] private GameObject errorPanel;
        [SerializeField] private TextMeshProUGUI errorText;

        [Header("Stage Indicators")]
        [SerializeField] private LoadingStageIndicator[] stageIndicators;

        [Header("Animation")]
        [SerializeField] private float fadeSpeed = 2f;
        [SerializeField] private CanvasGroup canvasGroup;

        private void Awake()
        {
            if (canvasGroup == null)
                canvasGroup = GetComponent<CanvasGroup>();

            if (loadingPanel != null)
                loadingPanel.SetActive(false);

            if (errorPanel != null)
                errorPanel.SetActive(false);
        }

        /// <summary>
        /// Show the loading screen.
        /// </summary>
        public void Show()
        {
            if (loadingPanel != null)
                loadingPanel.SetActive(true);

            if (errorPanel != null)
                errorPanel.SetActive(false);

            UpdateProgress("Initializing...", 0f);

            // Fade in
            if (canvasGroup != null)
            {
                LeanTween.alphaCanvas(canvasGroup, 1f, 1f / fadeSpeed);
            }

            Debug.Log("[LoadingScreen] Shown");
        }

        /// <summary>
        /// Hide the loading screen.
        /// </summary>
        public void Hide()
        {
            // Fade out
            if (canvasGroup != null)
            {
                LeanTween.alphaCanvas(canvasGroup, 0f, 1f / fadeSpeed)
                    .setOnComplete(() =>
                    {
                        if (loadingPanel != null)
                            loadingPanel.SetActive(false);
                    });
            }
            else
            {
                if (loadingPanel != null)
                    loadingPanel.SetActive(false);
            }

            Debug.Log("[LoadingScreen] Hidden");
        }

        /// <summary>
        /// Update loading progress.
        /// </summary>
        public void UpdateProgress(string message, float progress)
        {
            if (loadingText != null)
                loadingText.text = message;

            if (progressBar != null)
                progressBar.value = progress;

            if (progressPercentage != null)
                progressPercentage.text = $"{Mathf.RoundToInt(progress * 100)}%";

            // Update stage indicators
            UpdateStageIndicators(progress);
        }

        /// <summary>
        /// Show an error message.
        /// </summary>
        public void ShowError(string message)
        {
            if (loadingPanel != null)
                loadingPanel.SetActive(false);

            if (errorPanel != null)
                errorPanel.SetActive(true);

            if (errorText != null)
                errorText.text = message;

            Debug.LogError($"[LoadingScreen] Error shown: {message}");
        }

        /// <summary>
        /// Retry after error.
        /// </summary>
        public void OnRetryButtonClicked()
        {
            if (errorPanel != null)
                errorPanel.SetActive(false);

            Show();

            // Reload scene or retry loading
            Debug.Log("[LoadingScreen] Retry clicked");
        }

        /// <summary>
        /// Update visual stage indicators.
        /// </summary>
        private void UpdateStageIndicators(float progress)
        {
            if (stageIndicators == null || stageIndicators.Length == 0)
                return;

            // Determine which stage based on progress
            int currentStage = Mathf.FloorToInt(progress * stageIndicators.Length);

            for (int i = 0; i < stageIndicators.Length; i++)
            {
                if (stageIndicators[i] != null)
                {
                    if (i < currentStage)
                    {
                        stageIndicators[i].SetComplete();
                    }
                    else if (i == currentStage)
                    {
                        stageIndicators[i].SetActive();
                    }
                    else
                    {
                        stageIndicators[i].SetPending();
                    }
                }
            }
        }
    }

    /// <summary>
    /// Individual stage indicator component.
    /// </summary>
    [System.Serializable]
    public class LoadingStageIndicator
    {
        [SerializeField] private GameObject pendingIcon;
        [SerializeField] private GameObject activeIcon;
        [SerializeField] private GameObject completeIcon;
        [SerializeField] private TextMeshProUGUI stageText;

        public void SetPending()
        {
            if (pendingIcon != null) pendingIcon.SetActive(true);
            if (activeIcon != null) activeIcon.SetActive(false);
            if (completeIcon != null) completeIcon.SetActive(false);
        }

        public void SetActive()
        {
            if (pendingIcon != null) pendingIcon.SetActive(false);
            if (activeIcon != null) activeIcon.SetActive(true);
            if (completeIcon != null) completeIcon.SetActive(false);
        }

        public void SetComplete()
        {
            if (pendingIcon != null) pendingIcon.SetActive(false);
            if (activeIcon != null) activeIcon.SetActive(false);
            if (completeIcon != null) completeIcon.SetActive(true);
        }
    }
}
