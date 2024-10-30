using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using Vuforia;
using Image = UnityEngine.UI.Image;

public class UIHandler : MonoBehaviour
{
	public ProjectileHandler projectileHandler;
	public SoundHandler soundHandler;

	public GameObject enemyWindow;
	public GameObject enemyShieldPrefab;
	public GameObject enemyGameObject;
	public GameObject gunShotPrefab;
	public ImageTargetBehaviour imageTargetBehaviour;

	public TMP_Text errorReloadText;
	public TMP_Text errorGunText;
	public TMP_Text errorBombText;
	public TMP_Text errorShieldText;

	private TMP_Text playerNumText;
	private TMP_Text settingsTextDescription;
	private Image healthImage;
	private TMP_Text healthNum;
	private Image shieldImage;
    public GameObject shieldBarWindow;
    public GameObject equipShieldIcon;
	private TMP_Text shieldHealthNum;
	private TMP_Text shieldAmmo;
	private TMP_Text bulletsNum;
    private TMP_Text bombsNum;
	private TMP_Text killsNum;
	private TMP_Text deathsNum;
	private Image reloadImage;
	public GameObject reloadWindow;
	private float reloadProgress;

	private float errorReloadTextDisplayTime = 1f;
	private float errorReloadTextRemaining = 0f;
	private float errorGunTextDisplayTime = 1f;
	private float errorGunTextRemaining = 0f;
	private float errorBombTextDisplayTime = 1f;
	private float errorBombTextRemaining = 0f;
	private float errorShieldTextDisplayTime = 1f;
	private float errorShieldTextRemaining = 0f;

	// For Enemy UI
	private Image enemyHealthImage;
	private TMP_Text enemyHealthNum;
	public GameObject enemyShieldBarWindow;
	private Image enemyShieldImage;
	private TMP_Text enemyShieldHealthNum;
	private Renderer rendEnemyObject;

	// Sets low hp overlay variables
	public Image lowHealthOverlay;	
	public float lowHpDuration;
	public float lowHpFadeSpeed;

	// Sets equip shield overlay variables
	public Image equipShieldOverlay;
	public float equipShieldDuration;
	public float equipShieldFadeSpeed;

	// Sets low hp overlay variables
	public Image deathOverlay;
	public float deathDuration;
	public float deathFadeSpeed;

	private float lowHpDurationTimer;
	private float equipShieldDurationTimer;
	private float deathDurationTimer;

	// For enemy shield bubble object
	private GameObject instantiatedObject;

	public void SetMaxHealth()
    {
        healthImage.fillAmount = 1.0f;
        healthNum.text = "100";
    }
    public void SetMaxBullets()
    {
        bulletsNum.text = "6";
    }
    public void SetMaxBombs()
    {
        bombsNum.text = "2";
    }
	public void SetMaxShieldAmmo()
	{
		shieldAmmo.text = "3";
		shieldBarWindow.gameObject.SetActive(false);
		equipShieldIcon.gameObject.SetActive(false);
	}

	public void SetMaxShield()
    {
		shieldBarWindow.gameObject.SetActive(true);
		equipShieldIcon.gameObject.SetActive(true);
		shieldImage.fillAmount = 1.0f;
		shieldHealthNum.text = "30";
		equipShieldDurationTimer = 0;
		equipShieldOverlay.color = new Color(equipShieldOverlay.color.r, equipShieldOverlay.color.g, equipShieldOverlay.color.b, 0.4f);

		// Play equip shield sfx
		soundHandler.PlayEquipShieldAudio();
	}
	public void SetKD()
	{
		deathsNum.text = "0";
		killsNum.text = "0";
	}

	public void SetShield(int shields, int shieldHealth)
	{
		shieldAmmo.text = shields.ToString();
		shieldImage.fillAmount = (float)shieldHealth / 30;
		shieldHealthNum.text = shieldHealth.ToString();
	}

