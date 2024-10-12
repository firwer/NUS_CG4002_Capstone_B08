import asyncio

import config
from comms.TCPC_Controller import TCPC_Controller


async def start_evaluation_process(eval_server_port: int, receive_queue: asyncio.Queue,
                                   send_queue: asyncio.Queue):
    ec = EvaluationProcess(eval_server_port, receive_queue, send_queue)
    await ec.tcpClient.connect()
    await ec.tcpClient.init_handshake()
    while True:
        await ec.msg_sender()
        await ec.msg_receiver()


# Evaluation Process is responsible for the communication between the Evaluation Server and the Game Engine
class EvaluationProcess:
    """
        This class is responsible for the communication between the Evaluation Server and the Game Engine
        It will handle the messages from the Evaluation Server and send messages to the Evaluation Server

        receive_queue: Queue to receive messages from the Evaluation Server
        send_queue: Queue to send messages to the Evaluation Server
    """
    def __init__(self, eval_server_port, evaluation_server_to_engine_queue, engine_to_evaluation_server_queue):
        self.evaluation_server_to_engine_queue = evaluation_server_to_engine_queue
        self.engine_to_evaluation_server_queue = engine_to_evaluation_server_queue
        self.tcpClient = TCPC_Controller(ip=config.EVAL_SERVER_HOST,port=eval_server_port,
                                         secret_key=config.EVAL_SECRET_KEY)  # Used for communication with the
        # evaluation server
        self.response_pending = False  # Flag to track if a response is pending

    async def msg_receiver(self):
        msg = await self.tcpClient.recv()
        print(f"Received message from Evaluation Server: {msg}")
        await self.evaluation_server_to_engine_queue.put(msg)
        self.response_pending = False

    async def msg_sender(self):
        message = await self.engine_to_evaluation_server_queue.get()
        if self.response_pending:
            print("Response already pending, skipping send")
            return
        print(f"Sending message to Evaluation Server: {message}")
        await self.tcpClient.send(message)
        self.response_pending = True
