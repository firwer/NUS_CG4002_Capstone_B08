#include "internal.hpp"

volatile uint8_t beetle_seq_num = 0;  // data FROM beetle
volatile uint8_t relay_seq_num = 0;   // data FROM relay

volatile bool isConnected = false;

#define BUFFER_SZ 200
uint8_t buffer[BUFFER_SZ];
unsigned int buffer_writer = 0;  // write
unsigned int buffer_reader = 0;  // read
unsigned int buffer_fills = 0;   // |Bytes| the buffer has

// hard reset the buffer when things get gnarly for some reason
void reset_buffer() { 
  buffer_fills = 0;
  buffer_writer = 0;
  buffer_reader = 0;
}

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
  while (!isConnected) {
    // Stage 1 -- HELLO
    while (!helloReceived) {
      packet_general_t hello_packet = { 0 };
      // Wait forever for a HELLO to arrive.
      while (await_packet(&hello_packet, 1000));
      // Check if its a HELLO packet
      if (hello_packet.packet_type == PACKET_HELLO && verifyChecksum(&hello_packet)) {
        relay_seq_num = hello_packet.seq_num;
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
      if (!await_packet((packet_general_t*) &ack_packet, 1000)) {  // ack timeout, retransmit
        continue;
      }
      if (!verifyChecksum(&ack_packet)){
        write_serial((packet_general_t*) &ack_packet);
        reset_buffer(); // THIS MUST BE DONE.
        continue;
      }
      if (ack_packet.packet_type == PACKET_CONN_ESTAB) {
        isConnected = true;
        helloReceived = true;
        relay_seq_num = ack_packet.seq_num;  // we expect the next SN to be +1
        break;
      }
      reset_buffer();
    }
  }
  digitalWrite(13, 0);
}

void getRandomReliablePacket(packet_general_t* pkt) {
  int packet_choice = rand() % 3;
  if (packet_choice == 0) {
    pkt->packet_type = PACKET_DATA_BULLET;
    packet_bullet_t* tmp = (packet_bullet_t*)pkt;
    tmp->bullet_count = rand() % 256;  // choose between 0-255
  } else if (packet_choice == 1) {
    pkt->packet_type = PACKET_DATA_HEALTH;
    packet_health_t* tmp = (packet_health_t*)pkt;
    tmp->health_count = rand() % 256;  // choose between 0-255
  } else {
    pkt->packet_type = PACKET_DATA_KICK;
    packet_kick_t* tmp = (packet_kick_t*)pkt;
  }
}


// ----- Two-way TX/RX -----
// bool reliableBufferFilled = false;    // CONFIG: simulate buffer full (has something to send reliably)
// bool unreliableBufferFilled = false;  // CONFIG: simulate udp buffer full (has something to send unreliably)
uint8_t rel_tx_rate = 0;             // CONFIG: Tuning of reliable transfer rate in ms
uint8_t unrel_tx_rate = 0;           // CONFIG: Tuning of unreliable transfer rate in ms
long unreliableStartRateTime = 0;    // TESTING: rate limit for unreliable sending
long reliableStartRateTime = 0;      // TESTING: rate limit for reliable sending

bool canSendReliable = true;  // flag to allow tx
bool reliableSent = false;

long reliableTimeStart = 0;                   // timeout
uint8_t exp_beetle_seq_num = beetle_seq_num;  // this tracks the reliable seq_num

uint8_t test_health_number = 22;
uint8_t prev_rcv_ack = 0;  // track the previously received ack number
packet_general_t cached_packet = { 0 };


// ------ EXPOSED API FOR HARDWARE SUBCOMPONENT ------
// Usage:
//
// It is the responsibility of the internal comms 'black box' to:
//      > calculate CRC8
//      > handle seq numbering
//
// For each beetle node, we typically expect to only call ONE
//  of the push_XYZ

// Connect to the relay node.
// Returns true if connection is established, else false.
// This is a blocking function

// buffers for processing
bool unreliable_buffer_filled = false;
packet_imu_t unreliable_buffer;  // unreliable packet buffer

bool reliable_buffer_filled = false;
packet_general_t reliable_buffer;

bool receive_buffer_filled = false;
packet_gamestate_t receive_buffer;

bool ic_connect() {
  await_handshake(false);
  return true;
}

// Queue the data to be sent when communicate() is called.
// Returns true if data has been successfully put into the todo buffer
// else, returns false. You should re-send this.
bool ic_push_imu(MPUData data) {
  if (unreliable_buffer_filled) return false;
  unreliable_buffer.packet_type = PACKET_DATA_IMU;
  unreliable_buffer.accX = data.ax;
  unreliable_buffer.accY = data.ay;
  unreliable_buffer.accZ = data.az;
  unreliable_buffer.gyrX = data.gx;
  unreliable_buffer.gyrY = data.gy;
  unreliable_buffer.gyrZ = data.gz;
  unreliable_buffer_filled = true;
  return true;
}

// Queue the bullet data to be sent when communicate() is called.
// Returns true if data has been successfully put into the todo buffer
bool ic_push_bullet(uint8_t bullets) {
  if (reliable_buffer_filled) return false;
  reliable_buffer.packet_type = PACKET_DATA_BULLET;
  packet_bullet_t* pkt = (packet_bullet_t*)&reliable_buffer;
  pkt->bullet_count = bullets;
  reliable_buffer_filled = true;
  return true;
}

