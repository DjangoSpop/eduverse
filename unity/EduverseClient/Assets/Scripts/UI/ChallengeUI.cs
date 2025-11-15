using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using Eduverse.Data;

namespace Eduverse.UI
{
    /// <summary>
    /// UI for displaying and handling challenges (quiz, drag-drop, etc).
    /// </summary>
    public class ChallengeUI : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private GameObject challengePanel;
        [SerializeField] private TextMeshProUGUI promptText;
        [SerializeField] private TextMeshProUGUI hintText;
        [SerializeField] private Button hintButton;

        [Header("Multiple Choice")]
        [SerializeField] private GameObject multipleChoiceContainer;
        [SerializeField] private Button[] choiceButtons;
        [SerializeField] private TextMeshProUGUI[] choiceTexts;

        [Header("Feedback")]
        [SerializeField] private GameObject correctFeedback;
        [SerializeField] private GameObject incorrectFeedback;
        [SerializeField] private TextMeshProUGUI feedbackText;

        private Challenge currentChallenge;
        private System.Action<bool> onChallengeComplete;
        private bool hintShown = false;

        private void Awake()
        {
            if (challengePanel != null)
                challengePanel.SetActive(false);

            if (hintText != null)
                hintText.gameObject.SetActive(false);

            if (correctFeedback != null)
                correctFeedback.SetActive(false);

            if (incorrectFeedback != null)
                incorrectFeedback.SetActive(false);
        }

        /// <summary>
        /// Show a challenge to the learner.
        /// </summary>
        public void ShowChallenge(Challenge challenge, System.Action<bool> onComplete)
        {
            currentChallenge = challenge;
            onChallengeComplete = onComplete;
            hintShown = false;

            if (challengePanel != null)
                challengePanel.SetActive(true);

            // Set prompt
            if (promptText != null)
                promptText.text = challenge.prompt;

            // Reset hint
            if (hintText != null)
            {
                hintText.gameObject.SetActive(false);
                hintText.text = challenge.hint;
            }

            // Hide feedback
            if (correctFeedback != null)
                correctFeedback.SetActive(false);
            if (incorrectFeedback != null)
                incorrectFeedback.SetActive(false);

            // Setup based on challenge type
            SetupChallengeType(challenge);

            Debug.Log($"[ChallengeUI] Showing challenge: {challenge.prompt}");
        }

        /// <summary>
        /// Setup UI based on challenge type.
        /// </summary>
        private void SetupChallengeType(Challenge challenge)
        {
            // Hide all containers first
            if (multipleChoiceContainer != null)
                multipleChoiceContainer.SetActive(false);

            switch (challenge.type)
            {
                case "multiple_choice":
                    SetupMultipleChoice(challenge);
                    break;

                case "drag_drop":
                    // TODO: Implement drag-drop UI
                    Debug.LogWarning("[ChallengeUI] Drag-drop not yet implemented");
                    break;

                case "voice":
                    // TODO: Implement voice input
                    Debug.LogWarning("[ChallengeUI] Voice input not yet implemented");
                    break;

                default:
                    Debug.LogWarning($"[ChallengeUI] Unknown challenge type: {challenge.type}");
                    break;
            }
        }

        /// <summary>
        /// Setup multiple choice challenge.
        /// </summary>
        private void SetupMultipleChoice(Challenge challenge)
        {
            if (multipleChoiceContainer != null)
                multipleChoiceContainer.SetActive(true);

            if (challenge.choices == null || challenge.choices.Count == 0)
            {
                Debug.LogError("[ChallengeUI] Multiple choice has no choices!");
                return;
            }

            // Setup choice buttons
            for (int i = 0; i < choiceButtons.Length; i++)
            {
                if (i < challenge.choices.Count)
                {
                    choiceButtons[i].gameObject.SetActive(true);
                    choiceTexts[i].text = challenge.choices[i];

                    // Remove previous listeners
                    choiceButtons[i].onClick.RemoveAllListeners();

                    // Add click listener
                    int index = i; // Capture for closure
                    choiceButtons[i].onClick.AddListener(() => OnChoiceSelected(index));
                }
                else
                {
                    choiceButtons[i].gameObject.SetActive(false);
                }
            }
        }

        /// <summary>
        /// Handle choice selection.
        /// </summary>
        private void OnChoiceSelected(int choiceIndex)
        {
            if (currentChallenge == null || currentChallenge.choices == null)
                return;

            string selectedAnswer = currentChallenge.choices[choiceIndex];
            bool isCorrect = selectedAnswer == currentChallenge.correct_answer;

            Debug.Log($"[ChallengeUI] Selected: {selectedAnswer}, Correct: {isCorrect}");

            ShowFeedback(isCorrect);

            // Delay before completing challenge
            StartCoroutine(CompleteAfterDelay(isCorrect, 2f));
        }

        /// <summary>
        /// Show hint button click.
        /// </summary>
        public void OnHintButtonClicked()
        {
            if (hintText != null && !string.IsNullOrEmpty(currentChallenge?.hint))
            {
                hintText.gameObject.SetActive(true);
                hintShown = true;

                if (hintButton != null)
                    hintButton.interactable = false;

                Debug.Log("[ChallengeUI] Hint shown");
            }
        }

        /// <summary>
        /// Show feedback (correct/incorrect).
        /// </summary>
        private void ShowFeedback(bool correct)
        {
            if (correct)
            {
                if (correctFeedback != null)
                {
                    correctFeedback.SetActive(true);

                    if (feedbackText != null)
                        feedbackText.text = GetRandomCorrectFeedback();
                }
            }
            else
            {
                if (incorrectFeedback != null)
                {
                    incorrectFeedback.SetActive(true);

                    if (feedbackText != null)
                        feedbackText.text = GetRandomIncorrectFeedback();
                }
            }
        }

        /// <summary>
        /// Complete challenge after delay.
        /// </summary>
        private IEnumerator CompleteAfterDelay(bool success, float delay)
        {
            yield return new WaitForSeconds(delay);

            Hide();

            onChallengeComplete?.Invoke(success);
        }

        /// <summary>
        /// Hide the challenge UI.
        /// </summary>
        public void Hide()
        {
            if (challengePanel != null)
                challengePanel.SetActive(false);

            currentChallenge = null;
            onChallengeComplete = null;
        }

        #region Feedback Messages

        private string GetRandomCorrectFeedback()
        {
            string[] messages = {
                "Excellent work!",
                "That's correct!",
                "Great job!",
                "You got it!",
                "Perfect!",
                "Well done!",
                "Amazing!"
            };

            return messages[Random.Range(0, messages.Length)];
        }

        private string GetRandomIncorrectFeedback()
        {
            string[] messages = {
                "Not quite. Try again!",
                "Almost! Give it another shot!",
                "Good try! Keep going!",
                "Not this time. You can do it!",
                "Try again - you're learning!"
            };

            return messages[Random.Range(0, messages.Length)];
        }

        #endregion
    }
}
