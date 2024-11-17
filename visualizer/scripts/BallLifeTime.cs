using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Destroys instantiated ball prefab after 2 seconds
/// </summary>
public class BallLifeTime : MonoBehaviour
{
    void Start()
    {
        // Destroy the ball after 2 seconds
        Destroy(gameObject, 2f);
    }
}
