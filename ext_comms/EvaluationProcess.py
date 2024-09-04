import config
from comms.WebSocketController import WebSockController


async def start_evaluation_process(eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue):
    ec = EvaluationProcess(eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue)
    await ec.wsController.connect()
    await ec.wsController.init_handshake()
    while True:
        await ec.msg_sender()
        await ec.msg_receiver()


# Evaluation Process is responsible for the communication between the Evaluation Server and the Game Engine
class EvaluationProcess:
    def __init__(self, eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue):
        self.evaluation_server_to_engine_queue = evaluation_server_to_engine_queue
        self.engine_to_evaluation_server_queue = engine_to_evaluation_server_queue
        self.wsController = WebSockController(config.serverName, eval_server_port,
                                              config.secret_key)  # Used for communication with the evaluation server
        self.response_pending = False  # Flag to track if a response is pending

    async def msg_receiver(self):
        msg = await self.wsController.receive()
        print(f"Received message from Evaluation Server: {msg}")
        await self.evaluation_server_to_engine_queue.put(msg)
        self.response_pending = False

    async def msg_sender(self):
        message = await self.engine_to_evaluation_server_queue.get()
        print("SENDING MESSAGE TO EVAL")
        if self.response_pending:
            print("Response already pending, skipping send")
            return
        print(f"Sending message to Evaluation Server: {message}")
        await self.wsController.send(message)
        self.response_pending = True
