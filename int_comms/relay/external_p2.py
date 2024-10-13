import os
import random
import sys
import time
from queue import Queue
from threading import Thread

import config
from comms.TCPC_Controller_Sync import TCPC_Controller_Sync
from int_comms.relay.packet import PACKET_DATA_IMU, PACKET_DATA_BULLET, PACKET_DATA_HEALTH, PACKET_DATA_KICK, PacketImu, \
    PacketBullet, PacketHealth, PacketKick, get_packet

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

RELAY_NODE_PLAYER = 2


def get_user_input(sendToGameServerQueue):
    while True:
        user_input = input("Enter packet type to send: ")
        # Map user input to packet types
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
        sendToGameServerQueue.put(packet)


def receive_queue_handler(tcpController: TCPC_Controller_Sync, receive_queue: Queue):
    while True:
        try:
            msg = tcpController.recv_decrypt()
            receive_queue.put(msg)
        except Exception as e:
            print(f"Error receiving message: {e}")
            # Handle reconnection if needed


def send_queue_handler(tcpController: TCPC_Controller_Sync, send_queue: Queue):
    while True:
        message = send_queue.get(block=True)
        tcpController.send(message.to_bytearray())


#async def async_thread_main(fromBlunos: Queue, toBlunos: Queue, sendToGameServerQueue: Queue,
def thread_main(sendToGameServerQueue: Queue, receiveFromGameServerQueue: Queue):
    print("Establishing connection to TCP server...")
    wsController = TCPC_Controller_Sync(
        config.TCP_SERVER_HOST, config.TCP_SERVER_PORT, config.TCP_SECRET_KEY
    )

    wsController.connect()
    wsController.identify_relay_node(RELAY_NODE_PLAYER)

    send_thread = Thread(target=send_queue_handler, args=(wsController, sendToGameServerQueue))
    receive_thread = Thread(target=receive_queue_handler, args=(wsController, receiveFromGameServerQueue))
    user_input_thread = Thread(target=get_user_input, args=(sendToGameServerQueue,))

    send_thread.start()
    receive_thread.start()
    user_input_thread.start()

    send_thread.join()
    receive_thread.join()
    user_input_thread.join()


# def aggregator_thread_main(sendToGameServerQueue: Queue, from_beetles_queue, to_beetles_queues,
#                            receiveFromGameServerQueue: Queue):
#     """Aggregates the beetles' data"""
#     while True:
#         # Use a combined list of queues to wait on
#         for from_queue in from_beetles_queue:
#             try:
#                 data = from_queue.get(timeout=0.1)
#                 sendToGameServerQueue.put(data)
#             except Exception as error:
#                 continue
#         try:
#             data = receiveFromGameServerQueue.get(timeout=0.1)
#             for to_queue in to_beetles_queues:
#                 to_queue.put(data)
#         except Exception as error:
#             continue


def entry_thread(fromBeetle1: Queue, fromBeetle2: Queue, fromBeetle3: Queue, toBeetle1: Queue, toBeetle2: Queue):
    print("Starting entry thread")
    receiveFromGameServerQueue = Queue()
    sendToGameServerQueue = Queue()
    # from_beetles_queues = [fromBeetle1, fromBeetle2, fromBeetle3]
    # to_beetles_queues = [toBeetle1, toBeetle2]
    # Start the aggregator thread
    # agg_thread = Thread(target=aggregator_thread_main, args=(
    #     sendToGameServerQueue, from_beetles_queues, to_beetles_queues, receiveFromGameServerQueue))
    # agg_thread.start()

    # Start the async thread
    async_thread = Thread(target=thread_main, args=(sendToGameServerQueue, receiveFromGameServerQueue))
    async_thread.start()

    #agg_thread.join()
    async_thread.join()


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


def sim_beetle(id, toExternal: Queue, fromExternal: Queue = None):
    if id == 1:  # IMU, Bullet
        print(f"Starting IMU, Bullet Mock beetle{id}")
        packets = []
        while True:
            coin_flip = random.randrange(0, 2)
            if coin_flip == 1:
                for _ in range(60):
                    packets.append(get_packet(PACKET_DATA_IMU))
                # Send the packets in a period of 0.5s
                for packet in packets:
                    toExternal.put(packet)
                    time.sleep(0.5 / len(packets))  # distribute the packets over 0.5s
                packets.clear()  # Clear the packet list after sending them
            else:
                packet = get_packet(PACKET_DATA_BULLET)
                toExternal.put(packet)
            if not fromExternal.empty():
                print(f"beetle{id} got: {fromExternal.get_nowait()}")
    elif id == 2:
        print(f"Starting Health Mock beetle{id}")
        task_period_ns = 1000 * 1e6  # ms * ns_offset
        startTime = time.time_ns()
        while True:
            if time.time_ns() - startTime > task_period_ns:
                packet = get_packet(PACKET_DATA_HEALTH)
                toExternal.put(packet)
                startTime = time.time_ns()
            if not fromExternal.empty():
                print(f"beetle{id} got: {fromExternal.get_nowait()}")
    elif id == 3:
        print(f"Starting Kick Mock beetle{id}")
        while True:
            time.sleep(random.randrange(4, 11))
            packet = get_packet(PACKET_DATA_KICK)
            toExternal.put(packet)


def simulate():
    # simulate beetle passing messages
    global RELAY_NODE_PLAYER
    while RELAY_NODE_PLAYER != 1 and RELAY_NODE_PLAYER != 2:
        input("Select with player's relay node (1/2):")
        RELAY_NODE_PLAYER = int(input())
    print(f"Configured relay node for player {RELAY_NODE_PLAYER}")
    fromBeetle1 = Queue()
    fromBeetle2 = Queue()
    fromBeetle3 = Queue()
    toBeetle1 = Queue()
    toBeetle2 = Queue()

    thread_entry = Thread(target=entry_thread, args=(fromBeetle1, fromBeetle2, fromBeetle3, toBeetle1, toBeetle2,))
    thread_entry.start()
    thread_entry.join()

    #thread_entry = Thread(target=entry_thread, args=(fromBeetle1, fromBeetle2, fromBeetle3, toBeetle1, toBeetle2,))
    #thread_beetle1 = Thread(target=sim_beetle, args=(1, fromBeetle1, toBeetle1,))
    #thread_beetle2 = Thread(target=sim_beetle, args=(2, fromBeetle2, toBeetle2,))
    #thread_beetle3 = Thread(target=sim_beetle, args=(3, fromBeetle3,))
    # TODO: start the threads
    #thread_entry.start()
    # thread_beetle1.start()
    # thread_beetle2.start()
    # thread_beetle3.start()
    #thread_entry.join()
    # thread_beetle1.join()
    # thread_beetle2.join()
    # thread_beetle3.join()


if __name__ == "__main__":
    simulate()
