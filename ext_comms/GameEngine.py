# gameengine.py
import asyncio
import json
import random

import config
from ActionCooldownManager import ActionCooldownManager
from logger_config import setup_logger
from EvaluationProcess import start_evaluation_process
from GameLogicProcess import game_state_manager
from GameLogicProcess import getVState
from PredictionService import PredictionServiceProcess
from comms.AsyncMQTTController import AsyncMQTTController
from comms.TCPS_Controller import TCPS_Controller
from int_comms.relay.packet import get_packet, PACKET_DATA_HEALTH, PACKET_DATA_BULLET, PACKET_DATA_IMU, PACKET_DATA_KICK

logger = setup_logger(__name__)


class GamePlayerData:
    player_id: int
    action: str
    game_state: dict

    def __init__(self, player_id, action, game_state):
        self.player_id = player_id
        self.action = action
        self.game_state = game_state

    def to_json(self):
        return json.dumps({
            'player_id': self.player_id,
            'action': self.action,
            'game_state': self.game_state
        })

    # Json received from eval server
    def from_json(self, json_str):
        data = json.loads(json_str)
        self.game_state = data['p1']
        return self

    def update_state(self, action: str, game_state: dict):
        self.action = action
        self.game_state = game_state


class GameData:
    p1: GamePlayerData
    p2: GamePlayerData

    def __init__(self):
        self.p1 = GamePlayerData(1, 'none', {
            'hp': 100,
            'bullets': 6,
            'bombs': 2,
            'shield_hp': 0,
            'deaths': 0,
            'shields': 3
        })
        self.p2 = GamePlayerData(2, 'none', {
            'hp': 100,
            'bullets': 6,
            'bombs': 2,
            'shield_hp': 0,
            'deaths': 0,
            'shields': 3
        })

    def to_json(self, player_id):
        return json.dumps({
            'player_id': player_id,
            'p1': self.p1.to_json(),
            'p2': self.p2.to_json()
        })


async def evaluation_server_job(curr_game_data: GameData, player_id: int, eval_input_queue: asyncio.Queue,
                                eval_output_queue: asyncio.Queue):
    EvalGameData = {
        "player_id": player_id,
        "action": curr_game_data.p1.action if player_id == 1 else curr_game_data.p2.action,
        "game_state": {
            "p1": curr_game_data.p1.game_state,
            "p2": curr_game_data.p2.game_state
        }
    }
    try:
        # Send updated game state to evaluation server
        await eval_input_queue.put(json.dumps(EvalGameData))
        logger.info(f"[P{player_id}] Sent game data to evaluation server and waiting for response...")
        # Wait for evaluation response

        eval_resp = await asyncio.wait_for(eval_output_queue.get(), 5)
        logger.debug(f"[P{player_id}] Received evaluation response: {eval_resp}")

        eval_gs = json.loads(eval_resp)

        # Update game state based on evaluation response
        curr_game_data.p1.game_state = eval_gs.get('p1', curr_game_data.p1.game_state)
        curr_game_data.p2.game_state = eval_gs.get('p2', curr_game_data.p2.game_state)
        logger.info(f"[P{player_id}] Updated game state with evaluation response")
    except asyncio.TimeoutError:
        logger.warning(f"[P{player_id}] Timeout while waiting for evaluation response.")
    except Exception as e:
        logger.exception(f"[P{player_id}] Error communicating with evaluation server: {e}")


async def start_mqtt_job(receive_topic_p1: str,
                         receive_topic_p2: str,
                         send_topic: str,
                         receive_queue_p1: asyncio.Queue,
                         receive_queue_p2: asyncio.Queue,
                         send_queue: asyncio.Queue):
    try:
        mqtt_client = AsyncMQTTController(
            config.MQTT_BROKER_PORT,
            receive_queue_p1=receive_queue_p1,
            receive_queue_p2=receive_queue_p2,
            send_queue=send_queue
        )
        logger.info("Starting MQTT Client...")
        await mqtt_client.start(receive_topic_p1, receive_topic_p2, send_topic)
    except Exception as e:
        logger.exception(f"Failed to start MQTT job: {e}")


