using System.Collections.Generic;
using UnityEngine;

namespace Eduverse.Data
{
    /// <summary>
    /// Manages prefab loading for game objects and environments.
    /// Maps prefab keys from backend to actual Unity prefabs.
    /// </summary>
    [CreateAssetMenu(fileName = "PrefabLibrary", menuName = "Eduverse/Prefab Library")]
    public class PrefabLibrary : ScriptableObject
    {
        [System.Serializable]
        public class PrefabEntry
        {
            public string key;
            public GameObject prefab;
        }

        [Header("Environments")]
        [SerializeField] private List<PrefabEntry> environments = new List<PrefabEntry>();

        [Header("Characters")]
        [SerializeField] private List<PrefabEntry> characters = new List<PrefabEntry>();

        [Header("Collectibles")]
        [SerializeField] private List<PrefabEntry> collectibles = new List<PrefabEntry>();

        [Header("Interactables")]
        [SerializeField] private List<PrefabEntry> interactables = new List<PrefabEntry>();

        // Cache for faster lookups
        private Dictionary<string, GameObject> prefabCache;

        private void OnEnable()
        {
            BuildCache();
        }

        /// <summary>
        /// Build prefab lookup cache.
        /// </summary>
        private void BuildCache()
        {
            prefabCache = new Dictionary<string, GameObject>();

            AddToCache(environments);
            AddToCache(characters);
            AddToCache(collectibles);
            AddToCache(interactables);

            Debug.Log($"[PrefabLibrary] Cached {prefabCache.Count} prefabs");
        }

        private void AddToCache(List<PrefabEntry> entries)
        {
            foreach (var entry in entries)
            {
                if (!string.IsNullOrEmpty(entry.key) && entry.prefab != null)
                {
                    prefabCache[entry.key] = entry.prefab;
                }
            }
        }

        /// <summary>
        /// Load environment prefab by key.
        /// </summary>
        public GameObject LoadEnvironment(string key)
        {
            return LoadPrefab(key, "Environment");
        }

        /// <summary>
        /// Load any prefab by key.
        /// </summary>
        public GameObject LoadPrefab(string key, string category = "Prefab")
        {
            if (prefabCache == null)
                BuildCache();

            if (prefabCache.TryGetValue(key, out GameObject prefab))
            {
                Debug.Log($"[PrefabLibrary] Loaded {category}: {key}");
                return prefab;
            }

            Debug.LogWarning($"[PrefabLibrary] {category} not found: {key}");
            return null;
        }

        /// <summary>
        /// Check if prefab exists.
        /// </summary>
        public bool HasPrefab(string key)
        {
            if (prefabCache == null)
                BuildCache();

            return prefabCache.ContainsKey(key);
        }

        /// <summary>
        /// Get all available prefab keys.
        /// </summary>
        public List<string> GetAllKeys()
        {
            if (prefabCache == null)
                BuildCache();

            return new List<string>(prefabCache.Keys);
        }

#if UNITY_EDITOR
        /// <summary>
        /// Add a prefab entry (editor only).
        /// </summary>
        public void AddPrefab(string key, GameObject prefab, string category)
        {
            PrefabEntry entry = new PrefabEntry { key = key, prefab = prefab };

            switch (category.ToLower())
            {
                case "environment":
                    environments.Add(entry);
                    break;
                case "character":
                    characters.Add(entry);
                    break;
                case "collectible":
                    collectibles.Add(entry);
                    break;
                case "interactable":
                    interactables.Add(entry);
                    break;
            }

            BuildCache();
            UnityEditor.EditorUtility.SetDirty(this);
        }
#endif
    }
}
