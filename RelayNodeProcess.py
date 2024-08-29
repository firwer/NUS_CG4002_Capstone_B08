import config
from comms.MQTTController import MQTTController


def start_relay_mqtt_client_process(relay_mqtt_to_engine_queue, engine_to_relay_mqtt_queue):
    ec = RelayMQTTClientProcess(relay_mqtt_to_engine_queue)
    ec.mqttc.mqttc.loop_start()
    while True:
        t = engine_to_relay_mqtt_queue.get()
        ec.mqttc.publish(config.MQTT_ENGINE_TO_RELAY, t)


class RelayMQTTClientProcess:
    def __init__(self, relay_mqtt_to_engine_queue):
        self.relay_mqtt_to_engine_queue = relay_mqtt_to_engine_queue
        self.mqttc = MQTTController(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, relay_mqtt_to_engine_queue, None)
        self.mqttc.subscribe(config.MQTT_SENSOR_DATA_PLAYER1)
        print("Relay MQTT Client Process started.")
