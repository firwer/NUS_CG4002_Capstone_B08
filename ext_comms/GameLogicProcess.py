import asyncio

import config


async def reduce_health(targetGameState: dict, hp_reduction: int):
    # use the shield to protect the player

    if targetGameState["shield_hp"] > 0:
        new_hp_shield = max(0, targetGameState["shield_hp"] - hp_reduction)
        hp_reduction = max(0, hp_reduction - targetGameState["shield_hp"])
        # update the shield HP
        targetGameState["shield_hp"] = new_hp_shield

    # reduce the player HP
    targetGameState["hp"] = max(0, targetGameState["hp"] - hp_reduction)
    if targetGameState["hp"] == 0:
        # if we die, we spawn immediately
        targetGameState["deaths"] += 1

        # initialize all the states
        targetGameState["hp"] = config.GAME_MAX_HP
        targetGameState["bullets"] = config.GAME_MAX_BULLETS
        targetGameState["bombs"] = config.GAME_MAX_BOMBS
        targetGameState["shield_hp"] = 0
        targetGameState["shields"] = config.GAME_MAX_SHIELDS


async def gun_shoot(targetGameState: dict, opponentGameState: dict):
    if targetGameState["bullets"] <= 0:
        return
    targetGameState["bullets"] -= 1
    await reduce_health(opponentGameState, config.GAME_BULLET_DMG)


async def shield(targetGameState: dict):
    """Activate shield"""
    while True:
        if targetGameState["shields"] <= 0:
            # check the number of shields available
            break
        elif targetGameState["shield_hp"] > 0:
            # check if shield is already active
            break
        targetGameState["shield_hp"] = config.GAME_MAX_SHIELD_HEALTH
        targetGameState["shields"] -= 1


async def reload(targetGameState: dict):
    """ perform reload only if the magazine is empty"""
    if targetGameState["bullets"] <= 0:
        targetGameState["bullets"] = config.GAME_MAX_BULLETS


async def bomb_player(targetGameState: dict, opponentGameState: dict):
    """Throw a bomb at opponent"""
    if targetGameState["bombs"] <= 0:
        return
    targetGameState["bombs"] -= 1
    await reduce_health(opponentGameState, config.GAME_BOMB_DMG)


async def game_state_manager(currGameData, attacker_id: int,
                             pred_output_queue: asyncio.Queue,
                             visualizer_receive_queue: asyncio.Queue,
                             visualizer_send_queue: asyncio.Queue):
    prediction_action = await pred_output_queue.get()
    print(f"Received prediction from PredictionService: {prediction_action} for player {attacker_id}")

    if attacker_id == 1:
        currGameData.p1.action = prediction_action
        targetPlayerData = currGameData.p1.game_state
        OpponentPlayerData = currGameData.p2.game_state
    else:
        currGameData.p2.action = prediction_action
        targetPlayerData = currGameData.p2.game_state
        OpponentPlayerData = currGameData.p1.game_state

    print("Updating Visualizer..")
    # Send game state to visualizer (Attributes not yet adjusted, Visualizer will do on its own)
    await visualizer_send_queue.put(currGameData.to_json(attacker_id))
    targetInFOV = False
    if prediction_action in {"basket", "soccer", "volley", "bowl", "bomb"}:
        try:
            msg = await asyncio.wait_for(visualizer_receive_queue.get(),
                                         config.VISUALIZER_RESPONSE_TIMEOUT)  # Wait for visualizer response
            msgStr = msg.decode()
            if msgStr.startswith('in_sight_'):
                if msgStr[9:] == "True":
                    print("Target is in FOV, Valid attack")
                    targetInFOV = True
                else:
                    print("Target is not in FOV, Invalid attack")
                    targetInFOV = False
        except asyncio.TimeoutError:
            print("Visualizer did not respond in time. Default True")
            targetInFOV = True
    else:
        targetInFOV = True

    if prediction_action == "gun":
        await gun_shoot(targetPlayerData, OpponentPlayerData)
    elif prediction_action == "shield":
        await shield(targetPlayerData)
    elif prediction_action == "reload":
        await reload(targetPlayerData)
    elif prediction_action == "bomb":
        if targetInFOV:
            await bomb_player(targetPlayerData, OpponentPlayerData)
    elif prediction_action in {"basket", "soccer", "volley", "bowl"}:
        if targetInFOV:
            await reduce_health(OpponentPlayerData, config.GAME_AI_DMG)
    elif prediction_action == "logout":
        # TODO: Implement logout action
        pass
    else:
        pass
