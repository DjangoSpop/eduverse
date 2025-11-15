using UnityEngine;
using UnityEngine.UI;
using TMPro;
using DG.Tweening;
using System.Collections;
using System.Collections.Generic;

namespace Eduverse.UI
{
    /// <summary>
    /// Enhanced loading stage definition
    /// </summary>
    [System.Serializable]
    public class LoadingStage
    {
        public string name;
        public string description;
        public string iconEmoji;
        public Color color;
        public float durationEstimate;
        public Sprite characterSprite;
    }

    /// <summary>
    /// Enhanced loading screen with stages, animations, and interactive elements.
    /// Keeps learners engaged during AI processing and world generation.
    /// </summary>
    public class EnhancedLoadingScreen : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private CanvasGroup canvasGroup;
        [SerializeField] private Image background;
        [SerializeField] private Slider progressBar;
        [SerializeField] private Image progressBarFill;
        [SerializeField] private TextMeshProUGUI progressPercentText;
        [SerializeField] private TextMeshProUGUI stageDescriptionText;
        [SerializeField] private TextMeshProUGUI funFactText;

        [Header("Character Animation")]
        [SerializeField] private Transform characterContainer;
        [SerializeField] private Animator characterAnimator;
        [SerializeField] private Image characterImage;
        [SerializeField] private List<Sprite> characterStates;

        [Header("Stage Indicators")]
        [SerializeField] private Transform stageIndicatorContainer;
        [SerializeField] private GameObject stageIndicatorPrefab;

        [Header("Particle Effects")]
        [SerializeField] private ParticleSystem sparkleParticles;
        [SerializeField] private ParticleSystem progressParticles;

        [Header("Settings")]
        [SerializeField] private Gradient progressBarGradient;
        [SerializeField] private float minDisplayTime = 2f;
        [SerializeField] private bool useInteractiveElements = true;

        [Header("Audio")]
        [SerializeField] private AudioSource audioSource;
        [SerializeField] private AudioClip stageCompleteSound;
        [SerializeField] private AudioClip progressMilestoneSound;
        [SerializeField] private AudioClip loadingCompleteSound;

        private List<LoadingStageIndicator> stageIndicators = new List<LoadingStageIndicator>();
        private List<string> funFacts = new List<string>();
        private int currentStage = 0;
        private float currentProgress = 0f;
        private float startTime;
        private Coroutine factCoroutine;

        private readonly LoadingStage[] loadingStages = new LoadingStage[]
        {
            new LoadingStage
            {
                name = "Analyzing",
                description = "🔍 Reading your lesson...",
                iconEmoji = "📚",
                color = new Color(0.2f, 0.5f, 1f),
                durationEstimate = 5f
            },
            new LoadingStage
            {
                name = "AI Thinking",
                description = "✨ Creating magic ideas...",
                iconEmoji = "🧠",
                color = new Color(0.3f, 0.8f, 0.3f),
                durationEstimate = 10f
            },
            new LoadingStage
            {
                name = "Building World",
                description = "🌍 Making your adventure...",
                iconEmoji = "🏗️",
                color = new Color(1f, 0.8f, 0.2f),
                durationEstimate = 15f
            },
            new LoadingStage
            {
                name = "Preparing Mentor",
                description = "💬 Training your guide...",
                iconEmoji = "👨‍🏫",
                color = new Color(1f, 0.3f, 0.8f),
                durationEstimate = 5f
            },
            new LoadingStage
            {
                name = "Final Polish",
                description = "🎨 Adding fun touches...",
                iconEmoji = "✨",
                color = new Color(0.5f, 1f, 1f),
                durationEstimate = 5f
            }
        };

        private void Awake()
        {
            if (canvasGroup == null)
                canvasGroup = GetComponent<CanvasGroup>();

            canvasGroup.alpha = 0f;
            gameObject.SetActive(false);

            InitializeFunFacts();
            InitializeStages();
        }

        /// <summary>
        /// Show loading screen and start animations
        /// </summary>
        public void ShowLoading()
        {
            gameObject.SetActive(true);
            startTime = Time.time;
            currentStage = 0;
            currentProgress = 0f;

            UpdateProgress(0f);
            AdvanceToStage(0);

            canvasGroup.DOFade(1f, 0.5f).SetEase(Ease.InOutSine);

            if (factCoroutine != null)
                StopCoroutine(factCoroutine);
            factCoroutine = StartCoroutine(CycleFunFacts());

            Debug.Log("[EnhancedLoadingScreen] Loading started");
        }

        /// <summary>
        /// Hide loading screen with animation
        /// </summary>
        public void HideLoading()
        {
            if (factCoroutine != null)
                StopCoroutine(factCoroutine);

            canvasGroup.DOFade(0f, 0.5f)
                .SetEase(Ease.InOutSine)
                .OnComplete(() =>
                {
                    gameObject.SetActive(false);
                    Debug.Log("[EnhancedLoadingScreen] Loading hidden");
                });

            if (audioSource && loadingCompleteSound)
                audioSource.PlayOneShot(loadingCompleteSound);
        }

