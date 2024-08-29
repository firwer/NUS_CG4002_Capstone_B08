import json

import config
from comms.WebSocketController import WebSockController


def start_evaluation_process(eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue):
    ec = EvaluationProcess(eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue)
    while True:
        ec.msg_sender()
        ec.msg_receiver()


class EvaluationProcess:
    def __init__(self, eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue):
        self.evaluation_server_to_engine_queue = evaluation_server_to_engine_queue
        self.engine_to_evaluation_server_queue = engine_to_evaluation_server_queue
        self.wsController = WebSockController(config.serverName, eval_server_port,
                                              config.secret_key)  # Used for communication with the evaluation server
        self.wsController.init_handshake()

    def msg_receiver(self):
        msg = self.wsController.receive()
        print(f"Received message from Evaluation Server: {msg}")
        self.evaluation_server_to_engine_queue.put(msg)

    def msg_sender(self):
        message = self.engine_to_evaluation_server_queue.get()
        print(f"Sending message to Evaluation Server: {message}")
        self.wsController.send(message)
