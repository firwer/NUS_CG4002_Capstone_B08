import asyncio
import os
import random
import sys
import time
from int_comms.relay.packet import PacketImu

sys.path.append('/home/xilinx/IP')

from AIClass import AI


class PredictionServiceProcess:
    def __init__(self, predict_input_queue, predict_output_queue):
        self.relay_to_engine_queue = predict_input_queue
        self.prediction_service_to_engine_queue = predict_output_queue
        self.buffer = []
        self.expected_packets = 60  # Desired number of packets
        self.timeout = 4  # Timeout in seconds
        self.last_packet_time = None
        self.ai_inference = None  # Initialize to None
        self.current_imu_count = -1

    async def initialize_ai(self):
        self.ai_inference = AI()

    async def run(self):
        await self.initialize_ai()
        print("Prediction Service initialized.")
        while True:
            first_packet = await self.relay_to_engine_queue.get()
            print(f"First packet received, starting data collection.")
            #print(first_packet.adc)
            if first_packet.adc != self.current_imu_count:
                self.current_imu_count = first_packet.adc
            else:
                continue
            self.buffer.clear()
            start_time = time.time()
            #print("sanity check")
            self.buffer.append(first_packet)
            await self.collect_data(start_time)

    async def collect_data(self, start_time: time.time()):
        """
        Collects data packets and processes them when enough data is collected
        or a timeout occurs.
        """
        while len(self.buffer) < self.expected_packets:
            try:
                # Calculate remaining time for timeout
                remaining_time = self.timeout - (time.time() - start_time)
                if remaining_time <= 0:
                    raise asyncio.TimeoutError()

                # Wait for new data with the remaining timeout
                imu_packet = await asyncio.wait_for(
                    self.relay_to_engine_queue.get(), timeout=remaining_time
                )
                self.buffer.append(imu_packet)
            except asyncio.TimeoutError:
                # Timeout occurred
                if len(self.buffer) < self.expected_packets:
                    print("Not enough data to proceed; discarding buffer.")
                    return

        # Proceed to inference if enough data is collected
        if len(self.buffer) >= self.expected_packets:
            await self.process_data()

        # Purge queue for next iteration
        # while not self.relay_to_engine_queue.empty():
        #     await self.relay_to_engine_queue.get()

    def assemble_data(self):
        ax_list, ay_list, az_list = [], [], []
        gx_list, gy_list, gz_list = [], [], []

        for packet in self.buffer:
            # Convert bytearrays to signed integers (assuming big-endian format)
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

    async def process_data(self):
        combined_input = self.assemble_data()
        prediction_index = await asyncio.to_thread(self.ai_inference.predict, combined_input)
        print(f"Assembled Input: {combined_input}")
        action_names = ["basket", "bowl", "logout", "bomb",  "reload", "shield", "volley"]
        action = action_names[prediction_index]
        print(f"Prediction: {action}")
        await self.prediction_service_to_engine_queue.put(action)
        print("Prediction sent to Engine.")