        /// <summary>
        /// Update progress (0-1)
        /// </summary>
        public void UpdateProgress(float progress)
        {
            currentProgress = Mathf.Clamp01(progress);
            progressBar.value = currentProgress;

            if (progressBarFill && progressBarGradient != null)
                progressBarFill.color = progressBarGradient.Evaluate(currentProgress);

            if (progressPercentText)
                progressPercentText.text = $"{(int)(currentProgress * 100)}%";

            // Play milestone effects
            if (Mathf.Approximately(currentProgress % 0.25f, 0f) && currentProgress > 0f)
            {
                if (progressParticles)
                    progressParticles.Play();

                if (audioSource && progressMilestoneSound)
                    audioSource.PlayOneShot(progressMilestoneSound);
            }

            // Auto-advance stages based on progress
            int targetStage = Mathf.FloorToInt(currentProgress * loadingStages.Length);
            if (targetStage > currentStage && targetStage < loadingStages.Length)
            {
                AdvanceToStage(targetStage);
            }
        }

        /// <summary>
        /// Update stage with message
        /// </summary>
        public void UpdateStage(string message)
        {
            if (stageDescriptionText)
            {
                stageDescriptionText.text = message;
                stageDescriptionText.transform.DOPunchScale(Vector3.one * 0.1f, 0.3f);
            }
        }

        /// <summary>
        /// Show error message
        /// </summary>
        public void ShowError(string message)
        {
            if (stageDescriptionText)
            {
                stageDescriptionText.text = $"😕 {message}";
                stageDescriptionText.color = Color.red;
            }

            if (characterAnimator)
                characterAnimator.SetTrigger("Confused");

            Debug.LogError($"[EnhancedLoadingScreen] Error: {message}");
        }

        private void AdvanceToStage(int stage)
        {
            if (stage >= loadingStages.Length)
                return;

            currentStage = stage;
            var current = loadingStages[stage];

            if (stageDescriptionText)
            {
                stageDescriptionText.text = current.description;
                stageDescriptionText.DOColor(current.color, 0.5f);
            }

            // Update character
            if (characterAnimator)
                characterAnimator.SetInteger("State", stage);

            if (characterImage && characterStates.Count > stage)
                characterImage.sprite = characterStates[stage];

            // Update particles
            if (sparkleParticles)
            {
                var main = sparkleParticles.main;
                main.startColor = current.color;
                sparkleParticles.Play();
            }

            // Update indicators
            for (int i = 0; i < stageIndicators.Count; i++)
            {
                int state = i < stage ? 2 : (i == stage ? 1 : 0);
                stageIndicators[i].SetState(state);
            }

            if (audioSource && stageCompleteSound)
                audioSource.PlayOneShot(stageCompleteSound);

            Debug.Log($"[EnhancedLoadingScreen] Advanced to stage: {current.name}");
        }

        private void InitializeStages()
        {
            if (stageIndicatorPrefab == null || stageIndicatorContainer == null)
                return;

            foreach (var stage in loadingStages)
            {
                var indicatorObj = Instantiate(stageIndicatorPrefab, stageIndicatorContainer);
                var indicator = indicatorObj.GetComponent<LoadingStageIndicator>();

                if (indicator != null)
                {
                    indicator.Initialize(stage.iconEmoji, stage.color);
                    stageIndicators.Add(indicator);
                }
            }
        }

        private void InitializeFunFacts()
        {
            funFacts = new List<string>
            {
                "Did you know water covers 71% of Earth? 🌊",
                "Fun fact: Clouds can weigh as much as 100 elephants! ☁️",
                "The human brain has about 86 billion neurons! 🧠",
                "A day on Venus is longer than its year! 🪐",
                "Honey never spoils - archaeologists found 3000-year-old honey! 🍯",
                "Dolphins call each other by name! 🐬",
                "Trees can communicate through underground networks! 🌳",
                "Your heart beats about 100,000 times per day! ❤️"
            };
        }

        private IEnumerator CycleFunFacts()
        {
            while (true)
            {
                if (funFactText && funFacts.Count > 0)
                {
                    funFactText.text = funFacts[Random.Range(0, funFacts.Count)];
                    funFactText.DOFade(1f, 0.5f);
                }

                yield return new WaitForSeconds(4f);

                if (funFactText)
                    funFactText.DOFade(0f, 0.5f);

                yield return new WaitForSeconds(1f);
            }
        }

        /// <summary>
        /// Add custom fun fact
        /// </summary>
        public void AddFunFact(string fact)
        {
            funFacts.Add(fact);
        }

        /// <summary>
        /// Set fun facts for specific curriculum
        /// </summary>
        public void SetCurriculumFacts(List<string> facts)
        {
            if (facts != null && facts.Count > 0)
            {
                funFacts = new List<string>(facts);
            }
        }
    }
}
