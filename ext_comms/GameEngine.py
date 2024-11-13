# gameengine.py
import asyncio
import json

import config
from ActionCooldownManager import ActionCooldownManager
from logger_config import setup_logger
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


async def start_relay_node_data_handler(curr_round: int,
                                        src_input_queue_p1: asyncio.Queue,
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
                    logger.info(f"[Round {curr_round}][P{player_id}] HEALTH PACKET Received")
                    await target_health_queue.put("target_hit")
                elif pkt.packet_type == PACKET_DATA_BULLET:
                    await target_gun_queue.put("shoot_attempt")
                    await output_action_queue.put("gun")
                elif pkt.packet_type == PACKET_DATA_IMU:
                    await output_sensor_queue.put(pkt)
                elif pkt.packet_type == PACKET_DATA_KICK:
                    logger.info(f"[Round {curr_round}][P{player_id}] KICK PACKET Received")
                    await output_action_queue.put("soccer")
                else:
                    logger.warning(f"[Round {curr_round}][P{player_id}] Invalid packet type received: {pkt.packet_type}")
            except Exception as e:
                logger.exception(f"[Round {curr_round}][P{player_id}] Error in push_to_queue: {e}")

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
        self.cooldown_lock = asyncio.Lock()

        self.action_p1_event = asyncio.Event()
        self.action_p2_event = asyncio.Event()

        self.cooldown_msg_queue_p1 = asyncio.Queue()
        self.cooldown_msg_queue_p2 = asyncio.Queue()

        self.currGameData = GameData()
        self.gs_lock = asyncio.Lock()

        self.cooldown_manager = ActionCooldownManager(cooldown_period=config.GAME_ACTION_COOLDOWN,
                                                      cooldown_notify_queue_p1=self.cooldown_msg_queue_p1,
                                                      cooldown_notify_queue_p2=self.cooldown_msg_queue_p2)
        self.game_round_p1 = 1
        self.game_round_p2 = 1

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
                curr_round=self.game_round_p1,
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
            # start_evaluation_process(eval_server_port=self.eval_server_port,
            #                          receive_queue=self.evaluation_server_to_engine_queue,
            #                          send_queue=self.engine_to_evaluation_server_queue),

            getVState(visualizer_receive_queue=self.visualizer_to_engine_queue_p1, player_id=1),
            getVState(visualizer_receive_queue=self.visualizer_to_engine_queue_p2, player_id=2),

            self.game_data_process(1),
            self.game_data_process(2),

            # self.cooldown_service(self.cooldown_msg_queue_p1, player_id=1),
            # self.cooldown_service(self.cooldown_msg_queue_p2, player_id=2),
            #
            # self.supervisor_task()  # Start the supervisor task
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
            if player_id == 1:
                curr_round = self.game_round_p1
            else:
                curr_round = self.game_round_p2
            try:
                prediction_action = await pred_output_queue.get()
                async with self.gs_lock:
                    async with self.cooldown_lock:
                        # Verify FOV with visualizer and update game state
                        await game_state_manager(currGameData=self.currGameData, attacker_id=player_id,
                                                                    prediction_action=prediction_action,
                                                                    gun_state_queue=gun_state_queue,
                                                                    cooldown_manager=self.cooldown_manager,
                                                                    curr_round=curr_round)

                # Send updated game state to visualizer
                await visualizer_send_queue.put(
                    "gs_" + self.currGameData.to_json(player_id))  # Add gs_ prefix to indicate game

                logger.info(
                    f"[Round {curr_round}][P{player_id}] Returning Game State To Relay Node: {self.currGameData.to_json(player_id)}")
                # Send validated/verified game state to relay node
                await relay_node_input_queue.put(f"{self.currGameData.to_json(player_id)}")
            except Exception as e:
                logger.exception(f"[Round {curr_round}][P{player_id}] Error in game_data_process: {e}")

    # async def cooldown_service(self, cooldown_notify_queue: asyncio.Queue, player_id: int):
    #     while True:
    #         msg = await cooldown_notify_queue.get()
    #         await self.engine_to_visualizer_queue.put(msg)  # Send cooldown ended message to visualizer
    #
    #         async with self.cooldown_lock:
    #             if player_id == 1:
    #                 self.cooldown_p1_event.set()
    #             elif player_id == 2:
    #                 self.cooldown_p2_event.set()
    #             else:
    #                 logger.warning(f"Received cooldown message for unknown player_id: {player_id}")