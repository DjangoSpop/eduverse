using UnityEngine;
using System.Collections.Generic;

namespace Eduverse.Optimization
{
    /// <summary>
    /// Level of Detail (LOD) System Manager
    ///
    /// Optimizes rendering performance by automatically adjusting
    /// model complexity based on camera distance.
    ///
    /// Features:
    /// - Automatic LOD group configuration
    /// - Dynamic quality adjustment based on framerate
    /// - Mobile-optimized settings
    /// - Occlusion culling support
    ///
    /// Target: Maintain 50+ FPS on mid-range mobile devices
    /// </summary>
    public class LODSystemManager : MonoBehaviour
    {
        private static LODSystemManager _instance;
        public static LODSystemManager Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = FindObjectOfType<LODSystemManager>();

                    if (_instance == null)
                    {
                        GameObject go = new GameObject("LODSystemManager");
                        _instance = go.AddComponent<LODSystemManager>();
                        DontDestroyOnLoad(go);
                    }
                }
                return _instance;
            }
        }

        [Header("LOD Settings")]
        [SerializeField] private QualityPreset qualityPreset = QualityPreset.Medium;
        [SerializeField] private bool autoAdjustQuality = true;
        [SerializeField] private float targetFramerate = 50f;

        [Header("Distance Thresholds (Mobile Optimized)")]
        [SerializeField] private float lodHighDistance = 10f;      // Switch to medium detail
        [SerializeField] private float lodMediumDistance = 20f;    // Switch to low detail
        [SerializeField] private float lodLowDistance = 35f;       // Switch to culled
        [SerializeField] private float cullDistance = 50f;         // Completely disable

        [Header("Performance Monitoring")]
        [SerializeField] private bool enablePerformanceMonitoring = true;
        [SerializeField] private float monitoringInterval = 1f;
        [SerializeField] private int framerateWindowSize = 30;

        // State
        private Camera mainCamera;
        private List<LODGroup> managedLODGroups = new List<LODGroup>();
        private Queue<float> recentFramerates = new Queue<float>();
        private float lastMonitorTime;
        private int qualityAdjustments = 0;

        // Statistics
        private LODStatistics stats = new LODStatistics();

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
            mainCamera = Camera.main;

            if (mainCamera == null)
            {
                Debug.LogWarning("[LODSystemManager] No main camera found");
            }

            // Apply quality preset
            ApplyQualityPreset(qualityPreset);

            Debug.Log($"[LODSystemManager] Initialized with {qualityPreset} quality preset");
        }

        private void Update()
        {
            if (enablePerformanceMonitoring && Time.time - lastMonitorTime > monitoringInterval)
            {
                MonitorPerformance();
                lastMonitorTime = Time.time;
            }
        }

        /// <summary>
        /// Setup LOD for a GameObject
        /// </summary>
        public LODGroup SetupLOD(GameObject target, LODQuality quality = LODQuality.Auto)
        {
            if (target == null)
            {
                Debug.LogError("[LODSystemManager] Cannot setup LOD for null object");
                return null;
            }

            // Check if LODGroup already exists
            LODGroup lodGroup = target.GetComponent<LODGroup>();

            if (lodGroup == null)
            {
                lodGroup = target.AddComponent<LODGroup>();
            }

            // Configure LOD levels
            ConfigureLODGroup(lodGroup, quality == LODQuality.Auto ? qualityPreset : (QualityPreset)quality);

            // Track this LOD group
            if (!managedLODGroups.Contains(lodGroup))
            {
                managedLODGroups.Add(lodGroup);
            }

            stats.totalLODGroups++;

            Debug.Log($"[LODSystemManager] Setup LOD for {target.name}");

            return lodGroup;
        }

        /// <summary>
        /// Configure LOD group with appropriate levels
        /// </summary>
        private void ConfigureLODGroup(LODGroup lodGroup, QualityPreset preset)
        {
            // Get all renderers
            Renderer[] renderers = lodGroup.GetComponentsInChildren<Renderer>();

            if (renderers.Length == 0)
            {
                Debug.LogWarning($"[LODSystemManager] No renderers found on {lodGroup.gameObject.name}");
                return;
            }

            // Define LOD levels based on preset
            LOD[] lods;

            switch (preset)
            {
                case QualityPreset.VeryLow:
                    lods = CreateVeryLowQualityLODs(renderers);
                    break;

                case QualityPreset.Low:
                    lods = CreateLowQualityLODs(renderers);
                    break;

                case QualityPreset.Medium:
                    lods = CreateMediumQualityLODs(renderers);
                    break;

                case QualityPreset.High:
                    lods = CreateHighQualityLODs(renderers);
                    break;

                default:
                    lods = CreateMediumQualityLODs(renderers);
                    break;
            }

            // Apply LODs
            lodGroup.SetLODs(lods);
            lodGroup.RecalculateBounds();

            // Set fade mode for smoother transitions
            lodGroup.fadeMode = LODFadeMode.CrossFade;
            lodGroup.animateCrossFading = true;
        }

        /// <summary>
        /// Create Very Low quality LODs (mobile low-end)
        /// </summary>
        private LOD[] CreateVeryLowQualityLODs(Renderer[] renderers)
        {
            return new LOD[]
            {
                // LOD 0: Low detail (0-70%)
                new LOD(0.7f, renderers),

                // LOD 1: Culled (70-100%)
                new LOD(0.01f, new Renderer[0])
            };
        }

        /// <summary>
        /// Create Low quality LODs (mobile mid-range)
        /// </summary>
        private LOD[] CreateLowQualityLODs(Renderer[] renderers)
        {
            return new LOD[]
            {
                // LOD 0: Medium detail (0-50%)
                new LOD(0.5f, renderers),

                // LOD 1: Low detail (50-85%)
                new LOD(0.15f, renderers),

                // LOD 2: Culled (85-100%)
                new LOD(0.01f, new Renderer[0])
            };
        }

        /// <summary>
        /// Create Medium quality LODs (mobile high-end / tablet)
        /// </summary>
        private LOD[] CreateMediumQualityLODs(Renderer[] renderers)
        {
            return new LOD[]
            {
                // LOD 0: High detail (0-40%)
                new LOD(0.4f, renderers),

                // LOD 1: Medium detail (40-70%)
                new LOD(0.3f, renderers),

                // LOD 2: Low detail (70-90%)
                new LOD(0.1f, renderers),

                // LOD 3: Culled (90-100%)
                new LOD(0.01f, new Renderer[0])
            };
        }

        /// <summary>
        /// Create High quality LODs (desktop / high-end devices)
        /// </summary>
        private LOD[] CreateHighQualityLODs(Renderer[] renderers)
        {
            return new LOD[]
            {
                // LOD 0: Very high detail (0-30%)
                new LOD(0.3f, renderers),

                // LOD 1: High detail (30-50%)
                new LOD(0.2f, renderers),

                // LOD 2: Medium detail (50-75%)
                new LOD(0.25f, renderers),

                // LOD 3: Low detail (75-95%)
                new LOD(0.2f, renderers),

                // LOD 4: Culled (95-100%)
                new LOD(0.01f, new Renderer[0])
            };
        }

        /// <summary>
        /// Apply quality preset globally
        /// </summary>
        public void ApplyQualityPreset(QualityPreset preset)
        {
            qualityPreset = preset;

            // Update distance thresholds based on preset
            switch (preset)
            {
                case QualityPreset.VeryLow:
                    lodHighDistance = 5f;
                    lodMediumDistance = 10f;
                    lodLowDistance = 15f;
                    cullDistance = 20f;
                    QualitySettings.lodBias = 0.5f;
                    break;

                case QualityPreset.Low:
                    lodHighDistance = 8f;
                    lodMediumDistance = 15f;
                    lodLowDistance = 25f;
                    cullDistance = 35f;
                    QualitySettings.lodBias = 0.7f;
                    break;

                case QualityPreset.Medium:
                    lodHighDistance = 10f;
                    lodMediumDistance = 20f;
                    lodLowDistance = 35f;
                    cullDistance = 50f;
                    QualitySettings.lodBias = 1.0f;
                    break;

                case QualityPreset.High:
                    lodHighDistance = 15f;
                    lodMediumDistance = 30f;
                    lodLowDistance = 50f;
                    cullDistance = 75f;
                    QualitySettings.lodBias = 1.5f;
                    break;
            }

            // Reconfigure all managed LOD groups
            foreach (var lodGroup in managedLODGroups)
            {
                if (lodGroup != null)
                {
                    ConfigureLODGroup(lodGroup, preset);
                }
            }

            Debug.Log($"[LODSystemManager] Applied {preset} quality preset");

            qualityAdjustments++;
        }

        /// <summary>
        /// Monitor performance and auto-adjust quality
        /// </summary>
        private void MonitorPerformance()
        {
            if (!autoAdjustQuality) return;

            float currentFPS = 1f / Time.deltaTime;

            recentFramerates.Enqueue(currentFPS);

            // Keep only recent samples
            while (recentFramerates.Count > framerateWindowSize)
            {
                recentFramerates.Dequeue();
            }

            // Calculate average FPS
            float avgFPS = 0f;
            foreach (float fps in recentFramerates)
            {
                avgFPS += fps;
            }
            avgFPS /= recentFramerates.Count;

            stats.currentFPS = avgFPS;
            stats.averageFPS = avgFPS;

            // Auto-adjust quality based on performance
            if (avgFPS < targetFramerate - 10f)  // Significantly below target
            {
                // Decrease quality
                if (qualityPreset > QualityPreset.VeryLow)
                {
                    ApplyQualityPreset(qualityPreset - 1);
                    Debug.LogWarning($"[LODSystemManager] Performance below target ({avgFPS:F1} FPS), " +
                                   $"reducing quality to {qualityPreset}");
                }
            }
            else if (avgFPS > targetFramerate + 20f)  // Well above target
            {
                // Increase quality
                if (qualityPreset < QualityPreset.High)
                {
                    ApplyQualityPreset(qualityPreset + 1);
                    Debug.Log($"[LODSystemManager] Performance excellent ({avgFPS:F1} FPS), " +
                             $"increasing quality to {qualityPreset}");
                }
            }
        }

        /// <summary>
        /// Enable occlusion culling for a camera
        /// </summary>
        public void EnableOcclusionCulling(Camera camera = null)
        {
            if (camera == null)
            {
                camera = mainCamera;
            }

            if (camera == null)
            {
                Debug.LogError("[LODSystemManager] No camera provided for occlusion culling");
                return;
            }

            camera.useOcclusionCulling = true;

            Debug.Log($"[LODSystemManager] Enabled occlusion culling for {camera.name}");
        }

        /// <summary>
        /// Get current statistics
        /// </summary>
        public LODStatistics GetStatistics()
        {
            stats.managedLODGroups = managedLODGroups.Count;
            stats.currentQualityPreset = qualityPreset;
            stats.qualityAdjustments = qualityAdjustments;

            return stats;
        }

        /// <summary>
        /// Remove LOD from object
        /// </summary>
        public void RemoveLOD(GameObject target)
        {
            if (target == null) return;

            LODGroup lodGroup = target.GetComponent<LODGroup>();

            if (lodGroup != null)
            {
                managedLODGroups.Remove(lodGroup);
                Destroy(lodGroup);

                Debug.Log($"[LODSystemManager] Removed LOD from {target.name}");
            }
        }

        /// <summary>
        /// Clear all managed LOD groups
        /// </summary>
        public void ClearAllLODs()
        {
            managedLODGroups.Clear();
            stats = new LODStatistics();

            Debug.Log("[LODSystemManager] Cleared all LOD groups");
        }

        /// <summary>
        /// Get debug info
        /// </summary>
        public string GetDebugInfo()
        {
            var info = new System.Text.StringBuilder();
            info.AppendLine($"=== LOD System Manager ===");
            info.AppendLine($"Quality Preset: {qualityPreset}");
            info.AppendLine($"Managed LOD Groups: {managedLODGroups.Count}");
            info.AppendLine($"Current FPS: {stats.currentFPS:F1}");
            info.AppendLine($"Average FPS: {stats.averageFPS:F1}");
            info.AppendLine($"Target FPS: {targetFramerate}");
            info.AppendLine($"Quality Adjustments: {qualityAdjustments}");
            info.AppendLine($"LOD Bias: {QualitySettings.lodBias:F2}");

            return info.ToString();
        }
    }

    // Enums and data structures

    public enum QualityPreset
    {
        VeryLow = 0,   // Mobile low-end (old devices)
        Low = 1,       // Mobile mid-range
        Medium = 2,    // Mobile high-end / tablets (DEFAULT)
        High = 3       // Desktop / high-end devices
    }

    public enum LODQuality
    {
        Auto = -1,     // Use global preset
        VeryLow = 0,
        Low = 1,
        Medium = 2,
        High = 3
    }

    [System.Serializable]
    public class LODStatistics
    {
        public int totalLODGroups;
        public int managedLODGroups;
        public QualityPreset currentQualityPreset;
        public float currentFPS;
        public float averageFPS;
        public int qualityAdjustments;
    }
}
