#include <Wire.h>
#include <MPU6050.h>
#include <EEPROM.h>
#define LED_OUTPUT_PIN 5
#define IMU_INTERRUPT_PIN 2
#define MPU_SAMPLE_RATE 20
#define VIBRATOR_PIN 4
#define FEEDBACK_PLAY_TIME 750

#include "internal.hpp"
#include "packet.h"

MPU6050 mpu;

const unsigned long SAMPLING_DELAY = 1000 / MPU_SAMPLE_RATE;
unsigned long lastSampleTime = 0;
unsigned long playingFeedbackTime = 0;
bool isKickDetected = false;
bool playingFeedback = false;

void motionDetected();

struct CalibrationData
{
  int16_t xoffset;
  int16_t yoffset;
  int16_t zoffset;
  int16_t xgoffset;
  int16_t ygoffset;
  int16_t zgoffset;
};

CalibrationData calibration;

volatile unsigned long lastKickTime = 0;

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
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_16);
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);

  mpu.setDHPFMode(MPU6050_DHPF_1P25);
  mpu.setDLPFMode(MPU6050_DLPF_BW_20);
  mpu.setMotionDetectionThreshold(130);
  mpu.setMotionDetectionDuration(1);

  mpu.setIntMotionEnabled(true);

  pinMode(IMU_INTERRUPT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(IMU_INTERRUPT_PIN), motionDetected, RISING);
  pinMode(LED_OUTPUT_PIN, OUTPUT);
  pinMode(VIBRATOR_PIN, OUTPUT);
  while (!ic_connect())
    ;
  digitalWrite(LED_OUTPUT_PIN, HIGH);
  delay(100);
  digitalWrite(LED_OUTPUT_PIN, LOW);
}

void loop()
{
  // ensure that we are connected even when no kick is being done
  // WARN: might cause a spinlock.
  // @wanlin
  communicate();

  if (isKickDetected)
  {
    // push boolean kick detected to the server
    // @wanlin
    ic_push_kick();
    communicate();
    playingFeedback = true;
    isKickDetected = false;
    playingFeedbackTime = millis();
    digitalWrite(LED_OUTPUT_PIN, HIGH);
    digitalWrite(VIBRATOR_PIN, HIGH);
  }

  if (playingFeedback && millis() - playingFeedbackTime >= FEEDBACK_PLAY_TIME)
  {
    digitalWrite(LED_OUTPUT_PIN, LOW);
    digitalWrite(VIBRATOR_PIN, LOW);
    playingFeedback = false;
  }
}

void motionDetected()
{

  if (millis() - lastKickTime > 200) // 200 ms debounce
  {
    isKickDetected = true;
    lastKickTime = millis();
  }
}
