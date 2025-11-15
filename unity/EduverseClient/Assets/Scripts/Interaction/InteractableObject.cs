using UnityEngine;
using Eduverse.Data;

namespace Eduverse.Interaction
{
    /// <summary>
    /// Generic interactable object (portals, buttons, etc).
    /// </summary>
    public class InteractableObject : MonoBehaviour
    {
        private GameObjectData data;

        [Header("Interaction Settings")]
        [SerializeField] private float interactionRange = 2f;
        [SerializeField] private bool oneTimeUse = false;

        private bool playerInRange = false;
        private bool hasBeenUsed = false;

        public void Initialize(GameObjectData objectData)
        {
            data = objectData;

            // Add collider for interaction
            var collider = gameObject.AddComponent<SphereCollider>();
            collider.radius = interactionRange;
            collider.isTrigger = true;

            Debug.Log($"[Interactable] Initialized: {data.name}");
        }

        private void Update()
        {
            if (playerInRange && !hasBeenUsed && Input.GetKeyDown(KeyCode.E))
            {
                Interact();
            }
        }

        private void OnTriggerEnter(Collider other)
        {
            if (other.CompareTag("Player"))
            {
                playerInRange = true;
                Debug.Log($"[Interactable] Player in range of {data.name}");
            }
        }

        private void OnTriggerExit(Collider other)
        {
            if (other.CompareTag("Player"))
            {
                playerInRange = false;
            }
        }

        public void Interact()
        {
            if (hasBeenUsed && oneTimeUse)
                return;

            Debug.Log($"[Interactable] Interacted with: {data.name}");

            // Handle based on type
            if (data.type == "portal")
            {
                HandlePortal();
            }

            // Award XP
            var coordinator = FindObjectOfType<Core.GameCoordinator>();
            if (coordinator != null)
            {
                coordinator.AwardXP(data.xp_reward, $"Interacted with {data.name}");
            }

            if (oneTimeUse)
                hasBeenUsed = true;
        }

        private void HandlePortal()
        {
            Debug.Log("[Interactable] Portal activated - loading next scene");

            var coordinator = FindObjectOfType<Core.GameCoordinator>();
            if (coordinator != null)
            {
                coordinator.OnPortalActivated();
            }
        }

        public GameObjectData GetData()
        {
            return data;
        }
    }
}
