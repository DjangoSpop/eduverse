using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using Eduverse.Data;

namespace Eduverse.Core
{
    /// <summary>
    /// Loads lessons from backend and builds the 3D world.
    /// Main component responsible for scene generation.
    /// </summary>
    public class LessonLoader : MonoBehaviour
    {
        [Header("Configuration")]
        [SerializeField] private string lessonId = "test-lesson-123";
        [SerializeField] private string learnerId = "test-learner-456";

        [Header("References")]
        [SerializeField] private Transform worldRoot;
        [SerializeField] private LoadingScreen loadingScreen;

        [Header("Prefab Library")]
        [SerializeField] private PrefabLibrary prefabLibrary;

        // Current lesson data
        private SceneSpecification currentLesson;
        private int currentSceneIndex = 0;
        private string currentSessionId;

        // Spawned objects
        private List<GameObject> spawnedObjects = new List<GameObject>();

        #region Initialization

        private void Start()
        {
            if (worldRoot == null)
                worldRoot = transform;

            StartCoroutine(LoadLessonSequence());
        }

        #endregion

        #region Lesson Loading Sequence

        /// <summary>
        /// Main loading sequence.
        /// Fetches lesson from backend and builds the world.
        /// </summary>
        private IEnumerator LoadLessonSequence()
        {
            if (loadingScreen != null)
                loadingScreen.Show();

            // Stage 1: Fetch lesson from backend
            UpdateLoadingStage("Connecting to server...", 0.1f);
            yield return new WaitForSeconds(0.5f);

            bool lessonLoaded = false;
            string errorMessage = null;

            yield return APIClient.Instance.GetLesson(
                lessonId,
                (lesson) => {
                    currentLesson = lesson;
                    lessonLoaded = true;
                    Debug.Log($"[LessonLoader] Loaded lesson: {lesson.title}");
                },
                (error) => {
                    errorMessage = error;
                    Debug.LogError($"[LessonLoader] Failed to load lesson: {error}");
                }
            );

            if (!lessonLoaded)
            {
                ShowError($"Failed to load lesson: {errorMessage}");
                yield break;
            }

            // Stage 2: Start session
            UpdateLoadingStage("Starting session...", 0.3f);
            yield return new WaitForSeconds(0.3f);

            bool sessionStarted = false;

            yield return APIClient.Instance.StartSession(
                learnerId,
                lessonId,
                (response) => {
                    currentSessionId = response.id;
                    sessionStarted = true;
                    Debug.Log($"[LessonLoader] Session started: {currentSessionId}");
                },
                (error) => {
                    Debug.LogWarning($"[LessonLoader] Failed to start session: {error}");
                    // Continue anyway - session tracking is optional
                    sessionStarted = true;
                }
            );

            if (!sessionStarted)
            {
                Debug.LogWarning("[LessonLoader] Continuing without session tracking");
            }

            // Stage 3: Build first scene
            UpdateLoadingStage("Building world...", 0.5f);
            yield return new WaitForSeconds(0.5f);

            yield return BuildScene(currentLesson.scenes[0]);

            // Stage 4: Complete
            UpdateLoadingStage("Ready to play!", 1.0f);
            yield return new WaitForSeconds(0.5f);

            if (loadingScreen != null)
                loadingScreen.Hide();

            // Start gameplay
            StartGameplay();
        }

        #endregion

        #region Scene Building

        /// <summary>
        /// Build a scene from SceneData.
        /// Spawns environment and all game objects.
        /// </summary>
        private IEnumerator BuildScene(SceneData sceneData)
        {
            Debug.Log($"[LessonLoader] Building scene: {sceneData.name}");

            // Clear existing objects
            ClearScene();

            // Load environment
            UpdateLoadingStage($"Loading {sceneData.name}...", 0.6f);

            GameObject environment = null;

            if (prefabLibrary != null)
            {
                environment = prefabLibrary.LoadEnvironment(sceneData.environment_prefab);
            }

            if (environment != null)
            {
                environment.transform.SetParent(worldRoot);
                environment.transform.localPosition = Vector3.zero;
                spawnedObjects.Add(environment);
            }
            else
            {
                Debug.LogWarning($"[LessonLoader] Could not load environment: {sceneData.environment_prefab}");
                // Create placeholder
                environment = GameObject.CreatePrimitive(PrimitiveType.Plane);
                environment.transform.localScale = new Vector3(10, 1, 10);
                environment.transform.SetParent(worldRoot);
                spawnedObjects.Add(environment);
            }

            yield return new WaitForSeconds(0.2f);

            // Spawn game objects
            UpdateLoadingStage("Spawning objects...", 0.7f);

            foreach (var objData in sceneData.objects)
            {
                SpawnGameObject(objData);
                yield return null; // Spread over frames
            }

            // Setup challenges
            UpdateLoadingStage("Preparing challenges...", 0.9f);
            yield return new WaitForSeconds(0.2f);

            Debug.Log($"[LessonLoader] Scene built with {sceneData.objects.Count} objects and {sceneData.challenges.Count} challenges");
        }

