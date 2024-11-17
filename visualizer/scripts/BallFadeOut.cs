using System.Collections;
using UnityEngine;

public class BallFadeOut : MonoBehaviour
{
    public float fadeDuration = 0.5f;  // Duration for the fade effect in seconds
    private Material sphereMaterial;
    private Color originalColor;

    void Start()
    {
        // Get the material of the sphere
        sphereMaterial = GetComponent<Renderer>().material;
        originalColor = sphereMaterial.color;

        // Start the fading process after a delay of 0.8 seconds
        StartCoroutine(StartFadeAfterDelay(0.9f));
    }

    private IEnumerator StartFadeAfterDelay(float delay)
    {
        // Wait for the specified delay
        yield return new WaitForSeconds(delay);

        // Start fading out after the delay
        yield return FadeOutCoroutine();
    }

    private IEnumerator FadeOutCoroutine()
    {
        float startAlpha = originalColor.a;
        float time = 0;

        while (time < fadeDuration)
        {
            time += Time.deltaTime;
            float alpha = Mathf.Lerp(startAlpha, 0, time / fadeDuration);
            sphereMaterial.color = new Color(originalColor.r, originalColor.g, originalColor.b, alpha);
            yield return null;
        }
    }
}
