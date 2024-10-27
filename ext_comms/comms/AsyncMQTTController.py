import asyncio
import aiomqtt
from logger_config import setup_logger
import config

logger = setup_logger(__name__)

class AsyncMQTTController:
    """
    Class to handle asynchronous MQTT communication with the visualizers.
    """

    def __init__(self, mqtt_port, receive_queue_p1=None, receive_queue_p2=None, send_queue=None):
        self.mqtt_port = mqtt_port
        self.receive_data_queue_p1 = receive_queue_p1 or asyncio.Queue()
        self.receive_data_queue_p2 = receive_queue_p2 or asyncio.Queue()
        self.send_data_queue = send_queue or asyncio.Queue()
        self.connected = False
        self.mqttc = None

    async def run_tasks(self, receive_topic_p1: str, receive_topic_p2: str, send_topic: str):
        try:
            async with aiomqtt.Client(
                hostname=config.MQTT_BROKER_HOST,
                port=self.mqtt_port,
                username=config.MQTT_GAME_ENGINE_USER,
                password=config.MQTT_GAME_ENGINE_PASS
            ) as client:
                self.mqttc = client
                self.connected = True
                logger.info("Connected to MQTT broker.")

                listen_task = asyncio.create_task(self.listen(receive_topic_p1, receive_topic_p2))
                publish_task = asyncio.create_task(self.publish_loop(send_topic))
                await asyncio.gather(listen_task, publish_task)
        except (aiomqtt.MqttError, aiomqtt.MqttCodeError) as e:
            logger.error(f"MQTT error in run_tasks: {e}")
            self.connected = False
            raise e  # Allow higher-level handlers to manage reconnection
        except Exception as e:
            logger.exception(f"Unexpected error in run_tasks: {e}")

    async def start(self, receive_topic_p1: str, receive_topic_p2: str, send_topic: str):
        attempt = 0
        delay = 1  # Start with 1-second delay
        max_retries = 10

        while attempt < max_retries:
            try:
                logger.info(f"Attempting to connect to MQTT broker (Attempt {attempt + 1}/{max_retries})...")
                await self.run_tasks(receive_topic_p1, receive_topic_p2, send_topic)
            except (aiomqtt.MqttError, aiomqtt.MqttCodeError) as e:
                logger.error(f"MQTT connection error: {e}. Retrying in {delay} seconds...")
                attempt += 1
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)  # Exponential backoff
            except Exception as e:
                logger.exception(f"Unexpected error in MQTT start: {e}")
                break

        logger.critical("Max MQTT connection retries reached. Could not connect to MQTT broker.")
        raise ConnectionError("Failed to connect to MQTT broker after maximum retries.")

    async def listen(self, topic_receive_p1: str, topic_receive_p2: str):
        logger.info(f"Subscribing to topics: {topic_receive_p1}, {topic_receive_p2}")
        await self.mqttc.subscribe(topic_receive_p1)
        await self.mqttc.subscribe(topic_receive_p2)
        logger.info("Subscribed to MQTT topics. Listening for messages...")

        async for message in self.mqttc.messages:
                try:
                    if message.topic == topic_receive_p1:
                        await self.receive_data_queue_p1.put(message.payload.decode())
                        logger.debug(f"Received message on {topic_receive_p1}: {message.payload.decode()}")
                    elif message.topic == topic_receive_p2:
                        await self.receive_data_queue_p2.put(message.payload.decode())
                        logger.debug(f"Received message on {topic_receive_p2}: {message.payload.decode()}")
                    else:
                        logger.warning(f"Received message on unexpected topic {message.topic}: {message.payload.decode()}")
                except Exception as e:
                    logger.exception(f"Error processing received MQTT message: {e}")

    async def publish_loop(self, topic_send: str):
        logger.info(f"Starting MQTT publish loop for topic: {topic_send}")
        while self.connected:
            try:
                logger.debug("Waiting for message to send to MQTT...")
                msg = await self.send_data_queue.get()
                await self.mqttc.publish(topic_send, msg)
                logger.info(f"Published message to {topic_send}: {msg}")
            except (aiomqtt.MqttError, aiomqtt.MqttCodeError) as e:
                logger.error(f"MQTT publish error: {e}. Disconnecting publish loop.")
                self.connected = False
                raise e
            except Exception as e:
                logger.exception(f"Unexpected error in publish_loop: {e}")

    async def broadcast_message(self, message: str, topic_send: str):
        """Optional helper to publish a message to a specific topic."""
        try:
            await self.mqttc.publish(topic_send, message)
            logger.info(f"Broadcasted message to {topic_send}: {message}")
        except Exception as e:
            logger.exception(f"Failed to broadcast message: {e}")
