# Relay Node Configuration
RELAY_NODE_LOCAL_TEST = True  # Set to True for local env relay node testing

# Evaluation Server Configurations
EVAL_SERVER_HOST = '127.0.0.1'
EVAL_SECRET_KEY = "bitcoingoingmoon"

# Ultra96 TCP Server Configuration
TCP_SERVER_HOST = "127.0.0.1"
TCP_SERVER_PORT = 12345
TCP_SECRET_KEY = "ethgoingmoon"

# Ultra96 SSH Credentials
ssh_host = "172.26.190.125"
ssh_user = "xilinx"
ssh_password = "leonardo"  # Add password here

# MQTT Broker Configurations
MQTT_BROKER_HOST = "35.247.174.182"
MQTT_BROKER_PORT = 1884
MQTT_QOS = 1  # Lower values mean less reliability but faster communication

MQTT_SENSOR_DATA_RELAY_TO_ENG_P1 = "sensor_data/p1/relay_to_engine"
MQTT_SENSOR_DATA_ENG_TO_RELAY_P1 = "sensor_data/p1/engine_to_relay"

MQTT_SENSOR_DATA_RELAY_TO_ENG_P2 = "sensor_data/p2/relay_to_engine"
MQTT_SENSOR_DATA_ENG_TO_RELAY_P2 = "sensor_data/p2/engine_to_relay"

MQTT_ENG_TO_VISUALIZER = "game_state/engine_to_visualizer"
MQTT_VISUALIZER_TO_ENG = "game_state/visualizer_to_engine"

MQTT_ENGINE_TO_RELAY = "sensor_data/return"

# MQTT Broker Exponential Backoff Recovery Config
FIRST_RECONNECT_DELAY = 1
MAX_RECONNECT_COUNT = 5
RECONNECT_RATE = 2
MAX_RECONNECT_DELAY = 60

# Game Player Max Attribute Configurations
GAME_MAX_BOMBS = 2
GAME_MAX_SHIELDS = 3
GAME_MAX_SHIELD_HEALTH = 30
GAME_MAX_BULLETS = 6
GAME_MAX_HP = 100

# Game Action Effects
GAME_BULLET_DMG = 5  # the hp reduction for bullet
GAME_AI_DMG = 10  # the hp reduction for AI action
GAME_BOMB_DMG = 5
GAME_RAIN_DMG = 5
