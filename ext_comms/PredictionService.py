import asyncio
import os
import random
import sys
import time

import config
from int_comms.relay.packet import PacketImu

sys.path.append('/home/xilinx/IP')

from AIClass import AI


def assemble_data(buffer):
    """
    Converts a list of PacketImu objects into a combined input list for the AI.
    """
    ax_list, ay_list, az_list = [], [], []
    gx_list, gy_list, gz_list = [], [], []

    for packet in buffer:
        # Convert bytearrays to signed integers (assuming little-endian format)
        ax = int.from_bytes(packet.accelX, byteorder='little', signed=True)
        ay = int.from_bytes(packet.accelY, byteorder='little', signed=True)
        az = int.from_bytes(packet.accelZ, byteorder='little', signed=True)
        gx = int.from_bytes(packet.gyroX, byteorder='little', signed=True)
        gy = int.from_bytes(packet.gyroY, byteorder='little', signed=True)
        gz = int.from_bytes(packet.gyroZ, byteorder='little', signed=True)

        ax_list.append(ax)
        ay_list.append(ay)
        az_list.append(az)
        gx_list.append(gx)
        gy_list.append(gy)
        gz_list.append(gz)

    # Combine all sensor readings
    combined_input = ax_list + ay_list + az_list + gx_list + gy_list + gz_list

    return combined_input


class PredictionServiceProcess:
    def __init__(self,
                 predict_input_queue_p1: asyncio.Queue,
                 predict_input_queue_p2: asyncio.Queue,
                 predict_output_queue_p1: asyncio.Queue,
                 predict_output_queue_p2: asyncio.Queue):
        self.predict_input_queue_p1 = predict_input_queue_p1
        self.predict_input_queue_p2 = predict_input_queue_p2
        self.predict_output_queue_p1 = predict_output_queue_p1
        self.predict_output_queue_p2 = predict_output_queue_p2
        self.ai_inference = None  # Initialize to None
        self.lock = asyncio.Lock()  # To synchronize AI access

    async def initialize_ai(self):
        self.ai_inference = AI()

    async def run(self):
        await self.initialize_ai()
        print("Prediction Service initialized.")

        task_p1 = asyncio.create_task(self.process_player(player_id=1))
        task_p2 = asyncio.create_task(self.process_player(player_id=2))

        await asyncio.gather(task_p1, task_p2)

    async def process_player(self, player_id: int):
        """
        Process IMU packets for a specific player.
        """
        curr_imu_count = -1
        prev_imu_count = -1
        dataBuf = []
        if player_id == 1:
            input_queue = self.predict_input_queue_p1
            output_queue = self.predict_output_queue_p1
        elif player_id == 2:
            input_queue = self.predict_input_queue_p2
            output_queue = self.predict_output_queue_p2
        else:
            print(f"Invalid player_id: {player_id}")
            return
        while True:
            try:
                dataBuf.clear()
                # Wait for the first packet from stream
                imu_packet = await input_queue.get()
                if imu_packet.adc == prev_imu_count:
                    continue
                dataBuf.append(imu_packet)

                # Collect remaining packets with timeout
                while len(dataBuf) < config.GAME_AI_PACKET_COUNT:
                    imu_packet_new = await asyncio.wait_for(input_queue.get(), timeout=30)
                    curr_imu_count = imu_packet_new.adc
                    dataBuf.append(imu_packet_new)
                    print(f"Player {player_id}: Collected {len(dataBuf)}/{config.GAME_AI_PACKET_COUNT} IMU packets.")

                if len(dataBuf) == config.GAME_AI_PACKET_COUNT:
                    # Assemble data for AI
                    combined_input = assemble_data(dataBuf)
                    print(f"Player {player_id}: Assembled {len(combined_input)} data points for AI prediction.")

                    # Acquire lock to perform AI prediction
                    async with self.lock:
                        print(f"Player {player_id}: Acquired AI lock. Performing prediction.")
                        # Offload AI prediction to a separate thread
                        prediction_index = await asyncio.to_thread(self.ai_inference.predict, combined_input)
                        print(f"Player {player_id}: AI Prediction index: {prediction_index}")

                    # Map prediction index to action
                    action_names = ["basket", "bowl", "logout", "bomb", "reload", "shield", "volley"]
                    action = action_names[prediction_index] if 0 <= prediction_index < len(action_names) else "unknown"
                    print(f"Player {player_id}: AI Prediction: {action}")

                    # Send prediction to the respective output queue
                    await output_queue.put(action)
                    print(f"Player {player_id}: Sent prediction to output queue.")

                    prev_imu_count = curr_imu_count

            except asyncio.TimeoutError:
                print(f"Player {player_id}: Timeout while waiting for IMU packets. Clearing buffer.")
            except Exception as e:
                print(f"Player {player_id}: Error processing IMU packets: {e}")