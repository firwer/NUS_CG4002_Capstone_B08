#include <Arduino.h>
#include <IRremote.hpp>
#include <MPU6050.h>
#include <Tone.h>
#include <ArduinoQueue.h>
#include <EEPROM.h>

// Include communication logic
#include "internal.hpp"
#include "packet.h"

// Define I/O pins
#define IMU_INTERRUPT_PIN 2
#define IR_SEND_PIN 5
#define BUTTON_PIN 4
#define BUZZER_PIN 3
#define FLEX_SENSOR_PIN A0
#define FLEX_THRESHOLD 500
#define NOTE_DELAY 100
#define DEBOUNCE_DELAY 50
#define MPU_SAMPLING_RATE 40
#define NUM_RECORDED_POINTS 60

const uint8_t PLAYER_1_ADDRESS = 0x23; // 8-bits, no need for 16-bits
const uint8_t PLAYER_2_ADDRESS = 0x77;

// Queue reduced to save memory
ArduinoQueue<uint16_t> soundQueue(10); // Tones are now stored in 16-bit integers

// Updated to uint16_t to support values up to 1000
uint16_t soundList[10] = {
    NOTE_C5,
    NOTE_D5,
    NOTE_E5,
    NOTE_F5,
    NOTE_G5,
    NOTE_A5,
    NOTE_B5,
    NOTE_C6,
    NOTE_D6,
    NOTE_E6};

// For gun shot
bool isReloaded = false;
uint8_t curr_bulletsLeft = 6;
uint8_t incoming_bulletState = 0;
bool isFullMagazineTonePlayed = false;
uint16_t flexValue = 0;
bool isButtonPressed = false;
bool shotBeenFired = false;
uint8_t buttonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long lastSoundTime = 0;

Tone shotFired;

MPU6050 mpu;
const unsigned long SAMPLING_DELAY = 1000 / MPU_SAMPLING_RATE;
unsigned long lastSampleTime = 0;
bool isRecording = false;
bool isMotionDetected = false;
bool isMotionTunePlayed = false;
bool hasMotionEnded = false;

MPUData mpuData; // @wanlin

struct MPUData_FLOAT
{
  int16_t accelXreal;
  int16_t accelYreal;
  int16_t accelZreal;
  int16_t gyroXreal;
  int16_t gyroYreal;
  int16_t gyroZreal;
} MPUData_FLOAT;
struct CalibrationData
{
  int16_t xoffset;
  int16_t yoffset;
  int16_t zoffset;
  int16_t xgoffset;
  int16_t ygoffset;
  int16_t zgoffset;
};

CalibrationData calibrationData;
uint8_t recordedPoints = 0; // Max 40, 8-bits is enough

void motionDetected();
void sendIMUData();
void detectReload();
void playNoBulletsLeftTone();
void playFullMagazineTone();
void playMotionFeedback();
void playMotionEndFeedback();

void setup()
{
  Serial.begin(115200);
  mpu.initialize();
  if (!mpu.testConnection())
  {
    // Serial.println("MPU6050 connection failed");
    while (1)
      ;
  }
  // THIS IS RED GLOVE CALIBRATION DATA
  calibrationData.xoffset = -1021;
  calibrationData.yoffset = -898;
  calibrationData.zoffset = 1591;
  calibrationData.xgoffset = 6;
  calibrationData.ygoffset = -38;
  calibrationData.zgoffset = 31;
  // THIS IS GREEN GLOVE CALIBRATION DATA the one with the capacitor
  //  calibrationData.xoffset = -2322 ;
  //  calibrationData.yoffset = -1300;
  //  calibrationData.zoffset = 981;
  //  calibrationData.xgoffset = 103;
  //  calibrationData.ygoffset = -27;
  //  calibrationData.zgoffset = 3;

  // EEPROM.put(0, PLAYER_1_ADDRESS); //TODO: Store in EEPROM
  // EEPROM.put(0, PLAYER_2_ADDRESS); //TODO: Store in EEPROM
  // EEPROM.put(1, calibrationData); //TODO: Store in EEPROM

  mpu.setXAccelOffset(calibrationData.xoffset);
  mpu.setYAccelOffset(calibrationData.yoffset);
  mpu.setZAccelOffset(calibrationData.zoffset);
  mpu.setXGyroOffset(calibrationData.xgoffset);
  mpu.setYGyroOffset(calibrationData.ygoffset);
  mpu.setZGyroOffset(calibrationData.zgoffset);

  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_8);
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);

  mpu.setDHPFMode(MPU6050_DHPF_1P25);
  mpu.setDLPFMode(MPU6050_DLPF_BW_20);
  mpu.setMotionDetectionThreshold(60);
  mpu.setMotionDetectionDuration(5);

  mpu.setIntMotionEnabled(true);

  pinMode(IMU_INTERRUPT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(IMU_INTERRUPT_PIN), motionDetected, RISING);
  pinMode(BUZZER_PIN, OUTPUT);
  shotFired.begin(BUZZER_PIN);
  pinMode(FLEX_SENSOR_PIN, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // Serial.print(F("Send IR signals at pin "));
  Serial.println(IR_SEND_PIN);
  IrSender.begin(IR_SEND_PIN);

  // COMMUNICATION @wanlin
  while (ic_connect())
    ;
  shotFired.play(NOTE_A7, 100);
}

