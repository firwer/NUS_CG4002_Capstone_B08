import time
from bluepy import btle
from packet import * 
from checksum import *
import threading

BLUNO_MAC_ADDRESS = "F4:B8:5E:42:4C:BB"
CHARACTERISTIC_UUID = "0000dfb1-0000-1000-8000-00805f9b34fb"  # Correct characteristic UUID
TIMEOUT_MS = 1000

class NotifyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.buffer = bytearray()
        self.buffer_len = len(self.buffer)
        self.lock = threading.Lock()  # Lock to manage concurrency

    def handleNotification(self, cHandle, data: bytes):
        # print(f"Got a notification: {len(data)}: {data.hex()}")
        # TODO: write the fragmentation logic here and count fragments
        self.buffer += bytearray(data)

    def has_packet(self) -> bool:
        return len(self.buffer) >= 20

    def get_packet_bytes(self) -> bytearray | None:
        """returns a 20B bytearray representing a packet from the buffer. else, None"""
        if not self.has_packet():
            return None
        data = self.buffer[:20]
        self.buffer = self.buffer[20:]
        # print(len(self.buffer)//20)
        return data
    
    def reset_buffer(self):
        data = bytearray()

# A beetle object maintains its own connection and state
class Beetle:
    def __init__(self, MAC_ADDRESS) -> None:
        self.relay_seq_num = 0
        self.beetle_seq_num = 0 # expected number
        self.MAC = MAC_ADDRESS
        self.chr = CHARACTERISTIC_UUID
        self.connected = False
        self.receiver = NotifyDelegate()
        self.errors = 0
        self.peripheral = None

    def run(self):
        while True:
            if not self.connected or self.errors > 2:
                print(f"Restarting connection: {self.connected}, {self.errors}")
                self.receiver.reset_buffer()
                self.errors = 0
                self.connect_to_beetle()
                continue
            # Collect notifications
            try:
                # print("Waiting for notifications...")
                self.peripheral.waitForNotifications(1)
            except Exception as e:
                print(f"Device disconnected {e}. Re-connecting...")
                self.connected = False
                continue
            # TODO: check if have things to send
            # Otherwise, receive...
            shouldConnEstab = True
            ackNum = -1 # track the largest reliable ack num rcv
            latestPacket = None
            # print(f"{len(self.receiver.buffer)}")
            while(self.receiver.has_packet()):
                if self.errors > 3:
                    break

                data = self.receiver.get_packet_bytes()
                # data should be hex
                # check for incomplete data
                # print(data.hex())
                if not verify_checksum(data):
                    print(f"err: checksum failed for PKT {self.beetle_seq_num}")
                    self.errors += 1
                    print(f"Moving to next packet in buffer...")
                    continue

                pkt = get_packet(data)

                # check what kind of packet
                if pkt.packet_type == PACKET_SYN_ACK:
                    print("skipping due to SYN ACK")
                    continue

                # if we get normal data packets, then no need to comm_estab
                shouldConnEstab = False
                # Is unreliable send
                if pkt.packet_type == PACKET_DATA_IMU:
                    # do work
                    print(f"PKT {pkt.seq_num}")
                    continue

                # Is reliable packet
                if pkt.packet_type == PACKET_DATA_HEALTH: # or ...
                    latestPacket = pkt
                    self.beetle_seq_num = max(self.beetle_seq_num, pkt.seq_num + 1)
                    ackNum = pkt.seq_num 
                    print(f"RCV PKT {latestPacket.seq_num}, {latestPacket.health}")

            # handle post-buffer drain actions
            if shouldConnEstab:
                resp = PacketConnEstab()
                resp.seq_num = self.relay_seq_num
                resp.crc8 = get_checksum(resp.to_bytearray())
                self.write_packet(resp)
            if ackNum == -1:
                continue
            # we received an 
            resp = PacketAck()
            resp.seq_num = (ackNum + 1) % 256
            resp.crc8 = get_checksum(resp.to_bytearray())
            self.write_packet(resp)
            # finally, deal with the packet
            if latestPacket is not None:
                print(f"ACK {resp.seq_num}, for PKT {latestPacket.seq_num}, {latestPacket.health}")
            else:
                print(f"ACK {resp.seq_num}")


    def bytes_to_packet(self, bytearray):
        """takes a 20B bytearray, CRC8 checks, then wraps it in the packet class.
        returns Packet() is OK, else a PacketInvalid
        """
        # print("Received data:", bytearray.hex())
        # TODO: consider if a None would be faster
        if not verify_checksum(bytearray):
            print("err: checksum failed")
            return PacketInvalid()
        return get_packet(bytearray)

    def write_packet(self, packet):
        try:
            self.chr.write(packet.to_bytearray())
        except Exception as e:
            print(f"Error writing, {e}")
            self.connected = False

    def get_notifications(self, timeout=1.5):
        try:
            return self.peripheral.waitForNotifications(timeout)
        except Exception as e:
            print(f"Error getting notif: {e}")
            self.connected = False
            return False

    def reset_bluepy(self):
        if self.peripheral is not None:
            # print("Disconnecting")
            self.peripheral.disconnect()
            self.peripheral = None

        while(self.peripheral is None):
            try:
                self.peripheral = btle.Peripheral(BLUNO_MAC_ADDRESS)
                self.peripheral.setDelegate(self.receiver)
                self.chr = self.peripheral.getCharacteristics(uuid=CHARACTERISTIC_UUID)[0]
                print("Setup!")
                break
            except Exception as e: # keep trying
                print(f"peripheral fail: {e}")
                continue

    def connect_to_beetle(self):
        """blocking 3 way handshake"""
        self.reset_bluepy()
        print("THREE WAY START")
        while(1):
            if self.connected == False:
                self.reset_bluepy()
            # STAGE 1: Hello
            pkt = PacketHello()
            pkt.seq_num = self.relay_seq_num
            pkt.crc8 = get_checksum(pkt.to_bytearray())
            print("THREE WAY: Sending HELLO")
            self.write_packet(pkt)

            # STAGE 2: SYN-ACK wait
            print("THREE WAY: Wait SYN-ACK")
            hasSynAck = False
            if(self.get_notifications(1)): # cannot set too low
                while self.receiver.has_packet():
                    data = self.receiver.get_packet_bytes()
                    if data is None:
                        print("data not exist")
                        continue
                    if not verify_checksum(data):
                        print(f"checksum fail {data.hex()}")
                        continue
                    packet = get_packet(data)
                    if packet is None:
                        print("packet type unknown")
                        continue
                    if packet.packet_type != PACKET_SYN_ACK:
                        print("non SYNACK received")
                        continue
                    # syn-ack received
                    self.beetle_seq_num = pkt.seq_num
                    hasSynAck = True
                    print("SYN-ACK received")
            else:
                print("Timeout: SYN-ACK not received.")
                continue  # Retry the handshake
            if not hasSynAck:
                continue
            # STAGE 3: CONN_ESTAB
            resp = PacketConnEstab()
            resp.seq_num = self.relay_seq_num
            resp.crc8 = get_checksum(resp.to_bytearray())
            print(f"THREE WAY: ACK")
            self.write_packet(resp)
            self.connected = True
            break  # Exit the loop after successful connection
        print("Connection established.")
        
    def print_packet(self, packet):
        print(f"PKT: {packet.packet_type}, {packet.seq_num}")

def discover_services_and_characteristics(bluno):
    print("Discovering services and characteristics...")
    for service in bluno.getServices():
        print(f"Service: {service.uuid}")
        for char in service.getCharacteristics():
            print(f"Characteristic: {char.uuid} (Handle: {char.getHandle()})")

def main():
    beetle = Beetle(BLUNO_MAC_ADDRESS)
    beetle.run()

if __name__ == "__main__":
    main()
