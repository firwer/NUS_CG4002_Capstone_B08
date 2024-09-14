#include <Arduino.h>
#include "internal.hpp"

// Define the LED pin; change this if the LED is connected to a different pin
const int ledPin = 13;
bool ledState = LOW; // Initial state of the LED

void setup() {
    Serial.begin(115200);
    pinMode(ledPin, OUTPUT); // Set the LED pin as an output
}

void loop() {
    // Wait until the handshake is completed
    while(!isConnected) {
        await_handshake(false);
    }
    
    // setLED(1);
    while(1){
      // test_throughput_unreliable(50);
      // test_throughput_reliable(50);
      test_receive_reliable();
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