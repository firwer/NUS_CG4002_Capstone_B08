import asyncio
import json
import os
import sys

from sshtunnel import SSHTunnelForwarder

import config
from comms.TCPC_Controller import TCPC_Controller


# To be deprecated. For testing purposes only
async def user_input(send_queue: asyncio.Queue, receive_queue: asyncio.Queue):
    while True:
        message = input("Input message: ")
        if not message.startswith("p1_") and not message.startswith("p2_"):
            print("Invalid message format. Must start with 'p1_' or 'p2_'")
            continue
        await send_queue.put(message)
        print(f"Waiting for message")
        msg = await receive_queue.get()
        root = json.loads(msg)
        player1 = json.loads(root['p1'])
        player2 = json.loads(root['p2'])

        p1Data = f"Action: {player1['action']}\nHealth: {player1['game_state']['hp']}\nBullets: {player1['game_state']['bullets']}\nBombs: {player1['game_state']['bombs']}\nShield HP: {player1['game_state']['shield_hp']}\nDeaths: {player1['game_state']['deaths']}\nShields: {player1['game_state']['shields']}\n"

        p2Data = f"Action: {player2['action']}\nHealth: {player2['game_state']['hp']}\nBullets: {player2['game_state']['bullets']}\nBombs: {player2['game_state']['bombs']}\nShield HP: {player2['game_state']['shield_hp']}\nDeaths: {player2['game_state']['deaths']}\nShields: {player2['game_state']['shields']}\n"

        print(f"Game State Update: \nPLAYER 1:\n{p1Data}\nPLAYER 2:\n{p2Data}")


# Receives data from TCP Server and places it in the queue. Will be replaced/superseded by MQTT
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


async def run_tcp_client(send_queue: asyncio.Queue, receive_queue: asyncio.Queue, port: int):
    """
    Establish a connection to the TCP server and handle reconnections.
    """
    wsController = TCPC_Controller(config.TCP_SERVER_HOST, port, config.TCP_SECRET_KEY)

    await wsController.connect()

    # Tasks for sending and receiving messages
    tasks = [
        asyncio.create_task(msg_sender(wsController, send_queue)),
        asyncio.create_task(msg_receiver(wsController, receive_queue)),
        asyncio.create_task(user_input(send_queue, receive_queue))
    ]

    await asyncio.gather(*tasks)  # Ensure both sender and receiver tasks run concurrently


async def main():
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


if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(main())
