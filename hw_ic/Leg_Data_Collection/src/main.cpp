#include <Arduino.h>
#include <MPU6050.h>
#include <Tone.h>
#include <ArduinoQueue.h>
#include <EEPROM.h>

// Include communication logic
#include "internal.hpp"
#include "packet.h"

#define IMU_INTERRUPT_PIN 2
#define BUZZER_PIN 3
#define NOTE_DELAY 100

#define MPU_SAMPLING_RATE 40
#define NUM_RECORDED_POINTS 54

#define KICK_DEBOUNCE_TIME 1000

unsigned long lastKickTime = 0;

ArduinoQueue<uint16_t> noteQueue(10); // Tones are now stored in 16-bit integers
unsigned long lastSoundTime = 0;
Tone melody;

MPU6050 mpu;
const unsigned long SAMPLING_DELAY = 1000 / MPU_SAMPLING_RATE;
unsigned long lastSampleTime = 0;
bool isRecording = false;
bool isMotionDetected = false;
bool isMotionTunePlayed = false;
bool hasMotionEnded = false;
uint8_t actionCounter = 0;
MPUData mpuData; // @wanlin

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
uint8_t recordedPoints = 0;
void motionDetected();
void playBLEFeedback();
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

  EEPROM.get(0, calibrationData); // TODO: Store in EEPROM

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
  mpu.setMotionDetectionThreshold(80);
  mpu.setMotionDetectionDuration(5);

  mpu.setIntMotionEnabled(true);

  pinMode(IMU_INTERRUPT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(IMU_INTERRUPT_PIN), motionDetected, RISING);
  pinMode(BUZZER_PIN, OUTPUT);
  melody.begin(BUZZER_PIN);

  // COMMUNICATION @wanlin
  while (!ic_connect())
    ;
  playBLEFeedback();
}

void loop()
{
  if(communicate()){
      playBLEFeedback();
  }
  
  if (millis() - lastSoundTime > NOTE_DELAY)
  {
    if (noteQueue.itemCount() > 0)
    {
      uint16_t note = noteQueue.dequeue();
      melody.play(note, 100); // Play note for 50ms
    }
    lastSoundTime = millis();
  }

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
      // CHANGE THIS SHIT TODO TODO CHANGE CHANGE
      mpuData.ax = (((mpuData.ax) / 32767.0) * 4.0 * 9.81) * 100;
      mpuData.ay = (((mpuData.ay) / 32767.0) * 4.0 * 9.81) * 100;
      mpuData.az = (((mpuData.az) / 32767.0) * 4.0 * 9.81) * 100;
      // same for gyroscope scaling
      mpuData.gx = (((mpuData.gx) / 32767.0) * 250.0) * 100;
      mpuData.gy = (((mpuData.gy) / 32767.0) * 250.0) * 100;
      mpuData.gz = (((mpuData.gz) / 32767.0) * 250.0) * 100;

      // @wanlin
      ic_push_imu(mpuData, actionCounter, IMU_DEVICE_LEG);
      ic_udp_quicksend();
      // communicate();

      lastSampleTime = millis();
      recordedPoints++;

      if (recordedPoints >= NUM_RECORDED_POINTS && !hasMotionEnded)
      {

        playMotionEndFeedback();
        isRecording = false;
        recordedPoints = 0;
        isMotionTunePlayed = false;
        hasMotionEnded = true;
        ++actionCounter;
      }
    }
  }
}

void motionDetected()
{
  if (!isRecording && millis() - lastKickTime > KICK_DEBOUNCE_TIME)
  {
    isMotionDetected = true;
    isRecording = true;
    lastKickTime = millis();
  }
}

void playBLEFeedback()
{
  noteQueue.enqueue(NOTE_F6);
  noteQueue.enqueue(NOTE_G6);
  noteQueue.enqueue(NOTE_A6);
}
void playMotionFeedback()
{
  noteQueue.enqueue(NOTE_CS6);
  noteQueue.enqueue(NOTE_D6);
  noteQueue.enqueue(NOTE_E6);
}
void playMotionEndFeedback()
{
  noteQueue.enqueue(NOTE_E6);
  noteQueue.enqueue(NOTE_D6);
  noteQueue.enqueue(NOTE_CS6);
}
