PACKET_ACK = 0x1
PACKET_SYN_ACK = 0x2
PACKET_DATA_IMU = 0x3
PACKET_DATA_KICK = 0x4
PACKET_DATA_BULLET = 0x5
PACKET_DATA_HEALTH = 0x6
PACKET_DATA_GAMESTATE = 0x7
PACKET_CONN_ESTAB = 0xD
PACKET_INVALID = 0xE
PACKET_HELLO = 0xF


def get_packettype_string(packet_type):
    """Takes in a byte and returns the associated type"""
    if packet_type == PACKET_DATA_HEALTH:
        return "Health"
    elif packet_type == PACKET_DATA_KICK:
        return "Kick"
    elif packet_type == PACKET_DATA_BULLET:
        return "Bullet"
    elif packet_type == PACKET_DATA_IMU:
        return "IMU"
    return "Unknown"


def get_packet(bytearray: bytearray):
    """Convert the bytearray a PacketClass and returns it."""
    pkt_typ = bytearray[0]  # Extract the first byte to determine the packet type
    if pkt_typ == PACKET_HELLO:
        return PacketHello(bytearray)
    elif pkt_typ == PACKET_SYN_ACK:
        return PacketSynAck(bytearray)
    elif pkt_typ == PACKET_ACK:
        return PacketAck(bytearray)
    elif pkt_typ == PACKET_DATA_HEALTH:
        return PacketHealth(bytearray)
    elif pkt_typ == PACKET_DATA_BULLET:
        return PacketBullet(bytearray)
    elif pkt_typ == PACKET_DATA_KICK:
        return PacketKick(bytearray)
    elif pkt_typ == PACKET_DATA_IMU:
        return PacketImu(bytearray)
    else:
        # print(f"err: unknown packet type: {pkt_typ}, {bytearray.hex()}")
        return PacketInvalid()


class PacketInvalid():
    def __init__(self) -> None:
        self.packet_type = PACKET_INVALID


class PacketAck():
    def __init__(self, byteArray=None) -> None:
        self.packet_type = PACKET_ACK
        if byteArray is None:
            self.seq_num = 0
            self.padding = bytearray(17)
            self.crc8 = 0x0
        else:
            self.seq_num = byteArray[1]
            self.padding = byteArray[2:19]
            self.crc8 = byteArray[19]

    def to_bytearray(self) -> bytearray:
        byte_array = bytearray()
        byte_array.append(self.packet_type)
        byte_array.append(self.seq_num)
        byte_array.extend(self.padding)
        byte_array.append(self.crc8)
        return byte_array


class PacketConnEstab():
    def __init__(self, byteArray=None) -> None:
        self.packet_type = PACKET_CONN_ESTAB
        if byteArray is None:
            self.seq_num = 0
            self.padding = bytearray(17)
            self.crc8 = 0x0
        else:
            self.seq_num = byteArray[1]
            self.padding = byteArray[2:19]
            self.crc8 = byteArray[19]

    def to_bytearray(self) -> bytearray:
        byte_array = bytearray()
        byte_array.append(self.packet_type)
        byte_array.append(self.seq_num)
        byte_array.extend(self.padding)
        byte_array.append(self.crc8)
        return byte_array


class PacketSynAck():
    def __init__(self, byteArray=None) -> None:
        self.packet_type = PACKET_SYN_ACK
        if byteArray is None:
            self.seq_num = 0
            self.padding = bytearray(17)
            self.crc8 = 0x0
        else:
            self.seq_num = byteArray[1]
            self.padding = byteArray[2:19]
            self.crc8 = byteArray[19]

    def to_bytearray(self) -> bytearray:
        byte_array = bytearray()
        byte_array.append(self.packet_type)
        byte_array.append(self.seq_num)
        byte_array.extend(self.padding)
        byte_array.append(self.crc8)
        return byte_array


class PacketHello():
    def __init__(self, byteArray=None) -> None:
        self.packet_type = PACKET_HELLO
        if byteArray is None:
            self.seq_num = 0
            self.padding = bytearray(17)
            self.crc8 = 0x0
        else:
            self.seq_num = byteArray[1]
            self.padding = byteArray[2:19]
            self.crc8 = byteArray[19]

    def to_bytearray(self) -> bytearray:
        byte_array = bytearray()
        byte_array.append(self.packet_type)
        byte_array.append(self.seq_num)
        byte_array.extend(self.padding)
        byte_array.append(self.crc8)
        return byte_array


