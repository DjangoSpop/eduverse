using UnityEngine;
using UnityEngine.UI;
using TMPro;
using DG.Tweening;

namespace Eduverse.UI
{
    /// <summary>
    /// Visual indicator for a single loading stage.
    /// Shows pending/active/complete states with animations.
    /// </summary>
    public class LoadingStageIndicator : MonoBehaviour
    {
        [Header("UI Elements")]
        [SerializeField] private Image backgroundCircle;
        [SerializeField] private TextMeshProUGUI iconText;
        [SerializeField] private Image checkmark;
        [SerializeField] private Image progressRing;

        [Header("Particle Effects")]
        [SerializeField] private ParticleSystem completionParticles;

        [Header("Colors")]
        [SerializeField] private Color pendingColor = Color.gray;
        [SerializeField] private Color activeColor = Color.yellow;
        [SerializeField] private Color completeColor = Color.green;

        private Color baseColor;
        private int currentState = 0; // 0:Pending, 1:Active, 2:Complete

        /// <summary>
        /// Initialize the stage indicator
        /// </summary>
        public void Initialize(string icon, Color color)
        {
            baseColor = color;

            if (iconText != null)
                iconText.text = icon;

            if (backgroundCircle != null)
                backgroundCircle.color = pendingColor;

            if (checkmark != null)
                checkmark.gameObject.SetActive(false);

            if (progressRing != null)
                progressRing.fillAmount = 0f;

            currentState = 0;
        }

        /// <summary>
        /// Set the state of the indicator
        /// 0 = Pending, 1 = Active, 2 = Complete
        /// </summary>
        public void SetState(int state)
        {
            if (currentState == state)
                return;

            currentState = state;

            switch (state)
            {
                case 0: // Pending
                    SetPending();
                    break;

                case 1: // Active
                    SetActive();
                    break;

                case 2: // Complete
                    SetComplete();
                    break;
            }
        }

        private void SetPending()
        {
            if (backgroundCircle != null)
            {
                backgroundCircle.DOColor(pendingColor, 0.3f);
            }

            if (progressRing != null)
            {
                progressRing.fillAmount = 0f;
            }

            if (checkmark != null)
            {
                checkmark.gameObject.SetActive(false);
            }

            transform.localScale = Vector3.one * 0.9f;
        }

        private void SetActive()
        {
            if (backgroundCircle != null)
            {
                backgroundCircle.DOColor(baseColor, 0.5f);
            }

            // Pulse animation
            transform.DOScale(1.1f, 0.5f)
                .SetEase(Ease.OutBounce)
                .OnComplete(() =>
                {
                    // Breathing effect while active
                    transform.DOScale(1.05f, 1f)
                        .SetLoops(-1, LoopType.Yoyo)
                        .SetEase(Ease.InOutSine);
                });

            // Animated progress ring
            if (progressRing != null)
            {
                progressRing.DOFillAmount(1f, 2f)
                    .SetEase(Ease.Linear);
            }

            // Glow effect
            if (iconText != null)
            {
                iconText.DOColor(Color.white, 0.3f);
            }
        }

        private void SetComplete()
        {
            // Stop any active animations
            DOTween.Kill(transform);

            if (backgroundCircle != null)
            {
                backgroundCircle.DOColor(completeColor, 0.5f);
            }

            if (progressRing != null)
            {
                progressRing.fillAmount = 1f;
            }

            // Show checkmark with animation
            if (checkmark != null)
            {
                checkmark.gameObject.SetActive(true);
                checkmark.transform.localScale = Vector3.zero;
                checkmark.transform.DOScale(1f, 0.5f)
                    .SetEase(Ease.OutBounce);
            }

            // Completion animation
            transform.DOScale(1.2f, 0.3f)
                .SetEase(Ease.OutBounce)
                .OnComplete(() =>
                {
                    transform.DOScale(1f, 0.3f);
                });

            // Play particles
            if (completionParticles != null)
            {
                completionParticles.Play();
            }
        }

        /// <summary>
        /// Update progress for active stage (0-1)
        /// </summary>
        public void UpdateProgress(float progress)
        {
            if (currentState == 1 && progressRing != null)
            {
                progressRing.fillAmount = Mathf.Clamp01(progress);
            }
        }

        private void OnDestroy()
        {
            DOTween.Kill(transform);
        }
    }
}
