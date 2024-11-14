# Arduino Kick Detection System

This utilises an Arduino Bluno, MPU6050 sensor, and a Kalman filter to detect kicks based on acceleration and pitch without the use of AI (ie kick, no kick). It provides feedback through a buzzer, LED, and vibrator motor.

## Features
- **Kick Detection** using accelerometer and gyroscope data
- **Kalman Filtering** to reduce noise and to return roll, pitch and yaw in degrees
- **Moving Average** for stable readings
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
- [Kalman Filter Library](https://github.com/TKJElectronics/KalmanFilter) by TKJElectronics: Used to reduce noise in accelerometer and gyroscope data.
- [MPU6050 Library](https://github.com/ElectronicCats/mpu6050) by Electronic Cats: Enables easy communication with the MPU6050 sensor.
- [EEPROM Library](https://docs.arduino.cc/learn/built-in-libraries/eeprom/): Built-in Arduino library for storing data in the non-volatile memory.
