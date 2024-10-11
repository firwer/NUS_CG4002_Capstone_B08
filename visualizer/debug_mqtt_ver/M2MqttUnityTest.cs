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

using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using uPLibrary.Networking.M2Mqtt;
using uPLibrary.Networking.M2Mqtt.Messages;
using Newtonsoft.Json;
using M2MqttUnity;
using Newtonsoft.Json.Bson;
using GameDataNameSpace;
using System.Linq;
using UnityEngine.Windows;
using System.Net.Configuration;

/// <summary>
/// Examples for the M2MQTT library (https://github.com/eclipse/paho.mqtt.m2mqtt),
/// </summary>
namespace M2MqttUnity.Examples
{
    /// <summary>
    /// Script for testing M2MQTT with a Unity UI
    /// </summary>
    public class M2MqttUnityTest : M2MqttUnityClient
    {

        public MsgHandler msgHandlerGameObject;
        public UIHandler uiHandlerGameObject;
        public CollisionHandler collisionHandlerGameObject;

        [Tooltip("Set this to true to perform a testing cycle automatically on startup")]
        public bool autoTest = false;
        [Header("User Interface")]
        public Button connectButton;
        public Button disconnectButton;

        private List<string> eventMessages = new List<string>();
        
        private int tempPlayerDeath = 0;
        private int tempEnemyDeath = 0;

