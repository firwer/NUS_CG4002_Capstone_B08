import asyncio
import os
import random
import sys
import time

sys.path.append('/home/xilinx/IP')

from AIClass import AI

# async def start_prediction_service_process(predict_input_queue: asyncio.Queue,
#                                            predict_output_queue: asyncio.Queue):
#     ps = PredictionServiceProcess(predict_input_queue, predict_output_queue)
#     while True:
#         await ps.predict()


class PredictionServiceProcess:
    def __init__(self, predict_input_queue, predict_output_queue):
        self.relay_to_engine_queue = predict_input_queue
        self.prediction_service_to_engine_queue = predict_output_queue
        self.buffer = []
        self.buffer_size = 60  # Desired number of packets
        self.timeout = 10 # Timeout in seconds
        self.min_packets = int(0.95 * self.buffer_size)  # Minimum packets threshold (80%)
        self.last_packet_time = None
        self.ai_inference = AI()  # Instance of your AI inference class

    async def run(self):
        while True:
            await self.collect_data()

    async def collect_data(self):
        """
        Collects data packets and processes them when enough data is collected
        or a timeout occurs.
        """
        self.buffer.clear()
        start_time = time.time()
        while True:
            try:
                # Calculate remaining time for timeout
                remaining_time = self.timeout - (time.time() - start_time)
                if remaining_time <= 0:
                    raise asyncio.TimeoutError()

                # Wait for new data with the remaining timeout
                data = await asyncio.wait_for(
                    self.relay_to_engine_queue.get(), timeout=remaining_time
                )

                # Proceed to inference if enough data is collected
                if len(self.buffer) >= self.buffer_size:
                    await self.process_data()
                    self.buffer.clear()
                    start_time = time.time()  # Reset the timer for the next batch
            except asyncio.TimeoutError:
                # Timeout occurred
                if len(self.buffer) >= self.min_packets:
                    await self.process_data()
                else:
                    # Not enough data; decide whether to proceed or discard
                    print("Not enough data to proceed; discarding buffer.")
                self.buffer.clear()
                start_time = time.time()  # Reset the timer for the next batch

    # async def predict(self):
    #     data = await self.relay_mqtt_to_engine_queue.get()
    #     print(f"Received data from RelayNode: {data}, predicting...")
    #     # Randomly generate a prediction from actions
    #     # TODO: Replace with actual prediction model
    #     data = random.choice(["basket", "volley", "bowl", "bomb", "logout", "shield", "reload"])
    #     await asyncio.sleep(0.2)  # Simulating processing time
    #     print(f"Prediction: {data}")
    #     await self.prediction_service_to_engine_queue.put(data)

    def assemble_data(self):
        ax_list, ay_list, az_list = [], [], []
        gx_list, gy_list, gz_list = [], [], []

        for packet in self.buffer:
            # Convert bytearrays to signed integers (assuming big-endian format)
            ax = int.from_bytes(packet.accelX, byteorder='big', signed=True)
            ay = int.from_bytes(packet.accelY, byteorder='big', signed=True)
            az = int.from_bytes(packet.accelZ, byteorder='big', signed=True)
            gx = int.from_bytes(packet.gyroX, byteorder='big', signed=True)
            gy = int.from_bytes(packet.gyroY, byteorder='big', signed=True)
            gz = int.from_bytes(packet.gyroZ, byteorder='big', signed=True)

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
        prediction_index = self.ai_inference.predict(combined_input)
        action_names = ["basket", "volley", "bowl", "bomb", "logout", "shield", "reload"]
        action = action_names[prediction_index]
        print(f"Prediction: {action}")
        await self.prediction_service_to_engine_queue.put(action)
