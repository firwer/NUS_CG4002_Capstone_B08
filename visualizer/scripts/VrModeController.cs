//-----------------------------------------------------------------------
// <copyright file="VrModeController.cs" company="Google LLC">
// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// </copyright>
//-----------------------------------------------------------------------

using System.Collections;
using Google.XR.Cardboard;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;
using UnityEngine.InputSystem.Utilities;
using UnityEngine.XR;
using UnityEngine.XR.Management;

using InputSystemTouchPhase = UnityEngine.InputSystem.TouchPhase;

/// <summary>
/// Turns VR mode on and off.
/// </summary>
public class VrModeController : MonoBehaviour
{
    // Field of view value to be used when the scene is not in VR mode. In case
    // XR isn't initialized on startup, this value could be taken from the main
    // camera and stored.
    private const float _defaultFieldOfView = 60.0f;
    private Google.XR.Cardboard.XRLoader loader;

    // Main camera from the scene.
    public Camera _mainCamera;
    public GameObject settingsMenu;

    private bool _IPhoneinitialized = false;

	/// <summary>
	/// Gets a value indicating whether the VR mode is enabled.
	/// </summary>
	private bool _isVrModeEnabled
    {
        get
        {
            return XRGeneralSettings.Instance.Manager.isInitializationComplete;
        }
    }

    /// <summary>
    /// Start is called before the first frame update.
    /// </summary>
    public void Start()
    {
		if (Application.platform == RuntimePlatform.IPhonePlayer)
		{
			loader = ScriptableObject.CreateInstance<Google.XR.Cardboard.XRLoader>();
			Application.targetFrameRate = 60;
			Screen.brightness = 1.0f;

            if (loader != null)
            {
                loader.Initialize();
                _IPhoneinitialized = true;
            }
            else
            {
                Debug.Log("loader is null!");
            }

		}
		else if (Application.platform == RuntimePlatform.Android)
        {

            //Screen.sleepTimeout = SleepTimeout.NeverSleep;
            Screen.sleepTimeout = SleepTimeout.SystemSetting;

            Application.targetFrameRate = 60;

            // Checks if the device parameters are stored and scans them if not.
            // This is only required if the XR plugin is initialized on startup,
            // otherwise these API calls can be removed and just be used when the XR
            // plugin is started.
            if (!Api.HasDeviceParams())
            {
                Api.ScanDeviceParams();
            }
        }

	}

    /// <summary>
    /// Update is called once per frame.
    /// </summary>
    public void Update()
    {
		if (Application.platform == RuntimePlatform.IPhonePlayer)
		{
			if (Api.IsCloseButtonPressed)
			{
                Debug.Log("CAPSTONE: Exit button pressed");
				ExitVR();
			}

		}
		else if (Application.platform == RuntimePlatform.Android)
		{

			if (_isVrModeEnabled)
			{
				if (Api.IsCloseButtonPressed)
				{
					ExitVR();
				}
			}
		}
		//Api.UpdateScreenParams();
	}

	/// <summary>
	/// Enters VR mode.
	/// </summary>
	public void EnterVR()
    {
        if (Application.platform == RuntimePlatform.IPhonePlayer)
        {
			if (!_IPhoneinitialized)
			{
				loader.Initialize();
			}
			loader.Start();
			// Set the resolution dynamically based on the device's current resolution
			int screenWidth = Screen.currentResolution.width;
			int screenHeight = Screen.currentResolution.height;
			Screen.SetResolution(screenWidth, screenHeight, true);

			// Adjust render quality based on resolution using QualitySettings
			if (screenWidth > 1920)
			{
				QualitySettings.resolutionScalingFixedDPIFactor = 1.5f; // Higher quality for high-res screens
			}
			else
			{
				QualitySettings.resolutionScalingFixedDPIFactor = 1.0f; // Standard quality for lower-res screens
			}
		}
        else if (Application.platform == RuntimePlatform.Android)
        {
			StartCoroutine(StartXR());
			if (Api.HasNewDeviceParams())
			{
				Api.ReloadDeviceParams();
			}
		}
	}

	/// <summary>
	/// Exits VR mode.
	/// </summary>
	private void ExitVR()
    {
		if (Application.platform == RuntimePlatform.IPhonePlayer)
		{
			loader.Stop();
            loader.Deinitialize();
            _IPhoneinitialized = false;
			Debug.Log("CAPSTONE: Exited VR");
		}
		else if (Application.platform == RuntimePlatform.Android)
		{
			StopXR();
		}
		
    }

    /// <summary>
    /// Initializes and starts the Cardboard XR plugin.
    /// See https://docs.unity3d.com/Packages/com.unity.xr.management@3.2/manual/index.html.
    /// </summary>
    ///
    /// <returns>
    /// Returns result value of <c>InitializeLoader</c> method from the XR General Settings Manager.
    /// </returns>
    private IEnumerator StartXR()
    {
        Debug.Log("Initializing XR...");
        yield return XRGeneralSettings.Instance.Manager.InitializeLoader();

        if (XRGeneralSettings.Instance.Manager.activeLoader == null)
        {
            Debug.LogError("Initializing XR Failed.");
        }
        else
        {
            Debug.Log("XR initialized.");

            Debug.Log("Starting XR...");
            XRGeneralSettings.Instance.Manager.StartSubsystems();
            Debug.Log("XR started.");
        }
    }

    /// <summary>
    /// Stops and deinitializes the Cardboard XR plugin.
    /// See https://docs.unity3d.com/Packages/com.unity.xr.management@3.2/manual/index.html.
    /// </summary>
    private void StopXR()
    {
        Debug.Log("Stopping XR...");
        XRGeneralSettings.Instance.Manager.StopSubsystems();
        Debug.Log("XR stopped.");

        Debug.Log("Deinitializing XR...");
        XRGeneralSettings.Instance.Manager.DeinitializeLoader();
        Debug.Log("XR deinitialized.");

        _mainCamera.ResetAspect();
        _mainCamera.fieldOfView = _defaultFieldOfView;
    }
}
