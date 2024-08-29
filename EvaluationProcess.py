import json

import config
from comms.WebSocketController import WebSockController


def start_evaluation_process(eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue):
    ec = EvaluationProcess(eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue)
    while True:
        ec.msg_sender()
        ec.msg_receiver()


# Evaluation Process is responsible for the communication between the Evaluation Server and the Game Engine
class EvaluationProcess:
    def __init__(self, eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue):
        self.evaluation_server_to_engine_queue = evaluation_server_to_engine_queue
        self.engine_to_evaluation_server_queue = engine_to_evaluation_server_queue
        self.wsController = WebSockController(config.serverName, eval_server_port,
                                              config.secret_key)  # Used for communication with the evaluation server
        self.wsController.init_handshake()

        self.response_pending = False  # Flag to track if a response is pending

    def msg_receiver(self):
        msg = self.wsController.receive()
        print(f"Received message from Evaluation Server: {msg}")
        self.evaluation_server_to_engine_queue.put(msg)
        self.response_pending = False

    def msg_sender(self):
        message = self.engine_to_evaluation_server_queue.get()
        print("SENDING MESSAGE TO EVAL")
        if self.response_pending:
            print("Response already pending, skipping send")
            return
        print(f"Sending message to Evaluation Server: {message}")
        self.wsController.send(message)
        self.response_pending = True
