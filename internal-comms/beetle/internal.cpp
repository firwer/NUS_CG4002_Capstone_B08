#include "internal.hpp"

volatile uint8_t beetle_seq_num = 0;  // data FROM beetle
volatile uint8_t relay_seq_num = 0;   // data FROM relay

volatile bool isConnected = false;

#define BUFFER_SZ 200
uint8_t buffer[BUFFER_SZ];
unsigned int buffer_writer = 0;  // write
unsigned int buffer_reader = 0;  // read
unsigned int buffer_fills = 0;   // |Bytes| the buffer has

// fill the serial buffer
void fill_buffer() {
  unsigned int start = millis();
  while (Serial.available() && buffer_fills < BUFFER_SZ) {  // && millis() - start < fill_for_ms) {
    buffer[buffer_writer] = Serial.read();
    buffer_writer = (buffer_writer + 1) % BUFFER_SZ;
    ++buffer_fills;
    if (buffer_fills >= BUFFER_SZ) {
      break;
    }
  }
}

bool hasPacket() {
  return buffer_fills >= 20;
}

bool await_packet(struct packet_general_t* packet_buffer, int timeout_ms) {
  uint8_t bytes_rcv = 0;
  uint8_t* packet_bytes = (uint8_t*)packet_buffer;
  unsigned long start_time = millis();

  while (millis() - start_time < timeout_ms) {
    fill_buffer();  // Fill buffer in small intervals
    if (hasPacket()) {
      for (int i = 0; i < PACKET_SIZE; ++i) {
        packet_bytes[bytes_rcv++] = buffer[buffer_reader++];
        buffer_reader %= BUFFER_SZ;
      }
      buffer_fills -= PACKET_SIZE;
      return true;
    }
  }
  return false;  // Timeout
}

// Calculate CRC8
void setChecksum(packet_general_t* packet) {
  uint8_t crc = 0xFF;
  uint8_t* packetBytes = (uint8_t*)packet;
  // Consider: quick CRC8, skip the padding?
  for (uint8_t i = 0; i < 19; ++i) {
    crc = crc8_lut[crc ^ packetBytes[i]];
  }
  packet->crc8 = crc;
}

// Check CRC8
bool verifyChecksum(struct packet_general_t* packet) {
  uint8_t crc = 0xFF;
  uint8_t* packetBytes = (uint8_t*)packet;
  // Consider: quick CRC8, skip the padding?
  for (uint8_t i = 0; i < 19; ++i) {
    crc = crc8_lut[crc ^ packetBytes[i]];
  }
  return crc == packet->crc8;
}

// Sets the checksum and writes the packet
void write_serial(packet_general_t* packet) {
  setChecksum(packet);
  Serial.write(reinterpret_cast<uint8_t*>(packet), 20);
}

// checks the validity of the packet, including checksum and returns its type
uint8_t checkPacketValidity(packet_general_t* packet) {
  // invariant: packet is fully formed
  // first, check for the packet type
  uint8_t type = packet->packet_type;

  if (type == PACKET_INVALID || type == PACKET_SYN_ACK)
    return PACKET_INVALID;

  // then, checksum
  if (!verifyChecksum(packet))
    return PACKET_INVALID;

  // checksum is OK therefore valid
  return type;
}

// Wait for a HELLO and complete the 3-way handshake.
// The three-way handshake MUST be stop-and-wait.
void await_handshake(bool helloReceived) {
  isConnected = false;  // TODO check if this should be removed
  digitalWrite(13, 1);
  while (!isConnected) {
    // Stage 1 -- HELLO
    while (!helloReceived) {
      packet_general_t hello_packet = { 0 };
      // Wait forever for a HELLO to arrive.
      while(await_packet(&hello_packet, TIMEOUT_MS)){}
      // Check if its a HELLO packet
      if (hello_packet.packet_type == PACKET_HELLO && verifyChecksum(&hello_packet)) {
        break;
      }
    }
    // we have gotten a valid checksum. Complete the handshake
    // Send the SYN-ACK. Retransmit a max of 2 times before giving up and going back to waiting
    packet_ack_t syn_ack_packet = { 0 };
    syn_ack_packet.packet_type = PACKET_SYN_ACK;
    packet_general_t ack_packet = { 0 };
    syn_ack_packet.seq_num = beetle_seq_num;  // TODO: check if this is problematic

    // Stage 2 -- SYN_ACK
    while (1) {  // keep retransmitting SYN-ACK
      write_serial((packet_general_t*)&syn_ack_packet);
      // Stage 3 -- ACK
      if (!await_packet(&ack_packet, 500)) {  // ack timeout, retransmit
        continue;
      }
      if (!verifyChecksum(&ack_packet))  // checksum failed, retransmit
        continue;
      if (ack_packet.packet_type == PACKET_CONN_ESTAB) {
        isConnected = true;
        break;
      }
    }
    helloReceived = (isConnected) ? true : false;
  }
  digitalWrite(13, 0);
}

