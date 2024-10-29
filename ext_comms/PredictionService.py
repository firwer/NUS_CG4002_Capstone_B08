# PredictionService.py
import asyncio
import os
import sys

from logger_config import setup_logger
import config

# Ensure correct path
sys.path.append('/home/xilinx/IP')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import int_comms.relay.packet
from AI50Class import AI

logger = setup_logger(__name__)


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
    logger.debug(f"Assembled data from buffer with {len(buffer)} packets.")
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
        try:
            self.ai_inference = AI()
            logger.info("AI Inference engine initialized successfully.")
        except Exception as e:
            logger.exception(f"Failed to initialize AI Inference engine: {e}")

    async def run(self):
        await self.initialize_ai()
        if self.ai_inference is None:
            logger.critical("AI Inference engine not initialized. Exiting PredictionServiceProcess.")
            return
        logger.info("Prediction Service started.")

        task_p1 = asyncio.create_task(self.process_player(player_id=1))
        task_p2 = asyncio.create_task(self.process_player(player_id=2))

        await asyncio.gather(task_p1, task_p2)

    async def process_player(self, player_id: int):
        """
        Process IMU packets for a specific player.
        """
        logger.debug(f"[P{player_id}] Starting prediction processing service")
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
            logger.error(f"Invalid player_id: {player_id}")
            return
        while True:
            try:
                dataBuf.clear()
                # Wait for the first packet from stream
                imu_packet = await input_queue.get()
                if imu_packet.adc == prev_imu_count:
                    logger.debug(f"[P{player_id}] Duplicate IMU packet detected. Skipping.")
                    continue
                dataBuf.append(imu_packet)
                logger.debug(f"[P{player_id}] Collected 1/{config.GAME_AI_PACKET_COUNT} IMU packets.")

                # Collect remaining packets with timeout
                while len(dataBuf) < config.GAME_AI_PACKET_COUNT:
                    imu_packet_new = await asyncio.wait_for(input_queue.get(), timeout=15)
                    curr_imu_count = imu_packet_new.adc
                    dataBuf.append(imu_packet_new)
                    logger.debug(
                        f"[P{player_id}] Collected {len(dataBuf)}/{config.GAME_AI_PACKET_COUNT} IMU packets.")

                if len(dataBuf) == config.GAME_AI_PACKET_COUNT:
                    # Assemble data for AI
                    combined_input = assemble_data(dataBuf)
                    logger.info(f"[P{player_id}] Assembled {len(combined_input)} data points for AI prediction.")

                    # Acquire lock to perform AI prediction
                    async with self.lock:
                        logger.debug(f"[P{player_id}] Acquired AI lock. Performing prediction.")
                        # Offload AI prediction to a separate thread
                        predicted_action = await asyncio.to_thread(self.ai_inference.predict, combined_input)

                    logger.info(f"[P{player_id}] AI Prediction: {predicted_action}")

                    # Send prediction to the respective output queue
                    await output_queue.put(predicted_action)
                    logger.debug(f"[P{player_id}] Sent prediction to output queue.")

                    prev_imu_count = curr_imu_count
            except asyncio.TimeoutError:
                logger.warning(f"[P{player_id}] Timeout while waiting for IMU packets. Clearing buffer.")
            except Exception as e:
                logger.exception(f"[P{player_id}] Error processing IMU packets: {e}")
