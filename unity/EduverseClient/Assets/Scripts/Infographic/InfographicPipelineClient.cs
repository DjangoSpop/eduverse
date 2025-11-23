using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System;

namespace Eduverse.Infographic
{
    /// <summary>
    /// Client for the infographic generation pipeline.
    /// Handles PDF upload, progress tracking, and result retrieval.
    /// </summary>
    public class InfographicPipelineClient : MonoBehaviour
    {
        [Header("Backend Configuration")]
        [SerializeField] private string backendURL = "http://localhost:8000";
        [SerializeField] private int timeout = 120; // 2 minutes

        [Header("References")]
        [SerializeField] private InfographicRenderer renderer;
        [SerializeField] private InfographicAnimationPlayer animationPlayer;

        [Header("UI (Optional)")]
        [SerializeField] private UnityEngine.UI.Slider progressBar;
        [SerializeField] private TMPro.TextMeshProUGUI progressText;

        // Events
        public event Action<string> OnProgressUpdate;
        public event Action<string, string> OnInfographicGenerated; // infographic JSON, animation JSON
        public event Action<string> OnError;

        /// <summary>
        /// Generate infographic from PDF file path.
        /// </summary>
        public void GenerateFromPDF(string pdfPath, string ageRange = "6-10", string style = "colorful")
        {
            StartCoroutine(GenerateFromPDFCoroutine(pdfPath, ageRange, style));
        }

        private IEnumerator GenerateFromPDFCoroutine(string pdfPath, string ageRange, string style)
        {
            UpdateProgress(0f, "Loading PDF...");

            // Read PDF file
            byte[] pdfBytes = null;
            try
            {
                pdfBytes = System.IO.File.ReadAllBytes(pdfPath);
                Debug.Log($"[PipelineClient] Loaded PDF: {pdfBytes.Length} bytes");
            }
            catch (Exception e)
            {
                HandleError($"Failed to load PDF: {e.Message}");
                yield break;
            }

            UpdateProgress(0.1f, "Uploading PDF...");

            // Create multipart form data
            WWWForm form = new WWWForm();
            form.AddBinaryData("file", pdfBytes, System.IO.Path.GetFileName(pdfPath), "application/pdf");

            string url = $"{backendURL}/api/infographic/generate?age_range={ageRange}&style={style}&variations=1";

            using (UnityWebRequest request = UnityWebRequest.Post(url, form))
            {
                request.timeout = timeout;

                var operation = request.SendWebRequest();

                // Poll for progress
                while (!operation.isDone)
                {
                    float progress = Mathf.Clamp01(operation.progress * 0.5f + 0.1f); // 10% to 60%
                    UpdateProgress(progress, "Processing PDF...");
                    yield return null;
                }

                UpdateProgress(0.6f, "Generating infographic...");

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseJson = request.downloadHandler.text;
                    Debug.Log($"[PipelineClient] Response received: {responseJson.Length} chars");

                    UpdateProgress(0.8f, "Parsing results...");

                    try
                    {
                        // Parse response
                        PipelineResponse response = JsonUtility.FromJson<PipelineResponse>(responseJson);

                        if (response.results != null && response.results.Length > 0)
                        {
                            var result = response.results[0];

                            UpdateProgress(0.9f, "Rendering infographic...");

                            // Render infographic
                            string infographicJson = JsonUtility.ToJson(result.infographic);
                            string animationJson = JsonUtility.ToJson(result.animation);

                            OnInfographicGenerated?.Invoke(infographicJson, animationJson);

                            // Render if components are assigned
                            if (renderer != null)
                            {
                                renderer.RenderInfographic(infographicJson);
                            }

                            if (animationPlayer != null)
                            {
                                animationPlayer.LoadAnimation(animationJson, play: true);
                            }

                            UpdateProgress(1f, "Complete!");

                            Debug.Log($"[PipelineClient] Generated: '{result.title}' ({result.element_count} elements, {result.animation_duration}s)");
                        }
                        else
                        {
                            HandleError("No results in response");
                        }
                    }
                    catch (Exception e)
                    {
                        HandleError($"Failed to parse response: {e.Message}");
                    }
                }
                else
                {
                    HandleError($"Request failed: {request.error}\n{request.downloadHandler.text}");
                }
            }
        }

