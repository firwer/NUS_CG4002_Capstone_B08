using System.Collections;
using UnityEngine;
using TMPro;
using Image = UnityEngine.UI.Image;

/// <summary>
/// Handles the error messages and UI changes for the HUD
/// </summary>
public class UIErrorHandler : MonoBehaviour
{
    // Respective Error messages that will show up in middle of screen
    public TMP_Text errorReloadText;
    public TMP_Text errorGunText;
    public TMP_Text errorBombText;
    public TMP_Text errorShieldText;
    public TMP_Text errorInvalidActionText;
    public TMP_Text errorOnCooldownText;
    public TMP_Text randomActionAlertText;

    // GameObjects and colors for changing UI/HUD on cooldown
    public GameObject[] gameObjectsBackground;
    public GameObject[] gameObjectsGlow;
    public GameObject[] gameObjectsBorder;
    public TMP_Text[] allHUDText;
    public GameObject healthBarFilled;

    private Color borderColor = new Color(0x63 / 255f, 0xC6 / 255f, 0xFF / 255f, 1f);
    private Color backgroundColor = new Color(0x2D / 255f, 0x2D / 255f, 0x2D / 255f, 0.7843137f);
    private Color glowColor = new Color(0x63 / 255f, 0xC6 / 255f, 0xFF / 255f, 0.1960784f);

    private Color borderColorDisabled = new Color(0.5f, 0.5f, 0.5f, 0.5f);
    private Color backgroundColorDisabled = new Color(0.4f, 0.4f, 0.4f, 0.08f);
    private Color glowColorDisabled = new Color(0.2f, 0.2f, 0.2f, 0.5f);

    private Color textColor = new Color(1f, 1f, 1f, 1f);
    private Color textColorDisabled = new Color(0.6f, 0.6f, 0.6f, 1f);

    // GameObjects for Connected/Disconnected UI
    public GameObject connectedGameObject;
    public GameObject disconnectedGameObject;

    // Track the currently displayed error message
    private TMP_Text currentErrorText;


    public void DisplayError(TMP_Text errorText, float displayTime = 3f)
    {
        // Hide the current error message if one is displayed
        if (currentErrorText != null && currentErrorText.gameObject.activeSelf)
        {
            currentErrorText.gameObject.SetActive(false);
        }

        // Display the new error message
        currentErrorText = errorText;
        errorText.gameObject.SetActive(true);
        StartCoroutine(HideTextAfterDelay(errorText, displayTime));
    }

    private IEnumerator HideTextAfterDelay(TMP_Text errorText, float delay)
    {
        yield return new WaitForSeconds(delay);
        errorText.gameObject.SetActive(false);

        // Reset the current error message if it's the one being hidden
        if (currentErrorText == errorText)
        {
            currentErrorText = null;
        }
    }

    public void DisplayErrorReloadText()
    {
        DisplayError(errorReloadText);
    }

    public void DisplayErrorGunText()
    {
        DisplayError(errorGunText);
    }

    public void DisplayErrorBombText()
    {
        DisplayError(errorBombText);
    }

    public void DisplayErrorShieldText()
    {
        DisplayError(errorShieldText);
    }

    public void DisplayErrorInvalidActionText()
    {
        DisplayError(errorInvalidActionText);
    }
    public void DisplayErrorOnCooldownText()
    {
        DisplayError(errorOnCooldownText);
    }
    public void DisplayRandomActionAlertText()
    {
        DisplayError(randomActionAlertText);
    }

    public void DisplayCooldownUI()
    {
        foreach (GameObject objBorder in gameObjectsBorder)
        {
            Image image = objBorder.GetComponent<Image>();
            if (image != null)
            {
                image.color = borderColorDisabled;
            }
        }
        foreach (GameObject objGlow in gameObjectsGlow)
        {
            Image image = objGlow.GetComponent<Image>();
            if (image != null)
            {
                image.color = glowColorDisabled;
            }
        }
        foreach (GameObject objBackground in gameObjectsBackground)
        {
            Image image = objBackground.GetComponent<Image>();
            if (image != null)
            {
                image.color = backgroundColorDisabled;
            }
        }
        foreach (TMP_Text textObj in allHUDText)
        {
            if (textObj != null)
            {
                textObj.color = textColorDisabled;
            }
        }
        healthBarFilled.GetComponent<Image>().color = textColorDisabled;
    }

    public void DisplayAvailableUI()
    {
        foreach (GameObject objBorder in gameObjectsBorder)
        {
            Image image = objBorder.GetComponent<Image>();
            if (image != null)
            {
                image.color = borderColor;
            }
        }
        foreach (GameObject objGlow in gameObjectsGlow)
        {
            Image image = objGlow.GetComponent<Image>();
            if (image != null)
            {
                image.color = glowColor;
            }
        }
        foreach (GameObject objBackground in gameObjectsBackground)
        {
            Image image = objBackground.GetComponent<Image>();
            if (image != null)
            {
                image.color = backgroundColor;
            }
        }
        foreach (TMP_Text textObj in allHUDText)
        {
            if (textObj != null)
            {
                textObj.color = textColor;
            }
        }
        healthBarFilled.GetComponent<Image>().color = textColor;
    }

    public void DisplayConnectedSignal()
    {
        connectedGameObject.SetActive(true);
        disconnectedGameObject.SetActive(false);
    }

    public void DisplayDisconnectedSignal()
    {
        connectedGameObject.SetActive(false);
        disconnectedGameObject.SetActive(true);
    }
}
