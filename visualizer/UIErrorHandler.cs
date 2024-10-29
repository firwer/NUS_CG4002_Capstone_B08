using System.Collections;
using UnityEngine;
using TMPro;

public class UIErrorHandler : MonoBehaviour
{
	public TMP_Text errorReloadText;
	public TMP_Text errorGunText;
	public TMP_Text errorBombText;
	public TMP_Text errorShieldText;
	public TMP_Text errorInvalidActionText;

	public void DisplayError(TMP_Text errorText, float displayTime = 1f)
	{
		errorText.gameObject.SetActive(true);
		StartCoroutine(HideTextAfterDelay(errorText, displayTime));
	}

	private IEnumerator HideTextAfterDelay(TMP_Text errorText, float delay)
	{
		yield return new WaitForSeconds(delay);
		errorText.gameObject.SetActive(false);
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

	//private float errorReloadTextDisplayTime = 1f;
	//private float errorReloadTextRemaining = 0f;
	//private float errorGunTextDisplayTime = 1f;
	//private float errorGunTextRemaining = 0f;
	//private float errorBombTextDisplayTime = 1f;
	//private float errorBombTextRemaining = 0f;
	//private float errorShieldTextDisplayTime = 1f;
	//private float errorShieldTextRemaining = 0f;
	//private float errorInvalidActionTextDisplayTime = 1f;
	//private float errorInvalidActionTextRemaining = 0f;

	//public void DisplayErrorReloadText()
	//{
	//	errorReloadText.gameObject.SetActive(true);
	//	errorReloadTextRemaining = errorReloadTextDisplayTime;
	//}
	//public void DisplayErrorGunText()
	//{
	//	errorGunText.gameObject.SetActive(true);
	//	errorGunTextRemaining = errorGunTextDisplayTime;
	//}
	//public void DisplayErrorBombText()
	//{
	//	errorBombText.gameObject.SetActive(true);
	//	errorBombTextRemaining = errorBombTextDisplayTime;
	//}
	//public void DisplayErrorShieldText()
	//{
	//	errorShieldText.gameObject.SetActive(true);
	//	errorShieldTextRemaining = errorShieldTextDisplayTime;
	//}
	//public void DisplayErrorInvalidActionText()
	//{
	//	errorInvalidActionText.gameObject.SetActive(true);
	//	errorInvalidActionTextRemaining = errorInvalidActionTextDisplayTime;
	//}

	//// Update is called once per frame
	//void Update()
	//   {
	//	// If the text is being shown, decrease the time remaining
	//	if (errorReloadTextRemaining > 0)
	//	{
	//		errorReloadTextRemaining -= Time.deltaTime;

	//		// If the time is up, hide the text
	//		if (errorReloadTextRemaining <= 0)
	//		{
	//			errorReloadText.gameObject.SetActive(false);
	//		}
	//	}
	//	// If the text is being shown, decrease the time remaining
	//	if (errorGunTextRemaining > 0)
	//	{
	//		errorGunTextRemaining -= Time.deltaTime;

	//		// If the time is up, hide the text
	//		if (errorGunTextRemaining <= 0)
	//		{
	//			errorGunText.gameObject.SetActive(false);
	//		}
	//	}
	//	// If the text is being shown, decrease the time remaining
	//	if (errorBombTextRemaining > 0)
	//	{
	//		errorBombTextRemaining -= Time.deltaTime;

	//		// If the time is up, hide the text
	//		if (errorBombTextRemaining <= 0)
	//		{
	//			errorBombText.gameObject.SetActive(false);
	//		}
	//	}
	//	// If the text is being shown, decrease the time remaining
	//	if (errorShieldTextRemaining > 0)
	//	{
	//		errorShieldTextRemaining -= Time.deltaTime;

	//		// If the time is up, hide the text
	//		if (errorShieldTextRemaining <= 0)
	//		{
	//			errorShieldText.gameObject.SetActive(false);
	//		}
	//	}
	//	// If the text is being shown, decrease the time remaining
	//	if (errorInvalidActionTextRemaining > 0)
	//	{
	//		errorInvalidActionTextRemaining -= Time.deltaTime;

	//		// If the time is up, hide the text
	//		if (errorInvalidActionTextRemaining <= 0)
	//		{
	//			errorInvalidActionText.gameObject.SetActive(false);
	//		}
	//	}
	//}
}
