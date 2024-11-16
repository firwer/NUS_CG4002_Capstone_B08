using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Vuforia;

/// <summary>
/// Handles the reset of the world rain gameObjects when the anchor is found
/// by repositioning the rain objects based on the anchor's position.
/// </summary>
public class WorldResetHandler : MonoBehaviour
{
    public ImageTargetBehaviour anchorImageTarget;

    private Vector3 initialAnchorPosition;
    private bool anchorFound = false;

    public List<GameObject> rainObjects = new List<GameObject>();
    public List<Vector3> rainObjectInitalPos = new List<Vector3>();

    private void Start()
    {
        //anchorImageTarget.OnTargetFound += OnAnchorFound;
        //anchorImageTarget.OnTargetLost += OnAnchorLost;
    }
    public void OnAnchorFound()
    {
        StartCoroutine(HandleAnchorFound());
    }
    private IEnumerator HandleAnchorFound()
    {
        // Wait until the anchor's position is updated by Vuforia
        while (anchorImageTarget.transform.position == Vector3.zero)
        {
            yield return null;
        }

        Vector3 currentAnchorPosition = anchorImageTarget.transform.position;

        if (!anchorFound)
        {
            initialAnchorPosition = currentAnchorPosition;
            anchorFound = true;

            Debug.Log($"Initial Anchor Position Set: {initialAnchorPosition}");
        }
        else
        {
            Vector3 offset = currentAnchorPosition - initialAnchorPosition;

            for (int i = 0; i < rainObjects.Count; i++)
            {
                if (rainObjects[i] != null)
                {
                    // Adjust the rain object's position
                    rainObjects[i].transform.position += offset;

                    // Update the initial position
                    rainObjectInitalPos[i] += offset;
                }
            }

            initialAnchorPosition = currentAnchorPosition;
            Debug.Log("Rain objects repositioned based on new anchor position.");
        }
    }

    public void AddRainToList(GameObject rain)
    {
        rainObjects.Add(rain);
        rainObjectInitalPos.Add(rain.transform.position);
    }
}
