import asyncio
import json
import os
import sys
import time

from sshtunnel import SSHTunnelForwarder

from ...ext_comms import config
from ...ext_comms.comms import TCPC_Controller
from ...ext_comms.comms import AsyncMQTTController as async_mqtt

from queue import Queue
from threading import Thread

async def user_input(send_queue: asyncio.Queue, receive_queue: asyncio.Queue, fromQueue:Queue):
    while True:
        if fromQueue.empty():
            time.sleep(10) # allow thread to be blocked to allow others to use. not strictly needed
            continue
        message = fromQueue.get()
        if not message.startswith("p1_") and not message.startswith("p2_"):
            print("Invalid message format. Must start with 'p1_' or 'p2_'")
            continue
        await send_queue.put(message) # @WP TODO: is await really needed?


async def msg_receiver(wsController: TCPC_Controller, receive_queue: asyncio.Queue):
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


async def msg_sender(wsController: TCPC_Controller, send_queue: asyncio.Queue):
    """
    Send messages from the relay node to the TCP server.
    """
    while True:
        message = await send_queue.get()
        await wsController.send(message)


async def run_tcp_client(send_queue: asyncio.Queue, receive_queue: asyncio.Queue, port: int, fromQueue: Queue):
    """
    Establish a connection to the TCP server and handle reconnections.
    """
    wsController = TCPC_Controller(config.TCP_SERVER_HOST, port, config.TCP_SECRET_KEY)

    await wsController.connect()

    # Tasks for sending and receiving messages
    tasks = [
        asyncio.create_task(msg_sender(wsController, send_queue)),
        asyncio.create_task(msg_receiver(wsController, receive_queue)),
        asyncio.create_task(user_input(send_queue, receive_queue, fromQueue))
    ]

    await asyncio.gather(*tasks)  # Ensure both sender and receiver tasks run concurrently

async def ext_main(fromBlunos, toBlunos):
    send_queue = asyncio.Queue()
    receive_queue = asyncio.Queue()
    if config.RELAY_NODE_LOCAL_TEST:
        print("DEV: LOCAL RELAY NODE TEST RUN")
        print("DEV: Starting TCP Client")
        print(f"DEV: Connecting to {config.TCP_SERVER_HOST}:{config.TCP_SERVER_PORT}")
        local_port = config.TCP_SERVER_PORT
    else:
        print("PROD: PRODUCTION RUN")
        print("PROD: SSH Tunneling to Ultra96")
        server = SSHTunnelForwarder(
            ssh_host=config.ssh_host,
            ssh_username=config.ssh_user,
            ssh_password=config.ssh_password,
            remote_bind_address=(config.TCP_SERVER_HOST, config.TCP_SERVER_PORT)
        )
        server.start()

        print(f"PROD: Forwarding port {server.local_bind_port} to ULTRA96 TCP Server port {config.TCP_SERVER_PORT}")
        print("PROD: Starting TCP Client")
        local_port = server.local_bind_port

    await run_tcp_client(send_queue, receive_queue, local_port)
    server.stop()


def aggregator_thread(fromQueue: Queue, from1: Queue, from2: Queue, from3: Queue, to1: Queue, to2: Queue, MQTT_receive: Queue):
    """Aggregates the beetles' data"""
    # round robin executor
    while True:
        if not from1.empty():
            fromQueue.put(from1.get())
        if not from2.empty():
            fromQueue.put(from2.get())
        if not from3.empty():
            fromQueue.put(from3.get())
        if not MQTT_receive.empty():
            data = MQTT_receive.get()
            to1.put(data)
            to2.put(data)

def mqtt_thread(MQTT_receive: Queue):
    # @WP TODO: Create a connection to the broker, receive data and send to MQTT_receive
    foo = asyncio.Queue()
    bar = asyncio.Queue()
    rx = asyncio.Queue()
    async_mqtt.AsyncMQTTController(config.MQTT_BROKER_PORT, foo, bar, rx)

def entry_thread(from1: Queue, from2: Queue, from3: Queue, to1: Queue, to2: Queue):
    # This thread should be run from main()
    fromQueue = Queue()
    MQTT_receive = Queue()
    agg_thread = Thread(target=aggregator_thread, args=(fromQueue, from1, from2, from3, to1, to2, MQTT_receive))
    agg_thread.run()
    # @WP TODO: we will launch the MQTT thread here
    asyncio.run(ext_main(from1, from2, from3, to1, to2))  
    agg_thread.join()
    
if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(ext_main())