async def start_tcp_job(tcp_port: int, receive_queue_p1: asyncio.Queue, receive_queue_p2: asyncio.Queue,
                        send_queue: asyncio.Queue):
    try:
        tcp_server = TCPS_Controller(
            ip=config.TCP_SERVER_HOST,
            port=tcp_port,
            secret_key=config.TCP_SECRET_KEY,
            receive_queue_p1=receive_queue_p1,
            receive_queue_p2=receive_queue_p2,
            send_queue=send_queue
        )
        logger.info(f"Starting TCP Server on port {tcp_port}...")
        await tcp_server.start_server()
    except Exception as e:
        logger.exception(f"Failed to start TCP server on port {tcp_port}: {e}")


async def start_relay_node_data_handler(src_input_queue_p1: asyncio.Queue,
                                        src_input_queue_p2: asyncio.Queue,
                                        output_sensor_data_p1: asyncio.Queue,
                                        output_sensor_data_p2: asyncio.Queue,
                                        output_action_data_p1: asyncio.Queue,
                                        output_action_data_p2: asyncio.Queue,
                                        output_gun_state_p1: asyncio.Queue,
                                        output_gun_state_p2: asyncio.Queue):
    bullet_queue_p1 = asyncio.Queue()
    bullet_queue_p2 = asyncio.Queue()
    health_queue_p1 = asyncio.Queue()
    health_queue_p2 = asyncio.Queue()

    async def push_to_queue(player_id: int):
        if player_id == 1:
            input_queue = src_input_queue_p1
            output_sensor_queue = output_sensor_data_p1
            output_action_queue = output_action_data_p1
            target_gun_queue = bullet_queue_p1
            target_health_queue = health_queue_p1
        else:
            input_queue = src_input_queue_p2
            output_sensor_queue = output_sensor_data_p2
            output_action_queue = output_action_data_p2
            target_gun_queue = bullet_queue_p2
            target_health_queue = health_queue_p2

        logger.debug(f"[P{player_id}] Starting Relay Node Sorting Service")
        while True:
            try:
                msg = await input_queue.get()
                pkt = get_packet(msg)
                if pkt.packet_type == PACKET_DATA_HEALTH:
                    logger.info(f"[P{player_id}] HEALTH PACKET Received")
                    await target_health_queue.put("target_hit")
                elif pkt.packet_type == PACKET_DATA_BULLET:
                    await target_gun_queue.put("shoot_attempt")
                    await output_action_queue.put("gun")
                elif pkt.packet_type == PACKET_DATA_IMU:
                    await output_sensor_queue.put(pkt)
                elif pkt.packet_type == PACKET_DATA_KICK:
                    logger.info(f"[P{player_id}] KICK PACKET Received")
                    await output_action_queue.put("soccer")
                else:
                    logger.warning(f"[P{player_id}] Invalid packet type received: {pkt.packet_type}")
            except Exception as e:
                logger.exception(f"[P{player_id}] Error in push_to_queue: {e}")

    async def sync_gun_action(player_id: int):
        if player_id == 1:
            bullet_queue = bullet_queue_p1
            opponent_health_queue = health_queue_p2
            output_gun_state_queue = output_gun_state_p1
        else:
            bullet_queue = bullet_queue_p2
            opponent_health_queue = health_queue_p1
            output_gun_state_queue = output_gun_state_p2
        logger.debug(f"[P{player_id}] Starting sync_gun_action.")
        while True:
            try:
                # Wait for a bullet packet
                await bullet_queue.get()
                logger.info(f"[P{player_id}] Attempted to shoot")
                try:
                    # Wait for corresponding health packet from the opponent
                    await asyncio.wait_for(opponent_health_queue.get(), timeout=config.GAME_HEALTH_PKT_TIMEOUT)
                    logger.info(f"[P{player_id}] Received health packet from Opponent's IR sensor")
                    output_gun_state_queue.put_nowait("hit")
                except asyncio.TimeoutError:
                    logger.info(f"[P{player_id}] Did not receive health packet from Opponent's IR sensor")
                    output_gun_state_queue.put_nowait("miss")
            except Exception as e:
                logger.exception(f"[P{player_id}] Error in sync_gun_action: {e}")

    try:
        push_to_queue_p1 = asyncio.create_task(push_to_queue(1))
        push_to_queue_p2 = asyncio.create_task(push_to_queue(2))

        check_gun_p1 = asyncio.create_task(sync_gun_action(1))
        check_gun_p2 = asyncio.create_task(sync_gun_action(2))

        logger.info("Starting relay node data handler tasks.")
        await asyncio.gather(push_to_queue_p1, push_to_queue_p2, check_gun_p1, check_gun_p2)
    except Exception as e:
        logger.exception(f"Error in start_relay_node_data_handler: {e}")


