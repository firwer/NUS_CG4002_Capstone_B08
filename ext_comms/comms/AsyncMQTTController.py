import asyncio

import aiomqtt

import config


class AsyncMQTTController:
    """
        Class to handle asynchronous MQTT communication with the visualizers
    """

    mqttc: aiomqtt.Client
    send_data_queue: asyncio.Queue

    def __init__(self, mqtt_port, receive_queue_p1=None, receive_queue_p2=None, send_queue=None):
        self.mqtt_port = mqtt_port
        self.receive_data_queue_p1 = receive_queue_p1 or asyncio.Queue()
        self.receive_data_queue_p2 = receive_queue_p2 or asyncio.Queue()
        self.send_data_queue = send_queue or asyncio.Queue()
        self.connected = False

    async def run_tasks(self, receive_topic_p1: str, receive_topic_p2: str, send_topic: str):
        try:
            async with (aiomqtt.Client(hostname=config.MQTT_BROKER_HOST, port=self.mqtt_port,
                                       username=config.MQTT_GAME_ENGINE_USER, password=config.MQTT_GAME_ENGINE_PASS)
                        as client):
                self.mqttc = client
                self.connected = True
                listen_task = asyncio.create_task(self.listen(receive_topic_p1, receive_topic_p2))
                publish_task = asyncio.create_task(self.publish_loop(send_topic))
                await asyncio.gather(listen_task, publish_task)
        except (aiomqtt.MqttError, aiomqtt.MqttCodeError) as e:
            print(f"Error in tasks: {e}")
            self.connected = False
            raise e  # This will break and allow to reconnect

    async def start(self, receive_topic_p1: str, receive_topic_p2: str, send_topic: str):
        attempt = 0
        delay = 1  # Start with 1-second delay
        max_retries = 10

        while attempt < max_retries:
            try:
                await self.run_tasks(receive_topic_p1, receive_topic_p2, send_topic)
            except (aiomqtt.MqttError, aiomqtt.MqttCodeError) as e:
                print(f"Error occurred: {e}, retrying connection...")
                attempt += 1
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)  # Exponential backoff
            except Exception as e:
                print(f"Unexpected error: {e}")
                break

        print("Max retries reached. Could not connect to MQTT broker.")
        raise ConnectionError("Failed to connect to MQTT broker after retries")

    async def listen(self, topic_receive_p1: str, topic_receive_p2 : str):
        print(f"Subscribing to topic: {topic_receive_p1}")
        print(f"Subscribing to topic: {topic_receive_p2}")
        await self.mqttc.subscribe(topic_receive_p1)
        await self.mqttc.subscribe(topic_receive_p2)
        print("Listening for messages...")
        async for message in self.mqttc.messages:
            if message.topic.matches(topic_receive_p1):
                await self.receive_data_queue_p1.put(message.payload)
            elif message.topic.matches(topic_receive_p2):
                await self.receive_data_queue_p2.put(message.payload)

    async def publish_loop(self, topic_send: str):
        while self.connected:
            try:
                print("Waiting for message to send...")
                msg = await self.send_data_queue.get()
                print(f"Publishing message: {msg}")
                await self.mqttc.publish(topic_send, msg)
                print(f"Published message: {msg}")
            except (aiomqtt.MqttError, aiomqtt.MqttCodeError) as e:
                self.connected = False
                raise e