// Queue the health data to be sent when communicate() is called
// Returns true if data has been successfully put in the todo bufer
bool ic_push_health(uint8_t health) {
  if (reliable_buffer_filled) return false;
  reliable_buffer.packet_type = PACKET_DATA_HEALTH;
  packet_health_t* pkt = (packet_health_t*)&reliable_buffer;
  pkt->health_count = health;
  reliable_buffer_filled = true;
  return true;
}

bool ic_push_kick() {
  if (reliable_buffer_filled) return false;
  reliable_buffer.packet_type = PACKET_DATA_KICK;
  reliable_buffer_filled = true;
  return true;
}

// Get the gamestate, if any.
// WARNING: returns an empty packet with TYPE_INVALID if there is nothing.
//          You MUST handle this properly.
packet_gamestate_t ic_get_state() {
  if (!receive_buffer_filled) {
    packet_gamestate_t invalid;
    invalid.packet_type = PACKET_INVALID;
    return (packet_gamestate_t) invalid;
  }
  receive_buffer_filled = false;
  packet_gamestate_t my_buf = receive_buffer;
  return my_buf;  // return a copy
}

// ----- COMMUNICATION LOGIC -----

// Send all reliable & unreliable data in the buffer and receive gamestate data where applicable
void communicate() {

  // ---- RECEIVING LOGIC ----
  packet_general_t rcv = { 0 };
  bool shouldAck = false;
  if (await_packet((packet_general_t*)&rcv, 10)) {
    // case 1: checksum error (continue)
    if (verifyChecksum(&rcv)) {
      // case 2: hello
      // > relay wants to re-estab connections. handshake.
      if (rcv.packet_type == PACKET_HELLO) {
        await_handshake(true);
        return;
      }

      // case 4: ACKn
      if (rcv.packet_type == PACKET_ACK) {
        if (rcv.seq_num == exp_beetle_seq_num) {
          // > flag that we need not resend
          canSendReliable = true;
        }
      }
      // case 5: Receive a gamestate
      if (rcv.packet_type == PACKET_DATA_GAMESTATE) {
        // check if relay sequence number is correct
        shouldAck = true;
        if (relay_seq_num == rcv.seq_num) {
          // we have found the correct sequence number.
          relay_seq_num = (relay_seq_num + 1) % 256;
          // Actually handle the packet for hardware integration
          // WARN: if multiple gamestate comes in, this will OVERWRITE.
          receive_buffer_filled = true;
          packet_gamestate_t* tmp = (packet_gamestate_t*) &rcv;
          receive_buffer.bullet_num = tmp->bullet_num;
          receive_buffer.health_num = tmp->health_num;
        }
        // incorrect serial number, ignore
      }

      // For all other packet types from relay, we ignore them
    }
  }

  // ---- TRANSMISSION LOGIC ----

  // TRANSMIT UNRELIABLE DATA
  if (unreliable_buffer_filled && millis() - unreliableStartRateTime > unrel_tx_rate) {
    unreliableStartRateTime = millis();
    
    packet_imu_t& pkt = unreliable_buffer;

    // YAGNI, but left here for testing 
    // packet_imu_t pkt = { 0 };
    // pkt.packet_type = PACKET_DATA_IMU;
    // pkt.accX = rand() % 512;
    // pkt.accY = rand() % 512;
    // pkt.accZ = rand() % 512;
    // pkt.gyrX = rand() % 512;
    // pkt.gyrY = rand() % 512;
    // pkt.gyrZ = rand() % 512;
    // pkt.adc = rand() % 256;

    pkt.seq_num = beetle_seq_num;
    ++beetle_seq_num;
    setChecksum((packet_general_t*)&pkt);
    write_serial((packet_general_t*)&pkt);

    unreliable_buffer_filled = false;
  }

  // SEND RELIABLE DATA
  // if ACKn received AND there is something to send, send it!
  if (canSendReliable) {
    if (reliable_buffer_filled && millis() - reliableStartRateTime > rel_tx_rate) {  // simulate checking of reliableBuffer to send
      reliableStartRateTime = millis();
      canSendReliable = false;
      reliableSent = true;

      packet_general_t pkt = reliable_buffer;
      reliable_buffer_filled = false;

      // YAGNI, but left for testing purposes
      // packet_general_t pkt = {0};
      // getRandomReliablePacket(&pkt); // randomly choose a packet

      pkt.seq_num = beetle_seq_num;
      ++beetle_seq_num;
      exp_beetle_seq_num = beetle_seq_num;
      setChecksum((packet_general_t*)&pkt);
      write_serial((packet_general_t*)&pkt);
      memcpy(&cached_packet, &pkt, 20);
      reliableTimeStart = millis();
    }
    // reliable buffer not filled, contnue
  } else if (reliableSent && millis() - reliableTimeStart > 500) {  // constant here must be big
    // else we handle reliable packet timeout;
    reliableTimeStart = millis();
    write_serial(&cached_packet);
  }

  
  // TRANSMIT ACK
  if (shouldAck) {
    packet_ack_t ack = { 0 };
    ack.packet_type = PACKET_ACK;
    ack.seq_num = relay_seq_num;
    setChecksum((packet_general_t*)&ack);
    write_serial((packet_general_t*)&ack);
  }

}