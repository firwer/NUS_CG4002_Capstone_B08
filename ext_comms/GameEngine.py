import asyncio
import json

import config
from EvaluationProcess import start_evaluation_process
from GameLogicProcess import game_state_manager
from PredictionService import PredictionServiceProcess
from comms.AsyncMQTTController import AsyncMQTTController
from comms.TCPS_Controller import TCPS_Controller
from int_comms.relay.packet import get_packet, PACKET_DATA_HEALTH, PACKET_DATA_BULLET, PACKET_DATA_IMU, PACKET_DATA_KICK


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
            'player_id': player_id,  # This is to identify which player the data came from so that the FOV can be sent
            # to the correct player
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
    print("SENDING TO EVAL SERVER ", EvalGameData)
    # Send updated game state to evaluation server
    await eval_input_queue.put(json.dumps(EvalGameData))
    # Wait for evaluation response
    eval_resp = await eval_output_queue.get()
    eval_gs = json.loads(eval_resp)

    # Update game state based on evaluation response
    curr_game_data.p1.game_state = eval_gs['p1']
    curr_game_data.p2.game_state = eval_gs['p2']


# Need this function for visualizer to provide feedback on whether player is in sight. If game state did not change (
# i.e. health is unchanged, it means player is not in sight)

async def start_mqtt_job(receive_topic_p1: str,
                         receive_topic_p2: str,
                         send_topic: str,
                         receive_queue_p1: asyncio.Queue,
                         receive_queue_p2: asyncio.Queue,
                         send_queue: asyncio.Queue):
    mqtt_client = AsyncMQTTController(config.MQTT_BROKER_PORT, receive_queue_p1=receive_queue_p1,
                                      receive_queue_p2=receive_queue_p2,
                                      send_queue=send_queue)
    await mqtt_client.start(receive_topic_p1, receive_topic_p2, send_topic)


async def start_tcp_job(tcp_port: int, receive_queue_p1: asyncio.Queue, receive_queue_p2: asyncio.Queue,
                        send_queue: asyncio.Queue):
    tcp_server = TCPS_Controller(ip=config.TCP_SERVER_HOST, port=tcp_port, secret_key=config.TCP_SECRET_KEY,
                                 receive_queue_p1=receive_queue_p1,
                                 receive_queue_p2=receive_queue_p2,
                                 send_queue=send_queue)
    await tcp_server.start_server()


