#include <Wire.h>
#include <MPU6050.h>
#include <EEPROM.h>
#define LED_OUTPUT_PIN 5
#define IMU_INTERRUPT_PIN 2
#define MPU_SAMPLE_RATE 20
#define VIBRATOR_PIN 4

#include "internal.hpp"
#include "packet.h"

MPU6050 mpu;

const unsigned long SAMPLING_DELAY = 1000 / MPU_SAMPLE_RATE;
unsigned long lastSampleTime = 0;
bool isRecording = false;
bool isMotionDetected = false;
bool isKickDetected = false;

uint8_t recordedPoints = 0; // Max 40, 8-bits is enough

void motionDetected();
unsigned long previousMillis = 0;
const long interval = 500;
bool isLedOn = false;

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

volatile unsigned long lastInterruptTime = 0;

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

  pinMode(IMU_INTERRUPT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(IMU_INTERRUPT_PIN), motionDetected, RISING);
  pinMode(LED_OUTPUT_PIN, OUTPUT);
  pinMode(VIBRATOR_PIN, OUTPUT);
  while(!ic_connect());
}

void loop()
{
  // ensure that we are connected even when no kick is being done
  // WARN: might cause a spinlock.
  // @wanlin
  communicate();
  unsigned long currentMillis = millis();

  if (isKickDetected && !isLedOn)
  {
    // push boolean kick detected to the server
    // @wanlin
    ic_push_kick();
    communicate();
    
    digitalWrite(LED_OUTPUT_PIN, HIGH);
    digitalWrite(VIBRATOR_PIN, HIGH);
    previousMillis = currentMillis;
    isLedOn = true;
    isKickDetected = false;
  }

  if (isLedOn && currentMillis - previousMillis >= interval)
  {
    digitalWrite(LED_OUTPUT_PIN, LOW);
    digitalWrite(VIBRATOR_PIN, LOW);
    isLedOn = false;
  }
}

void motionDetected()
{
  unsigned long interruptTime = millis();
  if (interruptTime - lastInterruptTime > 200) // 200 ms debounce
  {
    if (!isRecording)
    {
      isMotionDetected = true;
      isRecording = true;
      isKickDetected = true;
    }
    lastInterruptTime = interruptTime;
  }
}
