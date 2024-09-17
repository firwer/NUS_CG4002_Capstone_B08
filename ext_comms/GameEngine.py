import asyncio
import json

import config
from EvaluationProcess import start_evaluation_process
from GameLogicProcess import game_state_manager
from PredictionService import start_prediction_service_process
from comms.AsyncMQTTController import AsyncMQTTController
from comms.TCPS_Controller import TCPS_Controller


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

    def to_json(self):
        return json.dumps({
            'p1': self.p1.to_json(),
            'p2': self.p2.to_json()
        })


async def evaluation_server_job(curr_game_data: GameData, player_id: int, eval_input_queue: asyncio.Queue,
                                eval_output_queue: asyncio.Queue):
    EvalGameData = {
        "player_id": player_id,
        "action": curr_game_data.p1.action,
        "game_state": {
            "p1": curr_game_data.p1.game_state,
            "p2": curr_game_data.p2.game_state
        }
    }
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


async def start_tcp_job(tcp_port: int, receive_queue: asyncio.Queue, send_queue: asyncio.Queue):
    tcp_server = TCPS_Controller(ip=config.TCP_SERVER_HOST, port=tcp_port, secret_key=config.TCP_SECRET_KEY,
                                 receive_queue=receive_queue,
                                 send_queue=send_queue)
    await tcp_server.start_server()


async def start_relay_node_data_sorter(src_input_queue: asyncio.Queue,
                                       output_sensor_data_p1: asyncio.Queue,
                                       output_sensor_data_p2: asyncio.Queue):
    while True:
        data = await src_input_queue.get()
        print(f"Received data from RelayNode: {data}, sorting...")
        if data.startswith('p1_'):
            await output_sensor_data_p1.put(data[3:])
        elif data.startswith('p2_'):
            await output_sensor_data_p2.put(data[3:])
        else:
            print("Unknown player origin data received from Relay Node.")


class GameEngine:
    currGameData: GameData

    def __init__(self, eval_server_port):
        self.eval_server_port = eval_server_port

        self.prediction_input_queue_p1 = asyncio.Queue()
        self.prediction_input_queue_p2 = asyncio.Queue()

        self.prediction_output_queue_p1 = asyncio.Queue()
        self.prediction_output_queue_p2 = asyncio.Queue()

        self.engine_to_evaluation_server_queue_p1 = asyncio.Queue()
        self.engine_to_evaluation_server_queue_p2 = asyncio.Queue()

        self.evaluation_server_to_engine_queue_p1 = asyncio.Queue()
        self.evaluation_server_to_engine_queue_p2 = asyncio.Queue()

        self.relay_mqtt_to_engine_queue = asyncio.Queue()  # Pipeline from relay node for P1
        self.engine_to_relay_mqtt_queue = asyncio.Queue()  # Pipeline to relay node for P1

        self.engine_to_visualizer_queue = asyncio.Queue()
        self.visualizer_to_engine_queue_p1 = asyncio.Queue()
        self.visualizer_to_engine_queue_p2 = asyncio.Queue()

        self.currGameData = GameData()

    async def start_game(self):
        tasks = [

            # Start MQTT Broker Connection & TCP Server
            start_tcp_job(tcp_port=config.TCP_SERVER_PORT,
                          receive_queue=self.relay_mqtt_to_engine_queue,
                          send_queue=self.engine_to_relay_mqtt_queue),

            start_mqtt_job(receive_topic_p1=config.MQTT_VISUALIZER_TO_ENG_P1,
                           receive_topic_p2=config.MQTT_VISUALIZER_TO_ENG_P2,
                           send_topic=config.MQTT_ENG_TO_VISUALIZER,
                           receive_queue_p1=self.visualizer_to_engine_queue_p1,
                           receive_queue_p2=self.visualizer_to_engine_queue_p2,
                           send_queue=self.engine_to_visualizer_queue),

            start_relay_node_data_sorter(src_input_queue=self.relay_mqtt_to_engine_queue,
                                         output_sensor_data_p1=self.prediction_input_queue_p1,
                                         output_sensor_data_p2=self.prediction_input_queue_p2),

            start_prediction_service_process(predict_input_queue=self.prediction_input_queue_p1,
                                             predict_output_queue=self.prediction_output_queue_p1),

            start_prediction_service_process(predict_input_queue=self.prediction_input_queue_p2,
                                             predict_output_queue=self.prediction_output_queue_p2),

            # Start Evaluation Server Process
            start_evaluation_process(eval_server_port=self.eval_server_port,
                                     receive_queue=self.evaluation_server_to_engine_queue_p1,
                                     send_queue=self.engine_to_evaluation_server_queue_p1),

            start_evaluation_process(eval_server_port=self.eval_server_port,
                                     receive_queue=self.evaluation_server_to_engine_queue_p2,
                                     send_queue=self.engine_to_evaluation_server_queue_p2),

            self.game_data_process(1),
            self.game_data_process(2)
        ]

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    async def game_data_process(self, player_id):
        # Select appropriate queues based on player_id
        visualizer_send_queue = self.engine_to_visualizer_queue
        # Currently all data for relay node sent back to this queue regardless of player
        relay_node_input_queue = self.engine_to_relay_mqtt_queue

        if player_id == 1:
            pred_output_queue = self.prediction_output_queue_p1
            visualizer_receive_queue = self.visualizer_to_engine_queue_p1
        else:
            pred_output_queue = self.prediction_output_queue_p2
            visualizer_receive_queue = self.visualizer_to_engine_queue_p2

        while True:
            # Check for predicted action

            await game_state_manager(currGameData=self.currGameData, attacker_id=player_id,
                                     pred_output_queue=pred_output_queue,
                                     visualizer_receive_queue=visualizer_receive_queue,
                                     visualizer_send_queue=visualizer_send_queue)
            print("EVALUATING...")
            # Send updated game state to evaluation server
            await evaluation_server_job(curr_game_data=self.currGameData,
                                        player_id=1,
                                        eval_input_queue=self.engine_to_evaluation_server_queue_p1,
                                        eval_output_queue=self.evaluation_server_to_engine_queue_p1)
            # if config.PLAYER_MODE == 2:
            #     await evaluation_server_job(curr_game_data=self.currGameData,
            #                                 player_id=2,
            #                                 eval_input_queue=self.engine_to_evaluation_server_queue_p2,
            #                                 eval_output_queue=self.evaluation_server_to_engine_queue_p2)

            print(f"SENDING TO RELAY: {self.currGameData.to_json()}")
            # Send validated/verified game state to relay node
            await relay_node_input_queue.put(f"{self.currGameData.to_json()}")
