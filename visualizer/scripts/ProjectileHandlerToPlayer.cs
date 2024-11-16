using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ProjectileHandlerToPlayer : MonoBehaviour
{
    public SoundHandler soundHandler;

    public Transform player; // Start point (A)
    public GameObject basketballToThrow;
    public GameObject soccerToThrow;
    public GameObject bowlingToThrow;
    public GameObject volleyballToThrow;
    public GameObject rainBombToThrow;
    public GameObject ballsOnHitExplosionPrefab;

    public float speed = 1f; // Speed of projectile movement along the curve
    public float arcHeightToPlayer = 0.3f;
    private float t = 0f; // Time parameter for curve (0 to 1)
    private GameObject projectileInstance; // Instance of the projectile
    private Vector3 controlPoint; // Calculated control point (E)
    Vector3 pointInFront; // Point in front of player if enemy not in FOV
    private string ballToThrow;
    private bool enemyInFOV;

    // Update is called once per frame
    void Update()
    {
        if (projectileInstance != null && t <= 1f)
        {
            // Update projectile position along the Bezier curve
            UpdateReverseProjectilePosition();
        }
    }

    public void ThrowBallToPlayer(string ball, bool inFOV)
    {
        enemyInFOV = inFOV;
        ballToThrow = ball;

        Debug.Log("CAPSTONE: PlayerNotThrowing ball");
        switch (ballToThrow)
        {
            default:
                Debug.Log("Unable to get ball");
                break;
            case "basket":
                ShootBackAtPlayer(basketballToThrow);
                break;
            case "soccer":
                ShootBackAtPlayer(soccerToThrow);
                break;
            case "bowl":
                ShootBackAtPlayer(bowlingToThrow);
                break;
            case "volley":
                ShootBackAtPlayer(volleyballToThrow);
                break;
            case "bomb":
                ShootBackAtPlayer(rainBombToThrow);
                break;
        }
    }

    public void ShootBackAtPlayer(GameObject projectilePrefab)
    {
        Debug.Log("CAPSTONE: ProjectileHandlerToPlayer: ShootBackAtPlayer called");
        // Get the middle of the screen in world coordinates
        float distanceFromCamera = 2f;

        pointInFront = player.position + player.forward * distanceFromCamera;
        // Calculate the midpoint between the player and the point in front
        Vector3 midpoint = (player.position + pointInFront) / 2f;
        projectileInstance = Instantiate(projectilePrefab, pointInFront, Quaternion.identity);

        // Set the control point to create an arc similar to your forward projectile
        controlPoint = new Vector3(midpoint.x, midpoint.y + arcHeightToPlayer, midpoint.z);

        // Reset t to start the curve animation
        t = 0f;
    }

    public void UpdateReverseProjectilePosition()
    {
        // Same Bezier curve logic as in UpdateProjectilePosition, but with player as the target
        t += Time.deltaTime * speed;
        t = Mathf.Clamp01(t);

        // Calculate the projectile position using the Bezier curve
        Vector3 position = (1 - t) * (1 - t) * pointInFront +
                           2 * t * (1 - t) * controlPoint +
                           t * t * player.position;

        // Set the projectile's position and rotation
        projectileInstance.transform.position = position;
        projectileInstance.transform.Rotate(450f * Time.deltaTime, 0f, 0f, Space.Self);

        // Destroy the projectile when it reaches the player
        if (t >= 1f)
        {
            Destroy(projectileInstance);
        }
    }
}
