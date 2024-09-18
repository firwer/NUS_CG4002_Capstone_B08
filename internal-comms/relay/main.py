import argparse
import random
import time
from bluepy import btle
from packet import * 
from checksum import *
import threading

BLUNO0_MAC_ADDRESS = "F4:B8:5E:42:4C:BB"
BLUNO1_MAC_ADDRESS = "F4:B8:5E:42:61:6A"
BLUNO2_MAC_ADDRESS = "F4:B8:5E:42:6D:1E"

CHARACTERISTIC_UUID = "0000dfb1-0000-1000-8000-00805f9b34fb"

def millis():
    return time.time_ns() // 1_000_000

def delay(time_ms): # spinlock
    start = millis()
    while(millis() - start < time_ms): pass

class NotifyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.buffer = bytearray()
        self.buffer_len = len(self.buffer)
        self.fragmented_packets = 0
        self.total_packets = 0
        self.throughputStartTime = millis()
        self.bitsReceived = 0
        
        # TODO: Remove the testing flags
        self.dropProbability = 0.0
        # TODO: Remove the throughput flags
        # we take throughput readings every 10 notifications
        self.notificationsRcv = 0
        self.notificationMod = 64
        self.highestThroughput = 0
        self.lowestThroughput = 1e9        

    def handleNotification(self, cHandle, data: bytes):
        if len(data) < 20: # data is fragmented
            # print(f"Fragmentation: {len(data)}: {data.hex()}")
            self.fragmented_packets += 1
        elif random.random() <= self.dropProbability:
            print(f"Dropping packet: {data.hex()}")
            return 
        self.notificationsRcv += 1
        self.bitsReceived += len(data) * 8
        self.buffer += bytearray(data)
        if self.notificationsRcv >= self.notificationMod:
            self.notificationsRcv = 0
            self.print_statistics()

    def print_statistics(self):
        print(f"=============== TRANSMISSION STATISTICS ===============")
        self.get_throughput()

    def get_throughput(self):
        """return the throughput in kbps (kilobits) from the last time this function was called"""
        elapsed_time_seconds = (millis() - self.throughputStartTime) / 1000  # Time in seconds
        kbps = (self.bitsReceived / 1000) / elapsed_time_seconds  # Convert bits to kilobits
        self.highestThroughput = max(kbps, self.highestThroughput)
        self.lowestThroughput = min(kbps, self.lowestThroughput)
        print(f"{'=' * 15} Tx Rate: {kbps:>3.3f} kbps     {'=' * 15}")
        print(f"{'=' * 15} Min Rate: {self.lowestThroughput:>3.3f} kbps    {'=' * 15}")
        print(f"{'=' * 15} Max Rate: {self.highestThroughput:>3.3f} kbps    {'=' * 15}")
        print(f"{'=' * 15} Fragmented Pkts: {self.fragmented_packets//2:>3}    {'=' * 15}")
        self.throughputStartTime = millis()
        self.bitsReceived = 0
        return kbps

    def has_packet(self) -> bool:
        return len(self.buffer) >= 20 and len(self.buffer) % 20 == 0

    def get_packet_bytes(self) -> bytearray | None:
        """returns a 20B bytearray representing a packet from the buffer. else, None"""
        if not self.has_packet():
            return None
        data = self.buffer[:20]
        self.buffer = self.buffer[20:]
        return data
    
    def reset_buffer(self):
        self.data = bytearray()

