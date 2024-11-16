using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BallLifeTime : MonoBehaviour
{
    void Start()
    {
        // Destroy the ball after 2 seconds
        Destroy(gameObject, 2f);
    }
}
