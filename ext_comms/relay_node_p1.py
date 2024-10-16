import asyncio
import json
import os
import sys

import config
from comms.TCPC_Controller import TCPC_Controller
from int_comms.relay.external import sim_get_packet
from int_comms.relay.packet import PACKET_DATA_IMU, PACKET_DATA_HEALTH, PACKET_DATA_KICK, PACKET_DATA_BULLET

RELAY_NODE_PLAYER_NUMBER = 1  # Player number for the relay node


# To be deprecated. For testing purposes only
async def user_input(send_queue: asyncio.Queue, receive_queue: asyncio.Queue):
    while True:
        user_input = input("Input message: ")
        packet_type = user_input.strip().upper()
        if packet_type == 'IMU':
            packet = sim_get_packet(PACKET_DATA_IMU)
        elif packet_type == 'BULLET':
            packet = sim_get_packet(PACKET_DATA_BULLET)
        elif packet_type == 'HEALTH':
            packet = sim_get_packet(PACKET_DATA_HEALTH)
        elif packet_type == 'KICK':
            packet = sim_get_packet(PACKET_DATA_KICK)
        else:
            print("Invalid packet type.")
            continue
        print(f"Sending {packet.packet_type} packet")
        await send_queue.put(packet.to_bytearray())
        print(f"Waiting for message")
        msg = await receive_queue.get()
        root = json.loads(msg)
        player1 = json.loads(root['p1'])
        player2 = json.loads(root['p2'])

        p1Data = f"Action: {player1['action']}\nHealth: {player1['game_state']['hp']}\nBullets: {player1['game_state']['bullets']}\nBombs: {player1['game_state']['bombs']}\nShield HP: {player1['game_state']['shield_hp']}\nDeaths: {player1['game_state']['deaths']}\nShields: {player1['game_state']['shields']}\n"

        p2Data = f"Action: {player2['action']}\nHealth: {player2['game_state']['hp']}\nBullets: {player2['game_state']['bullets']}\nBombs: {player2['game_state']['bombs']}\nShield HP: {player2['game_state']['shield_hp']}\nDeaths: {player2['game_state']['deaths']}\nShields: {player2['game_state']['shields']}\n"

        print(f"Game State Update: \nPLAYER 1:\n{p1Data}\nPLAYER 2:\n{p2Data}")


# Constantly receives data from TCP Server and places it in the queue. Will be replaced/superseded by MQTT
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


# Constantly listens and sends off any data in the send_queue
async def msg_sender(wsController: TCPC_Controller, send_queue: asyncio.Queue):
    """
    Send messages from the relay node to the TCP server.
    """
    while True:
        message = await send_queue.get()
        await wsController.send_no_encrypt(message)


# Async Task Manager for TCP Communication and data transfer
async def run_tcp_client(send_queue: asyncio.Queue, receive_queue: asyncio.Queue, port: int):
    """
    Establish a connection to the TCP server and handle reconnections.
    """
    wsController = TCPC_Controller(config.TCP_SERVER_HOST, port, config.TCP_SECRET_KEY)

    await wsController.connect()
    await wsController.identify_relay_node(RELAY_NODE_PLAYER_NUMBER)

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
    await run_tcp_client(send_queue, receive_queue, config.TCP_SERVER_PORT)


if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(main())
