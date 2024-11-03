#ifndef PACKET_H
#define PACKET_H

#include <stdint.h>

#define PACKET_ACK 0x1
#define PACKET_SYN_ACK 0x2
#define PACKET_DATA_IMU 0x3
#define PACKET_DATA_KICK 0x4
#define PACKET_DATA_BULLET 0x5
#define PACKET_DATA_HEALTH 0x6
#define PACKET_DATA_GAMESTATE 0x7
#define PACKET_CONN_ESTAB 0xD
#define PACKET_INVALID 0xE
#define PACKET_HELLO 0xF

#define PACKET_SIZE 20
#define TIMEOUT_MS 1000

#define MASK_DEVICE_ID 0x02
#define MASK_PACKET_TYPE 0x20

typedef struct packet_imu_t {
    uint8_t packet_type;
    uint8_t seq_num;
    uint8_t adc;
    int16_t accX;
    int16_t accY;
    int16_t accZ;
    int16_t gyrX;
    int16_t gyrY;
    int16_t gyrZ;
    uint8_t device;
    uint8_t pad0;
    uint16_t pad1;
    uint8_t crc8;
};

// use this before casting
typedef struct packet_general_t {
    uint8_t packet_type;
    uint8_t seq_num;
    uint64_t data;
    uint64_t data1;
    uint8_t data2;
    uint8_t crc8;
};

typedef struct packet_bullet_t {
    uint8_t packet_type;
    uint8_t seq_num;
    uint8_t bullet_count;
    uint64_t pad0;
    uint64_t pad1;
    uint8_t crc8;
};

typedef struct packet_health_t {
    uint8_t packet_type;
    uint8_t seq_num;
    uint8_t health_count;
    uint8_t shield_count;
    uint64_t pad0;
    uint32_t pad1;
    uint16_t pad2;
    uint8_t pad3;
    uint8_t crc8;
};

typedef struct packet_kick_t { // NOTE: receiving a KICK packet implies a kick happened
    uint8_t packet_type;
    uint8_t seq_num;
    uint8_t pad0;
    uint64_t pad1;
    uint64_t pad2;
    uint8_t crc8;
};

typedef struct packet_gamestate_t {
    uint8_t packet_type;
    uint8_t seq_num;
    uint8_t bullet_num;
    uint8_t health_num;
    uint8_t shield_num;
    uint64_t pad0;
    uint32_t pad1;
    uint16_t pad2;
    uint8_t crc8;
};

typedef struct packet_ack_t {
    uint8_t packet_type;
    uint8_t seq_num;
    uint16_t pad0;
    uint64_t pad1;
    uint32_t pad2;
    uint16_t pad3;
    uint8_t pad4;
    uint8_t crc8;
};

typedef struct packet_conn_estab_t {
    uint8_t packet_type;
    uint8_t seq_num;
    uint16_t pad0;
    uint64_t pad1;
    uint32_t pad2;
    uint16_t pad3;
    uint8_t pad4;
    uint8_t crc8;
};

#endif // PACKET_H