class GameEngine:
    currGameData: GameData

    def __init__(self, eval_server_port):
        self.eval_server_port = eval_server_port

        self.prediction_input_queue_p1 = asyncio.Queue()
        self.prediction_input_queue_p2 = asyncio.Queue()

        self.prediction_output_queue_p1 = asyncio.Queue()
        self.prediction_output_queue_p2 = asyncio.Queue()

        self.engine_to_evaluation_server_queue = asyncio.Queue()
        self.evaluation_server_to_engine_queue = asyncio.Queue()

        self.relay_node_to_engine_queue_p1 = asyncio.Queue()  # Pipeline from relay node for P1
        self.relay_node_to_engine_queue_p2 = asyncio.Queue()  # Pipeline from relay node for P2

        self.engine_to_relay_node_queue = asyncio.Queue()  # Pipeline to relay node for both players

        self.engine_to_visualizer_queue = asyncio.Queue()
        self.visualizer_to_engine_queue_p1 = asyncio.Queue()
        self.visualizer_to_engine_queue_p2 = asyncio.Queue()

        self.gun_state_queue_p1 = asyncio.Queue()
        self.gun_state_queue_p2 = asyncio.Queue()

        # Shared state for tracking cooldowns
        self.cooldown_p1_event = asyncio.Event()
        self.cooldown_p2_event = asyncio.Event()
        self.cooldown_lock = asyncio.Lock()

        self.cooldown_msg_queue_p1 = asyncio.Queue()
        self.cooldown_msg_queue_p2 = asyncio.Queue()

        self.currGameData = GameData()

        self.cooldown_manager = ActionCooldownManager(cooldown_period=config.GAME_ACTION_COOLDOWN,
                                                      cooldown_notify_queue_p1=self.cooldown_msg_queue_p1,
                                                      cooldown_notify_queue_p2=self.cooldown_msg_queue_p2)
        self.game_round = 1

        self.round_timeout = 50  # Initialize the round timeout
        self.current_round_task = None  # To keep track of the supervisor task
        logger.info("Game Engine Initialized.")

    async def start_game(self):
        logger.info("Initializing game engine tasks.")

        tasks = [
            # Start TCP Server
            start_tcp_job(
                tcp_port=config.TCP_SERVER_PORT,
                receive_queue_p1=self.relay_node_to_engine_queue_p1,
                receive_queue_p2=self.relay_node_to_engine_queue_p2,
                send_queue=self.engine_to_relay_node_queue
            ),

            # Start MQTT Job
            start_mqtt_job(
                receive_topic_p1=config.MQTT_VISUALIZER_TO_ENG_P1,
                receive_topic_p2=config.MQTT_VISUALIZER_TO_ENG_P2,
                send_topic=config.MQTT_ENG_TO_VISUALIZER,
                receive_queue_p1=self.visualizer_to_engine_queue_p1,
                receive_queue_p2=self.visualizer_to_engine_queue_p2,
                send_queue=self.engine_to_visualizer_queue
            ),

            # Start Relay Node Data Handler
            start_relay_node_data_handler(
                src_input_queue_p1=self.relay_node_to_engine_queue_p1,
                src_input_queue_p2=self.relay_node_to_engine_queue_p2,
                output_sensor_data_p1=self.prediction_input_queue_p1,
                output_sensor_data_p2=self.prediction_input_queue_p2,
                output_action_data_p1=self.prediction_output_queue_p1,
                output_action_data_p2=self.prediction_output_queue_p2,
                output_gun_state_p1=self.gun_state_queue_p1,
                output_gun_state_p2=self.gun_state_queue_p2
            ),

            # Start Prediction Service Process
            PredictionServiceProcess(
                predict_input_queue_p1=self.prediction_input_queue_p1,
                predict_input_queue_p2=self.prediction_input_queue_p2,
                predict_output_queue_p1=self.prediction_output_queue_p1,
                predict_output_queue_p2=self.prediction_output_queue_p2
            ).run(),

            # Start Evaluation Server Process
            start_evaluation_process(eval_server_port=self.eval_server_port,
                                     receive_queue=self.evaluation_server_to_engine_queue,
                                     send_queue=self.engine_to_evaluation_server_queue),

            getVState(visualizer_receive_queue=self.visualizer_to_engine_queue_p1, player_id=1),
            getVState(visualizer_receive_queue=self.visualizer_to_engine_queue_p2, player_id=2),

            self.game_data_process(1),
            self.game_data_process(2),

            self.cooldown_service(self.cooldown_msg_queue_p1, player_id=1),
            self.cooldown_service(self.cooldown_msg_queue_p2, player_id=2),

            self.supervisor_task()  # Start the supervisor task
        ]

        logger.info("Starting all game engine tasks concurrently.")
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.exception(f"An error occurred while running game engine tasks: {e}")

    async def game_data_process(self, player_id):
        logger.debug(f"[P{player_id}] Starting game data process service")
        visualizer_send_queue = self.engine_to_visualizer_queue
        relay_node_input_queue = self.engine_to_relay_node_queue

        if player_id == 1:
            pred_output_queue = self.prediction_output_queue_p1
            gun_state_queue = self.gun_state_queue_p1
        else:
            pred_output_queue = self.prediction_output_queue_p2
            gun_state_queue = self.gun_state_queue_p2

        while True:
            try:
                # Verify FOV with visualizer and update game state
                predicted_action = await game_state_manager(currGameData=self.currGameData, attacker_id=player_id,
                                                            pred_output_queue=pred_output_queue,
                                                            gun_state_queue=gun_state_queue,
                                                            cooldown_manager=self.cooldown_manager,
                                                            cooldown_p1_event=self.cooldown_p1_event,
                                                            cooldown_p2_event=self.cooldown_p2_event)
                if predicted_action == "cooldown-progress":
                    logger.warning(
                        f"[P{player_id}] Action received during cooldown period. Discarding action.")

                # Only send game state to evaluation server if the action is a valid one
                if predicted_action in ['gun', 'bomb', 'shield', 'rain', 'logout', 'reload', "basket", "soccer",
                                        "volley", "bowl"]:
                    # Send updated game state to evaluation server
                    await evaluation_server_job(curr_game_data=self.currGameData,
                                                player_id=player_id,
                                                eval_input_queue=self.engine_to_evaluation_server_queue,
                                                eval_output_queue=self.evaluation_server_to_engine_queue)

                # Send updated game state to visualizer
                await visualizer_send_queue.put(
                    "gs_" + self.currGameData.to_json(player_id))  # Add gs_ prefix to indicate game

                logger.info(
                    f"[P{player_id}] Returning Game State To Relay Node: {self.currGameData.to_json(player_id)}")
                # Send validated/verified game state to relay node
                await relay_node_input_queue.put(f"{self.currGameData.to_json(player_id)}")
            except Exception as e:
                logger.exception(f"[P{player_id}] Error in game_data_process: {e}")

    async def wait_for_any_cooldown(self):
        """Wait until at least one player's cooldown event is set."""
        await asyncio.wait(
            [self.cooldown_p1_event.wait(), self.cooldown_p2_event.wait()],
            return_when=asyncio.FIRST_COMPLETED
        )

    async def supervisor_task(self):
        while True:
            # Wait until at least one cooldown event is set
            await self.wait_for_any_cooldown()

            async with self.cooldown_lock:
                # Determine which player's cooldown has been set
                if self.cooldown_p1_event.is_set() and not self.cooldown_p2_event.is_set():
                    active_player = 1
                    inactive_player = 2
                elif self.cooldown_p2_event.is_set() and not self.cooldown_p1_event.is_set():
                    active_player = 2
                    inactive_player = 1
                else:
                    # Either both are set (handled elsewhere) or both are not set
                    continue

            logger.supervisor(
                f"Supervisor detected cooldown end for P{active_player}. Starting timeout for P{inactive_player}.")

            # Start the timeout for the inactive player
            timeout_task = asyncio.create_task(self.handle_inactive_player(inactive_player))

            # Wait for both cooldown events or timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        self.cooldown_p1_event.wait(),
                        self.cooldown_p2_event.wait()
                    ),
                    timeout=config.GAME_TIMEOUT  # By right not needed because it should NEVER timeout given auto
                    # sending of action for inactive player after 50 seconds
                )
                # Both cooldowns received in time
                logger.cooldown_end(f"Both Players Cooldown period ended. READY FOR NEXT ROUND {self.game_round+1}")
            except asyncio.TimeoutError:
                # Timeout occurred; inject random action for inactive player
                logger.exception(
                    f"Round {self.game_round}: Round Cooldown timeout reached. AUTO INACTIVE PLAYER ACTION-SENDER "
                    f"MALFUNCTIONED!")
            finally:
                # Reset the cooldown events for the next round
                self.cooldown_p1_event.clear()
                self.cooldown_p2_event.clear()
                self.game_round += 1
                logger.info(f"Round {self.game_round} started.")
                # Ensure the timeout task is canceled if still running
                if not timeout_task.done():
                    timeout_task.cancel()

    async def cooldown_service(self, cooldown_notify_queue: asyncio.Queue, player_id: int):
        while True:
            msg = await cooldown_notify_queue.get()
            await self.engine_to_visualizer_queue.put(msg)  # Send cooldown ended message to visualizer

            async with self.cooldown_lock:
                if player_id == 1:
                    self.cooldown_p1_event.set()
                elif player_id == 2:
                    self.cooldown_p2_event.set()
                else:
                    logger.warning(f"Received cooldown message for unknown player_id: {player_id}")

    async def handle_inactive_player(self, player_id: int):
        """Handle the timeout for the inactive player by injecting a random action."""
        try:
            await asyncio.sleep(config.PLAYER_TIMEOUT_RANDOM_ACTION)
            # Check if the inactive player's cooldown is still not set
            random_action = random.choice(config.PLAYER_RANDOM_ACTIONS)
            logger.supervisor(f"Round {self.game_round}: Action timeout reached for P{player_id}. "
                           f"Sending random action: {random_action}.")
            if not self.cooldown_p1_event.is_set() and player_id == 1:
                await self.prediction_output_queue_p1.put(random_action)
            elif not self.cooldown_p2_event.is_set() and player_id == 2:
                await self.prediction_output_queue_p2.put(random_action)
        except asyncio.CancelledError:
            # The timeout was canceled because the inactive player completed their cooldown
            pass
