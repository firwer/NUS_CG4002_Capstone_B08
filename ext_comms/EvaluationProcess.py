import asyncio

import config
from comms.TCPC_Controller import TCPC_Controller
from logger_config import setup_logger

logger = setup_logger(__name__)


async def start_evaluation_process(eval_server_port: int, receive_queue: asyncio.Queue,
                                   send_queue: asyncio.Queue):
    ec = EvaluationProcess(eval_server_port, receive_queue, send_queue)
    await ec.tcpClient.connect()
    await ec.tcpClient.init_handshake()
    # Create concurrent tasks for sending and receiving messages
    sender_task = asyncio.create_task(ec.msg_sender())
    receiver_task = asyncio.create_task(ec.msg_receiver())

    # Await both tasks to run indefinitely
    await asyncio.gather(sender_task, receiver_task)


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
        self.tcpClient = TCPC_Controller(ip=config.EVAL_SERVER_HOST, port=eval_server_port,
                                         secret_key=config.EVAL_SECRET_KEY)  # Used for communication with the
        # evaluation server

    async def msg_receiver(self):
        """
        Coroutine to continuously receive messages from the Evaluation Server
        and place them into the evaluation_server_to_engine_queue.
        """
        try:
            while True:
                msg = await self.tcpClient.recv()
                await self.evaluation_server_to_engine_queue.put(msg)
        except asyncio.CancelledError:
            logger.info("Message Receiver task has been cancelled.")
        except Exception as e:
            logger.exception(f"Exception in msg_receiver: {e}")

    async def msg_sender(self):
        """
        Coroutine to continuously send messages from the engine_to_evaluation_server_queue
        to the Evaluation Server.
        """
        try:
            while True:
                message = await self.engine_to_evaluation_server_queue.get()
                await self.tcpClient.send(message)
        except asyncio.CancelledError:
            logger.info("Message Sender task has been cancelled.")
        except Exception as e:
            logger.exception(f"Exception in msg_sender: {e}")
