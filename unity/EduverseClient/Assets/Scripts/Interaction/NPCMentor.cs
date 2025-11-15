using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Eduverse.Data;

namespace Eduverse.Interaction
{
    /// <summary>
    /// NPC Mentor character that guides the learner.
    /// Displays dialogue and provides hints.
    /// </summary>
    public class NPCMentor : MonoBehaviour
    {
        private GameObjectData data;
        private int currentDialogueIndex = 0;

        [Header("Interaction Settings")]
        [SerializeField] private float interactionRange = 3f;
        [SerializeField] private float dialogueDelay = 2f;

        [Header("Visual Feedback")]
        [SerializeField] private GameObject interactionPrompt;

        private bool playerInRange = false;
        private bool isShowingDialogue = false;

        public void Initialize(GameObjectData objectData)
        {
            data = objectData;

            Debug.Log($"[NPC] Initialized: {data.name} with {data.dialogue?.Count ?? 0} dialogue lines");

            // Add sphere collider for interaction range
            var collider = gameObject.AddComponent<SphereCollider>();
            collider.radius = interactionRange;
            collider.isTrigger = true;
        }

        private void Update()
        {
            if (playerInRange && Input.GetKeyDown(KeyCode.E))
            {
                Interact();
            }
        }

        private void OnTriggerEnter(Collider other)
        {
            if (other.CompareTag("Player"))
            {
                playerInRange = true;
                ShowInteractionPrompt(true);
            }
        }

        private void OnTriggerExit(Collider other)
        {
            if (other.CompareTag("Player"))
            {
                playerInRange = false;
                ShowInteractionPrompt(false);
            }
        }

        public void Interact()
        {
            if (isShowingDialogue)
                return;

            if (data.dialogue != null && data.dialogue.Count > 0)
            {
                StartCoroutine(ShowDialogueSequence());
            }
            else
            {
                Debug.LogWarning($"[NPC] {data.name} has no dialogue");
            }
        }

        private IEnumerator ShowDialogueSequence()
        {
            isShowingDialogue = true;

            foreach (string line in data.dialogue)
            {
                ShowDialogue(line);
                yield return new WaitForSeconds(dialogueDelay);
            }

            isShowingDialogue = false;

            // Award XP for talking to NPC
            var coordinator = FindObjectOfType<Core.GameCoordinator>();
            if (coordinator != null)
            {
                coordinator.AwardXP(data.xp_reward, $"Talked to {data.name}");
            }
        }

        private void ShowDialogue(string text)
        {
            Debug.Log($"[{data.name}]: {text}");

            // Show in UI
            var dialogueUI = FindObjectOfType<UI.DialogueUI>();
            if (dialogueUI != null)
            {
                dialogueUI.ShowDialogue(data.name, text);
            }
        }

        private void ShowInteractionPrompt(bool show)
        {
            if (interactionPrompt != null)
            {
                interactionPrompt.SetActive(show);
            }

            // Could also show UI prompt
            Debug.Log($"[NPC] Interaction prompt: {show}");
        }

        public GameObjectData GetData()
        {
            return data;
        }
    }
}
