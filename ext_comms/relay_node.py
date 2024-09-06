import asyncio
import os
import sys

from sshtunnel import SSHTunnelForwarder

import config
from comms.AsyncMQTTController import AsyncMQTTController
from comms.TCPController import TCPController


async def user_input(send_queue: asyncio.Queue, receive_queue: asyncio.Queue):
    while True:
        message = input("Input message: ")
        await send_queue.put(message)
        msg = await receive_queue.get()
        print(f"Received message: {msg}")


async def msg_receiver(wsController, receive_queue: asyncio.Queue):
    msg = await wsController.receive()
    await receive_queue.put(msg)


async def msg_sender(wsController, send_queue: asyncio.Queue):
    message = await send_queue.get()
    await wsController.send(message)


async def run_tcp_client(send_queue: asyncio.Queue, receive_queue: asyncio.Queue):
    wsController = TCPController(config.TCP_SERVER_HOST, config.TCP_SERVER_PORT,
                                 config.TCP_SECRET_KEY)  # Used for communication with the evaluation server
    await wsController.connect()
    while True:
        await msg_sender(wsController, send_queue)
        await msg_receiver(wsController, receive_queue)


async def main():
    send_queue = asyncio.Queue()
    receive_queue = asyncio.Queue()
    if config.RELAY_NODE_LOCAL_TEST:
        print("DEV: LOCAL RELAY NODE TEST RUN")
        print("DEV: Starting TCP Client")
        print(f"DEV: Connecting to {config.TCP_SERVER_HOST}:{config.TCP_SERVER_PORT}")
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

    tcp_p1 = asyncio.create_task(run_tcp_client(send_queue=send_queue, receive_queue=receive_queue))
    debug_input = asyncio.create_task(user_input(send_queue, receive_queue))
    await asyncio.gather(tcp_p1, debug_input)
    server.stop()


if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(main())
