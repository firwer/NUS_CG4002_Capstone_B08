# Relay Node Configuration
RELAY_NODE_LOCAL_TEST = True  # Set to True for local env relay node testing

# Evaluation Server Configurations
serverName = '127.0.0.1'
secret_key = "bitcoingoingmoon"

# Ultra96 SSH Credentials
ssh_host = "172.26.190.125"
ssh_user = "xilinx"
ssh_password = "leonardo"  # Add password here

# MQTT Broker Configurations
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1884
MQTT_QOS = 1  # Lower values mean less reliability but faster communication

MQTT_SENSOR_DATA_PLAYER1 = "sensor_data/player1"
MQTT_SENSOR_DATA_PLAYER2 = "sensor_data/player2"

MQTT_ENGINE_TO_RELAY = "sensor_data/return"

# MQTT Broker Exponential Backoff Recovery Config
FIRST_RECONNECT_DELAY = 1
MAX_RECONNECT_COUNT = 5
RECONNECT_RATE = 2
MAX_RECONNECT_DELAY = 60
