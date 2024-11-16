using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using Vuforia;
using Image = UnityEngine.UI.Image;
using UnityEngine.Video;

/// <summary>
/// Handles the UI changes for the HUD
/// </summary>
public class UIHandler : MonoBehaviour
{
    public ProjectileHandler projectileHandler;
    public ProjectileHandlerToPlayer projectileHandlerToPlayer;
    public SoundHandler soundHandler;

    public GameObject enemyWindow;
    public GameObject enemyShieldPrefab;
    public GameObject enemyGameObject;
    public GameObject gunShotPrefab;
    public ImageTargetBehaviour imageTargetBehaviour;

    private TMP_Text playerNumText;
    private TMP_Text settingsTextDescription;
    private Image healthImage;
    private TMP_Text healthNum;
    private Image shieldImage;
    public GameObject shieldBarWindow;
    public TMP_Text inRainText;
    private TMP_Text shieldHealthNum;
    private TMP_Text shieldAmmo;
    private TMP_Text bulletsNum;
    private TMP_Text bombsNum;
    private TMP_Text killsNum;
    private TMP_Text deathsNum;
    private Image reloadImage;
    public GameObject reloadWindow;
    private float reloadProgress;

    // For Enemy UI
    private Image enemyHealthImage;
    private TMP_Text enemyHealthNum;
    public GameObject enemyShieldBarWindow;
    private Image enemyShieldImage;
    private TMP_Text enemyShieldHealthNum;
    private Renderer rendEnemyObject;

    // Sets low hp overlay variables
    public Image lowHealthOverlay;	
    private float lowHpDuration = 0.3f;
    private float lowHpFadeSpeed = 2f;

    // Sets equip shield overlay variables
    public Image equipShieldOverlay;
    private float equipShieldDuration = 0.5f;
    private float equipShieldFadeSpeed = 2f;

    // Sets low hp overlay variables
    public Image deathOverlay;
    //private float deathDuration = 0.1f;
    //private float deathFadeSpeed = 3f;

    private float lowHpDurationTimer;
    private float equipShieldDurationTimer;
    private float deathDurationTimer;
    public VideoPlayer videoPlayer;

    public Image[] ProfOverlayImages;
    private float fadeDurationProfOverlay = 0.3f; // Time to fade in/out
    private float displayDurationProfOverlay = 6.2f; // Time to stay visible after fading in
    private Color initialColorProfOverlay;

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
    }

    public void SetMaxShield(int shields)
    {
        shieldBarWindow.gameObject.SetActive(true);
        shieldAmmo.text = shields.ToString();
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
        if (shieldHealth == 0)
        {
            shieldBarWindow.gameObject.SetActive(false);
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
        //deathDurationTimer = 0;
        //deathOverlay.color = new Color(deathOverlay.color.r, deathOverlay.color.g, deathOverlay.color.b, 0.8f);
        SetMaxHealth();
        SetMaxBullets();
        SetMaxBombs();
        SetMaxShieldAmmo();

        // Play died sfx
        soundHandler.PlayDiedAudio();
        soundHandler.PlayReviveAudio();

        videoPlayer.gameObject.SetActive(true);
        if (!videoPlayer.isPlaying)
        {
            videoPlayer.Play();  // Start playing the video
        }
        ShowProfImageWithFade();
    }
    void OnVideoFinished(VideoPlayer vp)
    {
        // Stop the video
        vp.Stop();
        vp.gameObject.SetActive(false);
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
        }
        soundHandler.PlayGunAudio();
    }

    public void SetBombs(int bombs)
    {
        bombsNum.text = bombs.ToString();
    }
    public void ThrowBalls(string ball)
    {
        if (rendEnemyObject.enabled == true)
        {
            projectileHandler.ThrowBall(ball, true);
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
            projectileHandler.ThrowBall(ball, false);
        }
    }
    public void EnemyThrowBalls(string ball)
    {
        Debug.Log("CAPSTONE: UIHandler: Calling projectileHandler ThrowBall");
        projectileHandlerToPlayer.ThrowBallToPlayer(ball, false);
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
        instantiatedObject.transform.localPosition = new Vector3(0, 0, -0.4f);
        
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

    public void UpdateSettingsDescription(string text)
    {
        settingsTextDescription.text = text;
    }

    public bool GetEnemyFOV()
    {
        // Return True if enemy is in FOV, False if enemy not in FOV
        return rendEnemyObject.enabled;
    }

    public void SetInRainNumber(string inRainNumber)
    {
        inRainText.text = inRainNumber;
    }

    public void ShowProfImageWithFade()
    {
        StartCoroutine(FadeInAndOut());
    }

    private IEnumerator FadeInAndOut()
    {
        // Fade In
        float elapsedTime = 0f;

        // Fade in each image
        while (elapsedTime < fadeDurationProfOverlay)
        {
            float t = elapsedTime / fadeDurationProfOverlay;
            foreach (Image img in ProfOverlayImages)
            {
                Color color = img.color;
                color.a = Mathf.Lerp(0f, 1f, t);
                img.color = color;
            }

            elapsedTime += Time.deltaTime;
            yield return null;
        }

        // Ensure all images are fully visible
        foreach (Image img in ProfOverlayImages)
        {
            Color color = img.color;
            color.a = 1f;
            img.color = color;
        }

        // Wait for the display duration
        yield return new WaitForSeconds(displayDurationProfOverlay);

        // Fade Out
        elapsedTime = 0f;

        // Fade out each image
        while (elapsedTime < fadeDurationProfOverlay)
        {
            float t = elapsedTime / fadeDurationProfOverlay;
            foreach (Image img in ProfOverlayImages)
            {
                Color color = img.color;
                color.a = Mathf.Lerp(1f, 0f, t);
                img.color = color;
            }

            elapsedTime += Time.deltaTime;
            yield return null;
        }

        // Ensure all images are fully transparent
        foreach (Image img in ProfOverlayImages)
        {
            Color color = img.color;
            color.a = 0f;
            img.color = color;
        }
    }

    public void PlayLogOut()
    {
        soundHandler.PlayLogOutAudio();
        videoPlayer.gameObject.SetActive(true);
        if (!videoPlayer.isPlaying)
        {
            videoPlayer.Play();  // Start playing the video
        }
        ShowProfImageWithFade();
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
        //inRainWindow.gameObject.SetActive(false);
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
        videoPlayer.loopPointReached += OnVideoFinished;

        lowHealthOverlay.color = new Color(lowHealthOverlay.color.r, lowHealthOverlay.color.g, lowHealthOverlay.color.b, 0);
        equipShieldOverlay.color = new Color(equipShieldOverlay.color.r, equipShieldOverlay.color.g, equipShieldOverlay.color.b, 0);
        deathOverlay.color = new Color(deathOverlay.color.r, deathOverlay.color.g, deathOverlay.color.b, 0);
        videoPlayer.playOnAwake = false;
        Debug.Log("UI START");
        foreach (Image img in ProfOverlayImages)
        {
            Color initialColor = img.color;
            initialColor.a = 0f;
            //Debug.Log("setting to 0 alpha");
            img.color = initialColor;
        }
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
        // Display reloading screen
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
    }
}
