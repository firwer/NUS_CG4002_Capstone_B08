# Arduino Kick Detection System

This utilises an Arduino Bluno and a MPU6050 IMU to detect leg motions (such as walk, stomp, kick), collect tri-axis accelerometer and gyroscope readings. It provides feedback through a buzzer, LED, and vibrator motor. This feeds the AI model to differentiate between the different motions.

## Features
- **Motion Detection** using accelerometer and gyroscope data
- **Feedback Mechanisms**: Buzzer, LED, and vibrator motor
- **Bluetooth Communication** with an external server for logging

## Hardware Requirements
- Arduino Bluno (DFR-0339)
- MPU6050 Accelerometer
- Buzzer (Pin 3), LED (Pin 5), Vibrator Motor (Pin 4)
- 3.7V battery with 5V power boost board

## Library Requirements
This project uses the following open-source libraries:

- [Tone Library](https://github.com/bhagman/Tone) by Brett Hagman: Provides functions for generating tones on Arduino.
- [MPU6050 Library](https://github.com/ElectronicCats/mpu6050) by Electronic Cats: Enables easy communication with the MPU6050 sensor.
- [EEPROM Library](https://docs.arduino.cc/learn/built-in-libraries/eeprom/): Built-in Arduino library for storing data in the non-volatile memory. In this case, we used it to store the unique calibration offsets for different IMUs.