packet_gamestate_t pkt;
void loop()
{
  // @wanlin
  // Synchronize the bullet state
  communicate();
  pkt = ic_get_state();
  if (pkt.packet_type == PACKET_DATA_GAMESTATE)
  {
    incoming_bulletState = pkt.bullet_num;
  }

  //==================== GUN SHOT SUBROUTINE ====================
  detectReloadAndSynchronise(incoming_bulletState); // TODO integrate with game engine

  flexValue = analogRead(FLEX_SENSOR_PIN);
  buttonState = digitalRead(BUTTON_PIN);
  if (millis() - lastDebounceTime > DEBOUNCE_DELAY)
  {
    if (buttonState == LOW)
    {
      isButtonPressed = true;
    }
    else
    {
      isButtonPressed = false;
      shotBeenFired = false;
    }
    lastDebounceTime = millis();
  }

  if (millis() - lastSoundTime > NOTE_DELAY)
  {
    if (soundQueue.itemCount() > 0)
    {
      uint16_t note = soundQueue.dequeue();
      shotFired.play(note, 100); // Play note for 50ms
    }
    lastSoundTime = millis();
  }

  if (curr_bulletsLeft == 6 && !isFullMagazineTonePlayed)
  {
    playFullMagazineTone();
    isFullMagazineTonePlayed = true;
  }

  if (isButtonPressed && !shotBeenFired && flexValue >= FLEX_THRESHOLD)
  {
    if (curr_bulletsLeft > 0)
    {
      IrSender.sendNEC2(PLAYER_1_ADDRESS, 0x23, 0);
      curr_bulletsLeft--;
      isFullMagazineTonePlayed = false;
      soundQueue.enqueue(soundList[curr_bulletsLeft]);
      // @wanlin
    }
    else
    {
      playNoBulletsLeftTone();
    }
    // push bullet packet for any gun action attempted, regardless of num bullets
    ic_push_bullet(curr_bulletsLeft);
    communicate();
    shotBeenFired = true;
  }

  //==================== MPU6050 SUBROUTINE====================

  if (isRecording)
  {
    if (!isMotionTunePlayed)
    {
      // Serial.println("Motion Detected. Displaying raw then corresponding real readings.");
      playMotionFeedback();
      isMotionTunePlayed = true;
      hasMotionEnded = false;
    }
    if (millis() - lastSampleTime >= SAMPLING_DELAY && recordedPoints < NUM_RECORDED_POINTS)
    {
      mpu.getMotion6(&mpuData.ax, &mpuData.ay, &mpuData.az, &mpuData.gx, &mpuData.gy, &mpuData.gz);
      // Take the raw 16bit data, divide by 32767 to get the ratio, multiply by 4g to get the real value,
      // then multiply by 9.81 to get m/s^2
      // multiply by 100 to get integers
      mpuData.ax = (((mpuData.ax) / 32767.0) * 4.0 * 9.81) * 100;
      mpuData.ay = (((mpuData.ay) / 32767.0) * 4.0 * 9.81) * 100;
      mpuData.az = (((mpuData.az) / 32767.0) * 4.0 * 9.81) * 100;
      // same for gyroscope scaling
      mpuData.gx = (((mpuData.gx) / 32767.0) * 250.0) * 100;
      mpuData.gy = (((mpuData.gy) / 32767.0) * 250.0) * 100;
      mpuData.gz = (((mpuData.gz) / 32767.0) * 250.0) * 100;

      // @wanlin
      ic_push_imu(mpuData);
      communicate();

      lastSampleTime = millis();
      recordedPoints++;

      if (recordedPoints >= NUM_RECORDED_POINTS && !hasMotionEnded)
      {

        playMotionEndFeedback();
        isRecording = false;
        recordedPoints = 0;
        isMotionTunePlayed = false;
        hasMotionEnded = true;
      }
    }
  }
}

void detectReloadAndSynchronise(uint8_t incoming_bulletState)
{
  if (curr_bulletsLeft == 0 && incoming_bulletState == 6)
  {
    isReloaded = true;
    curr_bulletsLeft = 6;
  }
  else if (curr_bulletsLeft != incoming_bulletState && curr_bulletsLeft != 0)
  {
    curr_bulletsLeft = incoming_bulletState;
  }
  else
  {
    isReloaded = false;
  }
}

void playNoBulletsLeftTone()
{
  soundQueue.enqueue(NOTE_C6);
  soundQueue.enqueue(NOTE_A5);
  soundQueue.enqueue(NOTE_C5);
}

void playFullMagazineTone()
{
  soundQueue.enqueue(NOTE_C5);
  soundQueue.enqueue(NOTE_A5);
  soundQueue.enqueue(NOTE_C6);
}

void motionDetected()
{
  if (!isRecording)
  {
    isMotionDetected = true;
    isRecording = true;
  }
}

void playMotionFeedback()
{
  soundQueue.enqueue(NOTE_CS6);
  soundQueue.enqueue(NOTE_D6);
  soundQueue.enqueue(NOTE_E6);
}
void playMotionEndFeedback()
{
  soundQueue.enqueue(NOTE_E6);
  soundQueue.enqueue(NOTE_D6);
  soundQueue.enqueue(NOTE_CS6);
}