async def start_prediction_service_process(predict_input_queue: asyncio.Queue, predict_output_queue: asyncio.Queue):
    PredictionService = PredictionServiceProcess(predict_input_queue=predict_input_queue,
                                                 predict_output_queue=predict_output_queue)
    print("Prediction Service Started")
    await PredictionService.run()


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

        while True:
            msg = await input_queue.get()
            pkt = get_packet(msg)
            if pkt.packet_type == PACKET_DATA_HEALTH:
                print("HEALTH PACKET Received")
                await target_health_queue.put("target_hit")
            elif pkt.packet_type == PACKET_DATA_BULLET:
                print("BULLET PACKET Received")
                await target_gun_queue.put("shoot_attempt")
                await output_action_queue.put("gun")
            elif pkt.packet_type == PACKET_DATA_IMU:
                print("IMU PACKET Received")
                # Send to prediction service
                await output_sensor_queue.put(pkt)
            elif pkt.packet_type == PACKET_DATA_KICK:
                print("A KICK PACKET Received")
                await output_action_queue.put("soccer")
            else:
                print("Invalid packet type received")

    async def sync_gun_action(player_id: int):
        if player_id == 1:
            bullet_queue = bullet_queue_p1
            opponent_health_queue = health_queue_p2
            output_gun_state_queue = output_gun_state_p1
        else:
            bullet_queue = bullet_queue_p2
            opponent_health_queue = health_queue_p1
            output_gun_state_queue = output_gun_state_p2
        while True:
            # Wait for a bullet packet
            await bullet_queue.get()
            print(f"Player {player_id} attempted to shoot")
            try:
                # Wait for corresponding health packet from the opponent
                # fixme: what if there is accumulated health packet from previous round? We need to the health packet round by round
                await asyncio.wait_for(opponent_health_queue.get(), timeout=1)
                print(f"Shot from Player {player_id} hit the opponent")
                output_gun_state_queue.put_nowait("hit")
            except asyncio.TimeoutError:
                print(f"Shot from Player {player_id} missed")
                output_gun_state_queue.put_nowait("miss")

    push_to_queue_p1 = asyncio.create_task(
        push_to_queue(1))
    push_to_queue_p2 = asyncio.create_task(
        push_to_queue(2))

    check_gun_p1 = asyncio.create_task(sync_gun_action(1))
    check_gun_p2 = asyncio.create_task(sync_gun_action(2))

    await asyncio.gather(push_to_queue_p1, push_to_queue_p2, check_gun_p1, check_gun_p2)

    # Packet IMU - Standard AI Dmg except soccer
    # Packet Bullet - Send straight for game state update (deduct attacker bullet)
    # Packet Health - Send straight for game state update (deduct opponent health)
    # Packet Kick - Send straight for game state update (deduct opponent health)


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

        self.currGameData = GameData()

    async def start_game(self):
        tasks = [

            # Start MQTT Broker Connection & TCP Server
            start_tcp_job(tcp_port=config.TCP_SERVER_PORT,
                          receive_queue_p1=self.relay_node_to_engine_queue_p1,
                          receive_queue_p2=self.relay_node_to_engine_queue_p2,
                          send_queue=self.engine_to_relay_node_queue),

            start_mqtt_job(receive_topic_p1=config.MQTT_VISUALIZER_TO_ENG_P1,
                           receive_topic_p2=config.MQTT_VISUALIZER_TO_ENG_P2,
                           send_topic=config.MQTT_ENG_TO_VISUALIZER,
                           receive_queue_p1=self.visualizer_to_engine_queue_p1,
                           receive_queue_p2=self.visualizer_to_engine_queue_p2,
                           send_queue=self.engine_to_visualizer_queue),

            start_relay_node_data_handler(src_input_queue_p1=self.relay_node_to_engine_queue_p1,
                                          src_input_queue_p2=self.relay_node_to_engine_queue_p2,
                                          output_sensor_data_p1=self.prediction_input_queue_p1,
                                          output_sensor_data_p2=self.prediction_input_queue_p2,
                                          output_action_data_p1=self.prediction_output_queue_p1,
                                          output_action_data_p2=self.prediction_output_queue_p2,
                                          output_gun_state_p1=self.gun_state_queue_p1,
                                          output_gun_state_p2=self.gun_state_queue_p2),

            start_prediction_service_process(predict_input_queue=self.prediction_input_queue_p1,
                                             predict_output_queue=self.prediction_output_queue_p1),

            # start_prediction_service_process(predict_input_queue=self.prediction_input_queue_p2,
            #                                  predict_output_queue=self.prediction_output_queue_p2),

            # Start Evaluation Server Process
            start_evaluation_process(eval_server_port=self.eval_server_port,
                                     receive_queue=self.evaluation_server_to_engine_queue,
                                     send_queue=self.engine_to_evaluation_server_queue),

            self.game_data_process(1),
            self.game_data_process(2)
        ]

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    async def game_data_process(self, player_id):
        # Select appropriate queues based on player_id
        visualizer_send_queue = self.engine_to_visualizer_queue
        # Currently all data for relay node sent back to this queue regardless of player
        relay_node_input_queue = self.engine_to_relay_node_queue

        if player_id == 1:
            pred_output_queue = self.prediction_output_queue_p1
            visualizer_receive_queue = self.visualizer_to_engine_queue_p1
            gun_state_queue = self.gun_state_queue_p1
        else:
            pred_output_queue = self.prediction_output_queue_p2
            visualizer_receive_queue = self.visualizer_to_engine_queue_p2
            gun_state_queue = self.gun_state_queue_p2

        while True:
            # Verify FOV with visualizer and update game state
            await game_state_manager(currGameData=self.currGameData, attacker_id=player_id,
                                     pred_output_queue=pred_output_queue,
                                     visualizer_receive_queue=visualizer_receive_queue,
                                     visualizer_send_queue=visualizer_send_queue,
                                     gun_state_queue=gun_state_queue)
            print("EVALUATING...")
            # Send updated game state to evaluation server
            await evaluation_server_job(curr_game_data=self.currGameData,
                                        player_id=player_id,
                                        eval_input_queue=self.engine_to_evaluation_server_queue,
                                        eval_output_queue=self.evaluation_server_to_engine_queue)

            print(f"SENDING TO RELAY: {self.currGameData.to_json(player_id)}")
            # Send validated/verified game state to relay node
            await relay_node_input_queue.put(f"{self.currGameData.to_json(player_id)}")
