import asyncio
import json

import aiomqtt

import config
from EvaluationProcess import start_evaluation_process
from PredictionService import start_prediction_service_process
from comms.AsyncMQTTController import AsyncMQTTController


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

    def update_state(self, action, game_state):
        self.action = action
        self.game_state = game_state


class GameData:
    p1: GamePlayerData
    p2: GamePlayerData

    def __init__(self):
        self.p1 = GamePlayerData(1, 'none', {
            'hp': 90,
            'bullets': 6,
            'bombs': 2,
            'shield_hp': 30,
            'deaths': 0,
            'shields': 3
        })
        self.p2 = GamePlayerData(2, 'none', {
            'hp': 90,
            'bullets': 6,
            'bombs': 2,
            'shield_hp': 30,
            'deaths': 0,
            'shields': 3
        })

    def to_json(self):
        return json.dumps({
            'p1': self.p1.to_json(),
            'p2': self.p2.to_json()
        })


def update_game_state(curr_player_data: GamePlayerData, action: str):
    # Update the game state object based on the action
    if action == 'bomb':
        curr_player_data.game_state['bombs'] -= 1
    elif action == 'shoot':
        curr_player_data.game_state['bullets'] -= 1
    elif action == 'shield':
        curr_player_data.game_state['shields'] -= 1
    elif action == 'reload':
        curr_player_data.game_state['bullets'] += 1
    return curr_player_data.game_state


async def evaluation_server_job(curr_game_data: GameData, player_id: int, eval_input_queue: asyncio.Queue,
                                eval_output_queue: asyncio.Queue):
    # Send updated game state to evaluation server
    if player_id == 1:
        await eval_input_queue.put(curr_game_data.p1.to_json())
    else:
        await eval_input_queue.put(curr_game_data.p2.to_json())
    # Wait for evaluation response
    eval_resp = await eval_output_queue.get()

    # Parse & update evaluation response
    _, json_str = eval_resp.split('_', 1)
    eval_gs = json.loads(json_str)

    # Update game state based on evaluation response
    curr_game_data.p1.game_state = eval_gs['p1']
    curr_game_data.p2.game_state = eval_gs['p2']


# Need this function for visualizer to provide feedback on whether player is in sight. If game state did not change (
# i.e. health is unchanged, it means player is not in sight)
async def start_visualizer_mqtt_job(receive_topic: str, send_topic: str, input_queue: asyncio.Queue,
                                    output_queue: asyncio.Queue):
    # Send updated game state to visualizer
    # await visualizer_input_queue.put(curr_game_data.to_json())
    mqttc_visualizer = AsyncMQTTController(config.MQTT_BROKER_PORT, output_queue, input_queue)

    while True:  # Is there a need for this loop????
        await mqttc_visualizer.start(receive_topic, send_topic)
    # TODO IMPLEMENT VISUALIZER SIDE RESPONSE
    # Wait for visualizer response
    #visualizer_resp = visualizer_output_queue.get()
    #curr_game_state.game_state = visualizer_resp


async def start_relay_node_mqtt_job(receive_topic: str, send_topic: str, receive_queue: asyncio.Queue,
                                    send_queue: asyncio.Queue):
    mqttc_relay = AsyncMQTTController(config.MQTT_BROKER_PORT, receive_queue=receive_queue, send_queue=send_queue)
    while True:
        await mqttc_relay.start(receive_topic, send_topic)


