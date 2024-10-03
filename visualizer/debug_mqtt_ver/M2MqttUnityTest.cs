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
		//public class GameState
  //      {
  //          public int hp { get; set; }
  //          public int bullets { get; set; }
  //          public int bombs { get; set; }
  //          public int shield_hp { get; set; }
  //          public int deaths { get; set; }
  //          public int shields { get; set; }
  //      }

  //      public static class GameConfig
  //      {
  //          public const int GAME_MAX_HP = 100;
  //          public const int GAME_MAX_BULLETS = 6;
  //          public const int GAME_MAX_BOMBS = 2;
  //          public const int GAME_MAX_SHIELD_HEALTH = 30;
  //          public const int GAME_MAX_SHIELDS = 3;
  //          public const int GAME_BULLET_DMG = 5;
  //          public const int GAME_AI_DMG = 10;
  //          public const int GAME_BOMB_DMG = 5;
  //      }

  //      public class PlayerData
  //      {
  //          public int player_id { get; set; }
  //          public string action { get; set; }
  //          public GameState game_state { get; set; }
  //      }
        [Tooltip("Set this to true to perform a testing cycle automatically on startup")]
        public bool autoTest = false;
        [Header("User Interface")]
        public Button connectButton;
        public Button disconnectButton;

        private List<string> eventMessages = new List<string>();

        public void PublishFOVState(int player_id, string msg)
        {
            // Publish the randomly generated message
            if (player_id == 2) {
                client.Publish("game_state/visualizer_to_engine/p2", System.Text.Encoding.UTF8.GetBytes(msg), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
            } else {
                client.Publish("game_state/visualizer_to_engine/p1", System.Text.Encoding.UTF8.GetBytes(msg), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false); 
            }
            
            //AddUiMessage($"{messageToPublish} published.");
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
                this.isP1 = true;
				playerMsg = "Setting player mode to Player 1";
			}
            else
            {
                this.isP1 = false;
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
            string playerView = this.isP1 ? "Player 1 VIEW" : "Player 2 VIEW";
            string connectedDescription = "Connected to broker on " + brokerAddress + "\n" + " Currently " + playerView + "\n";
			uiHandlerGameObject.UpdateSettingsDescription(connectedDescription);
			Debug.Log(connectedDescription);

            if (autoTest)
            {
                PublishFOVState(1, "in_sight_True");
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
        
        public void ReduceHealth(PlayerData targetPlayer, int hpReduction)
        {
            // Use the shield to protect the player
            if (targetPlayer.game_state.shield_hp > 0)
            {
                int newShieldHp = Mathf.Max(0, targetPlayer.game_state.shield_hp - hpReduction);
                hpReduction = Mathf.Max(0, hpReduction - targetPlayer.game_state.shield_hp);
                // Update the shield HP
                targetPlayer.game_state.shield_hp = newShieldHp;
            }

            // Reduce the player HP
            targetPlayer.game_state.hp = Mathf.Max(0, targetPlayer.game_state.hp - hpReduction);
            msgHandlerGameObject.HandleReduceHealth(targetPlayer);
            if (targetPlayer.game_state.hp == 0)
            {
                // If the player dies, increment deaths and reset stats
                targetPlayer.game_state.deaths += 1;
                msgHandlerGameObject.HandleDeath(targetPlayer);
				// Reset player stats
				targetPlayer.game_state.hp = GameConfig.GAME_MAX_HP;
                targetPlayer.game_state.bullets = GameConfig.GAME_MAX_BULLETS;
                targetPlayer.game_state.bombs = GameConfig.GAME_MAX_BOMBS;
                targetPlayer.game_state.shield_hp = 0;
                targetPlayer.game_state.shields = GameConfig.GAME_MAX_SHIELDS;
            }
        }

        public void GunShoot(PlayerData player, PlayerData opponent)
        {
            if (player.game_state.bullets <= 0)
            {
                return;
            }

			player.game_state.bullets -= 1;
            ReduceHealth(opponent, GameConfig.GAME_BULLET_DMG);
        }

        public void ActivateShield(GameState playerState)
        {
            if (playerState.shields <= 0 || playerState.shield_hp > 0)
            {
                // No shields left or shield already active
                return;
            }

            playerState.shield_hp = GameConfig.GAME_MAX_SHIELD_HEALTH;
            playerState.shields -= 1;
        }

        public void Reload(GameState playerState)
        {
            if (playerState.bullets <= 0)
            {
                playerState.bullets = GameConfig.GAME_MAX_BULLETS;
            }
        }

        public void BombAttack(GameState attackerState, PlayerData opponent)
        {
            if (attackerState.bombs <= 0)
            {
                return;
            }

            attackerState.bombs -= 1;
            ReduceHealth(opponent, GameConfig.GAME_BOMB_DMG); // Adjust damage as needed
        }

        public void LogoutPlayer(PlayerData player)
        {
            // Implement logout logic, such as removing the player from the game
            Debug.Log($"Player {player.player_id} has logged out.");
        }






        public void ProcessPlayerAction(PlayerData attacker, PlayerData opponent, string in_sight)
        {
            string action = attacker.action;
            GameState attackerState = attacker.game_state;
            GameState opponentState = opponent.game_state;

            bool targetInFOV = true;
            // Check if action requires Field of View validation
            if (new List<string> { "basket", "soccer", "volley", "bowl", "bomb" }.Contains(action))
            {
                if (in_sight == "in_sight_False") {
                    targetInFOV = false;
                }
            }

			switch (action)
            {
				case "gun":
                    GunShoot(attacker, opponent);
					msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
					break;

                case "shield":
                    ActivateShield(attackerState);
					msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
					break;

                case "reload":
                    Reload(attackerState);
					msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
					break;

                case "bomb":
                    if (targetInFOV)
                    {
                        BombAttack(attackerState, opponent);
						msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
					}
                    break;

                case "basket":
                case "soccer":
                case "volley":
                case "bowl":
                    if (targetInFOV)
                    {
                        ReduceHealth(opponent, GameConfig.GAME_AI_DMG);
						msgHandlerGameObject.HandleAIAction(action, attacker, opponent);
					}
                    break;
                case "logout":
                    // Implement logout action
                    LogoutPlayer(attacker);
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

        private void ProcessMessage(string msg)
        {
            RootObject rootObject = JsonConvert.DeserializeObject<RootObject>(msg); // The struct of this is at M2MqttUnityClient.cs
            
            // Retrieve the player_id (Where this data came from)
            string dataOriginPlayerId = rootObject.player_id;
            
            // Deserialize player 1 and player 2 data
            PlayerData player1 = JsonConvert.DeserializeObject<PlayerData>(rootObject.p1);
            PlayerData player2 = JsonConvert.DeserializeObject<PlayerData>(rootObject.p2);

            // Checks if Enemy is in FOV
			string in_sight_msg = uiHandlerGameObject.GetEnemyFOV();

            // Process game state based on who is the attacker
            if (dataOriginPlayerId == "1") {
                ProcessPlayerAction(player1, player2, in_sight_msg);
            } else {
                ProcessPlayerAction(player2, player1, in_sight_msg);
            }

            string formattedMsg = FormatPlayerData(player1, player2, in_sight_msg, dataOriginPlayerId);

            Debug.Log(formattedMsg); // PRINTS on console to see if it receives msg properly

            if (player1.action == "basket" || player1.action == "soccer" || player1.action == "volley" || player1.action == "bowl" || player1.action == "bomb") {
                if (this.isP1 && dataOriginPlayerId == "1") {
                    PublishFOVState(1, in_sight_msg);
                } else if (!this.isP1 && dataOriginPlayerId == "2") {
                    PublishFOVState(2, in_sight_msg);
                }
            }
        }

        // Helper function to format player data into a string
        private string FormatPlayerData(PlayerData player1, PlayerData player2, string in_sight_msg, string dataOriginPlayerId)
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
                    ProcessMessage(msg);
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
