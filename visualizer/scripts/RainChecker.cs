using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Append rain objects to the list and check if the enemy object is visible.
/// If the enemy object is not visible, disable the rain objects.
/// </summary>
public class RainChecker : MonoBehaviour
{
    public GameObject enemyObject;
    private GameObject rainObject;
    private Renderer rendEnemyObject;
    private List<GameObject> rainObjects = new List<GameObject>();

    // Start is called before the first frame update
    void Start()
    {
        // Cache the renderer component once at the start
        rendEnemyObject = enemyObject.GetComponent<Renderer>();
    }

    // Update is called once per frame
    void Update()
    {
        // Loop through all the rain objects
        foreach (var rainObject in rainObjects)
        {
            if (rendEnemyObject.enabled == false)
            {
                //Debug.Log("CAPSTONE: RainChecker: Enemy not found, disabling rain");
                rainObject.SetActive(false);
            }
            else
            {
                rainObject.SetActive(true);
            }
        }

    }
    public void GetRainBomb(GameObject rainBomb)
    {
        rainObject = rainBomb.transform.Find("StormCloudEffect").Find("Rain").gameObject;
        rainObjects.Add(rainObject); // Add the new rain object to the list
    }
}
