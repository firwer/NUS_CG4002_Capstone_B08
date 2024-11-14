
# Arduino Laser Tag Health and Shield System

This project uses an Arduino Bluno to manage player health and shield states in a laser tag game, providing feedback via IR signals, a buzzer, and a vibration motor.

## Features
- **Health and Shield Management**: Tracks player health and shield values.
- **IR Receiver**: Receives attacks from opponents.
- **Feedback Mechanisms**: Provides audio and vibration feedback for health/shield changes.
- **Bluetooth Communication**: Syncs health and shield states with the game engine.

## Hardware Requirements
- Arduino Bluno
- IR Receiver (Pin 4)
- Buzzer (Pin 3, PWM)
- Vibration Motor (Pin 5)
- 3.7V battery with 5v power boost board

## Library Requirements
This project uses the following open-source libraries:
- [Tone Library](https://github.com/bhagman/Tone) by Brett Hagman: Provides functions for generating tones on Arduino.
- [EEPROM Library](https://docs.arduino.cc/learn/built-in-libraries/eeprom/): Built-in Arduino library for storing data in the non-volatile memory.
- [ArduinoQueue Library](https://github.com/EinarArnason/ArduinoQueue): Backbone of audio feedback system.
- [IRremote Library](https://github.com/Arduino-IRremote/Arduino-IRremote)