    public void SetHealth(int health, int shields, int shieldHealth)
    {
		if (health == 100)
		{
			soundHandler.PlayReviveAudio();
			return;
		}

        if (shieldHealth == 0)
        {
            shieldBarWindow.gameObject.SetActive(false);
			equipShieldIcon.gameObject.SetActive(false);
		}
        else
        {
            SetShield(shields, shieldHealth);
        }
		
		// For red flashing screen upon taking dmg
		lowHpDurationTimer = 0;
		lowHealthOverlay.color = new Color(lowHealthOverlay.color.r, lowHealthOverlay.color.g, lowHealthOverlay.color.b, 0.4f);
		// Update health bar
		healthImage.fillAmount = (float)health / 100;
        healthNum.text = health.ToString();

		// Play take damage sfx
		soundHandler.PlayTakeDamageAudio();
	}

	public void UpdateDeaths(int deaths)
	{
		deathsNum.text = deaths.ToString();
	}

	public void UpdateKills(int kills)
	{
		killsNum.text = kills.ToString();
	}

	public void SetDeath()
	{   
		// For grey flashing screen upon death
		deathDurationTimer = 0;
		deathOverlay.color = new Color(deathOverlay.color.r, deathOverlay.color.g, deathOverlay.color.b, 0.8f);
		SetMaxHealth();
		SetMaxBullets();
		SetMaxBombs();
		SetMaxShieldAmmo();

		// Play died sfx
		soundHandler.PlayDiedAudio();
	}

	public void SetBullets(int bullets)
    {
		bulletsNum.text = bullets.ToString();
    }

	public void ShootGun()
	{
		if (rendEnemyObject.enabled == true)
		{
			Instantiate(gunShotPrefab, enemyGameObject.transform);
			soundHandler.PlayGunAudio();
		}
	}

    public void SetBombs(int bombs)
    {
        bombsNum.text = bombs.ToString();
    }
	public void ThrowBalls(string ball)
	{
		if (rendEnemyObject.enabled == true)
		{
			projectileHandler.ThrowBall(ball, true, true);
			if (ball == "bowl")
			{
				soundHandler.PlayThrowBowlingBallAudio();
			}
			if (ball == "bomb")
			{
				soundHandler.PlayThrowRainBombAudio();
			}
			else
			{
				soundHandler.PlayThrowBallAudio();
			}
		}
		else
		{
			projectileHandler.ThrowBall(ball, false, true);
		}
	}
	public void EnemyThrowBalls(string ball)
	{
		projectileHandler.ThrowBall(ball, false, false);
	}
	public void Reload()
	{
		reloadWindow.gameObject.SetActive(true);
		reloadImage.color = new Color(reloadImage.color.r, reloadImage.color.g, reloadImage.color.b, 1);
		reloadProgress = 0;

		// Play reload sfx
		soundHandler.PlayReloadAudio();
	}
	public void SetEnemyHealth(int enemyHealth, int enemyShieldHealth)
	{

		if (enemyShieldHealth == 0)
		{
			enemyShieldBarWindow.gameObject.SetActive(false);
			Destroy(instantiatedObject);
		}
		else
		{
			SetEnemyShield(enemyShieldHealth);
		}
		enemyHealthImage.fillAmount = (float)enemyHealth / 100;
		enemyHealthNum.text = enemyHealth.ToString();

	}

	public void SetEnemyMaxShield()
	{
		instantiatedObject = Instantiate(enemyShieldPrefab, enemyGameObject.transform.position, Quaternion.Euler(90, 0, 0));

		// Set the parent to the ImageTarget
		instantiatedObject.transform.SetParent(imageTargetBehaviour.transform, false);
		instantiatedObject.transform.localPosition = new Vector3(0, 0, -0.15f);
		
		enemyShieldBarWindow.gameObject.SetActive(true);
		enemyShieldImage.fillAmount = 1.0f;
		enemyShieldHealthNum.text = "30";
	}
	public void SetEnemyShield(int enemyShieldHealth)
	{
		enemyShieldImage.fillAmount = (float)enemyShieldHealth / 30;
		enemyShieldHealthNum.text = enemyShieldHealth.ToString();
	}
	public void SetPlayerNumText(int playerID)
	{
		if (playerID == 1)
		{
			playerNumText.text = "Player 1";
		}
		else if (playerID == 2)
		{
			playerNumText.text = "Player 2";
		}
	}

