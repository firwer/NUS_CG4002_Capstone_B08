import asyncio
import aiomqtt
import config


async def start_relay_mqtt_client_process(relay_mqtt_to_engine_queue, engine_to_relay_mqtt_queue):
    client = aiomqtt.Client(hostname=config.MQTT_BROKER_HOST, port=config.MQTT_BROKER_PORT)
    async with client:
        await client.subscribe(config.MQTT_SENSOR_DATA_PLAYER1)
        async for message in client.messages:
            if message.topic.matches(config.MQTT_SENSOR_DATA_PLAYER1):
                await relay_mqtt_to_engine_queue.put(message.payload)