// --------------- TESTING CODE --------------

// Sets the checksum and writes the packet. Adds some fuzzing to incur checksum fails
void write_serial_with_fuzz(packet_general_t* packet, bool fuzz) {
  setChecksum(packet);
  if (fuzz) {
    flip_bits_with_probability(packet, 0.05);  // fuzzing purposes
  }
  Serial.write(reinterpret_cast<uint8_t*>(packet), sizeof(packet_general_t));
}

// if pr(prob) is passed, pkt will be corrupted.
void flip_bits_with_probability(packet_general_t* pkt, float probability) {
  uint8_t* packetBytes = (uint8_t*)pkt;       // Cast the packet to a byte array for easy manipulation
  int packetSize = sizeof(packet_general_t);  // Determine the size of the packet

  // Generate a random number between 0 and 1 (1000 to be more accurate)
  float randomValue = random(0, 1000) / 1000.0;

  // If the random value is less than the specified probability, flip the 18th bit
  if (randomValue < probability) {
    // Calculate the byte and bit position for the 18th bit
    int bitPosition = 18;             // 0-based index
    int byteIndex = bitPosition / 8;  // Integer division to find byte index
    int bitIndex = bitPosition % 8;   // Modulo to find bit index within the byte

    // Ensure the byte index is within bounds
    if (byteIndex < packetSize) {
      // Flip the 18th bit in the byte
      packetBytes[byteIndex] ^= (1 << bitIndex);
    }
  }
}

// Test how resilient unreliable throughput is
void test_throughput_unreliable(int rate_ms) {
  packet_imu_t pkt = { 0 };
  packet_general_t rcv = { 0 };
  int await_delay = 50;
  pkt.packet_type = PACKET_DATA_IMU;
  while (1) {
    pkt.seq_num = beetle_seq_num;
    ++beetle_seq_num;
    write_serial_with_fuzz((packet_general_t*)&pkt, true);
    if (await_packet((packet_general_t*)&rcv, await_delay)) {
      if (rcv.packet_type == PACKET_HELLO) {  // this is the trigger for reconnx
        await_handshake(true);
      }
      if (rcv.packet_type == PACKET_CONN_ESTAB) {
        // duplicate, continue;
      }
      continue;
    }
    delay(rate_ms - await_delay);
  }
}

// Test single stop-and-wait
void test_throughput_reliable(int rate_ms) {
  uint8_t exp_beetle_seq_num = beetle_seq_num; // this tracks the reliable seq_num
  bool canSendReliable = true;
  uint8_t test_health_number = 22;
  uint8_t prev_rcv_ack = 0; // track the previously received ack number
  long reliableTimeStart = 0;
  uint8_t timeout_ms = max(rate_ms+100, 500);
  packet_general_t cached_packet = {0};
  uint8_t to_send = 10;
  // simulate event driver
  while (1) {
    auto rate_start = millis();

    // bool resendReliable = false;
    packet_general_t rcv = {0};
    if (await_packet((packet_general_t*)&rcv, 50)) {
      // case 1: checksum error
      // > ignore
      if(verifyChecksum(&rcv)){
        // case 2: hello
        // > relay wants to re-estab connections. handshake.
        if(rcv.packet_type == PACKET_HELLO){
          await_handshake(true);
        }
        // case 3: conn_estab
        // > ignore this duplicate
        if(rcv.packet_type == PACKET_CONN_ESTAB){
        
        }
        // case 4: ACKn
        if(rcv.packet_type == PACKET_ACK){
          if(rcv.seq_num == exp_beetle_seq_num){
            // > flag that we need not resend
            canSendReliable = true;
          }
        }
      }
    }

    // if ACKn received AND there is something to send, send it!
    if(canSendReliable){
      delay(rate_ms);
        
      canSendReliable = false;
      packet_health_t pkt = {0};
      pkt.health_count = test_health_number--;
      pkt.packet_type = PACKET_DATA_HEALTH;
      pkt.seq_num = beetle_seq_num;
      ++beetle_seq_num;
      exp_beetle_seq_num = beetle_seq_num;
      setChecksum((packet_general_t*)&pkt);
      write_serial_with_fuzz((packet_general_t*)&pkt, 1);
      memcpy(&cached_packet, &pkt, 20);
      reliableTimeStart = millis();
      

    }else if(millis() - reliableTimeStart > 1000){ // constant here must be big
      // else we handle reliable packet timeout;
      digitalWrite(13, 1);
      reliableTimeStart = millis();
      write_serial_with_fuzz(&cached_packet, 1);
      digitalWrite(13, 0);     
    }

    // then, do unreliable sending (omitted)

  }
}
