import asyncio

from ...ext_comms import config
from ...ext_comms.comms import TCPC_Controller

from queue import Queue
from threading import Thread
import packet

RELAY_NODE_PLAYER = 1


async def send_to_server(fromBruno: Queue, toBruno: Queue, send_queue: Queue, receive_queue: Queue):
    if RELAY_NODE_PLAYER == 1:
        prefix = b'p1_'
    elif RELAY_NODE_PLAYER == 2:
        prefix = b'p2_'
    else:
        raise ValueError('Invalid RELAY_NODE_PLAYER value. Must be 1 or 2.')

    loop = asyncio.get_running_loop()

    async def get_from_thread_queue(q):
        return await loop.run_in_executor(None, q.get)

    async def put_to_thread_queue(q, item):
        await loop.run_in_executor(None, q.put, item)

    async def process_fromBruno():
        while True:
            data = await get_from_thread_queue(fromBruno)
            message = prefix + data
            await send_queue.put(message)

    async def process_receive_queue():
        while True:
            data = await receive_queue.get()
            await put_to_thread_queue(toBruno, data)

    await asyncio.gather(
        process_fromBruno(),
        process_receive_queue()
    )
"""
 Functions to handle direct communication between the queue and the TCP server
"""


async def receive_queue_handler(wsController: TCPC_Controller, receive_queue: Queue):
    """
    Continuously receive messages from the TCP server and place them in the queue.
    """
    while True:
        try:
            msg = await wsController.recv_decrypt()
            await receive_queue.put(msg)
        except (asyncio.IncompleteReadError, ConnectionResetError, ConnectionAbortedError):
            print("Connection lost. Attempting to reconnect...")
            await wsController.reconnect()
            continue  # After reconnection, continue receiving


async def send_queue_handler(wsController: TCPC_Controller, send_queue: Queue):
    """
    Continuously get messages in queue and send to the TCP server.
    """
    while True:
        message = await send_queue.get()
        message = message.decode()
        await wsController.send(message)


async def async_thread_main(fromBlunos: Queue, toBlunos: Queue, sendToGameServerQueue: Queue,
                            receiveFromGameServerQueue: Queue):
    # Establish a connection to the TCP server and handle reconnections.
    wsController = TCPC_Controller.TCPC_Controller(config.TCP_SERVER_HOST, config.TCP_SERVER_PORT, config.TCP_SECRET_KEY)
    await wsController.connect()

    # Async queues are used for communication between the TCP server and the relay node
    # Tasks for sending and receiving messages
    tasks = [
        asyncio.create_task(receive_queue_handler(wsController, receiveFromGameServerQueue)),
        asyncio.create_task(send_queue_handler(wsController, sendToGameServerQueue)),
        asyncio.create_task(send_to_server(fromBlunos, toBlunos, sendToGameServerQueue, receiveFromGameServerQueue))
    ]

    await asyncio.gather(*tasks)  # Ensure both sender and receiver tasks run concurrently


def aggregator_thread_main(sendToGameServerQueue: Queue, from1: Queue, from2: Queue, from3: Queue, to1: Queue, to2: Queue,
                           receiveFromGameServerQueue: Queue):
    """Aggregates the beetles' data"""
    # round robin executor
    while True:
        if not from1.empty():
            sendToGameServerQueue.put(from1.get())
        if not from2.empty():
            sendToGameServerQueue.put(from2.get())
        if not from3.empty():
            sendToGameServerQueue.put(from3.get())
        if not receiveFromGameServerQueue.empty():
            # Received data from the game server, propagate latest game states to the beetles
            data = receiveFromGameServerQueue.get()
            to1.put(data)
            to2.put(data)

        #busy wait issue fixme


def entry_thread(fromBeetle1: Queue, fromBeetle2: Queue, fromBeetle3: Queue, toBeetle1: Queue, toBeetle2: Queue):
    receiveFromGameServerQueue = Queue()
    sendToGameServerQueue = Queue()
    # This thread should be run from main()
    # Start the aggregator thread
    agg_thread = Thread(target=aggregator_thread_main, args=(
        sendToGameServerQueue, fromBeetle1, fromBeetle2, fromBeetle3, toBeetle1, toBeetle2, receiveFromGameServerQueue))
    agg_thread.start()

    # Start the async thread
    async_thread = Thread(target=async_thread_main, args=(sendToGameServerQueue, receiveFromGameServerQueue))
    async_thread.start()

    agg_thread.join()
    async_thread.join()

def sim_get_packet():
    """Chooses a packet to send to the external comms side. """
    pass

def sim_beetle(id, toExternal: Queue, fromExternal: Queue=None):
    packets = []
    if id == 1: # IMU, Bullet
        pass
    elif id == 2:
        pass
    elif id == 3:
        pass
    else:
        pass

def simulate():
    # simulate beetle passing messages
    fromBeetle1 = Queue()
    fromBeetle2 = Queue()
    fromBeetle3 = Queue()
    toBeetle1 = Queue()
    toBeetle2 = Queue()
    thread_entry = Thread(target=entry_thread, args=(1, fromBeetle1, fromBeetle2, fromBeetle3, toBeetle1, toBeetle2,))
    thread_beetle1 = Thread(target=sim_beetle, args=(2, fromBeetle1, toBeetle1,))
    thread_beetle2 = Thread(target=sim_beetle, args=(3, fromBeetle2, toBeetle2,))
    thread_beetle3 =  Thread(target=sim_beetle, args=(fromBeetle3,))
    # TODO: start the threads
    thread_entry.start()

if __name__ == "__main__":
    simulate() 