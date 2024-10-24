import argparse
import os
import random
import signal
import time
from typing import Dict
from bluepy import btle
from packet import * 
from checksum import *
import threading
import pandas as pd

BLUNO_RED_MAC_ADDRESS = "F4:B8:5E:42:6D:49"
# BLUNO_RED_MAC_ADDRESS = "F4:B8:5E:42:4C:BB" #actually green

#FIXME: if we get 59 and then we get 61, ignore the first packet
CHARACTERISTIC_UUID = "0000dfb1-0000-1000-8000-00805f9b34fb"

def millis():
    return time.time_ns() // 1_000_000

def delay(time_ms): # spinlock
    start = millis()
    while(millis() - start < time_ms): pass

class NotifyDelegate(btle.DefaultDelegate):
    def __init__(self, color):
        btle.DefaultDelegate.__init__(self)
        self.buffer = bytearray()
        self.buffer_len = len(self.buffer)
        self.fragmented_packets = 0
        self.total_packets = 0
        self.throughputStartTime = millis()
        self.bitsReceived = 0
        self.COLOR = color 
        # TODO: Remove the testing flags
        self.dropProbability = 0.0
        # TODO: Remove the throughput flags
        # we take throughput readings every 10 notifications
        self.notificationsRcv = 0
        self.notificationMod = 30
        self.highestThroughput = 0
        self.lowestThroughput = 1e9        
        self.relayTxNumber = 0

        self.num = 0

    def handleNotification(self, cHandle, data: bytes):
        self.buffer += bytearray(data)
        if len(data) < 20: # data is fragmented
            print(f"Fragmentation: {len(data)}: {data.hex()}")
            self.fragmented_packets += 1
            # self.reset_buffer()

    def has_packet(self) -> bool:
        return len(self.buffer) >= 20 and len(self.buffer) % 20 == 0

    def get_packet_bytes(self) -> bytearray | None:
        """returns a 20B bytearray representing a packet from the buffer. else, None"""
        if not self.has_packet():
            return None
        data = self.buffer[:20]
        # print(f"RX {self.num} Bytes: {data.hex()}")
        self.num += 1
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

        # ----- DATA COLLECTION -----
        # self.my_csv = pd.DataFrame(columns=["gesture", "ax", "ay", "az", "gx", "gy", "gz"])
        self.my_csv = pd.DataFrame()
        self.ax = []
        self.ay = []
        self.az = []
        self.gx = []
        self.gy = []
        self.gz = []
        # basket, bowling, reload, volley, rainbomb, shield, logout,invalid
        self.GESTURE = "invalid"
        self.filename = "nich_red"
        self.EXPECTED_PKTS = 60
        self.CURRENT_PKTS = 0
        self.ROWS_TO_COLLECT = 10 # CONFIGURE ME - THIS CONTROLS HOW MANY ROWS  
        self.ROWS_LEFT = self.ROWS_TO_COLLECT 
        self.PREV_ADC = -1

        self.COLOR = RESET_COLOR if beetle_id is None else colors[beetle_id]
        self.relay_seq_num = 0
        self.beetle_seq_num = 0 # expected number
        self.MAC = MAC_ADDRESS
        self.chr = CHARACTERISTIC_UUID
        self.connected = False
        self.receiver = NotifyDelegate(self.COLOR)
        self.errors = 0
        self.peripheral = None

        # reliable gamestate send
        self.bullets = 10
        self.health = 20
        self.sendReliableStart = 0
        self.cachedPacket = None
        self.reliableRetransmissions = 0
        self.reliableTxRate = 50 # ms
        self.reliableTimeout = 100 # ms

        # CONFIG TEST: subcomponent test flags
        self.testRelayReliable = False
        self.killThread = False
        self.hasSentReliable = False

    def run(self):
        canSendReliable = True
        while not self.killThread:
            shouldAck = False
            # STEP 1. Handle reconnections if applicable
            if not self.connected or self.errors > 10 or self.reliableRetransmissions > 5:
                print(f"{self.COLOR}Restarting connection: isConnected={self.connected}, errors={self.errors}, retx={self.reliableRetransmissions}")
                self.receiver.reset_buffer()
                self.connect_to_beetle()
                self.errors = 0
                self.reliableRetransmissions = 0
                continue
            # STEP 2. Collect notifications 
            try:
                # print("Getting notifications...")
                self.peripheral.waitForNotifications(1)
            except Exception as e:
                print(f"{self.COLOR}Error: {(e)}. Re-connecting...")
                self.connected = False
                continue
               
            # STEP 3: RECEIVE DATA WHERE APPLICABLE 
            shouldConnEstab = False
            ackNum = -1 # track the largest reliable ack num rcv
            latestPacket = None
            while(self.receiver.has_packet()):
                if self.errors > 3:
                    break

                data = self.receiver.get_packet_bytes()
                if data is None:
                    print(f"{self.COLOR}No packet received (dropped?), continuing to read buffer...")
                    continue
                # verify the checksum - if fail, process the next packet
                if not verify_checksum(data):
                    # print(f"{self.COLOR}Error: checksum failed for this PKT {data.hex()}")
                    print(f"{self.COLOR}Error: checksum failed! Moving to next packet in buffer...")
                    self.errors += 1
                    # print(f"{self.COLOR}Moving to next packet in buffer...")
                    continue

                pkt = get_packet(data)
                # print(f"pkt {pkt.packet_type}")
                # Process based on packet type

                # ignore SYN_ACK packets
                if pkt.packet_type == PACKET_SYN_ACK:
                    shouldConnEstab = True

                # Is unreliable send

                if pkt.packet_type == PACKET_DATA_IMU:
                    # TODO do work
                    if pkt.adc == self.PREV_ADC:
                        print("Previous ADC detected, continuing...")
                        continue
                    print(f"RX {pkt.seq_num}: {pkt.to_bytearray().hex()}")
                    self.CURRENT_PKTS += 1
                    ax = int.from_bytes(pkt.accelX, byteorder='little', signed=True)  # Convert first 2 bytes to signed int
                    ay = int.from_bytes(pkt.accelY, byteorder='little', signed=True)  # Convert next 2 bytes to signed int
                    az = int.from_bytes(pkt.accelZ, byteorder='little', signed=True)  # Convert next 2 bytes to signed int
                    gx = int.from_bytes(pkt.gyroX, byteorder='little', signed=True)   # Convert first 2 bytes to signed int
                    gy = int.from_bytes(pkt.gyroY, byteorder='little', signed=True)   # Convert next 2 bytes to signed int
                    gz = int.from_bytes(pkt.gyroZ, byteorder='little', signed=True)   # Convert next 2 bytes to signed int

                    self.ax.append(ax)
                    self.ay.append(ay)
                    self.az.append(az)
                    self.gx.append(gx)
                    self.gy.append(gy)
                    self.gz.append(gz)

                    if self.CURRENT_PKTS == self.EXPECTED_PKTS:
                        print(f"Row found, #{self.ROWS_TO_COLLECT-self.ROWS_LEFT}")
                        self.PREV_ADC = pkt.adc
                        self.ROWS_LEFT -= 1
                        # Reset the packet count
                        self.CURRENT_PKTS = 0

                        # Create a new row (as a dictionary) for the CSV data
                        # basket, bowling, reload, volley, rainbomb, shield, logout
                        row = {
                            "gesture": self.GESTURE,
                            "ax": self.ax.copy(),
                            "ay": self.ay.copy(),
                            "az": self.az.copy(),
                            "gx": self.gx.copy(),
                            "gy": self.gy.copy(),
                            "gz": self.gz.copy()
                        }

                        # Convert the row into a DataFrame
                        row_df = pd.DataFrame([row])

                        # Concatenate the new row with the existing DataFrame
                        self.my_csv = pd.concat([self.my_csv, row_df], ignore_index=True)

                        # Clear the lists for the next batch of packets
                        self.ax.clear()
                        self.ay.clear()
                        self.az.clear()
                        self.gx.clear()
                        self.gy.clear()
                        self.gz.clear()

                        if self.ROWS_LEFT == 0:
                            # Save the DataFrame to a CSV file
                            print("done!")
                            file_path = f"{self.filename}.csv"
                            # Check if the file exists
                            if os.path.exists(file_path):
                                # Append without header if file exists
                                self.my_csv.to_csv(file_path, mode="a", index=False, header=False)
                            else:
                                # Write with header if file does not exist
                                self.my_csv.to_csv(file_path, mode="a", index=False, header=True)
                            exit(0)


                # Is reliable packet
                if pkt.packet_type == PACKET_DATA_HEALTH or \
                    pkt.packet_type == PACKET_DATA_BULLET or \
                        pkt.packet_type == PACKET_DATA_KICK: # or ...
                    shouldAck = True
                    latestPacket = pkt
                    self.beetle_seq_num = max(self.beetle_seq_num, pkt.seq_num + 1)
                    ackNum = pkt.seq_num
                    if pkt.packet_type == PACKET_DATA_HEALTH: 
                        # TODO: do work
                        print(f"{self.COLOR}RX PKT b{latestPacket.seq_num} <{get_packettype_string(pkt.packet_type)}> Health={pkt.health} (beetle reliable)")
                    elif pkt.packet_type == PACKET_DATA_BULLET:    
                        # TODO: do work
                        print(f"{self.COLOR}RX PKT b{latestPacket.seq_num} <{get_packettype_string(pkt.packet_type)}> Bullet={pkt.bullet} (beetle reliable)")
                    else:
                        # TODO: do work
                        print(f"{self.COLOR}RX PKT b{latestPacket.seq_num} <{get_packettype_string(pkt.packet_type)}> (beetle reliable)")

                # Is an ACK
                if pkt.packet_type == PACKET_ACK:
                    # is the ACK what we expected?
                    # print(f"{sendPkt.to_bytearray().hex()}")
                    print(f"{self.COLOR}RX ACK r{pkt.seq_num}, Relay SN: r{self.relay_seq_num} (relay reliable)")
                    if pkt.seq_num == (self.relay_seq_num + 1) % 256:
                        # We got the ack we wanted!
                        # canSendReliable implies that no more unacked pkt is in-flight
                        self.relay_seq_num = (self.relay_seq_num + 1) % 256
                        canSendReliable = True


            # STEP 4: HANDLE SYN-ACK RECIEVES
            if shouldConnEstab:
                print("Resending CONN_ESTAB")
                resp = PacketConnEstab()
                resp.seq_num = self.relay_seq_num
                resp.crc8 = get_checksum(resp.to_bytearray())
                self.write_packet(resp)
                continue

            # STEP 5: ACKNOWLEDGE RELIABLE BEETLE DATA
            if shouldAck and ackNum != -1:
                # we received an ACK-able data
                resp = PacketAck()
                resp.seq_num = (ackNum + 1) % 256
                resp.crc8 = get_checksum(resp.to_bytearray())
                self.write_packet(resp)
                # finally, deal with the packet
                if latestPacket is not None:
                    print(f"{self.COLOR}TX ACK b{resp.seq_num}, for RX b{latestPacket.seq_num} (beetle reliable)")
                else:
                    print(f"{self.COLOR}RX ACK b{resp.seq_num} (duplicate)")
            
            # STEP 6: SEND RELIABLE RELAY DATA 
            # TODO: remove this if wrapper when testing is done
            if self.testRelayReliable:
                if canSendReliable:
                    if millis() - self.sendReliableStart > self.reliableTxRate:
                        sendPkt = self.getDataToSend()
                        if sendPkt is not None:
                            self.cachedPacket = sendPkt
                            self.sendReliableStart = millis()
                            print(f"{self.COLOR}TX PKT r{sendPkt.seq_num}, curr r{self.relay_seq_num} (relay reliable)")
                            self.write_packet(sendPkt)
                            self.receiver.relayTxNumber += 1
                            canSendReliable = False
                            self.hasSentReliable = True
                elif self.hasSentReliable and millis() - self.sendReliableStart > self.reliableTimeout:  # 1000 ms = 1 second
                    self.sendReliableStart = millis()
                    self.reliableRetransmissions += 1
                    print(f"{self.COLOR}TX PKT r{self.cachedPacket.seq_num}, curr {self.relay_seq_num}, (relay reliable, timeout)")
                    sendPkt = self.cachedPacket
                    self.receiver.relayTxNumber += 1
                    self.write_packet(sendPkt)
                    canSendReliable = False


    def bytes_to_packet(self, bytearray):
        """takes a 20B bytearray, CRC8 checks, then wraps it in the packet class.
        returns Packet() is OK, else a PacketInvalid
        """
        # print("Received data:", bytearray.hex())
        # TODO: consider if a None would be faster
        if not verify_checksum(bytearray):
            print(f"{self.COLOR}err: checksum failed")
            return PacketInvalid()
        return get_packet(bytearray)

    def write_packet(self, packet):
        try:
            print(f"TX Bytes: {packet.to_bytearray().hex()}")
            self.chr.write(packet.to_bytearray())
        except Exception as e:
            print(f"{self.COLOR}Error writing, {e}")
            self.connected = False

    def get_notifications(self, timeout=2):
        try:
            return self.peripheral.waitForNotifications(timeout)
        except Exception as e:
            print(f"{self.COLOR}Error getting notif: {e}")
            self.connected = False
            return False

    def reset_bluepy(self):
        if self.peripheral is not None:
            self.peripheral.disconnect()
            self.peripheral = None

        while(self.peripheral is None):
            try:
                self.peripheral = btle.Peripheral(self.MAC)
                self.receiver = NotifyDelegate(self.COLOR)
                self.peripheral.setDelegate(self.receiver)
                self.chr = self.peripheral.getCharacteristics(uuid=CHARACTERISTIC_UUID)[0]
                break
            except Exception as e: # keep trying
                print(f"{self.COLOR}Bluepy peripheral fail: {e}")
                continue

    def connect_to_beetle(self):
        """blocking 3 way handshake"""
        while True:
            self.reset_bluepy()

            print(f"{self.COLOR}THREE WAY START")
            # STAGE 1: Hello
            pkt = PacketHello()
            pkt.seq_num = self.relay_seq_num
            pkt.crc8 = get_checksum(pkt.to_bytearray())
            print(f"{self.COLOR}THREE WAY: Sending HELLO r{self.relay_seq_num}")
            self.write_packet(pkt)

            # STAGE 2: SYN-ACK wait
            print(f"{self.COLOR}THREE WAY: Wait for SYN-ACK")
            hasSynAck = False
            if(self.get_notifications(1)):
                while self.receiver.has_packet():
                    data = self.receiver.get_packet_bytes()
                    if data is None:
                        print(f"None received")
                        continue
                    if not verify_checksum(data):
                        print(f"verify checksum failed for {data.hex()}")
                        continue
                    packet = get_packet(data)
                    if packet is None:
                        print("packet is none")
                        continue
                    if packet.packet_type != PACKET_SYN_ACK:
                        print("packet is not synack")
                        continue
                    print(f"{self.COLOR}THREE WAY: SYN-ACK received")
                    self.beetle_seq_num = pkt.seq_num
                    hasSynAck = True # break out of outer wait loop
                    break
            else:
                print("no notif?")
            if not hasSynAck:
                print(f"{self.COLOR}SYNACK not received. Resending hello...")
                continue # resend hello

            # STAGE 3: CONN_ESTAB
            resp = PacketConnEstab()
            resp.seq_num = self.relay_seq_num
            resp.crc8 = get_checksum(resp.to_bytearray())
            print(f"{self.COLOR}THREE WAY: Sending ACK/CONN_ESTAB")
            self.write_packet(resp)
            self.connected = True
            break  # Exit the loop after successful connection
        print(f"{self.COLOR}---- Connection established. ----")
        
    def getDataToSend(self):
        """Check if there is data to send to the beetle. Returns a packet if so, else None"""
        # Create a PacketGamestate instance
        # TODO: integrate with backend
        pkt = PacketGamestate()
        pkt.seq_num = self.relay_seq_num
        pkt.bullet = random.randint(0, 255)
        pkt.health = random.randint(0, 255)
        self.bullets = pkt.bullet
        self.health = pkt.health
        pkt.crc8 = get_checksum(pkt.to_bytearray())
        return pkt

def main():
    # Create Beetle instances
    # beetle0 = Beetle(BLUNO_RED_MAC_ADDRESS, 0, "red")
    beetle0 = Beetle(BLUNO_RED_MAC_ADDRESS, 0)
    beetle0.run()

if __name__ == "__main__":
    main()