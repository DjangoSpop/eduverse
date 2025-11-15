using System.Collections;
using UnityEngine;
using TMPro;

namespace Eduverse.UI
{
    /// <summary>
    /// Displays dialogue from NPCs and mentors.
    /// </summary>
    public class DialogueUI : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private GameObject dialoguePanel;
        [SerializeField] private TextMeshProUGUI speakerNameText;
        [SerializeField] private TextMeshProUGUI dialogueText;
        [SerializeField] private CanvasGroup canvasGroup;

        [Header("Settings")]
        [SerializeField] private float typingSpeed = 0.05f;
        [SerializeField] private float displayDuration = 3f;
        [SerializeField] private float fadeSpeed = 2f;

        private Coroutine currentDialogue;

        private void Awake()
        {
            if (dialoguePanel != null)
                dialoguePanel.SetActive(false);

            if (canvasGroup == null)
                canvasGroup = GetComponent<CanvasGroup>();
        }

        /// <summary>
        /// Show dialogue from a character.
        /// </summary>
        public void ShowDialogue(string speakerName, string text)
        {
            // Stop current dialogue
            if (currentDialogue != null)
                StopCoroutine(currentDialogue);

            currentDialogue = StartCoroutine(ShowDialogueSequence(speakerName, text));
        }

        /// <summary>
        /// Show dialogue with typing effect.
        /// </summary>
        private IEnumerator ShowDialogueSequence(string speakerName, string text)
        {
            // Show panel
            if (dialoguePanel != null)
                dialoguePanel.SetActive(true);

            // Set speaker name
            if (speakerNameText != null)
                speakerNameText.text = speakerName;

            // Fade in
            if (canvasGroup != null)
            {
                LeanTween.alphaCanvas(canvasGroup, 1f, 1f / fadeSpeed);
            }

            // Type out text
            if (dialogueText != null)
            {
                dialogueText.text = "";

                foreach (char c in text)
                {
                    dialogueText.text += c;
                    yield return new WaitForSeconds(typingSpeed);
                }
            }

            // Wait before hiding
            yield return new WaitForSeconds(displayDuration);

            // Fade out
            if (canvasGroup != null)
            {
                LeanTween.alphaCanvas(canvasGroup, 0f, 1f / fadeSpeed)
                    .setOnComplete(() =>
                    {
                        if (dialoguePanel != null)
                            dialoguePanel.SetActive(false);
                    });
            }
            else
            {
                if (dialoguePanel != null)
                    dialoguePanel.SetActive(false);
            }

            currentDialogue = null;
        }

        /// <summary>
        /// Hide dialogue immediately.
        /// </summary>
        public void Hide()
        {
            if (currentDialogue != null)
                StopCoroutine(currentDialogue);

            if (dialoguePanel != null)
                dialoguePanel.SetActive(false);
        }
    }
}
