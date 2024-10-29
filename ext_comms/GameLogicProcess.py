# gamelogicprocess.py
import asyncio

from logger_config import setup_logger
import config

logger = setup_logger(__name__)

# Define separate variables for each player
targetInFOV_p1 = False
numOfRain_p1 = 0
targetInFOV_p2 = False
numOfRain_p2 = 0


async def reduce_health(targetGameState: dict, hp_reduction: int):
    logger.debug(f"Reducing health by {hp_reduction}")
    try:
        # Use the shield to protect the player
        if targetGameState["shield_hp"] > 0:
            new_hp_shield = max(0, targetGameState["shield_hp"] - hp_reduction)
            hp_reduction = max(0, hp_reduction - targetGameState["shield_hp"])
            targetGameState["shield_hp"] = new_hp_shield
            logger.debug(f"Shield HP after reduction: {targetGameState['shield_hp']}")

        # Reduce the player HP
        targetGameState["hp"] = max(0, targetGameState["hp"] - hp_reduction)
        logger.info(f"Player HP after reduction: {targetGameState['hp']}")

        if targetGameState["hp"] == 0:
            targetGameState["deaths"] += 1
            logger.warning(f"Player died. Total deaths: {targetGameState['deaths']}")
            # Initialize all the states
            targetGameState["hp"] = config.GAME_MAX_HP
            targetGameState["bullets"] = config.GAME_MAX_BULLETS
            targetGameState["bombs"] = config.GAME_MAX_BOMBS
            targetGameState["shield_hp"] = 0
            targetGameState["shields"] = config.GAME_MAX_SHIELDS
            logger.info("Player state reset after death.")
    except Exception as e:
        logger.exception(f"Error in reduce_health: {e}")


async def gun_shoot(targetGameState: dict, opponentGameState: dict):
    if targetGameState["bullets"] <= 0:
        logger.warning("Attempted to shoot with no bullets.")
        return
    targetGameState["bullets"] -= 1
    logger.info(f"Bullets left after shooting: {targetGameState['bullets']}")
    await reduce_health(opponentGameState, config.GAME_BULLET_DMG)
    logger.debug("Executed gun_shoot.")


async def shield(targetGameState: dict):
    """Activate shield"""
    logger.info("Activating shield.")
    try:
        while True:
            if targetGameState["shields"] <= 0:
                logger.warning("No shields left to activate.")
                break
            elif targetGameState["shield_hp"] > 0:
                logger.debug("Shield already active.")
                break
            targetGameState["shield_hp"] = config.GAME_MAX_SHIELD_HEALTH
            targetGameState["shields"] -= 1
            logger.info(f"Shield activated. Shields left: {targetGameState['shields']}")
            break  # Exit after activation
    except Exception as e:
        logger.exception(f"Error in shield: {e}")


async def reload(targetGameState: dict):
    """Perform reload only if the magazine is empty"""
    if targetGameState["bullets"] <= 0:
        targetGameState["bullets"] = config.GAME_MAX_BULLETS
        logger.info("Reloaded bullets to maximum.")
    else:
        logger.debug("Reload attempted but bullets are not empty.")


async def bomb_player(targetGameState: dict, opponentGameState: dict, can_see: bool):
    """Throw a bomb at opponent"""
    if targetGameState["bombs"] <= 0:
        logger.warning("Attempted to throw bomb with no bombs left.")
        return

    targetGameState["bombs"] -= 1
    logger.info(f"Bombs left after throwing: {targetGameState['bombs']}")
    if can_see:
        await reduce_health(opponentGameState, config.GAME_BOMB_DMG)
        logger.info("Bomb hit the opponent.")
    else:
        logger.info("Bomb missed the opponent.")


async def getVState(visualizer_receive_queue: asyncio.Queue, player_id: int):
    global targetInFOV_p1, numOfRain_p1, targetInFOV_p2, numOfRain_p2
    logger.debug(f"Starting getVState for player {player_id}")
    while True:
        try:
            msg = await visualizer_receive_queue.get()
            msgStr = msg.decode()
            if msgStr.startswith('vstate_fov_'):
                parts = msgStr.split('_')
                if len(parts) < 5:
                    logger.warning(f"Malformed vstate_fov message: {msgStr}")
                    continue
                fov_bool = parts[2]
                num_of_rain = int(parts[4])

                if player_id == 1:
                    targetInFOV_p1 = fov_bool == "True"
                    numOfRain_p1 = num_of_rain
                    logger.info(f"Player 1: Opponent P2 FOV - {targetInFOV_p1} and numOfRain to {numOfRain_p1}")
                elif player_id == 2:
                    targetInFOV_p2 = fov_bool == "True"
                    numOfRain_p2 = num_of_rain
                    logger.info(f"Player 2: Opponent P1 FOV - {targetInFOV_p2} and numOfRain to {numOfRain_p2}")
        except Exception as e:
            logger.exception(f"Error in getVState for player {player_id}: {e}")


async def game_state_manager(currGameData, attacker_id: int,
                             pred_output_queue: asyncio.Queue,
                             gun_state_queue: asyncio.Queue):
    global targetInFOV_p1, numOfRain_p1, targetInFOV_p2, numOfRain_p2

    try:
        prediction_action = await pred_output_queue.get()
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
                logger.info(f"[P{attacker_id}] -5 HP RAIN BOMB")
                await reduce_health(OpponentPlayerData, config.GAME_RAIN_DMG)

        if prediction_action == "gun":
            result = await gun_state_queue.get()
            # Empty out gun_state_queue and get the last item to prevent accumulation
            while not gun_state_queue.empty():
                result = await gun_state_queue.get()
            if result == "hit":
                await gun_shoot(targetPlayerData, OpponentPlayerData)
            elif result == "miss":
                # Only deduct bullet
                if targetPlayerData["bullets"] > 0:
                    targetPlayerData["bullets"] -= 1
                    logger.info(f"[P{attacker_id}] Shot missed. Bullets left: {targetPlayerData['bullets']}")
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
            logger.info(f"[P{attacker_id}] User logout")
        else:
            logger.warning(f"[P{attacker_id}] Invalid action received: {prediction_action}. Doing nothing.")
    except Exception as e:
        logger.exception(f"[P{attacker_id}] Error in game_state_manager: {e}")
