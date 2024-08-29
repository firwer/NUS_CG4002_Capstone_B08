import datetime
import json
import time
from multiprocessing import Process, Queue
from threading import Thread

from EvaluationProcess import start_evaluation_process
from PredictionService import start_prediction_service_process
from RelayNodeProcess import start_relay_mqtt_client_process

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


def update_game_state(curr_game_state, action):
    # Update the game state object based on the action
    if action == 'bomb':
        curr_game_state.game_state['bombs'] -= 1
    elif action == 'shoot':
        curr_game_state.game_state['bullets'] -= 1
    elif action == 'shield':
        curr_game_state.game_state['shields'] -= 1
    elif action == 'reload':
        curr_game_state.game_state['bullets'] += 1
    return curr_game_state.game_state


def evaluation_server_job(curr_game_state, eval_input_queue, eval_output_queue):
    # Send updated game state to evaluation server
    eval_input_queue.put(curr_game_state.to_json())
    # Wait for evaluation response
    eval_resp = eval_output_queue.get()

    # Parse & update evaluation response
    _, json_str = eval_resp.split('_', 1)
    eval_gs = json.loads(json_str)
    curr_game_state.game_state = eval_gs['p1']


# Need this function for visualizer to provide feedback on whether player is in sight. If game state did not change (
# i.e. health is unchanged, it means player is not in sight)
def visualizer_job(curr_game_state, visualizer_input_queue, visualizer_output_queue):
    # Send updated game state to visualizer
    visualizer_input_queue.put(curr_game_state.to_json())

    # TODO IMPLEMENT VISUALIZER SIDE RESPONSE
    # Wait for visualizer response
    #visualizer_resp = visualizer_output_queue.get()
    #curr_game_state.game_state = visualizer_resp


