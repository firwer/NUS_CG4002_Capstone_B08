import asyncio
import datetime
from multiprocessing import Queue
import os, sys
from sshtunnel import SSHTunnelForwarder

import config
from comms.AsyncMQTTController import AsyncMQTTController


async def user_input(send_queue: asyncio.Queue, receive_queue: asyncio.Queue):
    while True:
        message = input("Input message: ")
        await send_queue.put(message)
        msg = await receive_queue.get()
        print(f"Received message: {msg}")


async def run_mqtt_client(mqttc, send_topic, receive_topic):
    try:
        await mqttc.start_duplex_comms(send_topic, receive_topic)
    except Exception as e:
        print(f"Error in Relay Node MQTT client Connection: {e}")
        await mqttc.connect()  # Attempt to reconnect


async def main():
    send_queue = asyncio.Queue()
    receive_queue = asyncio.Queue()
    if config.RELAY_NODE_LOCAL_TEST:
        print("DEV: LOCAL RELAY NODE TEST RUN")
        print("DEV: Starting MQTT Client")
        mqttc = AsyncMQTTController(config.MQTT_BROKER_PORT, receive_queue, send_queue)
    else:
        print("PROD: PRODUCTION RUN")
        print("PROD: SSH Tunneling to Ultra96")
        server = SSHTunnelForwarder(
            ssh_host=config.ssh_host,
            ssh_username=config.ssh_user,
            ssh_password=config.ssh_password,
            remote_bind_address=(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)
        )
        server.start()

        print(f"PROD: Forwarding port {server.local_bind_port} to broker port {config.MQTT_BROKER_PORT}")
        print("PROD: Starting MQTT Client")
        mqttc = AsyncMQTTController(server.local_bind_port, receive_queue, send_queue)

    mqtt_p1 = asyncio.create_task(mqttc.start(send_topic=config.MQTT_SENSOR_DATA_RELAY_TO_ENG_P1,
                                              receive_topic=config.MQTT_SENSOR_DATA_ENG_TO_RELAY_P1))
    # mqtt_p2 = asyncio.create_task(mqttc.start(send_topic=config.MQTT_SENSOR_DATA_RELAY_TO_ENG_P2,
    #                                             receive_topic=config.MQTT_SENSOR_DATA_ENG_TO_RELAY_P2))
    debug_input = asyncio.create_task(user_input(send_queue, receive_queue))
    #debug_output = asyncio.create_task(data_output(receive_queue))
    await asyncio.gather(mqtt_p1, debug_input)
    server.stop()


if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(main())
