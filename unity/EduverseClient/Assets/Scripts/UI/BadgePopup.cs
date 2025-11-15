using UnityEngine;
using UnityEngine.UI;
using TMPro;
using DG.Tweening;

namespace Eduverse.UI
{
    /// <summary>
    /// Animated popup for badge unlocks.
    /// Shows badge name, description, and plays celebration animation.
    /// </summary>
    public class BadgePopup : MonoBehaviour
    {
        [Header("UI Elements")]
        [SerializeField] private TextMeshProUGUI badgeNameText;
        [SerializeField] private TextMeshProUGUI badgeDescriptionText;
        [SerializeField] private Image badgeIcon;
        [SerializeField] private Image backgroundGlow;
        [SerializeField] private CanvasGroup canvasGroup;

        [Header("Animation Settings")]
        [SerializeField] private float animationDuration = 0.5f;
        [SerializeField] private float displayDuration = 3f;
        [SerializeField] private Ease entryEase = Ease.OutBounce;
        [SerializeField] private Ease exitEase = Ease.InBack;

        [Header("Particle Effects")]
        [SerializeField] private ParticleSystem celebrationParticles;
        [SerializeField] private ParticleSystem glitterParticles;

        [Header("Audio")]
        [SerializeField] private AudioSource audioSource;
        [SerializeField] private AudioClip popSound;

        private RectTransform rectTransform;
        private bool isShowing = false;

        private void Awake()
        {
            rectTransform = GetComponent<RectTransform>();

            if (canvasGroup == null)
            {
                canvasGroup = gameObject.AddComponent<CanvasGroup>();
            }

            // Start hidden
            canvasGroup.alpha = 0f;
            transform.localScale = Vector3.zero;
        }

        /// <summary>
        /// Show the badge popup with animation.
        /// </summary>
        public void Show(string badgeName, string description, Sprite icon = null)
        {
            if (isShowing) return;

            isShowing = true;

            // Set text content
            if (badgeNameText != null)
            {
                badgeNameText.text = badgeName;
            }

            if (badgeDescriptionText != null)
            {
                badgeDescriptionText.text = description;
            }

            // Set icon if provided
            if (icon != null && badgeIcon != null)
            {
                badgeIcon.sprite = icon;
            }

            // Play entrance animation
            PlayEntranceAnimation();

            // Auto-hide after duration
            Invoke(nameof(Hide), displayDuration);
        }

        /// <summary>
        /// Play entrance animation sequence.
        /// </summary>
        private void PlayEntranceAnimation()
        {
            // Reset initial state
            transform.localScale = Vector3.zero;
            canvasGroup.alpha = 0f;
            if (backgroundGlow != null)
            {
                backgroundGlow.color = new Color(1f, 1f, 1f, 0f);
            }

            // Create animation sequence
            Sequence entranceSequence = DOTween.Sequence();

            // Scale up
            entranceSequence.Append(transform.DOScale(1f, animationDuration).SetEase(entryEase));

            // Fade in
            entranceSequence.Join(canvasGroup.DOFade(1f, animationDuration * 0.7f));

            // Glow effect
            if (backgroundGlow != null)
            {
                entranceSequence.Join(backgroundGlow.DOFade(0.3f, animationDuration * 0.5f)
                    .OnComplete(() =>
                    {
                        backgroundGlow.DOFade(0.1f, 0.5f).SetLoops(-1, LoopType.Yoyo);
                    }));
            }

            // Badge icon animation
            if (badgeIcon != null)
            {
                badgeIcon.transform.localScale = Vector3.zero;
                entranceSequence.Append(badgeIcon.transform.DOScale(1f, 0.3f).SetEase(Ease.OutBounce));
            }

            // Play particles
            entranceSequence.AppendCallback(() =>
            {
                if (celebrationParticles != null)
                {
                    celebrationParticles.Play();
                }

                if (glitterParticles != null)
                {
                    glitterParticles.Play();
                }
            });

            // Play sound
            if (audioSource != null && popSound != null)
            {
                audioSource.PlayOneShot(popSound);
            }

            // Pulse effect for badge name
            if (badgeNameText != null)
            {
                badgeNameText.transform.DOScale(1.1f, 0.3f)
                    .SetEase(Ease.OutQuad)
                    .SetDelay(animationDuration)
                    .OnComplete(() =>
                    {
                        badgeNameText.transform.DOScale(1f, 0.3f);
                    });
            }
        }

        /// <summary>
        /// Hide the popup with animation.
        /// </summary>
        public void Hide()
        {
            if (!isShowing) return;

            // Kill any ongoing animations
            DOTween.Kill(transform);
            DOTween.Kill(canvasGroup);
            if (backgroundGlow != null)
            {
                DOTween.Kill(backgroundGlow);
            }

            // Create exit sequence
            Sequence exitSequence = DOTween.Sequence();

            // Scale down
            exitSequence.Append(transform.DOScale(0f, animationDuration * 0.7f).SetEase(exitEase));

            // Fade out
            exitSequence.Join(canvasGroup.DOFade(0f, animationDuration * 0.7f));

            // Destroy after animation
            exitSequence.OnComplete(() =>
            {
                Destroy(gameObject);
            });

            isShowing = false;
        }

        /// <summary>
        /// Immediately hide without animation (for cleanup).
        /// </summary>
        public void HideImmediate()
        {
            DOTween.Kill(transform);
            DOTween.Kill(canvasGroup);
            if (backgroundGlow != null)
            {
                DOTween.Kill(backgroundGlow);
            }

            Destroy(gameObject);
        }

        private void OnDestroy()
        {
            // Clean up any running tweens
            DOTween.Kill(transform);
            DOTween.Kill(canvasGroup);
            if (backgroundGlow != null)
            {
                DOTween.Kill(backgroundGlow);
            }
        }
    }
}