class PacketHealth():
    def __init__(self, byteArray=None) -> None:
        self.packet_type = PACKET_DATA_HEALTH
        if byteArray is None:
            self.seq_num = 0x0
            self.health = 0x0
            self.shield = 0x0
            self.padding = bytearray(15)
            self.crc8 = 0x0
        else:
            self.seq_num = byteArray[1]
            self.health = byteArray[2]
            self.shield = byteArray[3]
            self.padding = byteArray[4:19]
            self.crc8 = byteArray[19]

    def to_bytearray(self) -> bytearray:
        byte_array = bytearray()
        byte_array.append(self.packet_type)
        byte_array.append(self.seq_num)
        byte_array.append(self.health)
        byte_array.append(self.shield)
        byte_array.extend(self.padding)
        byte_array.append(self.crc8)
        return byte_array


class PacketBullet():
    def __init__(self, byteArray=None) -> None:
        self.packet_type = PACKET_DATA_BULLET
        if byteArray is None:
            self.seq_num = 0x0
            self.bullet = 0x0
            self.padding = bytearray(16)
            self.crc8 = 0x0
        else:
            self.seq_num = byteArray[1]
            self.bullet = byteArray[2]
            self.padding = byteArray[3:19]
            self.crc8 = byteArray[19]

    def to_bytearray(self) -> bytearray:
        byte_array = bytearray()
        byte_array.append(self.packet_type)
        byte_array.append(self.seq_num)
        byte_array.append(self.bullet)
        byte_array.extend(self.padding)
        byte_array.append(self.crc8)
        return byte_array


class PacketKick():
    def __init__(self, byteArray=None) -> None:
        self.packet_type = PACKET_DATA_KICK
        if byteArray is None:
            self.seq_num = 0x0
            self.padding = bytearray(17)
            self.crc8 = 0x0
        else:
            self.seq_num = byteArray[1]
            self.padding = byteArray[2:19]
            self.crc8 = byteArray[19]

    def to_bytearray(self) -> bytearray:
        byte_array = bytearray()
        byte_array.append(self.packet_type)
        byte_array.append(self.seq_num)
        byte_array.extend(self.padding)
        byte_array.append(self.crc8)
        return byte_array


class PacketImu():
    def __init__(self, byteArray=None) -> None:
        self.packet_type = PACKET_DATA_IMU
        if byteArray is None:
            self.seq_num = 0x0
            self.adc = 0x0
            self.accelX = bytearray(2)
            self.accelY = bytearray(2)
            self.accelZ = bytearray(2)
            self.gyroX = bytearray(2)
            self.gyroY = bytearray(2)
            self.gyroZ = bytearray(2)
            self.padding = bytearray(4)
            self.crc8 = 0x0
        else:
            self.seq_num = byteArray[1]
            self.adc = byteArray[2]
            self.accelX = byteArray[3:5]
            self.accelY = byteArray[5:7]
            self.accelZ = byteArray[7:9]
            self.gyroX = byteArray[9:11]
            self.gyroY = byteArray[11:13]
            self.gyroZ = byteArray[13:15]
            self.padding = byteArray[15:19]
            self.crc8 = byteArray[19]

    def to_bytearray(self) -> bytearray:
        byte_array = bytearray()
        byte_array.append(self.packet_type)
        byte_array.append(self.seq_num)
        byte_array.append(self.adc)
        byte_array.extend(self.accelX)
        byte_array.extend(self.accelY)
        byte_array.extend(self.accelZ)
        byte_array.extend(self.gyroX)
        byte_array.extend(self.gyroY)
        byte_array.extend(self.gyroZ)
        byte_array.extend(self.padding)
        byte_array.append(self.crc8)
        return byte_array


class PacketGamestate():
    def __init__(self, byteArray=None) -> None:
        self.packet_type = PACKET_DATA_GAMESTATE
        if byteArray is None:
            self.seq_num = 0x0
            self.bullet = 0x0
            self.health = 0x0
            self.shield = 0x0
            self.padding = bytearray(14)
            self.crc8 = 0x0
        else:
            self.seq_num = byteArray[1]
            self.bullet = byteArray[2]
            self.health = byteArray[3]
            self.shield = byteArray[4]
            self.padding = byteArray[5:19]
            self.crc8 = byteArray[19]

    def to_bytearray(self) -> bytearray:
        byte_array = bytearray()
        byte_array.append(self.packet_type)
        byte_array.append(self.seq_num)
        byte_array.append(self.bullet)
        byte_array.append(self.health)
        byte_array.append(self.shield)
        byte_array.extend(self.padding)
        byte_array.append(self.crc8)
        return byte_array
