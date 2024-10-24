import json
import struct
from logging import Logger
import logging
import os
import random
import sys
import time
from queue import Queue
from threading import Thread

import config
from int_comms.hardcoded_imu import basket_packets, bowling_packets, reload_packets, volley_packets, rainbomb_packets, \
    shield_packets, logout_packets

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from comms.TCPC_Controller_Sync import TCPC_Controller_Sync
from int_comms.relay.packet import PACKET_DATA_IMU, PACKET_DATA_BULLET, PACKET_DATA_HEALTH, PACKET_DATA_KICK, PacketImu, \
    PacketBullet, PacketHealth, PacketKick, PacketGamestate, get_packet

ext_logger = logging.getLogger("External2")

RELAY_NODE_PLAYER = 2
PLAYER_NUMBER = 2


def receive_queue_handler_integrated(tcpController: TCPC_Controller_Sync, receive_queues):
    """Receives gamestate from game engine. Packs it into PacketGamestate, sends to int-comms.
    WARN: Does not do any checksum logic.
    """
    prev_err = None
    while True:
        try:
            msg = tcpController.recv_decrypt()  # this is blocking?
            if msg is None:
                # ext_logger.info("msg is none, continuing..")
                continue
            ext_logger.info(f"MSG: {msg}")
            root = json.loads(msg)
            # ext_logger.info(f"ROOT: {root}")
            player = None
            pkt = PacketGamestate()
            if PLAYER_NUMBER == 1:
                player = json.loads(root['p1'])
                pkt.bullet = player["game_state"]["bullets"]
                pkt.health = player["game_state"]["hp"]
                ext_logger.info(f"P1 getting {pkt.bullet} bullets, {pkt.health} health")
            else:
                player = json.loads(root['p2'])
                pkt.bullet = player["game_state"]["bullets"]
                pkt.health = player["game_state"]["hp"]
                ext_logger.info(f"P2 getting {pkt.bullet} bullets, {pkt.health} health")
            # broadcast the queues 
            for receive_queue in receive_queues:
                receive_queue.put(pkt)
        except Exception as e:
            if prev_err != e:
                prev_err = e
                # ext_logger.debug(f"Error receiving message: {e}")


def receive_queue_handler(tcpController: TCPC_Controller_Sync, receive_queue: Queue):
    while True:
        try:
            msg = tcpController.recv_decrypt()
            receive_queue.put(msg)
        except Exception as e:
            print(f"Error receiving message: {e}")


def send_queue_handler(tcpController: TCPC_Controller_Sync, send_queue: Queue):
    while True:
        message = send_queue.get(block=True)
        tcpController.send(message.to_bytearray())


def begin_external(sendToGameServerQueue: Queue, receiveFromGameServerQueue0: Queue, receiveFromGameServerQueue1,
                   player_num):
    global RELAY_NODE_PLAYER
    RELAY_NODE_PLAYER = player_num
    ext_logger.debug("Controller sync begin...")
    wsController = TCPC_Controller_Sync(
        config.TCP_SERVER_HOST, config.TCP_SERVER_PORT, config.TCP_SECRET_KEY
    )
    ext_logger.debug("External comms liaison starting...")
    wsController.connect()
    wsController.identify_relay_node(RELAY_NODE_PLAYER)
    receiveQueues = [receiveFromGameServerQueue0, receiveFromGameServerQueue1]
    ext_logger.debug("External comms liaison connected!")
    # start the input thread
    send_thread = Thread(target=send_queue_handler, args=(wsController, sendToGameServerQueue))
    receive_thread = Thread(target=receive_queue_handler_integrated, args=(wsController, receiveQueues))
    send_thread.start()
    receive_thread.start()
    send_thread.join()
    receive_thread.join()


##
## HW Simulator Code Below
##
##
def sim_get_packet(type):
    """Chooses a packet to send to the external comms side."""
    if type == PACKET_DATA_IMU:
        print("Sending IMU packet")
        pkt = PacketImu()
        pkt.accelX = bytearray([random.randrange(0, 256) for _ in range(2)])
        pkt.accelY = bytearray([random.randrange(0, 256) for _ in range(2)])
        pkt.accelZ = bytearray([random.randrange(0, 256) for _ in range(2)])
        pkt.gyroX = bytearray([random.randrange(0, 256) for _ in range(2)])
        pkt.gyroY = bytearray([random.randrange(0, 256) for _ in range(2)])
        pkt.gyroZ = bytearray([random.randrange(0, 256) for _ in range(2)])
        return pkt
    elif type == PACKET_DATA_BULLET:
        print("Sending bullet packet")
        pkt = PacketBullet()
        pkt.bullet = random.randrange(0, 10)
        return pkt
    elif type == PACKET_DATA_HEALTH:
        print("Sending health packet")
        pkt = PacketHealth()
        pkt.health = random.randrange(0, 100)
        return pkt
    elif type == PACKET_DATA_KICK:
        print("Sending kick packet")
        pkt = PacketKick()
        return pkt
    assert False  # this should never trigger!


