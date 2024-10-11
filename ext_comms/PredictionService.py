import asyncio


async def start_prediction_service_process(predict_input_queue: asyncio.Queue,
                                           predict_output_queue: asyncio.Queue):
    ps = PredictionServiceProcess(predict_input_queue, predict_output_queue)
    while True:
        await ps.predict()


class PredictionServiceProcess:
    def __init__(self, predict_input_queue, predict_output_queue):
        self.relay_mqtt_to_engine_queue = predict_input_queue
        self.prediction_service_to_engine_queue = predict_output_queue

    async def predict(self):
        # TODO: Need to differentiate between GUN and other actions

        data = await self.relay_mqtt_to_engine_queue.get()
        print(f"Received data from RelayNode: {data}, predicting...")
        await asyncio.sleep(0.2)  # Simulating processing time
        print(f"Prediction: {data}")
        await self.prediction_service_to_engine_queue.put(data)
