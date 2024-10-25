using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.UIElements;

public class ProjectileHandler : MonoBehaviour
{
	public RainChecker rainChecker;
	public SoundHandler soundHandler;

	public Transform player; // Start point (A)
	public Transform enemy;  // End point (B)
	public GameObject basketballToThrow;
	public GameObject soccerToThrow;
	public GameObject bowlingToThrow;
	public GameObject volleyballToThrow;
	public GameObject rainBombToThrow;
	public GameObject rainBombRain;
	public GameObject ballsOnHitExplosionPrefab;

	public float speed = 0.1f; // Speed of projectile movement along the curve
	public float arcHeight = 0.6f; // The height of the arc (dynamic control point)
	private float t = 0f; // Time parameter for curve (0 to 1)
	private GameObject projectileInstance; // Instance of the projectile
	private Vector3 controlPoint; // Calculated control point (E)
	Vector3 pointInFront; // Point in front of player if enemy not in FOV
	private string ballToThrow;
	private bool enemyInFOV;
	void Update()
	{
		if (projectileInstance != null && t <= 1f)
		{
			// Update projectile position along the Bezier curve
			UpdateProjectilePosition();
		}
	}
	public void ThrowBall(string ball, bool inFOV, bool isPlayerThrowing)
	{
		enemyInFOV = inFOV;
		ballToThrow = ball;
		if (isPlayerThrowing)
		{
			switch (ballToThrow)
			{
				default:
					Debug.Log("Unable to get ball");
					break;
				case "basket":
					StartThrow(basketballToThrow);
					break;
				case "soccer":
					StartThrow(soccerToThrow);
					break;
				case "bowl":
					StartThrow(bowlingToThrow);
					break;
				case "volley":
					StartThrow(volleyballToThrow);
					break;
				case "bomb":
					StartThrow(rainBombToThrow);
					break;
			}
		}
		else
		{
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
	}

	public void StartThrow(GameObject projectilePrefab)
	{
		// Instantiate the projectile at the player's position
		projectileInstance = Instantiate(projectilePrefab, player.position, Quaternion.identity);
		Vector3 midpoint;
		if (enemyInFOV)
		{
			// Calculate the dynamic control point
			// Find the midpoint between player and enemy
			midpoint = (player.position + enemy.position) / 2f;
		}
		else
		{
			// When enemy is not in FOV, shoot directly in front of the player
			// Calculate a point some distance in front of the player (along player's forward direction)
			float distanceInFront = 0.5f; // You can adjust this value to control how far ahead the projectile goes
			pointInFront = player.position + player.forward * distanceInFront;

			// Calculate the midpoint between the player and the point in front
			midpoint = (player.position + pointInFront) / 2f;
		}
		// Add an offset in the y-axis to create an arc
		switch (ballToThrow)
		{
			default:
				break;
			case "basket":
			case "volley":
			case "bomb":
				controlPoint = new Vector3(midpoint.x, midpoint.y + arcHeight, midpoint.z );
				break;
			case "soccer":
			case "bowl":
				controlPoint = new Vector3(midpoint.x, midpoint.y, midpoint.z);
				break;
		}

		// Reset t to 0 to start the curve animation
		t = 0f;
	}

	public void UpdateProjectilePosition()
	{
		// Increase t over time, controlling the speed of the projectile
		t += Time.deltaTime * speed;

		// Ensure t stays in the range [0, 1]
		t = Mathf.Clamp01(t);
		Vector3 position;

		// Calculate the projectile position using the quadratic Bezier curve formula
		if (enemyInFOV)
		{
			// Calculate a point in front of the player when enemy is in the field of view
			position = (1 - t) * (1 - t) * player.position +
							   2 * t * (1 - t) * controlPoint +
							   t * t * enemy.position;
		}
		else
		{
			// Calculate a point in front of the player when enemy is not in the field of view
			// Calculate the projectile position using a Bezier curve where the endpoint is in front of the player
			position = (1 - t) * (1 - t) * player.position +
					   2 * t * (1 - t) * controlPoint +
					   t * t * pointInFront;
		}
		// Set the projectile's position to the calculated point
		projectileInstance.transform.position = position;
		// Spins the projectile
		projectileInstance.transform.Rotate(450f * Time.deltaTime, 0f, 0f, Space.Self);

		// Destroy the projectile once reaches target
		if (t >= 1f)
		{
			Destroy(projectileInstance);
			if (enemyInFOV)
			{
				Instantiate(ballsOnHitExplosionPrefab, enemy.position, Quaternion.identity);
				soundHandler.PlayOnHitAudio();
			}

			if (ballToThrow == "bomb")
			{
				GameObject rainBomb = Instantiate(rainBombRain, enemy.position, Quaternion.identity);
				soundHandler.PlayOnHitRainBombAudio();
				rainChecker.GetRainBomb(rainBomb);
			}
		}
	}
	public void ShootBackAtPlayer(GameObject projectilePrefab)
	{
		// Get the middle of the screen in world coordinates
		float distanceFromCamera = Camera.main.nearClipPlane;

		Vector3 screenMiddle = new Vector3(Screen.width / 2, Screen.height / 2, distanceFromCamera);
		Vector3 startMiddlePoint = Camera.main.ScreenToWorldPoint(screenMiddle);

		// Instantiate the projectile at the middle screen point
		projectileInstance = Instantiate(projectilePrefab, startMiddlePoint, Quaternion.identity);

		// Set the control point to create an arc similar to your forward projectile
		Vector3 midpoint = (startMiddlePoint + player.position) / 2f;
		controlPoint = new Vector3(midpoint.x, midpoint.y + arcHeight, midpoint.z);

		// Reset t to start the curve animation
		t = 0f;
	}

	public void UpdateReverseProjectilePosition()
	{
		// Same Bezier curve logic as in UpdateProjectilePosition, but with player as the target
		t += Time.deltaTime * speed;
		t = Mathf.Clamp01(t);

		// Calculate the projectile position using the Bezier curve
		Vector3 position = (1 - t) * (1 - t) * projectileInstance.transform.position +
						   2 * t * (1 - t) * controlPoint +
						   t * t * player.position;

		// Set the projectile's position and rotation
		projectileInstance.transform.position = position;
		projectileInstance.transform.Rotate(450f * Time.deltaTime, 0f, 0f, Space.Self);

		// Destroy the projectile when it reaches the player
		if (t >= 1f)
		{
			Destroy(projectileInstance);
			Instantiate(ballsOnHitExplosionPrefab, player.position, Quaternion.identity);
			soundHandler.PlayOnHitAudio();
		}
	}
}
