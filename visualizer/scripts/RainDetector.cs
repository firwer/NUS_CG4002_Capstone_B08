using UnityEngine;

/// <summary>
/// Handles the number of rain GameObjects in contact with the opponent
/// </summary>
public class RainDetector : MonoBehaviour
{
    private CapsuleCollider capsuleCollider;
    public LayerMask rainLayer; // Assign the Rain layer in the Inspector
    void Start()
    {
        // Get the CapsuleCollider component
        capsuleCollider = GetComponent<CapsuleCollider>();
        if (capsuleCollider == null)
        {
            Debug.LogError("RainDetector requires a CapsuleCollider component.");
        }
    }

    public int CountRainsInContact()
    {
        // Calculate the top and bottom points of the capsule
        Vector3 point1 = transform.position + transform.up * (capsuleCollider.height / 2 - capsuleCollider.radius);
        Vector3 point2 = transform.position - transform.up * (capsuleCollider.height / 2 - capsuleCollider.radius);

        // Use OverlapCapsule to detect overlapping rain GameObjects
        Collider[] hits = Physics.OverlapCapsule(point1, point2, capsuleCollider.radius, rainLayer);
        return hits.Length;
    }
}