# A beetle object maintains its own connection and state
class Beetle:
    def __init__(self, MAC_ADDRESS, beetle_id=None) -> None:
        RESET_COLOR = "\033[0m"  # Reset color
        RED_COLOR = "\033[31m"   # Red color
        GREEN_COLOR = "\033[32m"  # Green color
        YELLOW_COLOR = "\033[33m"  # Yellow color
        BLUE_COLOR = "\033[34m"   # Blue color
        MAGENTA_COLOR = "\033[35m" # Magenta color
        CYAN_COLOR = "\033[36m"   # Cyan color
        colors = [BLUE_COLOR, GREEN_COLOR, RED_COLOR]

        self.COLOR = RESET_COLOR if beetle_id is None else colors[beetle_id]
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
        self.reliableRetransmissions = 0
        self.reliableTxRate = 0 # ms
        self.reliableTimeout = 1000 # ms

        # CONFIG TEST: subcomponent test flags
        self.testRelayReliable = True
        self.corruptProbability = 0.1
        self.killThread = False

    def run(self):
        canSendReliable = True
        while not self.killThread:
            shouldAck = False
            # STEP 1. Handle reconnections if applicable
            if not self.connected or self.errors > 2 or self.reliableRetransmissions > 2:
                print(f"{self.COLOR}Restarting connection: isConnected={self.connected}, errors={self.errors}, retx={self.reliableRetransmissions}")
                self.receiver.reset_buffer() # should prevent bitshift fragmentations
                self.connect_to_beetle()
                self.errors = 0
                self.reliableRetransmissions = 0
                continue
            # STEP 2. Collect notifications 
            try:
                # print("Getting notifications...")
                self.peripheral.waitForNotifications(1)
            except Exception as e:
                print(f"Error: {(e)}. Re-connecting...")
                self.connected = False
                continue
               
            # STEP 3: RECEIVE DATA WHERE APPLICABLE 
            shouldConnEstab = True
            ackNum = -1 # track the largest reliable ack num rcv
            latestPacket = None
            while(self.receiver.has_packet()):
                if self.errors > 3:
                    break

                data = self.receiver.get_packet_bytes()
                if data is None:
                    print("No packet received (dropped?), continuing to read buffer...")
                    continue

                # TODO: REMOVE ME -- SUBCOMPONENT TESTING LOGIC
                # TEST: corrupt packet with probability of 10%
                if random.random() <= self.corruptProbability:
                    # print("Corrupting RX packet...")
                    byte_to_corrupt = random.randint(0, len(data) - 1)
                    bit_to_flip = 1 << random.randint(0, 7) 
                    data[byte_to_corrupt] ^= bit_to_flip

                # verify the checksum - if fail, process the next packet
                if not verify_checksum(data):
                    print(f"Error: checksum failed for this PKT {data.hex()}")
                    self.errors += 1
                    print(f"Moving to next packet in buffer...")
                    continue

                pkt = get_packet(data)

                # Process based on packet type

                # ignore SYN_ACK packets
                if pkt.packet_type == PACKET_SYN_ACK: continue

                # if we get normal data packets, then no need to comm_estab
                shouldConnEstab = False

                # Is unreliable send
                if pkt.packet_type == PACKET_DATA_IMU:
                    # do work
                    print(f"RX PKT b{pkt.seq_num} (beetle stream)")
                    continue

                # Is reliable packet
                if pkt.packet_type == PACKET_DATA_HEALTH or \
                    pkt.packet_type == PACKET_DATA_BULLET or \
                        pkt.packet_type == PACKET_DATA_KICK: # or ...
                    shouldAck = True
                    latestPacket = pkt
                    self.beetle_seq_num = max(self.beetle_seq_num, pkt.seq_num + 1)
                    ackNum = pkt.seq_num 
                    print(f"RX PKT b{latestPacket.seq_num} <{get_packettype_string(pkt.packet_type)}> (beetle reliable)")

                # Is an ACK
                if pkt.packet_type == PACKET_ACK:
                    # is the ACK what we expected?
                    print(f"RX PKT r{pkt.seq_num}, Relay SN: r{self.relay_seq_num} (relay reliable)")
                    if pkt.seq_num == (self.relay_seq_num + 1) % 256:
                        # We got the ack we wanted!
                        # canSendReliable implies that no more unacked pkt is in-flight
                        self.relay_seq_num = (self.relay_seq_num + 1) % 256
                        canSendReliable = True


            # STEP 4: HANDLE SYN-ACK RECIEVES
            if shouldConnEstab:
                resp = PacketConnEstab()
                resp.seq_num = self.relay_seq_num
                resp.crc8 = get_checksum(resp.to_bytearray())
                self.write_packet(resp)

            # STEP 5: ACKNOWLEDGE RELIABLE BEETLE DATA
            if shouldAck and ackNum != -1:
                # we received an ACK-able data
                resp = PacketAck()
                resp.seq_num = (ackNum + 1) % 256
                resp.crc8 = get_checksum(resp.to_bytearray())
                self.write_packet(resp)
                # finally, deal with the packet
                if latestPacket is not None:
                    print(f"TX ACK b{resp.seq_num}, for RX b{latestPacket.seq_num} (beetle reliable)")
                else:
                    print(f"RX ACK b{resp.seq_num} (duplicate)")
            
            # STEP 6: SEND RELIABLE RELAY DATA 
            # TODO: remove this if wrapper when testing is done
            if self.testRelayReliable:
                if canSendReliable:
                    if millis() - self.sendReliableStart > self.reliableTxRate:
                        sendPkt = self.getDataToSend()
                        if sendPkt is not None:
                            self.cachedPacket = sendPkt
                            # sendPkt = self.corrupt_packet(sendPkt) # WARN: should be removed in prod
                            self.sendReliableStart = millis()
                            print(f"TX PKT r{sendPkt.seq_num}, curr r{self.relay_seq_num} (relay reliable)")
                            self.write_packet(sendPkt)
                            canSendReliable = False
                elif millis() - self.sendReliableStart > self.reliableTimeout:  # 1000 ms = 1 second
                    self.sendReliableStart = millis()
                    self.reliableRetransmissions += 1
                    print(f"TX PKT r{self.cachedPacket.seq_num}, curr {self.relay_seq_num}, (relay reliable, timeout)")
                    sendPkt = self.cachedPacket
                    # sendPkt = self.corrupt_packet(sendPkt) # WARN: should be removed in prod
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
            self.peripheral.disconnect()
            self.peripheral = None

        while(self.peripheral is None):
            try:
                self.peripheral = btle.Peripheral(self.MAC)
                self.receiver = NotifyDelegate()
                self.peripheral.setDelegate(self.receiver)
                self.chr = self.peripheral.getCharacteristics(uuid=CHARACTERISTIC_UUID)[0]
                break
            except Exception as e: # keep trying
                print(f"Bluepy peripheral fail: {e}")
                continue

    def connect_to_beetle(self):
        """blocking 3 way handshake"""
        while True:
            self.reset_bluepy()

            print("THREE WAY START")
            # STAGE 1: Hello
            pkt = PacketHello()
            pkt.seq_num = self.relay_seq_num
            pkt.crc8 = get_checksum(pkt.to_bytearray())
            print(f"THREE WAY: Sending HELLO r{self.relay_seq_num}")
            self.write_packet(pkt)

            # STAGE 2: SYN-ACK wait
            print("THREE WAY: Wait for SYN-ACK")
            hasSynAck = False
            waitCount = 3 
            if(self.get_notifications(1)):
                while self.receiver.has_packet():
                    data = self.receiver.get_packet_bytes()
                    if data is None: continue
                    if not verify_checksum(data):
                        self.receiver.reset_buffer()
                        continue
                    packet = get_packet(data)
                    if packet is None: continue
                    if packet.packet_type != PACKET_SYN_ACK:
                        break
                    print("THREE WAY: SYN-ACK received")
                    self.beetle_seq_num = pkt.seq_num
                    hasSynAck = True
                    waitCount = 0 # break out of outer wait loop
                    break
            if not hasSynAck:
                print(f"Timeout {waitCount}: SYNACK not received. Resending hello...")
                continue # resend hello

            # STAGE 3: CONN_ESTAB
            resp = PacketConnEstab()
            resp.seq_num = self.relay_seq_num
            resp.crc8 = get_checksum(resp.to_bytearray())
            print(f"THREE WAY: Sending ACK/CONN_ESTAB")
            self.write_packet(resp)
            self.connected = True
            break  # Exit the loop after successful connection
        print("---- Connection established. ----")
        
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
        if random.random() < 0.1:  # 10% chance
            # print("Corrupting packet...")
            byte_array = pkt.to_bytearray()
            byte_to_corrupt = random.randint(0, len(byte_array) - 1)  # Pick a random byte
            bit_to_flip = 1 << random.randint(0, 7)  # Pick a random bit to flip (0-7)
            byte_array[byte_to_corrupt] ^= bit_to_flip  # XOR the bit to flip it
            # Update the packet with the corrupted byte array
            pkt = PacketGamestate(byte_array)
        return pkt

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run a Beetle instance with a specific ID.")
    parser.add_argument("beetle_id", type=int, help="ID of the Beetle instance to run (0, 1, or 2)")

    # Parse arguments
    args = parser.parse_args()
    beetle_id = args.beetle_id

    # Validate beetle_id
    if beetle_id not in [0, 1, 2]:
        print("Invalid beetle_id. Must be 0, 1, or 2.")
        return

    # Create Beetle instances
    beetle0 = Beetle(BLUNO0_MAC_ADDRESS, 0)
    beetle1 = Beetle(BLUNO1_MAC_ADDRESS, 1)
    beetle2 = Beetle(BLUNO2_MAC_ADDRESS, 2)

    # Dictionary to map beetle_id to Beetle instance
    beetles = {0: beetle0, 1: beetle1, 2: beetle2}

    # Run the selected Beetle instance
    beetles[beetle_id].run()

if __name__ == "__main__":
    main()
