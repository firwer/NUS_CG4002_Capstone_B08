using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using M2MqttUnity.Examples;
using GameDataNameSpace;

public class MsgHandler : MonoBehaviour
{
	public M2MqttUnityTest M2MqttUnityTestGameObject;

	public int myPlayerID;
	public int enemyID;

    public UIHandler uiHandler;
	
	public void Player1Button()
	{
		myPlayerID = 1;
		enemyID = 2;
		Debug.Log("I am Player 1");
		M2MqttUnityTestGameObject.GetPlayerNumber(myPlayerID);
		uiHandler.SetPlayerNumText(myPlayerID);
	}
	public void Player2Button()
	{
		myPlayerID = 2;
		enemyID = 1;
		Debug.Log("I am Player 2");
		M2MqttUnityTestGameObject.GetPlayerNumber(myPlayerID);
		uiHandler.SetPlayerNumText(myPlayerID);
	}
	public int GetPlayerNumber()
	{
		return myPlayerID;
	}

	public void HandleDeath(PlayerData targetPlayer)
	{
		// User has died
		if ((myPlayerID == 1 && targetPlayer.player_id == 1) || (myPlayerID == 2 && targetPlayer.player_id == 2))
		{
			uiHandler.SetDeath();
			uiHandler.UpdateDeaths(targetPlayer.game_state.deaths);
			Debug.Log("CAPSTONE: Player died, new hp: " + targetPlayer.game_state.hp);
		}
		// Enemy has died
		else
		{
			uiHandler.UpdateKills(targetPlayer.game_state.deaths);
			uiHandler.SetEnemyHealth(targetPlayer.game_state.hp, targetPlayer.game_state.shield_hp);
		}
	}
	public void HandleReduceHealth(PlayerData targetPlayer)
	{
		// User has reduce health
		if (myPlayerID == targetPlayer.player_id)
		{
			uiHandler.SetHealth(targetPlayer.game_state.hp, targetPlayer.game_state.shields, targetPlayer.game_state.shield_hp);
			Debug.Log("CAPSTONE: Hp deducted, new hp: " + targetPlayer.game_state.hp);
		}
		// Enemy has reduce health
		else
		{
			uiHandler.SetEnemyHealth(targetPlayer.game_state.hp, targetPlayer.game_state.shield_hp);

		}
	}

	// Plays the animation
	public void HandleAIAction(string action, int attackerID)
	{
		// User is the attacker
		if (myPlayerID == attackerID)
		{
			switch (action)
			{
				default:
					break;
				case "reload":
					uiHandler.Reload();
					break;
				case "gun":
					uiHandler.ShootGun();
					break;
				case "shield":
					uiHandler.SetMaxShield();
					break;
				case "basket":
				case "soccer":
				case "bowl":
				case "volley":
				case "bomb":
					uiHandler.ThrowBalls(action);
					break;
			}
		}
		// User is getting attacked
		else
		{
			switch (action)
			{
				default:
					break;
				case "gun":
					//uiHandler.ShootGun();
					break;
				case "shield":
					uiHandler.SetEnemyMaxShield();
					break;
				case "basket":
				case "soccer":
				case "bowl":
				case "volley":
				case "bomb":
					uiHandler.EnemyThrowBalls(action);
					break;

			}
		}
	}
	public void HandleState(string action, PlayerData attacker, PlayerData opponent)
	{
		// User is the attacker
		if (myPlayerID == attacker.player_id)
		{
			switch (action)
			{
				default:
					break;
				case "reload":
					uiHandler.SetBullets(attacker.game_state.bullets);
					Debug.Log(attacker.game_state.bullets);
					break;
				case "gun":
					uiHandler.SetBullets(attacker.game_state.bullets);
					Debug.Log("MyPlayer bullets: " + attacker.game_state.bullets);
					Debug.Log("EnemyPlayer health: " + opponent.game_state.hp);
					break;
				case "bomb":
					uiHandler.SetBombs(attacker.game_state.bombs);
					Debug.Log("Bombs left: " + attacker.game_state.bombs);
					break;
				case "shield":
					uiHandler.SetShield(attacker.game_state.shields, attacker.game_state.shield_hp);
					Debug.Log(attacker.game_state.shields);
					break;
			}
		}
	}

	public void HandleEnemyMsg(PlayerData myPlayer, PlayerData enemyPlayer)
	{
		// Handles the Enemy UI shown on myPlayer screen
		string enemyAction = enemyPlayer.action;
		Debug.Log("Enemy Action is: " + enemyAction);
		switch (enemyAction)
		{
			default:
				break;
			case "shot":
				uiHandler.SetEnemyHealth(enemyPlayer.game_state.hp, enemyPlayer.game_state.shield_hp);
				Debug.Log(enemyPlayer.game_state.hp);
				break;
			case "died":
				uiHandler.SetDeath();
				uiHandler.UpdateDeaths(enemyPlayer.game_state.deaths);
				Debug.Log(enemyPlayer.game_state.hp);
				break;
			/*			case "reload":
							uiHandler.SetMaxBullets();
							uiHandler.Reload();
							Debug.Log(rootObject.MyPlayer.Gamestate.bullets);
							break;
						case "gun":
							uiHandler.SetBullets(rootObject.MyPlayer.Gamestate.bullets);
							uiHandler.SetEnemyHealth(rootObject.EnemyPlayer.Gamestate.hp, rootObject.EnemyPlayer.Gamestate.shield_hp);
							uiHandler.UpdateDeaths(rootObject.MyPlayer.Gamestate.deaths);
							Debug.Log("MyPlayer bullets: " + rootObject.MyPlayer.Gamestate.bullets);
							Debug.Log("EnemyPlayer health: " + rootObject.EnemyPlayer.Gamestate.hp);
							break;
						case "bomb":
							uiHandler.SetBombs(rootObject.MyPlayer.Gamestate.bombs);
							uiHandler.ThrowBalls(rootObject.MyPlayer.action);
							Debug.Log(rootObject.MyPlayer.Gamestate.bombs);
							break;*/
			case "shield":
				uiHandler.SetEnemyMaxShield();
				Debug.Log("Enemy Shields left: " + enemyPlayer.game_state.shields);
				break;
				/*			case "basketball":
							case "soccer":
							case "bowling":
							case "volleyball":
								uiHandler.ThrowBalls(rootObject.MyPlayer.action);
								Debug.Log("MSG Handler: " + rootObject.MyPlayer.action);
								break;
							case "reset":
								uiHandler.SetMaxHealth();
								uiHandler.SetMaxBullets();
								uiHandler.SetMaxBombs();
								uiHandler.SetMaxShieldAmmo();
								break;*/
		}
	}
}