class GameEngine:
    currGameData: GameData

    def __init__(self, eval_server_port):
        self.eval_server_port = eval_server_port
        self.mqttClient = aiomqtt.Client(hostname=config.MQTT_BROKER_HOST, port=config.MQTT_BROKER_PORT)

        self.prediction_service_to_engine_queue_p1 = asyncio.Queue()
        self.prediction_service_to_engine_queue_p2 = asyncio.Queue()

        self.engine_to_evaluation_server_queue_p1 = asyncio.Queue()
        self.engine_to_evaluation_server_queue_p2 = asyncio.Queue()

        self.evaluation_server_to_engine_queue_p1 = asyncio.Queue()
        self.evaluation_server_to_engine_queue_p2 = asyncio.Queue()

        self.relay_mqtt_to_engine_queue_p1 = asyncio.Queue()  # Pipeline from relay node for P1
        self.engine_to_relay_mqtt_queue_p1 = asyncio.Queue()  # Pipeline to relay node for P1

        self.relay_mqtt_to_engine_queue_p2 = asyncio.Queue()  # Pipeline from relay node for P2
        self.engine_to_relay_mqtt_queue_p2 = asyncio.Queue()  # Pipeline to relay node for P2

        self.engine_to_visualizer_queue = asyncio.Queue()  # Pipeline from engine to visualizer for p1
        self.visualizer_to_engine_queue = asyncio.Queue()  # Pipeline from visualizer to engine for p2

        self.currGameData = GameData()

    async def start_game(self):
        tasks = [

            start_relay_node_mqtt_job(config.MQTT_SENSOR_DATA_RELAY_TO_ENG_P1, config.MQTT_SENSOR_DATA_ENG_TO_RELAY_P1,
                                      self.relay_mqtt_to_engine_queue_p1, self.engine_to_relay_mqtt_queue_p1),
            start_relay_node_mqtt_job(config.MQTT_SENSOR_DATA_RELAY_TO_ENG_P2, config.MQTT_SENSOR_DATA_ENG_TO_RELAY_P2,
                                      self.relay_mqtt_to_engine_queue_p2, self.engine_to_relay_mqtt_queue_p2),
            start_evaluation_process(self.eval_server_port, self.evaluation_server_to_engine_queue_p1,
                                     self.engine_to_evaluation_server_queue_p1),
            start_evaluation_process(self.eval_server_port, self.evaluation_server_to_engine_queue_p2,
                                     self.engine_to_evaluation_server_queue_p2),
            start_prediction_service_process(self.relay_mqtt_to_engine_queue_p1,
                                             self.prediction_service_to_engine_queue_p1),
            start_prediction_service_process(self.relay_mqtt_to_engine_queue_p2,
                                             self.prediction_service_to_engine_queue_p2),

            start_visualizer_mqtt_job(config.MQTT_VISUALIZER_TO_ENG, config.MQTT_ENG_TO_VISUALIZER,
                                      input_queue=self.engine_to_visualizer_queue,
                                      output_queue=self.visualizer_to_engine_queue),
            self.manage_game_state(1),
            self.manage_game_state(2)
        ]

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    async def manage_game_state(self, player_id):
        # Select appropriate queues based on player_id
        visualizer_input_queue = self.engine_to_visualizer_queue
        visualizer_output_queue = self.visualizer_to_engine_queue

        if player_id == 1:
            pred_output_queue = self.prediction_service_to_engine_queue_p1
            eval_input_queue = self.engine_to_evaluation_server_queue_p1
            eval_output_queue = self.evaluation_server_to_engine_queue_p1
            relay_node_input_queue = self.engine_to_relay_mqtt_queue_p1
        else:
            pred_output_queue = self.prediction_service_to_engine_queue_p2
            eval_input_queue = self.engine_to_evaluation_server_queue_p2
            eval_output_queue = self.evaluation_server_to_engine_queue_p2
            relay_node_input_queue = self.engine_to_relay_mqtt_queue_p2

        while True:
            # Check for predicted action
            prediction_action = await pred_output_queue.get()
            prediction_action = prediction_action.decode('utf-8')
            if player_id == 1:
                self.currGameData.p1.update_state(prediction_action,
                                                  update_game_state(self.currGameData.p1, prediction_action))
            elif player_id == 2:
                self.currGameData.p2.update_state(prediction_action,
                                                  update_game_state(self.currGameData.p2, prediction_action))
            print("EVALUATING...")
            # Send updated game state to evaluation server
            await evaluation_server_job(self.currGameData, player_id, eval_input_queue, eval_output_queue)

            print("Updating VISUALIZER...")
            # Send updated game state to visualizer
            await visualizer_output_queue.put(self.currGameData.to_json())

            #await visualizer_input_queue.get()  # Wait for visualizer response
            print(f"SENDING TO RELAY: {self.currGameData.to_json()}")
            # Send validated/verified game state to relay node
            await relay_node_input_queue.put(f"{self.currGameData.to_json()}")

            await asyncio.sleep(0.1)  # Non-blocking delay to prevent busy-waiting
