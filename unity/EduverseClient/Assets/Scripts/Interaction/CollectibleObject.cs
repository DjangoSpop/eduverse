using UnityEngine;
using Eduverse.Data;

namespace Eduverse.Interaction
{
    /// <summary>
    /// Collectible object that awards XP when collected.
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public class CollectibleObject : MonoBehaviour
    {
        private GameObjectData data;
        private bool isCollected = false;

        [Header("Visual Effects")]
        [SerializeField] private float rotationSpeed = 50f;
        [SerializeField] private float bobSpeed = 2f;
        [SerializeField] private float bobHeight = 0.3f;

        private Vector3 startPosition;
        private float bobOffset;

        public void Initialize(GameObjectData objectData)
        {
            data = objectData;
            startPosition = transform.localPosition;
            bobOffset = Random.Range(0f, Mathf.PI * 2f);

            // Make sure collider is trigger
            var collider = GetComponent<Collider>();
            if (collider != null)
                collider.isTrigger = true;

            Debug.Log($"[Collectible] Initialized: {data.name} (XP: {data.xp_reward})");
        }

        private void Update()
        {
            if (isCollected)
                return;

            // Rotate
            transform.Rotate(Vector3.up, rotationSpeed * Time.deltaTime);

            // Bob up and down
            float newY = startPosition.y + Mathf.Sin(Time.time * bobSpeed + bobOffset) * bobHeight;
            transform.localPosition = new Vector3(
                transform.localPosition.x,
                newY,
                transform.localPosition.z
            );
        }

        private void OnTriggerEnter(Collider other)
        {
            if (isCollected)
                return;

            // Check if player
            if (other.CompareTag("Player"))
            {
                Collect();
            }
        }

        private void Collect()
        {
            if (isCollected)
                return;

            isCollected = true;

            Debug.Log($"[Collectible] Collected: {data.name} (+{data.xp_reward} XP)");

            // Notify game coordinator
            var coordinator = FindObjectOfType<Core.GameCoordinator>();
            if (coordinator != null)
            {
                coordinator.OnCollectibleCollected(data);
            }

            // Play collection effect
            PlayCollectionEffect();

            // Destroy after animation
            Destroy(gameObject, 0.5f);
        }

        private void PlayCollectionEffect()
        {
            // TODO: Add particle effect
            // TODO: Add sound effect

            // Simple scale animation for now
            LeanTween.scale(gameObject, Vector3.zero, 0.5f)
                .setEaseInBack();
        }

        public GameObjectData GetData()
        {
            return data;
        }

        public bool IsCollected()
        {
            return isCollected;
        }
    }
}
