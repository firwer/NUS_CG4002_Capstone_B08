# Arduino Laser Tag Glove System

This project uses an Arduino Bluno with an MPU6050 IMU, IR communication, and a flex sensor to simulate a laser tag gun glove. It detects hand motion with the IMU, collecting tri-axis acceleration and tri-axis gyroscope data for AI gesture recognition (basket, bowl, bomb, reload, volley, logout and invalid). Audio feedbacks for gun shot and motion detection are provided via a buzzer.

## Features
- **Gun Shot Detection**: Uses a flex sensor and button to detect when a shot is fired.
- **Reload Synchronization**: Monitors bullet count and reloads when necessary, syncing with the game engine.
- **Motion Detection**: Detects and records IMU data for specific motions, with feedback for the start and end of data recording.
- **Feedback Mechanisms**: Buzzer feedback for shooting, reloading, and critical states.
- **Bluetooth Communication** with a game engine to update bullet states and to transmit IMU data to external servers.

## Hardware Requirements
- Arduino Bluno
- MPU6050 Accelerometer and Gyroscope
- IR Transmitter (Pin 5)
- Button (Pin 4)
- Buzzer (Pin 3)
- Flex Sensor (Pin A0)
- 3.7V battery with 5V power boost board should suffice (Note: For the gloves, we used 2x 18650 Li-ron batteries in a 5V output board strapped onto the player's forearm)

## Library Requirements
This project uses the following open-source libraries:

- [Tone Library](https://github.com/bhagman/Tone) by Brett Hagman: Provides functions for generating tones on Arduino.
- [MPU6050 Library](https://github.com/ElectronicCats/mpu6050) by Electronic Cats: Enables easy communication with the MPU6050 sensor.
- [IRremote Library](https://github.com/Arduino-IRremote/Arduino-IRremote): Allows for IR communication to simulate shots.
- [EEPROM Library](https://docs.arduino.cc/learn/built-in-libraries/eeprom/): Stores data in non-volatile memory, including player configuration. In this case, we also used it to store the unique calibration offsets for different IMUs.
- [MPU6050 Library](https://github.com/ElectronicCats/mpu6050) by Electronic Cats: Enables easy communication with the MPU6050 sensor.