        public void PublishState(int player_id, bool FOVmsg, bool inRainMsg, int inRainNumber)
        {
            string msgToSend = "vstate_fov_" + FOVmsg.ToString() + "_inbomb_" + inRainMsg.ToString() + "_" + inRainNumber.ToString();
            // Publish the generated message
            if (player_id == 2) {
                client.Publish("game_state/visualizer_to_engine/p2", System.Text.Encoding.UTF8.GetBytes(msgToSend), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
            } else {
                client.Publish("game_state/visualizer_to_engine/p1", System.Text.Encoding.UTF8.GetBytes(msgToSend), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false); 
            }
            Debug.Log(msgToSend);
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
			string connectingDescription = "Connecting to broker on " + brokerAddress + ":" + brokerPort.ToString() + "...\n";
			uiHandlerGameObject.UpdateSettingsDescription(connectingDescription);
			Debug.Log(connectingDescription);
        }

        protected override void OnConnected()
        {
            base.OnConnected();
            string playerView = isP1 ? "Player 1 VIEW" : "Player 2 VIEW";
            string connectedDescription = "Connected to broker on " + brokerAddress + "\n" + " Currently " + playerView + "\n";
			uiHandlerGameObject.UpdateSettingsDescription(connectedDescription);
			Debug.Log(connectedDescription);

            if (autoTest)
            {
                PublishState(1, true, true, 0);
            }
        }

        protected override void SubscribeTopics()
        {
            client.Subscribe(new string[] { "game_state/engine_to_visualizer" }, new byte[] { MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE });
        }

        protected override void UnsubscribeTopics()
        {
            client.Unsubscribe(new string[] { "game_state/engine_to_visualizer" });
        }

        protected override void OnConnectionFailed(string errorMessage)
        {
            Debug.Log("CONNECTION FAILED! " + errorMessage);
        }

        protected override void OnDisconnected()
        {
            string disconnectedMsg = "Disconnected";
			uiHandlerGameObject.UpdateSettingsDescription(disconnectedMsg);
			Debug.Log(disconnectedMsg);
        }

        protected override void OnConnectionLost()
        {
			Debug.Log("CONNECTION LOST!");
        }

        public void LogoutPlayer(PlayerData player)
        {
            // Implement logout logic, such as removing the player from the game
            Debug.Log($"Player {player.player_id} has logged out.");
        }

		private void CheckAndHandleDeath(PlayerData player)
		{
			if (player.game_state.deaths > tempPlayerDeath)
			{
				msgHandlerGameObject.HandleDeath(player);
                Debug.Log("DIED");
				
			}
			tempPlayerDeath = player.game_state.deaths;
            Debug.Log("tempPlayerDeath: " + tempPlayerDeath);
		}

		public void ProcessPlayerAction(PlayerData attacker, PlayerData opponent, bool targetInFOV)
        {
            string action = attacker.action;
            GameState attackerState = attacker.game_state;
            GameState opponentState = opponent.game_state;

            //// Check if action requires Field of View validation
            //if (new List<string> { "basket", "soccer", "volley", "bowl", "bomb" }.Contains(action))
            //{
            //    if (in_sight == "in_sight_False") {
            //        targetInFOV = false;
            //    }
            //}
			if (isP1)
			{
				if (attacker.player_id == 1)
				{
					CheckAndHandleDeath(attacker);
				}
				else if (opponent.player_id == 1)
				{
					CheckAndHandleDeath(opponent);
				}
			}
			else
			{
				if (attacker.player_id == 2)
				{
					CheckAndHandleDeath(attacker);
				}
				else if (opponent.player_id == 2)
				{
					CheckAndHandleDeath(opponent);
				}
			}

			switch (action)
            {
                case "gun":
                    msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
					msgHandlerGameObject.HandleReduceHealth(opponent);
					break;

                case "shield":
                    msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
                    break;

                case "reload":
                    msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
                    break;

                case "bomb":
                    if (targetInFOV)
                    {
						msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
						msgHandlerGameObject.HandleReduceHealth(opponent);
					}
                    break;

                case "basket":
                case "soccer":
                case "volley":
                case "bowl":
                    if (targetInFOV)
                    {
						msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
						msgHandlerGameObject.HandleReduceHealth(opponent);
					}
                    break;

                case "logout":
                    Disconnect();
					break;

                default:
                    // No action or unknown action
                    break;
            }
            
        }

        protected override void Start()
        {
            base.Start();
        }

        protected override void DecodeMessage(string topic, byte[] message)
        {
            string msg = System.Text.Encoding.UTF8.GetString(message);
            Debug.Log("Received: " + msg);
            StoreMessage(msg);

            if (topic == "game_state/engine_to_visualizer")
            {
                if (autoTest)
                {
                    autoTest = false;
                    Disconnect();
                }
            }
        }

        private void StoreMessage(string eventMsg)
        {
            eventMessages.Add(eventMsg);
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
			if (dataOriginPlayerId == "1") {
                ProcessPlayerAction(player1, player2, inSight);
            } else {
                ProcessPlayerAction(player2, player1, inSight);
            }

            string formattedMsg = FormatPlayerData(player1, player2, inSight, dataOriginPlayerId);

            Debug.Log("FormattedMsg: " + formattedMsg); // PRINTS on console to see if it receives msg properly @Darren

            //if (player1.action == "basket" || player1.action == "soccer" || player1.action == "volley" || player1.action == "bowl" || player1.action == "bomb") {
            //    if (this.isP1 && dataOriginPlayerId == "1") {
            //        PublishFOVState(1, in_sight_msg);
            //    } else if (!this.isP1 && dataOriginPlayerId == "2") {
            //        PublishFOVState(2, in_sight_msg);
            //    }
            //}
        }

		// Helper function to format player data into a string
		private string FormatPlayerData(PlayerData player1, PlayerData player2, bool in_sight_msg, string dataOriginPlayerId)
        {
            // Format Player 1 data
            string player1Data =$"  Health: {player1.game_state.hp}\n" +
                                $"  Bullets: {player1.game_state.bullets}\n" +
                                $"  Bombs: {player1.game_state.bombs}\n" +
                                $"  Shield HP: {player1.game_state.shield_hp}\n" +
                                $"  Deaths: {player1.game_state.deaths}\n" +
                                $"  Shields: {player1.game_state.shields}\n";

            // Format Player 2 data
            string player2Data = $"  Health: {player2.game_state.hp}\n" +
                                $"  Bullets: {player2.game_state.bullets}\n" +
                                $"  Bombs: {player2.game_state.bombs}\n" +
                                $"  Shield HP: {player2.game_state.shield_hp}\n" +
                                $"  Deaths: {player2.game_state.deaths}\n" +
                                $"  Shields: {player2.game_state.shields}\n";

            if (dataOriginPlayerId == "1") {
                player1Data = $"  Action: {player1.action}\n" + player1Data;
            } else if (dataOriginPlayerId == "2") {
                player2Data = $"  Action: {player2.action}\n" + player2Data;

            }
            
            // Combine both players' data
            if (this.isP1) {
                if (dataOriginPlayerId == "1" && player1.action != "logout" && player1.action != "gun" && player1.action != "reload" && player1.action != "shield") {
                    return $"Your Statistics (P1): \n{player1Data}\nOpponent Statistics (P2): \n{player2Data}\nP2 in FOV: {in_sight_msg}";
                } else {
                    return $"Your Statistics (P1): \n{player1Data}\nOpponent Statistics (P2): \n{player2Data}\n";
                }
            } else {
                if (dataOriginPlayerId == "2" && player2.action != "logout" &&  player2.action != "gun" &&  player2.action != "reload" &&  player2.action != "shield") {
                    return $"Your Statistics (P2): \n{player2Data}\nOpponent Statistics (P1): \n{player1Data}\nP1 in FOV: {in_sight_msg}";
                } else {
                    return $"Your Statistics (P2): \n{player2Data}\nOpponent Statistics (P1): \n{player1Data}\n";
                }
            }
        }
        protected override void Update()
        {
			base.Update(); // call ProcessMqttEvents()

            if (eventMessages.Count > 0)
            {
                foreach (string msg in eventMessages)
                {
					Debug.Log(msg);
					string[] parts = msg.Split(new char[] { '_' }, 2); // Split into 2 parts
                    string keyword = parts[0];

					// Checks if Enemy is in FOV
					bool in_sight_msg = uiHandlerGameObject.GetEnemyFOV();
					Debug.Log("DEBUG IN FOV: " + in_sight_msg);
                    bool in_rain_msg = collisionHandlerGameObject.IsInRain();
                    Debug.Log("DEBUG IN RAIN: " + in_rain_msg);
                    int in_rainbombs_number = collisionHandlerGameObject.GetInRainNumber();
					Debug.Log("DEBUG IN RAIN NUMBER: " + in_rainbombs_number);
					// action msg in format: action_<playerID>_<action>
					if (keyword == "action")
                    {
                        string[] tempArr = parts[1].Split(new char[] { '_' }, 2);
                        string playerID = tempArr[0];
                        string action = tempArr[1];
						if (new[] { "basket", "soccer", "volley", "bowl", "bomb", "gun" }.Contains(action))
						{
							if (this.isP1 && playerID == "1")
							{
								Debug.Log("Publishing");
								PublishState(1, in_sight_msg, in_rain_msg, in_rainbombs_number);
							}
							else if (!this.isP1 && playerID == "2")
							{
								PublishState(2, in_sight_msg, in_rain_msg, in_rainbombs_number);
							}
						}
					}
					// game state msg in format: gs_<gameStateMessage>
					else if (keyword == "gs")
                    {
                        ProcessMessage(parts[1], in_sight_msg);
                    }
                    else
                    {
                        Debug.Log("Invalid Message Format");
                    }
                }
                eventMessages.Clear();
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
}