	public void DisplayErrorReloadText()
	{
		errorReloadText.gameObject.SetActive(true);
		errorReloadTextRemaining = errorReloadTextDisplayTime;
	}
	public void DisplayErrorGunText()
	{
		errorGunText.gameObject.SetActive(true);
		errorGunTextRemaining = errorGunTextDisplayTime;
	}
	public void DisplayErrorBombText()
	{
		errorBombText.gameObject.SetActive(true);
		errorBombTextRemaining = errorBombTextDisplayTime;
	}
	public void DisplayErrorShieldText()
	{
		errorShieldText.gameObject.SetActive(true);
		errorShieldTextRemaining = errorShieldTextDisplayTime;
	}

	public void UpdateSettingsDescription(string text)
	{
		settingsTextDescription.text = text;
	}

	public bool GetEnemyFOV()
	{
		// Return True if enemy is in FOV, False if enemy not in FOV
		return rendEnemyObject.enabled;
	}

	// Start is called before the first frame update
	void Awake()
    {
		playerNumText = transform.Find("Canvas").Find("PlayerWindow").Find("PlayerText").GetComponent<TMP_Text>();
		settingsTextDescription = transform.Find("Canvas").Find("SettingsWindow").Find("Description").GetComponent<TMP_Text>();

		healthImage = transform.Find("Canvas").Find("PlayerWindow").Find("HealthBarWindow").Find("HealthBarFilled").GetComponent<Image>();
        healthNum = transform.Find("Canvas").Find("PlayerWindow").Find("HealthBarWindow").Find("HealthText").GetComponent<TMP_Text>();
		shieldImage = transform.Find("Canvas").Find("PlayerWindow").Find("ShieldBarWindow").Find("ShieldBarFilled").GetComponent<Image>();
		shieldHealthNum = transform.Find("Canvas").Find("PlayerWindow").Find("ShieldBarWindow").Find("ShieldText").GetComponent<TMP_Text>();
		shieldAmmo = transform.Find("Canvas").Find("ShieldWindow").Find("ShieldText").GetComponent<TMP_Text>();
		bulletsNum = transform.Find("Canvas").Find("WeaponWindow").Find("AmmoText").GetComponent<TMP_Text>();
        bombsNum = transform.Find("Canvas").Find("WaterBombWindow").Find("WaterBombText").GetComponent<TMP_Text>();
		reloadImage = transform.Find("Canvas").Find("ReloadWindow").Find("ReloadCircle").GetComponent<Image>();
		deathsNum = transform.Find("Canvas").Find("KDWindow").Find("DeathsNumber").GetComponent<TMP_Text>();
		killsNum = transform.Find("Canvas").Find("KDWindow").Find("KillsNumber").GetComponent<TMP_Text>();

		// For Enemy Hp/Shield Window
		enemyHealthImage = transform.Find("ImageTarget").Find("CanvasForEnemy").Find("EnemyWindow").Find("EnemyHealthBarWindow").Find("HealthBarFilled").GetComponent<Image>();
		enemyHealthNum = transform.Find("ImageTarget").Find("CanvasForEnemy").Find("EnemyWindow").Find("EnemyHealthBarWindow").Find("HealthText").GetComponent<TMP_Text>();
		enemyShieldImage = transform.Find("ImageTarget").Find("CanvasForEnemy").Find("EnemyWindow").Find("EnemyShieldBarWindow").Find("ShieldBarFilled").GetComponent<Image>();
		enemyShieldHealthNum = transform.Find("ImageTarget").Find("CanvasForEnemy").Find("EnemyWindow").Find("EnemyShieldBarWindow").Find("ShieldText").GetComponent<TMP_Text>();
		rendEnemyObject = transform.Find("ImageTarget").Find("Enemy").GetComponent<Renderer>();

		// No shield equipped on start for both player and enemy
		shieldBarWindow.gameObject.SetActive(false);
		equipShieldIcon.gameObject.	SetActive(false);
		enemyShieldBarWindow.gameObject.SetActive(false);

		// Init reload window to be invisible
		reloadWindow.gameObject.SetActive(false);
		reloadImage.color = new Color(reloadImage.color.r, reloadImage.color.g, reloadImage.color.b, 0);

		SetMaxHealth();
        SetMaxBullets();
        SetMaxBombs();
    }
	private void Start()
	{
		lowHealthOverlay.color = new Color(lowHealthOverlay.color.r, lowHealthOverlay.color.g, lowHealthOverlay.color.b, 0);
		equipShieldOverlay.color = new Color(equipShieldOverlay.color.r, equipShieldOverlay.color.g, equipShieldOverlay.color.b, 0);
		deathOverlay.color = new Color(deathOverlay.color.r, deathOverlay.color.g, deathOverlay.color.b, 0);
	}
	void Update()
	{
		// To show Enemy UI if enemy is in FOV
		if (rendEnemyObject.enabled == true)
		{
			enemyWindow.SetActive(true);
		}
		else
		{
			enemyWindow.SetActive(false);
		}
		// Flash red border
		if (lowHealthOverlay.color.a > 0)
		{
			lowHpDurationTimer += Time.deltaTime;
			if (lowHpDurationTimer > lowHpDuration)
			{
				float tempAlpha = lowHealthOverlay.color.a;
				tempAlpha -= Time.deltaTime * lowHpFadeSpeed;
				lowHealthOverlay.color = new Color(lowHealthOverlay.color.r, lowHealthOverlay.color.g, lowHealthOverlay.color.b, tempAlpha);
			}
		}
		// Flash blue border
		if (equipShieldOverlay.color.a > 0)
		{
			equipShieldDurationTimer += Time.deltaTime;
			if (equipShieldDurationTimer > equipShieldDuration)
			{
				float tempAlphaShield = equipShieldOverlay.color.a;
				tempAlphaShield -= Time.deltaTime * equipShieldFadeSpeed;
				equipShieldOverlay.color = new Color(equipShieldOverlay.color.r, equipShieldOverlay.color.g, equipShieldOverlay.color.b, tempAlphaShield);
			}
		}
		// Flash grey screen
		if (deathOverlay.color.a > 0)
		{
			deathDurationTimer += Time.deltaTime;
			if (deathDurationTimer > deathDuration)
			{
				float tempAlphaDeath = deathOverlay.color.a;
				tempAlphaDeath -= Time.deltaTime * lowHpFadeSpeed;
				deathOverlay.color = new Color(deathOverlay.color.r, deathOverlay.color.g, deathOverlay.color.b, tempAlphaDeath);
			}
		}
		if (reloadImage.color.a > 0)
		{
			reloadProgress += Time.deltaTime * 1.8f;
			reloadImage.fillAmount = reloadProgress;
			if (reloadProgress >= 1f)
			{
				reloadImage.color = new Color(reloadImage.color.r, reloadImage.color.g, reloadImage.color.b, 0);
				reloadWindow.gameObject.SetActive(false);
			}
		}

		// If the text is being shown, decrease the time remaining
		if (errorReloadTextRemaining > 0)
		{
			errorReloadTextRemaining -= Time.deltaTime;

			// If the time is up, hide the text
			if (errorReloadTextRemaining <= 0)
			{
				errorReloadText.gameObject.SetActive(false);
			}
		}
		// If the text is being shown, decrease the time remaining
		if (errorGunTextRemaining > 0)
		{
			errorGunTextRemaining -= Time.deltaTime;

			// If the time is up, hide the text
			if (errorGunTextRemaining <= 0)
			{
				errorGunText.gameObject.SetActive(false);
			}
		}
		// If the text is being shown, decrease the time remaining
		if (errorBombTextRemaining > 0)
		{
			errorBombTextRemaining -= Time.deltaTime;

			// If the time is up, hide the text
			if (errorBombTextRemaining <= 0)
			{
				errorBombText.gameObject.SetActive(false);
			}
		}
		// If the text is being shown, decrease the time remaining
		if (errorShieldTextRemaining > 0)
		{
			errorShieldTextRemaining -= Time.deltaTime;

			// If the time is up, hide the text
			if (errorShieldTextRemaining <= 0)
			{
				errorShieldText.gameObject.SetActive(false);
			}
		}

	}

}
