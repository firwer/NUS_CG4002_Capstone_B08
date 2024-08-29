import queue
import time
from multiprocessing import Queue

import config
import paho.mqtt.client as mqtt


class MQTTController:
    mqttc: mqtt.Client
    p1_data_queue: queue
    p2_data_queue: queue

    def __init__(self, host, port, p1_queue=Queue(), p2_queue=Queue()):
        self.p1_data_queue = p1_queue
        self.p2_data_queue = p2_queue
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect
        self.mqttc.on_message = self.on_message
        self.mqttc.connect(host, port, 60)

    def on_disconnect(self, client, userdata, rc, *extra_args):
        print("Disconnected with result code: %s", rc)
        reconnect_count, reconnect_delay = 0, config.FIRST_RECONNECT_DELAY
        while reconnect_count < config.MAX_RECONNECT_COUNT:
            print(f"Reconnecting in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)
            try:
                self.mqttc.reconnect()
                print("Reconnected successfully!")
                return
            except Exception as err:
                print("%s. Reconnect failed. Retrying...", err)

            reconnect_delay *= config.RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, config.MAX_RECONNECT_DELAY)
            reconnect_count += 1
        print(f"Reconnect failed after {reconnect_count} attempts. Exiting...")

    def on_connect(self, client, userdata, flags, rc, *extra_args):
        print(f"Connected to MQTT Broker Successfully!")
        if rc == 0:
            print("Connection established successfully.")
            self.subscribe(config.MQTT_SENSOR_DATA_PLAYER1)
        else:
            print(f"Connection failed with result code {rc}")

    def on_message(self, client, userdata, msg):
        if msg.topic == config.MQTT_ENGINE_TO_RELAY:
            print("pushing to relay")
            self.p1_data_queue.put(msg.payload)
        elif msg.topic == config.MQTT_SENSOR_DATA_PLAYER1:
            print("pushing to p1")
            self.p1_data_queue.put(msg.payload)
        elif msg.topic == config.MQTT_SENSOR_DATA_PLAYER2:
            self.p2_data_queue.put(msg.payload)
        else:
            print(f"Received message {msg.payload} from unknown topic {msg.topic}.")

    def publish(self, topic, message):
        msg_info = self.mqttc.publish(topic, message, qos=config.MQTT_QOS)
        if msg_info.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"Failed to publish message to topic {topic}.")
            return

    def subscribe(self, topic):
        e, _ = self.mqttc.subscribe(topic)
        if e != mqtt.MQTT_ERR_SUCCESS:
            print(f"Failed to subscribe to topic {topic}.")
            return
        print(f"Subscribed to topic {topic}")

    def loop_forever(self):
        self.mqttc.loop_forever()