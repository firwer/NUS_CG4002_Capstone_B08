using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using M2MqttUnity.Examples;
using GameDataNameSpace;
using System.Linq;

public class MsgHandler : MonoBehaviour
{
    public M2MqttUnityTest M2MqttUnityTestGameObject;

    public int myPlayerID;
    public int enemyID;

    public UIHandler uiHandler;
    public UIErrorHandler uiErrorHandler;
    public CollisionHandler collisionHandler;

    private int tempBombAmmo = 2;
    private int tempBulletAmmo = 6;
    private int tempShieldHpEquipped = 0;
    // Define a list of actions that do not require ammo
    private string[] noAmmoActions = { "reload", "shield", "volley", "basket", "soccer", "bowl", "logout" };

    public void Player1Button()
    {
        myPlayerID = 1;
        enemyID = 2;
        Debug.Log("CAPSTONE: I am Player 1");
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
    public void HandleAction(string action, PlayerData attacker)
    {
        // User is the attacker
        if (myPlayerID == attacker.player_id)
        {
            switch (action)
            {
                default:
                    break;
                case "reload":
                    uiHandler.Reload();
                    uiHandler.SetBullets(attacker.game_state.bullets);
                    break;
                case "gun":
                    uiHandler.ShootGun();
                    uiHandler.SetBullets(attacker.game_state.bullets);
                    break;
                case "shield":
                    uiHandler.SetMaxShield(attacker.game_state.shields);
                    break;
                case "basket":
                case "soccer":
                case "bowl":
                case "volley":
                    uiHandler.ThrowBalls(action);
                    break;
                case "bomb":
                    uiHandler.ThrowBalls(action);
                    uiHandler.SetBombs(attacker.game_state.bombs);
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
                    Debug.Log("CAPSTONE: MsgHandler: User getting attacked. Calling uiHandler EnemyThrowBalls");
                    uiHandler.EnemyThrowBalls(action);
                    break;

            }
        }
    }

    public void ActionChecker(string action, PlayerData attacker)
    {
        Debug.Log("CAPSTONE: Action received: " + action);
        if (action == "invalid")
        {
            uiErrorHandler.DisplayErrorInvalidActionText();
        }
        else if (action == "bomb" && tempBombAmmo <= 0)
        {
            uiErrorHandler.DisplayErrorBombText();
        }
        else if (action == "gun" && tempBulletAmmo <= 0)
        {
            uiErrorHandler.DisplayErrorGunText();
        }
        else if (action == "reload" && tempBulletAmmo > 0)
        {
            uiErrorHandler.DisplayErrorReloadText();
        }
        else if (action == "shield" && tempShieldHpEquipped > 0)
        {
            uiErrorHandler.DisplayErrorShieldText();
        }
        else if ((action == "bomb" && tempBombAmmo >= 1) || (action == "gun" && tempBulletAmmo >= 1) || noAmmoActions.Contains(action))
        {
            Debug.Log($"CAPSTONE: Processing player {attacker.player_id} action");
            HandleAction(action, attacker);
        }
        else
        {
            Debug.Log("CAPSTONE: Unable to ProcessPlayerAction");
        }

        tempBombAmmo = attacker.game_state.bombs;
        tempBulletAmmo = attacker.game_state.bullets;
        tempShieldHpEquipped = attacker.game_state.shield_hp;
    }

    public (bool, int) FovAndRainChecker()
    {
        return (uiHandler.GetEnemyFOV(), collisionHandler.GetInRainNumber());
    }
}