        /// <summary>
        /// Generate infographic from PDF bytes (for runtime-generated PDFs).
        /// </summary>
        public void GenerateFromPDFBytes(byte[] pdfBytes, string filename, string ageRange = "6-10", string style = "colorful")
        {
            StartCoroutine(GenerateFromPDFBytesCoroutine(pdfBytes, filename, ageRange, style));
        }

        private IEnumerator GenerateFromPDFBytesCoroutine(byte[] pdfBytes, string filename, string ageRange, string style)
        {
            UpdateProgress(0.1f, "Preparing PDF...");

            WWWForm form = new WWWForm();
            form.AddBinaryData("file", pdfBytes, filename, "application/pdf");

            string url = $"{backendURL}/api/infographic/generate?age_range={ageRange}&style={style}&variations=1";

            using (UnityWebRequest request = UnityWebRequest.Post(url, form))
            {
                request.timeout = timeout;

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    // Same processing as GenerateFromPDFCoroutine
                    string responseJson = request.downloadHandler.text;
                    ProcessPipelineResponse(responseJson);
                }
                else
                {
                    HandleError($"Request failed: {request.error}");
                }
            }
        }

        private void ProcessPipelineResponse(string responseJson)
        {
            try
            {
                PipelineResponse response = JsonUtility.FromJson<PipelineResponse>(responseJson);

                if (response.results != null && response.results.Length > 0)
                {
                    var result = response.results[0];

                    string infographicJson = JsonUtility.ToJson(result.infographic);
                    string animationJson = JsonUtility.ToJson(result.animation);

                    OnInfographicGenerated?.Invoke(infographicJson, animationJson);

                    if (renderer != null)
                    {
                        renderer.RenderInfographic(infographicJson);
                    }

                    if (animationPlayer != null)
                    {
                        animationPlayer.LoadAnimation(animationJson, play: true);
                    }

                    UpdateProgress(1f, "Complete!");
                }
            }
            catch (Exception e)
            {
                HandleError($"Failed to process response: {e.Message}");
            }
        }

        /// <summary>
        /// Get available infographic styles from backend.
        /// </summary>
        public void GetAvailableStyles(Action<string[]> callback)
        {
            StartCoroutine(GetAvailableStylesCoroutine(callback));
        }

        private IEnumerator GetAvailableStylesCoroutine(Action<string[]> callback)
        {
            string url = $"{backendURL}/api/infographic/styles";

            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    // Parse styles
                    string json = request.downloadHandler.text;
                    StylesResponse response = JsonUtility.FromJson<StylesResponse>(json);

                    string[] styleNames = new string[response.styles.Length];
                    for (int i = 0; i < response.styles.Length; i++)
                    {
                        styleNames[i] = response.styles[i].name;
                    }

                    callback?.Invoke(styleNames);
                }
                else
                {
                    Debug.LogError($"Failed to get styles: {request.error}");
                    callback?.Invoke(new string[] { "colorful", "playful", "minimal" });
                }
            }
        }

        /// <summary>
        /// Get pipeline statistics.
        /// </summary>
        public void GetStats(Action<string> callback)
        {
            StartCoroutine(GetStatsCoroutine(callback));
        }

        private IEnumerator GetStatsCoroutine(Action<string> callback)
        {
            string url = $"{backendURL}/api/infographic/stats";

            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    callback?.Invoke(request.downloadHandler.text);
                }
                else
                {
                    Debug.LogError($"Failed to get stats: {request.error}");
                }
            }
        }

        private void UpdateProgress(float progress, string message)
        {
            if (progressBar != null)
            {
                progressBar.value = progress;
            }

            if (progressText != null)
            {
                progressText.text = message;
            }

            OnProgressUpdate?.Invoke(message);

            Debug.Log($"[PipelineClient] Progress: {progress * 100:F0}% - {message}");
        }

        private void HandleError(string error)
        {
            Debug.LogError($"[PipelineClient] Error: {error}");
            OnError?.Invoke(error);

            if (progressText != null)
            {
                progressText.text = $"Error: {error}";
            }
        }
    }

    // Response data structures
    [Serializable]
    public class PipelineResponse
    {
        public string status;
        public int results_count;
        public PipelineResult[] results;
    }

    [Serializable]
    public class PipelineResult
    {
        public string infographic_id;
        public string title;
        public string subtitle;
        public int element_count;
        public float animation_duration;
        public InfographicData infographic;
        public AnimationData animation;
    }

    [Serializable]
    public class StylesResponse
    {
        public StyleInfo[] styles;
    }

    [Serializable]
    public class StyleInfo
    {
        public string name;
        public string description;
    }
}
