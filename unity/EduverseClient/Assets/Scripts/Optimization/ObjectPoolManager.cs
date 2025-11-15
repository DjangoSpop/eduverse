using UnityEngine;
using System.Collections.Generic;
using System;

namespace Eduverse.Optimization
{
    /// <summary>
    /// Object pooling system for efficient asset reuse
    ///
    /// Dramatically reduces garbage collection and instantiation overhead
    /// by reusing GameObjects instead of destroying/creating them.
    ///
    /// Target: 80% asset reuse to achieve 50+ FPS on mobile
    ///
    /// Usage:
    ///   GameObject obj = ObjectPoolManager.Instance.Get(prefab, position, rotation);
    ///   ObjectPoolManager.Instance.Return(obj);
    /// </summary>
    public class ObjectPoolManager : MonoBehaviour
    {
        private static ObjectPoolManager _instance;
        public static ObjectPoolManager Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = FindObjectOfType<ObjectPoolManager>();

                    if (_instance == null)
                    {
                        GameObject go = new GameObject("ObjectPoolManager");
                        _instance = go.AddComponent<ObjectPoolManager>();
                        DontDestroyOnLoad(go);
                    }
                }
                return _instance;
            }
        }

        [Header("Pool Settings")]
        [SerializeField] private int defaultPoolSize = 20;
        [SerializeField] private int maxPoolSize = 100;
        [SerializeField] private bool autoExpand = true;
        [SerializeField] private bool prewarmPools = true;

        [Header("Cleanup Settings")]
        [SerializeField] private bool enableAutoCleanupenabled = true;
        [SerializeField] private float cleanupInterval = 30f;  // Seconds
        [SerializeField] private int inactiveThreshold = 10;   // Objects unused for this many cycles

        // Pool storage
        private Dictionary<int, ObjectPool> pools = new Dictionary<int, ObjectPool>();
        private Transform poolContainer;

        // Statistics
        private PoolStatistics stats = new PoolStatistics();

        private void Awake()
        {
            if (_instance == null)
            {
                _instance = this;
                DontDestroyOnLoad(gameObject);
                Initialize();
            }
            else if (_instance != this)
            {
                Destroy(gameObject);
            }
        }

        private void Initialize()
        {
            // Create pool container
            poolContainer = new GameObject("PoolContainer").transform;
            poolContainer.SetParent(transform);

            Debug.Log("[ObjectPoolManager] Initialized");

            // Start cleanup coroutine
            if (enableAutoCleanupenabled)
            {
                InvokeRepeating(nameof(CleanupInactivePools), cleanupInterval, cleanupInterval);
            }
        }

        /// <summary>
        /// Get an object from the pool
        /// </summary>
        public GameObject Get(GameObject prefab, Vector3 position, Quaternion rotation)
        {
            if (prefab == null)
            {
                Debug.LogError("[ObjectPoolManager] Cannot get null prefab");
                return null;
            }

            int poolKey = prefab.GetInstanceID();

            // Create pool if it doesn't exist
            if (!pools.ContainsKey(poolKey))
            {
                CreatePool(prefab, defaultPoolSize);
            }

            ObjectPool pool = pools[poolKey];
            GameObject obj = pool.Get();

            if (obj == null)
            {
                // Pool exhausted, create new instance
                if (autoExpand && pool.GetTotalCount() < maxPoolSize)
                {
                    obj = CreateNewInstance(prefab, pool);
                    Debug.LogWarning($"[ObjectPoolManager] Pool expanded for {prefab.name}");
                }
                else
                {
                    Debug.LogError($"[ObjectPoolManager] Pool exhausted for {prefab.name}, max size reached");
                    return null;
                }
            }

            // Setup object
            obj.transform.position = position;
            obj.transform.rotation = rotation;
            obj.SetActive(true);

            // Update statistics
            stats.totalGets++;
            stats.activeObjects++;

            return obj;
        }

        /// <summary>
        /// Get an object from the pool (with default position/rotation)
        /// </summary>
        public GameObject Get(GameObject prefab)
        {
            return Get(prefab, Vector3.zero, Quaternion.identity);
        }

        /// <summary>
        /// Return an object to the pool
        /// </summary>
        public void Return(GameObject obj)
        {
            if (obj == null)
            {
                Debug.LogWarning("[ObjectPoolManager] Attempted to return null object");
                return;
            }

            // Find which pool this object belongs to
            int poolKey = GetPoolKeyForObject(obj);

            if (poolKey == 0 || !pools.ContainsKey(poolKey))
            {
                Debug.LogWarning($"[ObjectPoolManager] No pool found for {obj.name}, destroying instead");
                Destroy(obj);
                return;
            }

            ObjectPool pool = pools[poolKey];

            // Reset object
            obj.transform.SetParent(poolContainer);
            obj.SetActive(false);

            // Return to pool
            pool.Return(obj);

            // Update statistics
            stats.totalReturns++;
            stats.activeObjects--;
        }

        /// <summary>
        /// Return object after delay
        /// </summary>
        public void ReturnAfterDelay(GameObject obj, float delay)
        {
            StartCoroutine(ReturnAfterDelayCoroutine(obj, delay));
        }

        private System.Collections.IEnumerator ReturnAfterDelayCoroutine(GameObject obj, float delay)
        {
            yield return new WaitForSeconds(delay);
            Return(obj);
        }

        /// <summary>
        /// Create a new pool for a prefab
        /// </summary>
        public void CreatePool(GameObject prefab, int initialSize)
        {
            if (prefab == null)
            {
                Debug.LogError("[ObjectPoolManager] Cannot create pool for null prefab");
                return;
            }

            int poolKey = prefab.GetInstanceID();

            if (pools.ContainsKey(poolKey))
            {
                Debug.LogWarning($"[ObjectPoolManager] Pool already exists for {prefab.name}");
                return;
            }

            ObjectPool pool = new ObjectPool(prefab, poolContainer);
            pools[poolKey] = pool;

            // Prewarm pool
            if (prewarmPools)
            {
                for (int i = 0; i < initialSize; i++)
                {
                    GameObject obj = CreateNewInstance(prefab, pool);
                    obj.SetActive(false);
                    pool.Return(obj);
                }

                Debug.Log($"[ObjectPoolManager] Created pool for {prefab.name} with {initialSize} objects");
            }

            stats.totalPools++;
        }

        /// <summary>
        /// Create a new instance for a pool
        /// </summary>
        private GameObject CreateNewInstance(GameObject prefab, ObjectPool pool)
        {
            GameObject obj = Instantiate(prefab, poolContainer);
            obj.name = $"{prefab.name} (Pooled)";

            // Add pool tracking component
            var tracker = obj.AddComponent<PooledObjectTracker>();
            tracker.poolKey = prefab.GetInstanceID();

            pool.IncrementTotalCount();

            stats.totalInstantiations++;

            return obj;
        }

        /// <summary>
        /// Get pool key for an object
        /// </summary>
        private int GetPoolKeyForObject(GameObject obj)
        {
            var tracker = obj.GetComponent<PooledObjectTracker>();
            return tracker != null ? tracker.poolKey : 0;
        }

        /// <summary>
        /// Cleanup inactive pools
        /// </summary>
        private void CleanupInactivePools()
        {
            Debug.Log("[ObjectPoolManager] Running pool cleanup...");

            int destroyedObjects = 0;

            foreach (var kvp in pools)
            {
                ObjectPool pool = kvp.Value;
                destroyedObjects += pool.CleanupInactive(inactiveThreshold);
            }

            if (destroyedObjects > 0)
            {
                Debug.Log($"[ObjectPoolManager] Cleaned up {destroyedObjects} inactive objects");
                Resources.UnloadUnusedAssets();
            }
        }

        /// <summary>
        /// Clear all pools
        /// </summary>
        public void ClearAllPools()
        {
            Debug.Log("[ObjectPoolManager] Clearing all pools");

            foreach (var pool in pools.Values)
            {
                pool.Clear();
            }

            pools.Clear();
            stats = new PoolStatistics();

            Resources.UnloadUnusedAssets();
        }

        /// <summary>
        /// Get pool statistics
        /// </summary>
        public PoolStatistics GetStatistics()
        {
            stats.poolCount = pools.Count;
            stats.reuseRate = stats.totalGets > 0 ? 1f - ((float)stats.totalInstantiations / stats.totalGets) : 0f;

            return stats;
        }

        /// <summary>
        /// Get pool info for debugging
        /// </summary>
        public string GetPoolInfo()
        {
            var info = new System.Text.StringBuilder();
            info.AppendLine($"=== Object Pool Manager Stats ===");
            info.AppendLine($"Total Pools: {pools.Count}");
            info.AppendLine($"Active Objects: {stats.activeObjects}");
            info.AppendLine($"Total Gets: {stats.totalGets}");
            info.AppendLine($"Total Returns: {stats.totalReturns}");
            info.AppendLine($"Reuse Rate: {stats.reuseRate:P1}");
            info.AppendLine();

            foreach (var kvp in pools)
            {
                ObjectPool pool = kvp.Value;
                info.AppendLine($"{pool.prefab.name}: Available={pool.GetAvailableCount()}, Total={pool.GetTotalCount()}");
            }

            return info.ToString();
        }

        private void OnDestroy()
        {
            ClearAllPools();
        }
    }

    /// <summary>
    /// Individual object pool
    /// </summary>
    public class ObjectPool
    {
        public GameObject prefab;
        private Queue<GameObject> available = new Queue<GameObject>();
        private Transform container;
        private int totalCount = 0;
        private int inactiveCount = 0;

        public ObjectPool(GameObject prefab, Transform container)
        {
            this.prefab = prefab;
            this.container = container;
        }

        public GameObject Get()
        {
            GameObject obj = null;

            while (available.Count > 0)
            {
                obj = available.Dequeue();

                // Check if object was destroyed externally
                if (obj != null)
                {
                    inactiveCount = 0;  // Reset inactive counter
                    return obj;
                }
            }

            return null;  // Pool exhausted
        }

        public void Return(GameObject obj)
        {
            if (obj == null) return;

            available.Enqueue(obj);
        }

        public int GetAvailableCount()
        {
            return available.Count;
        }

        public int GetTotalCount()
        {
            return totalCount;
        }

        public void IncrementTotalCount()
        {
            totalCount++;
        }

        public int CleanupInactive(int threshold)
        {
            if (available.Count == 0)
            {
                inactiveCount++;
            }
            else
            {
                inactiveCount = 0;
            }

            // If pool hasn't been used in a while, shrink it
            if (inactiveCount >= threshold && available.Count > 0)
            {
                int destroyCount = Mathf.Min(available.Count / 2, 10);  // Destroy up to half or 10, whichever is smaller
                int destroyed = 0;

                for (int i = 0; i < destroyCount; i++)
                {
                    if (available.Count == 0) break;

                    GameObject obj = available.Dequeue();
                    if (obj != null)
                    {
                        UnityEngine.Object.Destroy(obj);
                        totalCount--;
                        destroyed++;
                    }
                }

                return destroyed;
            }

            return 0;
        }

        public void Clear()
        {
            while (available.Count > 0)
            {
                GameObject obj = available.Dequeue();
                if (obj != null)
                {
                    UnityEngine.Object.Destroy(obj);
                }
            }

            totalCount = 0;
        }
    }

    /// <summary>
    /// Component to track which pool an object belongs to
    /// </summary>
    public class PooledObjectTracker : MonoBehaviour
    {
        public int poolKey;
    }

    /// <summary>
    /// Pool statistics
    /// </summary>
    [Serializable]
    public class PoolStatistics
    {
        public int poolCount;
        public int activeObjects;
        public int totalGets;
        public int totalReturns;
        public int totalInstantiations;
        public int totalPools;
        public float reuseRate;  // 0-1, target is 0.8 (80%)
    }
}
