from multiprocessing import Queue

from sshtunnel import SSHTunnelForwarder

import config
from comms.MQTTController import MQTTController


def main():
    receiver_queue = Queue()
    if config.RELAY_NODE_LOCAL_TEST:
        print("DEV: LOCAL RELAY NODE TEST RUN")
        print("DEV: Starting MQTT Client")
        mqttc = MQTTController(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)
        mqttc.mqttc.loop_start()
        mqttc.mqttc.subscribe(config.MQTT_ENGINE_TO_RELAY)
        print(f"DEV: Subscribed to topic {config.MQTT_ENGINE_TO_RELAY}")
    else:
        print("PRODUCTION RUN")
        print("PROD: SSH Tunneling to Ultra96")
        server = SSHTunnelForwarder(
            ssh_host=config.ssh_host,
            ssh_username=config.ssh_user,
            ssh_password=config.ssh_password,
            remote_bind_address=(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)
        )
        server.start()

        print(f"Forwarding port {server.local_bind_port} to broker port {config.MQTT_BROKER_PORT}")
        print("PROD: Starting MQTT Client")
        mqttc = MQTTController(config.MQTT_BROKER_HOST, server.local_bind_port, receiver_queue)

    while True:
        message = input("Input message: ")
        mqttc.publish(config.MQTT_SENSOR_DATA_PLAYER1, f"{message}")
        #msg = receiver_queue.get()
        #print(f"Received message: {msg}")

    server.stop()


if __name__ == "__main__":
    main()
