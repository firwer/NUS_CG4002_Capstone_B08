import random
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

        # reliable gamestate send
        self.bullets = 10
        self.health = 20
        self.sendReliableStart = 0
        self.cachedPacket = None
        self.repeatedReliableSend = 0

    def run(self):
        canSendReliable = True
        while True:
            shouldAck = False

            if not self.connected or self.errors > 2 or self.repeatedReliableSend > 2:
                print(f"Restarting connection: {self.connected}, {self.errors}")
                self.receiver.reset_buffer()
                self.errors = 0
                self.repeatedReliableSend = 0
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
               
            # STEP 1: RECEIVE DATA WHERE APPLICABLE 
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
                    print(f"err: checksum failed for PKT b{self.beetle_seq_num}")
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
                    print(f"RCV PKT b{pkt.seq_num} (udp)")
                    continue

                # Is reliable packet
                if pkt.packet_type == PACKET_DATA_HEALTH: # or ...
                    latestPacket = pkt
                    self.beetle_seq_num = max(self.beetle_seq_num, pkt.seq_num + 1)
                    ackNum = pkt.seq_num 
                    print(f"RCV PKT b{latestPacket.seq_num}, {latestPacket.health}")

                # Is an ACK
                if pkt.packet_type == PACKET_ACK:
                    # is the ACK what we expected?
                    print(f"RCV PKT r{pkt.seq_num}, curr r{self.relay_seq_num}")
                    if pkt.seq_num == (self.relay_seq_num + 1) % 256:
                        # We got the ack we wanted!
                        # canSendReliable implies that no more unacked pkt is in-flight
                        self.relay_seq_num = (self.relay_seq_num + 1 % 256)
                        canSendReliable = True


            # STEP 2: HANDLE POST-BUFFER DRAIN ACTIONS
            # handle post-buffer drain actions
            if shouldConnEstab:
                resp = PacketConnEstab()
                resp.seq_num = self.relay_seq_num
                resp.crc8 = get_checksum(resp.to_bytearray())
                self.write_packet(resp)
            if shouldAck and ackNum != -1:
                # we received an ACK-able data
                resp = PacketAck()
                resp.seq_num = (ackNum + 1) % 256
                resp.crc8 = get_checksum(resp.to_bytearray())
                self.write_packet(resp)
                # finally, deal with the packet
                if latestPacket is not None:
                    print(f"RX ACK {resp.seq_num}, for PKT {latestPacket.seq_num}, {latestPacket.health}")
                else:
                    print(f"RX ACK {resp.seq_num} (dup)")
            
            # STEP 3: SEND DATA 
            if canSendReliable:
                sendPkt = self.getDataToSend()
                if sendPkt is not None:
                    self.cachedPacket = sendPkt
                    sendPkt = self.corrupt_packet(sendPkt) # WARN: should be removed in prod
                    self.sendReliableStart = time.time()
                    print(f"TX PKT r{sendPkt.seq_num}, curr r{self.relay_seq_num}")
                    self.write_packet(sendPkt)
                    canSendReliable = False
            elif time.time() - self.sendReliableStart > 1:  # 1000 ms = 1 second
                self.repeatedReliableSend += 1
                self.sendReliableStart = time.time()
                print(f"TX PKT r{self.cachedPacket.seq_num}, curr {self.relay_seq_num}, {self.cachedPacket.to_bytearray().hex()}")
                sendPkt = self.cachedPacket
                sendPkt = self.corrupt_packet(sendPkt) # WARN: should be removed in prod
                self.write_packet(sendPkt)
                canSendReliable = False


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
            print(f"THREE WAY: Sending HELLO r{self.relay_seq_num}")
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
        
    def getDataToSend(self):
        """Check if there is data to send to the beetle. Returns a packet if so, else None"""
        # Create a PacketGamestate instance
        pkt = PacketGamestate()
        pkt.seq_num = self.relay_seq_num
        pkt.bullet = max(0, min(255, self.bullets))  # Clamp between 0 and 255
        pkt.health = max(0, min(255, self.health))   # Clamp between 0 and 255
        self.bullets = max(0, self.bullets - 1)
        self.health = max(0, self.health - 1)
        pkt.crc8 = get_checksum(pkt.to_bytearray())
        return pkt

    def corrupt_packet(self, pkt):
        """Corrupt a gamestate packet for testing purposes"""
        if random.random() < 0.5:  # 10% chance
            print("Corrupting packet...")
            byte_array = pkt.to_bytearray()
            byte_to_corrupt = random.randint(0, len(byte_array) - 1)  # Pick a random byte
            bit_to_flip = 1 << random.randint(0, 7)  # Pick a random bit to flip (0-7)
            byte_array[byte_to_corrupt] ^= bit_to_flip  # XOR the bit to flip it
            # Update the packet with the corrupted byte array
            pkt = PacketGamestate(byte_array)
        return pkt

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
