/*
The MIT License (MIT)

Copyright (c) 2018 Giovanni Paolo Vigano'

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using uPLibrary.Networking.M2Mqtt;
using uPLibrary.Networking.M2Mqtt.Messages;
using Newtonsoft.Json;
using M2MqttUnity;
using GameDataNameSpace;

/// <summary>
/// Examples for the M2MQTT library (https://github.com/eclipse/paho.mqtt.m2mqtt),
/// </summary>
/// <summary>
/// Script for testing M2MQTT with a Unity UI
/// </summary>
public class M2MqttUnityTest : M2MqttUnityClient
{

    public MsgHandler msgHandlerGameObject;
    public UIHandler uiHandlerGameObject;
    public UIErrorHandler uiErrorHandlerGameObject;
    //public CollisionHandler collisionHandlerGameObject;

    [Tooltip("Set this to true to perform a testing cycle automatically on startup")]
    public bool autoTest = false;
    [Header("User Interface")]
    public Button connectButton;
    public Button disconnectButton;

    private List<string> eventMessages = new List<string>();
    private List<string> interDeviceMessages = new List<string>();

    private int tempPlayerDeath = 0;
    private int tempEnemyDeath = 0;
    private bool tempEnemyInFOV = false;
    private int tempInRain = -1;
    private bool tempPlayerInFOV = false;

    private float reconnectDelay = 4.5f; // Delay between reconnection attempts
    private bool isReconnecting = false;
    private bool firstConnect = false;
    private float reconnectTimer = 4.5f;

    private Coroutine fovExitCoroutine;
    private bool isPublishingExit = false;

    public void PublishState(int player_id, bool FOVmsg, int inRainNumber)
    {
        string msgToSend = "vstate_fov_" + FOVmsg.ToString() + "_inbomb_" + inRainNumber.ToString();
        // Publish the generated message

        // This is player 1
        if (player_id == 1) {
            client.Publish("game_state/visualizer_to_engine/p1", System.Text.Encoding.UTF8.GetBytes(msgToSend), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
            client.Publish("p1_to_p2_pipeline", System.Text.Encoding.UTF8.GetBytes(FOVmsg.ToString() + "_" + inRainNumber.ToString()), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
        }
        // This is player 2
        else
        {
            client.Publish("game_state/visualizer_to_engine/p2", System.Text.Encoding.UTF8.GetBytes(msgToSend), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
            client.Publish("p2_to_p1_pipeline", System.Text.Encoding.UTF8.GetBytes(FOVmsg.ToString() + "_" + inRainNumber.ToString()), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
        }

        Debug.Log("CAPSTONE: Publishing num of rain to enemy");
    }

    public void SetPlayerMode(bool isP1)
    {
        Debug.Log($"setting player mode isP1 to {isP1}");
        this.isP1 = isP1;
    }

    public void GetPlayerNumber(int playerNum)
    {
        string playerMsg;

        if (playerNum == 1)
        {
            isP1 = true;
            playerMsg = "Setting player mode to Player 1";
        }
        else
        {
            isP1 = false;
            playerMsg = "Setting player mode to Player 2";
                
        }
        Debug.Log(playerMsg);
        uiHandlerGameObject.UpdateSettingsDescription(playerMsg);
            
    }

    protected override void OnConnecting()
    {
        base.OnConnecting();
        string connectingDescription = "Connecting to broker on" + "...\n";
        uiHandlerGameObject.UpdateSettingsDescription(connectingDescription);
        Debug.Log(connectingDescription);
    }

    protected override void OnConnected()
    {
        base.OnConnected();
        string playerNum = isP1 ? "1" : "2";
        string connectedDescription = "Connected to broker" + "\n" + "You are PLAYER " + playerNum + "\n";
        firstConnect = true;
        uiHandlerGameObject.UpdateSettingsDescription(connectedDescription);
        uiErrorHandlerGameObject.DisplayConnectedSignal();
    }

    protected override void SubscribeTopics()
    {
        client.Subscribe(new string[] { "game_state/engine_to_visualizer", "p1_to_p2_pipeline", "p2_to_p1_pipeline" }, new byte[] { MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE });
        //client.Subscribe(new string[] { "game_state/engine_to_visualizer" }, new byte[] { MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE });
    }

    protected override void UnsubscribeTopics()
    {
        client.Unsubscribe(new string[] { "game_state/engine_to_visualizer", "p1_to_p2_pipeline", "p2_to_p1_pipeline" });
    }

    protected override void OnConnectionFailed(string errorMessage)
    {
        Debug.Log("CAPSTONE: CONNECTION FAILED! " + errorMessage);
    }

    protected override void OnDisconnected()
    {
        string disconnectedMsg = "CAPSTONE: Disconnected";
        uiHandlerGameObject.UpdateSettingsDescription(disconnectedMsg);
        Debug.Log(disconnectedMsg);
    }

    protected override void OnConnectionLost()
    {
        Debug.Log("CAPSTONE: CONNECTION LOST!");
        uiErrorHandlerGameObject.DisplayDisconnectedSignal();
    }

    private void CheckConnection()
    {
        if (firstConnect && (client == null || !client.IsConnected))
        {
            if (reconnectTimer >= reconnectDelay)
            {
                if (!isReconnecting)
                {
                    Debug.Log("Attempting to reconnect...");
                    isReconnecting = true;
                    reconnectTimer = 0f;
                    base.Connect();
                }
                else
                {
                    isReconnecting = false;
                }
            }
            else
            {
                reconnectTimer += Time.deltaTime;
            }
        }
        else if (isReconnecting && client != null && client.IsConnected)
        {
            Debug.Log("Reconnected successfully.");
            isReconnecting = false;
            reconnectTimer = 0f;
        }
    }

    public void LogoutPlayer(PlayerData player)
    {
        // Implement logout logic, such as removing the player from the game
        Debug.Log($"Player {player.player_id} has logged out.");
    }

    private void CheckAndHandleDeath(PlayerData myPlayer, PlayerData opponent)
    {
        if (myPlayer.game_state.deaths > tempPlayerDeath)
        {
            msgHandlerGameObject.HandleDeath(myPlayer);
            Debug.Log("CAPSTONE: I DIED");
                
        }
        if (opponent.game_state.deaths > tempEnemyDeath)
        {
            msgHandlerGameObject.HandleDeath(opponent);
            Debug.Log("CAPSTONE: ENEMY DIED");

        }
        tempPlayerDeath = myPlayer.game_state.deaths;
        tempEnemyDeath = opponent.game_state.deaths;
    }

    public void ProcessPlayerState(PlayerData attacker, PlayerData opponent, bool targetInFOV)
    {
        string action = attacker.action;

        if (isP1)
        {
            // If player is 1 and attacker id is 1
            if (attacker.player_id == 1)
            {
                msgHandlerGameObject.ActionChecker(action, attacker, tempPlayerInFOV);
                CheckAndHandleDeath(attacker, opponent);
            }
            // Player is 1, attacker id is 2
            else if (opponent.player_id == 1)
            {
                CheckAndHandleDeath(opponent, attacker);
                msgHandlerGameObject.HandleAction(action, attacker, tempPlayerInFOV);
            }
        }
        else
        {
            // Player is 2, attacker id is 2
            if (attacker.player_id == 2)
            {
                msgHandlerGameObject.ActionChecker(action, attacker, tempPlayerInFOV);
                CheckAndHandleDeath(attacker, opponent);
            }
            // Player is 2, attacker id is 1
            else if (opponent.player_id == 2)
            {
                CheckAndHandleDeath(opponent, attacker);
                msgHandlerGameObject.HandleAction(action, attacker, tempPlayerInFOV);
            }
        }

        // Updates opponent health no matter what happens (might be due to rain dmg)
        msgHandlerGameObject.HandleReduceHealth(attacker, opponent);
    }

    protected override void Start()
    {
        base.Start();
    }

    protected override void DecodeMessage(string topic, byte[] message)
    {
        string msg = System.Text.Encoding.UTF8.GetString(message);
        //Debug.Log("Received: " + msg);

        if ((isP1 && topic == "p2_to_p1_pipeline") || (!isP1 && topic == "p1_to_p2_pipeline"))
        {
            interDeviceMessages.Add(msg);
        }
        else if (topic == "game_state/engine_to_visualizer")
        {
            eventMessages.Add(msg);
        }
    }

    private void ProcessMessage(string msg, bool inSight)
    {
        RootObject rootObject = JsonConvert.DeserializeObject<RootObject>(msg); // The struct of this is at M2MqttUnityClient.cs
            
        // Retrieve the player_id (Where this data came from)
        string dataOriginPlayerId = rootObject.player_id;
            
        // Deserialize player 1 and player 2 data
        PlayerData player1 = JsonConvert.DeserializeObject<PlayerData>(rootObject.p1);
        PlayerData player2 = JsonConvert.DeserializeObject<PlayerData>(rootObject.p2);

        // Process game state based on who is the attacker
        if (dataOriginPlayerId == "1")
        {
            ProcessPlayerState(player1, player2, inSight);
        }
        else
        {
            ProcessPlayerState(player2, player1, inSight);
        }
    }
    private void ProcessCoolDownMessage(string playerID, string msg)
    {
        if ((isP1 && playerID == "1") || (!isP1 && playerID == "2"))
        {
            if (msg == "cooldown-end")
            {
                uiErrorHandlerGameObject.DisplayAvailableUI();
            }
        }
    }

    private void ProcessInterPlayerMessage(string msg)
    {
        string[] interPlayerMsgArr = msg.Split(new char[] { '_' }, 2); // Split into 2 parts
        tempPlayerInFOV = bool.Parse(interPlayerMsgArr[0]);
        uiHandlerGameObject.SetInRainNumber(interPlayerMsgArr[1]);
    }

    private IEnumerator HandleFovExit(bool currentFov, int rainCount)
    {
        isPublishingExit = true;
        //Debug.Log("CAPSTONE: HandleFovExit started. Waiting for 5 seconds before publishing exit state.");

        // Wait for 5 seconds
        yield return new WaitForSeconds(5f);

        // Re-check the current FOV and rain count after delay
        var (isStillInFOV, updatedRainCount) = msgHandlerGameObject.FovAndRainChecker();

        // If FOV is still False after delay, publish the exit state
        if (!isStillInFOV)
        {
            PublishState(isP1 ? 1 : 2, false, updatedRainCount);
            Debug.Log($"CAPSTONE: HANDLEFOV_EXIT Publishing: FALSE, RainCount: {updatedRainCount}");
            tempEnemyInFOV = false;
            tempInRain = updatedRainCount;
        }
        else
        {
            // FOV re-entered during the delay; do not publish
            //Debug.Log("CAPSTONE: HANDLEFOV_EXIT aborted due to re-entry into FOV within delay.");
        }

        isPublishingExit = false;
        fovExitCoroutine = null;
    }
    protected override void Update()
    {
        // call ProcessMqttEvents()
        base.Update();

        CheckConnection();

        // Check if enemy still in FOV/Rain
        var (isInFOV, rainCount) = msgHandlerGameObject.FovAndRainChecker();

        bool currentFov = isInFOV;
        int currentRain = rainCount;

        // Detect FOV changes
        if (tempEnemyInFOV != currentFov)
        {
            if (currentFov)
            {
                // Enemy has entered FOV
                //Debug.Log("CAPSTONE: Enemy has entered FOV.");

                // If there is an existing FOV exit coroutine, stop it
                if (fovExitCoroutine != null)
                {
                    //Debug.Log("CAPSTONE: Stopping existing FOV exit coroutine due to re-entry into FOV.");
                    StopCoroutine(fovExitCoroutine);
                    fovExitCoroutine = null;
                    isPublishingExit = false;
                }

                // Publish immediately as enemy is now in FOV
                PublishState(isP1 ? 1 : 2, true, currentRain);
                Debug.Log($"CAPSTONE: Publishing: InFOV = TRUE, RainCount = {currentRain}");

                // Update temporary state
                tempEnemyInFOV = currentFov;
                tempInRain = currentRain;
            }
            else
            {
                // Enemy has exited FOV; start the delayed publish
                Debug.Log("CAPSTONE: Enemy has exited FOV. Starting delayed publish coroutine.");

                // Start the HandleFovExit coroutine if not already running
                if (fovExitCoroutine == null && !isPublishingExit)
                {
                    fovExitCoroutine = StartCoroutine(HandleFovExit(currentFov, currentRain));
                }

                // Update temporary state
                tempEnemyInFOV = currentFov;
            }
        }

        // Detect rain count changes only if enemy is in FOV
        if (tempInRain != currentRain && currentFov)
        {
            //Debug.Log($"CAPSTONE: Rain count changed from {tempInRain} to {currentRain}. Publishing immediately.");
            PublishState(isP1 ? 1 : 2, currentFov, currentRain);
            Debug.Log($"CAPSTONE: Publishing: InFOV = {currentFov} , RainCount = {currentRain}");
            tempInRain = currentRain;
        }

        // Handles message coming in
        if (eventMessages.Count > 0)
        {
            foreach (string msg in eventMessages)
            {
                //Debug.Log(msg);
                string[] parts = msg.Split(new char[] { '_' }, 2); // Split into 2 parts
                string keyword = parts[0];

                // game state msg in format: gs_<gameStateMessage>
                if (keyword == "gs")
                {
                    //Debug.Log("CAPSTONE: Processing GS msg");
                    ProcessMessage(parts[1], tempEnemyInFOV);
                }
                else if (keyword == "1" || keyword == "2")
                {
                    ProcessCoolDownMessage(parts[0], parts[1]);
                }
                else
                {
                    //Debug.Log("CAPSTONE: Invalid Message Format");
                }
            }
            eventMessages.Clear();
        }
        // Process inter-device messages
        if (interDeviceMessages.Count > 0)
        {
            foreach (string msg in interDeviceMessages)
            {
                // Process inter-device message
                //Debug.Log("Processing inter-device message: " + msg);
                ProcessInterPlayerMessage(msg);
            }
            interDeviceMessages.Clear();
        }
    }

    private void OnDestroy()
    {
        Disconnect();
    }

    private void OnValidate()
    {
        if (autoTest)
        {
            autoConnect = true;
        }
    }
}