# Function to convert IMU data into byte array for PacketImu
def create_packet_from_imu_data(imu_data):
    # Convert IMU data to a byte array (each sensor value is 2 bytes - 16-bit signed integer)
    byte_array = bytearray()

    # Add the packet type (for simplicity, we'll assume it's 1 byte; you can adjust as needed)
    byte_array.append(PACKET_DATA_IMU)

    # Seq_num and adc are placeholders (assuming 1 byte each)
    byte_array.append(0)  # Placeholder for seq_num
    byte_array.append(0)  # Placeholder for adc

    # Convert each IMU value into 2 bytes (16-bit signed integer) and append to the byte array
    byte_array.extend(struct.pack('<h', imu_data['ax']))  # Convert ax to 2 bytes
    byte_array.extend(struct.pack('<h', imu_data['ay']))  # Convert ay to 2 bytes
    byte_array.extend(struct.pack('<h', imu_data['az']))  # Convert az to 2 bytes
    byte_array.extend(struct.pack('<h', imu_data['gx']))  # Convert gx to 2 bytes
    byte_array.extend(struct.pack('<h', imu_data['gy']))  # Convert gy to 2 bytes
    byte_array.extend(struct.pack('<h', imu_data['gz']))  # Convert gz to 2 bytes

    # Add 4 bytes of padding
    byte_array.extend(bytearray(4))

    # Add a placeholder for CRC8 (1 byte)
    byte_array.append(0)  # Placeholder for CRC8

    # Ensure the byte array has a total of 20 bytes (if something is missing, add padding)
    while len(byte_array) < 20:
        byte_array.append(0)

    return byte_array


def create_imu_packets(imu_data_list):
    packets = []

    for imu_data in imu_data_list:
        byte_array = create_packet_from_imu_data(imu_data)
        packet = PacketImu(byteArray=byte_array)  # Create a PacketImu instance with the byte array
        packets.append(packet)

    return packets


def get_user_input(sendToGameServerQueue: Queue):
    adc_counter = 0
    pkts = []
    while True:
        user_input = input("\nEnter packet type to send: ")
        # Map user input to packet types
        packet_type = user_input.strip().upper()
        if packet_type == 'BASKET':
            pkts = create_imu_packets(basket_packets)
        elif packet_type == 'BOWLING':
            pkts = create_imu_packets(bowling_packets)
        elif packet_type == 'RELOAD':
            pkts = create_imu_packets(reload_packets)
        elif packet_type == 'VOLLEY':
            pkts = create_imu_packets(volley_packets)
        elif packet_type == 'BOMB':
            pkts = create_imu_packets(rainbomb_packets)
        elif packet_type == 'SHIELD':
            pkts = create_imu_packets(shield_packets)
        elif packet_type == 'LOGOUT':
            pkts = create_imu_packets(logout_packets)
        elif packet_type == 'GUN':
            pkts = [sim_get_packet(PACKET_DATA_BULLET)]
        elif packet_type == 'HEALTH':
            pkts = [sim_get_packet(PACKET_DATA_HEALTH)]
        elif packet_type == 'SOCCER':
            pkts = [sim_get_packet(PACKET_DATA_KICK)]
        else:
            print("Invalid packet type.")
            continue
        for i, n in enumerate(pkts):
            n.adc = adc_counter
            print(f"Sending {i + 1}/60 packet")
            time.sleep(0.01)
            sendToGameServerQueue.put(n)
        adc_counter += 1


# This is only for testing/simulation purposes. Actual internal comms side entry point is not here.
def start_simulate():
    ext_logger.debug("DEV: SIMULATION STARTED. NOT FOR ACTUAL USE.")
    sendToGameServerQueue, receiveFromGameServerQueue0, receiveFromGameServerQueue1 = Queue(), Queue(), Queue()
    wsController = TCPC_Controller_Sync(
        config.TCP_SERVER_HOST, config.TCP_SERVER_PORT, config.TCP_SECRET_KEY
    )
    wsController.identify_relay_node(2)
    ext_logger.debug("External comms liaison connected!")
    receiveQueues = [receiveFromGameServerQueue0, receiveFromGameServerQueue1]
    send_thread = Thread(target=send_queue_handler, args=(wsController, sendToGameServerQueue))
    #receive_thread = Thread(target=receive_queue_handler, args=(wsController, receiveQueues))

    send_thread.start()
    #receive_thread.start()

    get_user_input(sendToGameServerQueue)

    send_thread.join()
    #receive_thread.join()


if __name__ == "__main__":
    start_simulate()
