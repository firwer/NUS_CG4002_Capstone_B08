import random
import time


def start_prediction_service_process(relay_mqtt_to_engine_queue, prediction_service_to_engine_queue):
    ps = PredictionServiceProcess(relay_mqtt_to_engine_queue, prediction_service_to_engine_queue)
    while True:
        ps.predict()


class PredictionServiceProcess:
    def __init__(self, relay_mqtt_to_engine_queue, prediction_service_to_engine_queue):
        self.relay_mqtt_to_engine_queue = relay_mqtt_to_engine_queue
        self.prediction_service_to_engine_queue = prediction_service_to_engine_queue

    def predict(self):
        data = self.relay_mqtt_to_engine_queue.get()
        print(f"Received data from RelayNode: {data}, predicting...")
        time.sleep(0.2)
        print(f"Prediction: {data}")
        self.prediction_service_to_engine_queue.put(data)