class GameEngine:
    currP1GameState: GamePlayerData
    currP2GameState: GamePlayerData

    def __init__(self, eval_server_port):
        self.eval_server_port = eval_server_port

        self.prediction_service_to_engine_queue_p1 = Queue()
        self.prediction_service_to_engine_queue_p2 = Queue()

        self.engine_to_evaluation_server_queue_p1 = Queue()
        self.engine_to_evaluation_server_queue_p2 = Queue()

        self.evaluation_server_to_engine_queue_p1 = Queue()
        self.evaluation_server_to_engine_queue_p2 = Queue()

        # TODO: Check if each player has their own queue for the following
        self.relay_mqtt_to_engine_queue_p1 = Queue()  # Pipeline from relay node for P1
        self.engine_to_relay_mqtt_queue_p1 = Queue()  # Pipeline to relay node for P1

        self.relay_mqtt_to_engine_queue_p2 = Queue()  # Pipeline from relay node for P2
        self.engine_to_relay_mqtt_queue_p2 = Queue()  # Pipeline to relay node for P2

        self.engine_to_visualizer_queue_p1 = Queue()  # Pipeline from engine to visualizer for p1
        self.visualizer_to_engine_queue_p1 = Queue()  # Pipeline from visualizer to engine for p2

        self.engine_to_visualizer_queue_p2 = Queue()  # Pipeline from engine to visualizer for p1
        self.visualizer_to_engine_queue_p2 = Queue()  # Pipeline from visualizer to engine for p2

        default_game_state = {
            'hp': 90,
            'bullets': 6,
            'bombs': 2,
            'shield_hp': 30,
            'deaths': 0,
            'shields': 3
        }

        self.currP1GameState = GamePlayerData(1, 'none', default_game_state)
        self.currP2GameState = GamePlayerData(2, 'none', default_game_state)

    def start_game(self):

        relay_p1 = Process(target=start_relay_mqtt_client_process,
                           args=(self.relay_mqtt_to_engine_queue_p1, self.engine_to_relay_mqtt_queue_p1))

        eval_p1 = Process(target=start_evaluation_process,
                          args=(self.eval_server_port, self.evaluation_server_to_engine_queue_p1,
                                self.engine_to_evaluation_server_queue_p1))
        eval_p2 = Process(target=start_evaluation_process,
                          args=(self.eval_server_port, self.evaluation_server_to_engine_queue_p2,
                                self.engine_to_evaluation_server_queue_p2))

        # Start prediction processes
        pred_p1 = Process(target=start_prediction_service_process,
                          args=(self.relay_mqtt_to_engine_queue_p1, self.prediction_service_to_engine_queue_p1))
        pred_p2 = Process(target=start_prediction_service_process,
                          args=(self.relay_mqtt_to_engine_queue_p2, self.prediction_service_to_engine_queue_p2))
        jobs = [relay_p1, eval_p1, pred_p1]
        for process in jobs: process.start()
        print("Game engine started successfully!")

        Thread(target=self.manage_game_state, args=(1,), daemon=True).start()
        #Thread(target=self.manage_game_state, args=(2,), daemon=True).start()

    # def validate_and_update(self, player_id):
    #     eval_queue = self.evaluation_server_to_engine_queue_p1 if player_id == 1 else self.evaluation_server_to_engine_queue_p2
    #     current_game_state = self.currP1GameState if player_id == 1 else self.currP2GameState
    #
    #     evaluation_response = eval_queue.get()  # Wait for evaluation response
    #     expected_game_state = GameStateData(0, '', {}).from_json(evaluation_response)
    #
    #     # Validate and update
    #     if current_game_state.game_state != expected_game_state.game_state:
    #         print(f"Discrepancy found for player {player_id}, updating game state.")
    #         if player_id == 1:
    #             self.currP1GameState = expected_game_state
    #         else:
    #             self.currP2GameState = expected_game_state
    #     #now = datetime.datetime.now()
    #     #self.engine_to_relay_mqtt_queue_p1.put(f"{now}-{self.currP1GameState.to_json()}")
    #     #print(f"Player {player_id} game state validated successfully. f{self.currP1GameState.to_json()}")

    def manage_game_state(self, player_id):
        # Select appropriate queues based on player_id
        if player_id == 1:
            pred_output_queue = self.prediction_service_to_engine_queue_p1
            eval_input_queue = self.engine_to_evaluation_server_queue_p1
            eval_output_queue = self.evaluation_server_to_engine_queue_p1

            visualizer_input_queue = self.engine_to_visualizer_queue_p1
            visualizer_output_queue = self.visualizer_to_engine_queue_p1

            relay_node_input_queue = self.engine_to_relay_mqtt_queue_p1
            curr_game_state = self.currP1GameState
        else:
            pred_output_queue = self.prediction_service_to_engine_queue_p2
            eval_input_queue = self.engine_to_evaluation_server_queue_p2
            eval_output_queue = self.evaluation_server_to_engine_queue_p2

            visualizer_input_queue = self.engine_to_visualizer_queue_p2
            visualizer_output_queue = self.visualizer_to_engine_queue_p2

            relay_node_input_queue = self.engine_to_relay_mqtt_queue_p2
            curr_game_state = self.currP2GameState

        while True:
            # Check for predicted action
            prediction_action = pred_output_queue.get()
            prediction_action = prediction_action.decode('utf-8')
            curr_game_state.update_state(prediction_action, update_game_state(curr_game_state, prediction_action))

            # TODO: Should we make it multi-threaded? If so, curr_game_state would require a lock

            # Send updated game state to evaluation server
            evaluation_server_job(curr_game_state, eval_input_queue, eval_output_queue)

            # Send updated game state to visualizer
            visualizer_job(curr_game_state, visualizer_input_queue, visualizer_output_queue)

            now = datetime.datetime.now()
            # Send validated/verified game state to relay node
            relay_node_input_queue.put(f"{now} - {curr_game_state.to_json()}")

            time.sleep(0.1)  # Small delay to prevent busy-waiting
