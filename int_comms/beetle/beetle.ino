#include <Arduino.h>
#include "internal.hpp"

// Define the LED pin; change this if the LED is connected to a different pin
const int ledPin = 13;
bool ledState = LOW; // Initial state of the LED

void setup() {
    Serial.begin(115200);
    pinMode(ledPin, OUTPUT); // Set the LED pin as an output
}

bool hasData(float probability){ // mock
    float r = random(0, 1000) / 1000.0;
    return r < probability;
}

void processGamestate(packet_gamestate_t state){ // mock
    delay(state.bullet_num);
}

// This driver code is to simulate usage of the internal comms API
void loop() {
    // Wait until the handshake is completed
    while(!ic_connect()) { }
    
    // Mock the IMU sending 
    long start_time = millis();
    long delay = 25; // 40Hz == period of 25ms
    packet_gamestate_t state;
    while(1){
        // For each loop in this FSM...

        // 1. Send reliable if there is anything
        if(hasData(0.1)){
            int bullets = rand() % 10; // mock
            while(!ic_push_bullet(bullets)){ // 
                communicate(); // ensure that the buffer is cleared
            }
        }

        // 2. Check for gamestate
        state = ic_get_state();
        if(state.packet_type == PACKET_DATA_GAMESTATE){
            // process the state here
            processGamestate(state);
        }

        // 3. Send MPU data at a constant rate
        if(millis() - start_time >= delay){
            MPUData data;
            data.ax = rand() % 512;
            data.ay = rand() % 512;
            data.az = rand() % 512;
            data.gx = rand() % 512;
            data.gy = rand() % 512;
            data.gz = rand() % 512;
            while(!ic_push_imu(data)){
                start_time = millis();
                communicate(); // ensure that the buffer is cleared
            }
        }

        // 4. Check for gamestate
        state = ic_get_state();
        if(state.packet_type == PACKET_DATA_GAMESTATE){
            // process the state here
            processGamestate(state);
        }
    }

}

// Function to toggle the LED state
void toggleLED() {
    ledState = !ledState; // Invert the current state of the LED
    digitalWrite(ledPin, ledState); // Set the LED pin to the new state
}

void setLED(bool on){
  digitalWrite(ledPin, on);
}