using System.Collections;
using System.Collections.Generic;
using UnityEngine;
//using M2MqttUnity.Examples;
using GameDataNameSpace;
using System.Linq;
using UnityEngine.SceneManagement;

public class MsgHandler : MonoBehaviour
{
    public M2MqttUnityTest M2MqttUnityTestGameObject;

    public int myPlayerID;
    public int enemyID;

    public UIHandler uiHandler;
    public UIErrorHandler uiErrorHandler;
    //public CollisionHandler collisionHandler;
    public RainDetector rainDetectorGameObject;

    private int tempBombAmmo = 2;
    private int tempBulletAmmo = 6;
    private int tempShieldHpEquipped = 0;
    private int prevPlayerHp = 100;
    private int prevPlayerShieldHp = 0;

    // Define a list of actions that do not require ammo
    private string[] noAmmoActions = { "reload", "shield", "volley", "basket", "soccer", "bowl", "logout" };

    public void Player1Button()
    {
        myPlayerID = 1;
        enemyID = 2;
        //Debug.Log("CAPSTONE: I am Player 1");
        M2MqttUnityTestGameObject.GetPlayerNumber(myPlayerID);
        M2MqttUnityTestGameObject.Connect();
        uiHandler.SetPlayerNumText(myPlayerID);
    }
    public void Player2Button()
    {
        myPlayerID = 2;
        enemyID = 1;
        //Debug.Log("CAPSTONE: I am Player 2");
        M2MqttUnityTestGameObject.GetPlayerNumber(myPlayerID);
        M2MqttUnityTestGameObject.Connect();
        uiHandler.SetPlayerNumText(myPlayerID);
    }
    public int GetPlayerNumber()
    {
        return myPlayerID;
    }

    public void ResetScene()
    {
        // Get the active scene and reload it
        SceneManager.LoadScene(SceneManager.GetActiveScene().name);
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
    public void HandleReduceHealth(PlayerData attacker, PlayerData opponent)
    {
        // Attacker is THIS player, enemy not
        if (attacker.player_id == myPlayerID)
        {
            // Update previous values for the next comparison
            prevPlayerHp = attacker.game_state.hp;
            prevPlayerShieldHp = attacker.game_state.shield_hp;

            uiHandler.SetEnemyHealth(opponent.game_state.hp, opponent.game_state.shield_hp);
            Debug.Log("CAPSTONE: Updating enemy health. New HP: " + opponent.game_state.hp + ", New Shield HP: " + opponent.game_state.shield_hp);
        }
        // Attacker is ENEMY, player not
        else if (attacker.player_id != myPlayerID)
        {
            bool healthDecreased = opponent.game_state.hp < prevPlayerHp;
            bool shieldDecreased = opponent.game_state.shield_hp < prevPlayerShieldHp;
            Debug.Log("CAPSTONE: Target HP:" + opponent.game_state.hp + "Prev Hp: " + prevPlayerHp + "Shield HP: " + opponent.game_state.shield_hp + "Prev ShieldHP: " + prevPlayerShieldHp);
            // Only call SetHealth if either health or shield decreases
            if (healthDecreased || shieldDecreased)
            {
                uiHandler.SetHealth(opponent.game_state.hp, opponent.game_state.shields, opponent.game_state.shield_hp);
                Debug.Log("CAPSTONE: My player - HP or Shield reduced. New HP: " + opponent.game_state.hp + ", New Shield HP: " + opponent.game_state.shield_hp);
            }

            // Update previous values for the next comparison
            prevPlayerHp = opponent.game_state.hp;
            prevPlayerShieldHp = opponent.game_state.shield_hp;
        }
    }

    // Plays the animation
    public void HandleAction(string action, PlayerData attacker, bool isPlayerInFOV)
    {
        // User is the attacker
        if (myPlayerID == attacker.player_id)
        {
            switch (action)
            {
                default:
                    break;
                case "reload":
                    //Debug.Log("CAPSTONE: Playing reloading action");
                    uiHandler.Reload();
                    uiHandler.SetBullets(attacker.game_state.bullets);
                    break;
                case "gun":
                    //Debug.Log("CAPSTONE: Playing gun action");
                    uiHandler.ShootGun();
                    uiHandler.SetBullets(attacker.game_state.bullets);
                    break;
                case "shield":
                    //Debug.Log("CAPSTONE: Playing shield action");
                    uiHandler.SetMaxShield(attacker.game_state.shields);
                    break;
                case "basket":
                case "soccer":
                case "bowl":
                case "volley":
                    //Debug.Log("CAPSTONE: Playing throwing ball action");
                    uiHandler.ThrowBalls(action);
                    break;
                case "bomb":
                    //Debug.Log("CAPSTONE: Playing throwing bomb action");
                    uiHandler.ThrowBalls(action);
                    uiHandler.SetBombs(attacker.game_state.bombs);
                    break;
                case "logout":
                    uiHandler.PlayLogOut();
                    break;
            }
        }
        // User is getting attacked
        else
        {
            if (action == "shield")
            {
                uiHandler.SetEnemyMaxShield();
            }
            if (isPlayerInFOV)
            {
                if (action.StartsWith("random_"))
                {
                    action = action.Substring(7);
                }
                switch (action)
                {
                    default:
                        break;
                    case "basket":
                    case "soccer":
                    case "bowl":
                    case "volley":
                    case "bomb":
                        //Debug.Log("CAPSTONE: MsgHandler: User getting attacked. Calling uiHandler EnemyThrowBalls");
                        uiHandler.EnemyThrowBalls(action);
                        break;
                }
            }
        }
    }

    public void ActionChecker(string action, PlayerData attacker, bool isPlayerInFOV)
    {
        if (action.StartsWith("random_"))
        {
            action = action.Substring(7);
            uiErrorHandler.DisplayRandomActionAlertText();
        }
        //Debug.Log("CAPSTONE: Action received: " + action);
        if (action == "invalid")
        {
            uiErrorHandler.DisplayErrorInvalidActionText();
        }
        else if (action == "cooldown-progress")
        {
            uiErrorHandler.DisplayErrorOnCooldownText();
        }
        else if (action == "bomb" && tempBombAmmo <= 0)
        {
            uiErrorHandler.DisplayErrorBombText();
            uiErrorHandler.DisplayCooldownUI();
        }
        else if (action == "gun" && tempBulletAmmo <= 0)
        {
            uiErrorHandler.DisplayErrorGunText();
            uiErrorHandler.DisplayCooldownUI();
        }
        else if (action == "reload" && tempBulletAmmo > 0)
        {
            uiErrorHandler.DisplayErrorReloadText();
            uiErrorHandler.DisplayCooldownUI();
        }
        else if (action == "shield" && tempShieldHpEquipped > 0)
        {
            uiErrorHandler.DisplayErrorShieldText();
            uiErrorHandler.DisplayCooldownUI();
        }
        else if ((action == "bomb" && tempBombAmmo >= 1) || (action == "gun" && tempBulletAmmo >= 1) || noAmmoActions.Contains(action))
        {
            Debug.Log($"CAPSTONE: Processing player {attacker.player_id} action");
            HandleAction(action, attacker, isPlayerInFOV);
            uiErrorHandler.DisplayCooldownUI();
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
        if (!uiHandler.GetEnemyFOV())
        {
            return (false, 0);
        }
        return (uiHandler.GetEnemyFOV(), rainDetectorGameObject.CountRainsInContact());
    }
}