        /// <summary>
        /// Spawn a single game object from data.
        /// </summary>
        private GameObject SpawnGameObject(GameObjectData objData)
        {
            GameObject prefab = null;

            if (prefabLibrary != null)
            {
                prefab = prefabLibrary.LoadPrefab(objData.prefab_key);
            }

            GameObject instance;

            if (prefab != null)
            {
                instance = Instantiate(prefab);
            }
            else
            {
                // Create placeholder
                Debug.LogWarning($"[LessonLoader] Prefab not found: {objData.prefab_key}, creating placeholder");
                instance = CreatePlaceholder(objData.type);
            }

            // Set position
            instance.transform.SetParent(worldRoot);
            instance.transform.localPosition = objData.position.ToVector3();
            instance.name = objData.name;

            // Add interactive component
            AddInteractiveComponent(instance, objData);

            spawnedObjects.Add(instance);

            return instance;
        }

        /// <summary>
        /// Create a placeholder object when prefab is missing.
        /// </summary>
        private GameObject CreatePlaceholder(string type)
        {
            GameObject placeholder;

            switch (type)
            {
                case "npc":
                    placeholder = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                    placeholder.GetComponent<Renderer>().material.color = Color.cyan;
                    break;

                case "collectible":
                    placeholder = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                    placeholder.GetComponent<Renderer>().material.color = Color.yellow;
                    placeholder.transform.localScale = Vector3.one * 0.5f;
                    break;

                case "obstacle":
                    placeholder = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    placeholder.GetComponent<Renderer>().material.color = Color.red;
                    break;

                default:
                    placeholder = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    placeholder.GetComponent<Renderer>().material.color = Color.white;
                    break;
            }

            return placeholder;
        }

        /// <summary>
        /// Add interactive component to object based on type.
        /// </summary>
        private void AddInteractiveComponent(GameObject obj, GameObjectData data)
        {
            switch (data.type)
            {
                case "collectible":
                    var collectible = obj.AddComponent<CollectibleObject>();
                    collectible.Initialize(data);
                    break;

                case "npc":
                    var npc = obj.AddComponent<NPCMentor>();
                    npc.Initialize(data);
                    break;

                case "portal":
                    var portal = obj.AddComponent<InteractableObject>();
                    portal.Initialize(data);
                    break;
            }
        }

        /// <summary>
        /// Clear all spawned objects.
        /// </summary>
        private void ClearScene()
        {
            foreach (var obj in spawnedObjects)
            {
                if (obj != null)
                    Destroy(obj);
            }
            spawnedObjects.Clear();
        }

        #endregion

        #region Gameplay Flow

        private void StartGameplay()
        {
            Debug.Log("[LessonLoader] Gameplay started!");

            if (currentLesson != null && currentLesson.scenes.Count > 0)
            {
                var firstScene = currentLesson.scenes[0];
                Debug.Log($"Scene: {firstScene.name}");
                Debug.Log($"Narration: {firstScene.narration}");
            }

            // Notify GameCoordinator
            var coordinator = FindObjectOfType<GameCoordinator>();
            if (coordinator != null)
            {
                coordinator.OnLessonLoaded(currentLesson, currentSessionId);
            }
        }

        #endregion

        #region Loading Screen Helpers

        private void UpdateLoadingStage(string message, float progress)
        {
            if (loadingScreen != null)
            {
                loadingScreen.UpdateProgress(message, progress);
            }
            Debug.Log($"[Loading] {message} ({progress:P0})");
        }

        private void ShowError(string message)
        {
            Debug.LogError($"[LessonLoader] ERROR: {message}");

            if (loadingScreen != null)
            {
                loadingScreen.ShowError(message);
            }
        }

        #endregion

        #region Public Interface

        /// <summary>
        /// Set the lesson ID to load.
        /// </summary>
        public void SetLessonId(string id)
        {
            lessonId = id;
        }

        /// <summary>
        /// Set the learner ID.
        /// </summary>
        public void SetLearnerId(string id)
        {
            learnerId = id;
        }

        /// <summary>
        /// Get current lesson data.
        /// </summary>
        public SceneSpecification GetCurrentLesson()
        {
            return currentLesson;
        }

        /// <summary>
        /// Get current session ID.
        /// </summary>
        public string GetSessionId()
        {
            return currentSessionId;
        }

        #endregion
    }
}
