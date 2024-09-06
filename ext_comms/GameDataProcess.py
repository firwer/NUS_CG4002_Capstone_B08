import asyncio

import config


async def reduce_resources(predicted_action: str, currGameData, attacker_id: int):
    if attacker_id == 1:
        targetPlayerData = currGameData.p2.game_state
    else:
        targetPlayerData = currGameData.p1.game_state

    if predicted_action == "gun":
        targetPlayerData["bullets"] = max(0, targetPlayerData["bullets"] - 1)
    elif predicted_action == "bomb":
        targetPlayerData["bombs"] = max(0, targetPlayerData["bombs"] - 1)
    elif predicted_action == "shield":
        targetPlayerData["shields"] = max(0, targetPlayerData["shields"] - 1)
    elif predicted_action == "reload":
        pass
    elif predicted_action in {"basket", "soccer", "volley", "bowl"}:
        pass
    elif predicted_action == "logout":
        pass
    else:
        pass


async def reduce_health(currGameData, attacker_id: int, hp_reduction: int):
    if attacker_id == 1:
        targetPlayerData = currGameData.p2.game_state
    else:
        targetPlayerData = currGameData.p1.game_state

    # use the shield to protect the player

    if targetPlayerData["shield_hp"] > 0:
        new_hp_shield = max(0, targetPlayerData["shield_hp"] - hp_reduction)
        hp_reduction = max(0, hp_reduction - targetPlayerData["shield_hp"])
        # update the shield HP
        targetPlayerData["shield_hp"] = new_hp_shield

    # reduce the player HP
    targetPlayerData["hp"] = max(0, targetPlayerData["hp"] - hp_reduction)
    if targetPlayerData["hp"] == 0:
        # if we die, we spawn immediately
        targetPlayerData["deaths"] += 1

        # initialize all the states
        targetPlayerData["hp"] = config.GAME_MAX_HP
        targetPlayerData["bullets"] = config.GAME_MAX_BULLETS
        targetPlayerData["bombs"] = config.GAME_MAX_BOMBS
        targetPlayerData["shield_hp"] = 0
        targetPlayerData["shields"] = config.GAME_MAX_SHIELDS


# def gun_shoot(currGameData, attacker_id: int):
#
#         if self.num_bullets <= 0:
#             break
#         self.num_bullets -= 1
#
#         # check if the opponent is visible
#         if not can_see:
#             break
#
#         opponent.reduce_health(self.hp_bullet)
#         break


async def shield(targetPlayerData, attacker_id: int):
    """Activate shield"""
    while True:
        if targetPlayerData["shields"] <= 0:
            # check the number of shields available
            break
        elif targetPlayerData["shield_hp"] > 0:
            # check if shield is already active
            break
        targetPlayerData["shield_hp"] = config.GAME_MAX_SHIELD_HEALTH
        targetPlayerData["shields"] -= 1


async def reload(currGameData, attacker_id: int):
    """ perform reload only if the magazine is empty"""
    if attacker_id == 1:
        targetPlayerData = currGameData.p1.game_state
    else:
        targetPlayerData = currGameData.p2.game_state

    if targetPlayerData["bullets"] <= 0:
        targetPlayerData["bullets"] = config.GAME_MAX_BULLETS


async def game_state_manager(currGameData, attacker_id: int, pred_output_queue: asyncio.Queue):
    prediction_action = await pred_output_queue.get()
    prediction_action = prediction_action.decode('utf-8')

    if attacker_id == 1:
        currGameData.p1.action = prediction_action
        attackingPlayerData = currGameData.p1.game_state
        targetPlayerData = currGameData.p2.game_state
    else:
        currGameData.p2.action = prediction_action
        targetPlayerData = currGameData.p1.game_state
        attackingPlayerData = currGameData.p2.game_state

    if prediction_action == "gun":
        await reduce_health(currGameData, attacker_id, config.GAME_BULLET_DMG)
    elif prediction_action == "shield":
        await shield(currGameData, attacker_id)
    elif prediction_action == "reload":
        await reload(currGameData, attacker_id)
    elif prediction_action == "bomb":
        pass
    elif prediction_action in {"basket", "soccer", "volley", "bowl"}:
        await reduce_health(currGameData, attacker_id, config.GAME_AI_DMG)
    elif prediction_action == "logout":
        pass
    else:
        pass

    # if attacker_id == 1:
    #     self.currGameData.p1.update_state(action=prediction_action, game_state=currGameData.p1.game_state)
    # elif attacker_id == 2:
    #     self.currGameData.p2.update_state(action=prediction_action, game_state=currGameData.p2.game_state)
