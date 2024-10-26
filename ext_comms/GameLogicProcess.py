import asyncio
import time

import config

# Define separate variables for each player
targetInFOV_p1 = False
numOfRain_p1 = 0
targetInFOV_p2 = False
numOfRain_p2 = 0

async def reduce_health(targetGameState: dict, hp_reduction: int):
    print(f"Reducing health by {hp_reduction}")
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


async def bomb_player(targetGameState: dict, opponentGameState: dict, can_see: bool):
    """Throw a bomb at opponent"""
    if targetGameState["bombs"] <= 0:
        return

    targetGameState["bombs"] -= 1
    if can_see:
        await reduce_health(opponentGameState, config.GAME_BOMB_DMG)

"""
    This function is used to get the visualizer response which indicates whether the target is in the FOV of the attacker
    and the number of rain bombs the target is currently in
"""
async def getVState(visualizer_receive_queue: asyncio.Queue, player_id: int):
    global targetInFOV_p1, numOfRain_p1, targetInFOV_p2, numOfRain_p2
    while True:
        try:
            msg = await visualizer_receive_queue.get()
            msgStr = msg.decode()
            if msgStr.startswith('vstate_fov_'):
                parts = msgStr.split('_')
                fov_bool = parts[2]
                num_of_rain = int(parts[4])

                # Update variables based on player ID
                if player_id == 1:
                    if fov_bool == "True":
                        targetInFOV_p1 = True
                    else:
                        targetInFOV_p1 = False
                    numOfRain_p1 = num_of_rain
                    print(f"Updated Player 1 FOV to {targetInFOV_p1} and numOfRain to {numOfRain_p1}")

                elif player_id == 2:
                    if fov_bool == "True":
                        targetInFOV_p2 = True
                    else:
                        targetInFOV_p2 = False
                    numOfRain_p2 = num_of_rain
                    print(f"Updated Player 2 FOV to {targetInFOV_p2} and numOfRain to {numOfRain_p2}")


                if fov_bool == "True":
                    print("Target is in FOV, Valid attack")
                    targetInFOV = True
                elif fov_bool == "False":
                    print("Target is not in FOV, Invalid attack")
                    targetInFOV = False
        except asyncio.TimeoutError:
            print("Visualizer did not respond in time. Default True")
            targetInFOV = True


async def game_state_manager(currGameData, attacker_id: int,
                             pred_output_queue: asyncio.Queue,
                             visualizer_send_queue: asyncio.Queue,
                             gun_state_queue: asyncio.Queue):
    
    global targetInFOV_p1, numOfRain_p1, targetInFOV_p2, numOfRain_p2

    prediction_action = await pred_output_queue.get()
    print(f"Received prediction from PredictionService: {prediction_action} for player {attacker_id}")

    if attacker_id == 1:
        targetInFOV = targetInFOV_p1
        numOfRain = numOfRain_p1
        currGameData.p1.action = prediction_action
        targetPlayerData = currGameData.p1.game_state
        OpponentPlayerData = currGameData.p2.game_state
    else:
        targetInFOV = targetInFOV_p2
        numOfRain = numOfRain_p2
        currGameData.p2.action = prediction_action
        targetPlayerData = currGameData.p2.game_state
        OpponentPlayerData = currGameData.p1.game_state
    
    # Handle rain bomb damage
    if targetInFOV:
        for _ in range(numOfRain):
            print("-5 HP RAIN BOMB")
            await reduce_health(OpponentPlayerData, config.GAME_RAIN_DMG)

    if prediction_action == "gun":
        result = await gun_state_queue.get()
        # empty out gun_state_queue and get the last item - Prevent accumulation
        while not gun_state_queue.empty():
            result = await gun_state_queue.get()
        if result == "hit":
            await gun_shoot(targetPlayerData, OpponentPlayerData)
        elif result == "miss":
            # Only deduct bullet
            if targetPlayerData["bullets"] > 0:
                targetPlayerData["bullets"] -= 1
    elif prediction_action == "shield":
        await shield(targetPlayerData)
    elif prediction_action == "reload":
        await reload(targetPlayerData)
    elif prediction_action == "bomb":
        await bomb_player(targetPlayerData, OpponentPlayerData, targetInFOV)
    elif prediction_action in {"basket", "soccer", "volley", "bowl"}:
        if targetInFOV:
            await reduce_health(OpponentPlayerData, config.GAME_AI_DMG)
    elif prediction_action == "logout":
        # TODO: Implement logout action
        print("User logout")
    else:
        print("Invalid action received. Doing nothing.")

    # Send updated game state to visualizer
    await visualizer_send_queue.put("gs_" + currGameData.to_json(attacker_id))  # Add gs_ prefix to indicate game
