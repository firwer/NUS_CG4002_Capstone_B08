import time
from bluepy import btle
from packet import * 
from checksum import *
import threading

BLUNO_MAC_ADDRESS = "F4:B8:5E:42:4C:BB"
CHARACTERISTIC_UUID = "0000dfb1-0000-1000-8000-00805f9b34fb"  # Correct characteristic UUID
TIMEOUT_MS = 1000

class NotifyDelegate(btle.DefaultDelegate):
    def __init__(self, buffer):
        btle.DefaultDelegate.__init__(self)
        self.buffer = buffer
        self.buffer_len = len(self.buffer)
        self.buffer_ptr = 0
        self.buffer_read = 0
        self.buffer_filled = 0
        self.lock = threading.Lock()  # Lock to manage concurrency

    def handleNotification(self, cHandle, data: bytes):
        # print(f"Got a notification: {len(data)}")
        # print(f"{self.buffer_ptr}, {self.buffer_filled}")
        for byte in data:
            if self.buffer_filled == self.buffer_len:
                break  # Buffer full, stop processing
            self.buffer[self.buffer_ptr] = byte
            self.buffer_ptr = (self.buffer_ptr + 1) % self.buffer_len
        self.buffer_filled += len(data)

    def has_packet(self) -> bool:
        return self.buffer_filled > 20

    def get_packet_bytes(self) -> bytearray | None:
        """returns a 20B bytearray representing a packet. else, None"""
        if self.buffer_filled < 20:
            return None
        data = bytearray(20)
        for i in range(20):
            data[i] = self.buffer[(self.buffer_read + i) % self.buffer_len]
        self.buffer_read = (self.buffer_read + 20) % self.buffer_len
        self.buffer_filled -= 20
        return data

    def flush_buffer(self):
        """reset buffer_filled"""
        self.buffer_filled = 0

# A beetle object maintains its own connection and state
class Beetle:
    def __init__(self, MAC_ADDRESS) -> None:
        self.relay_seq_num = 0
        self.beetle_seq_num = 0
        self.MAC = MAC_ADDRESS
        self.chr = CHARACTERISTIC_UUID
        self.connected = False
        self.packet_buffer = bytearray(20*10)
        self.receiver = NotifyDelegate(self.packet_buffer)
        self.errors = 0
        self.peripheral = None

    def run(self):
        while(1):
            if not self.connected or self.errors > 2:
                self.errors = 0
                self.connect_to_beetle()
            else: # connected
                # collect data
                try:
                    self.peripheral.waitForNotifications(timeout=500)
                except:
                    print("Device disconnected. Re-connecting...")
                    self.connected = False
                    continue
                # check if there is something to receive
                if self.receiver.has_packet():
                    bytearr = self.receiver.get_packet_bytes()
                    pkt = self.bytes_to_packet(bytearr)
                    if pkt.packet_type == PACKET_INVALID:
                        print("err: invalid packet")
                        self.errors += 1
                        continue
                    # SYNACK duplicate received, reply with CONN_ESTAB
                    if pkt.packet_type == PACKET_SYN_ACK:
                        print("Dup SYN_ACK, sending CONN_ESTAB")
                        # assert(self.beetle_seq_num == pkt.seq_num)
                        self.beetle_seq_num = pkt.seq_num
                        resp = PacketConnEstab()
                        resp.crc8 = get_checksum(resp.to_bytearray())
                        self.chr.write(resp.to_bytearray())
                        continue
                    
                    # The packet from here on is valid;
                    # Handle the packet
                    if pkt.packet_type == PACKET_DATA_IMU:
                        # stream of data, no need to ACK
                        print("IMU")
                        self.print_packet(pkt)
                    elif pkt.packet_type == PACKET_DATA_HEALTH:
                        # reliable receive
                        ack = PacketAck()
                        if pkt.seq_num == self.beetle_seq_num:
                            # correct seq num received
                            self.beetle_seq_num = (self.beetle_seq_num + 1 ) % 256
                            ack.seq_num = self.beetle_seq_num
                            ack.crc8 = get_checksum(ack.to_bytearray())
                            self.write_packet(ack)
                            print(f"ACK {ack.seq_num} PKT {pkt.seq_num}, {pkt.health}")
                        else:
                            # ask for the last expected seq num
                            ack.seq_num = self.beetle_seq_num
                            ack.crc8 = get_checksum(ack.to_bytearray())
                            self.write_packet(ack)
                            print(f"NACK: {self.beetle_seq_num}, rcv: {pkt.seq_num}")
                    else: 
                        # do nothing
                        pass

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
    
    def reliable_receive(self):
        pass

    def write_packet(self, packet):
        self.chr.write(packet.to_bytearray())

    def connect_to_beetle(self):
        """blocking 3 way handshake"""
        while(self.peripheral is None):
            try:
                peripheral = btle.Peripheral(BLUNO_MAC_ADDRESS)
                self.peripheral = peripheral
                self.peripheral.setDelegate(self.receiver)
                self.chr = self.peripheral.getCharacteristics(uuid=CHARACTERISTIC_UUID)[0]
                break
            except: # keep trying
                print("peripheral fail")
                pass
        print("THREE WAY START")
        while(1):
            # STAGE 1: Hello
            pkt = PacketHello()
            pkt.seq_num = self.relay_seq_num
            pkt.crc8 = get_checksum(pkt.to_bytearray())
            print("THREE WAY: Sending HELLO")
            self.chr.write(pkt.to_bytearray())
            self.receiver.flush_buffer() # clear the buffer

            # STAGE 2: SYN-ACK wait
            print("THREE WAY: Wait SYN-ACK")
            if(self.peripheral.waitForNotifications(1000)):
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
                print("SYN-ACK received")
            else:
                print("Timeout: SYN-ACK not received.")
                continue  # Retry the handshake

            # STAGE 3: ACK
            ack = PacketAck()
            ack.seq_num = self.beetle_seq_num
            ack.crc8 = get_checksum(ack.to_bytearray())
            print("THREE WAY: ACK")
            self.write_packet(ack)
            self.connected = True
            break  # Exit the loop after successful connection
        print("Connection established.")
        self.receiver.flush_buffer() # clear the buffer
        
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
