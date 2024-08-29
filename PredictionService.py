import asyncio
import random
import time


async def start_prediction_service_process(relay_mqtt_to_engine_queue, prediction_service_to_engine_queue):
    ps = PredictionServiceProcess(relay_mqtt_to_engine_queue, prediction_service_to_engine_queue)
    while True:
        await ps.predict()


class PredictionServiceProcess:
    def __init__(self, relay_mqtt_to_engine_queue, prediction_service_to_engine_queue):
        self.relay_mqtt_to_engine_queue = relay_mqtt_to_engine_queue
        self.prediction_service_to_engine_queue = prediction_service_to_engine_queue

    async def predict(self):
        data = await self.relay_mqtt_to_engine_queue.get()
        print(f"Received data from RelayNode: {data}, predicting...")
        await asyncio.sleep(0.2)  # Simulating processing time
        print(f"Prediction: {data}")
        await self.prediction_service_to_engine_queue.put(data)
