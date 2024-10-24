#include <Wire.h>
#include <MPU6050.h>
#include <EEPROM.h>
#include "internal.hpp"
#include "packet.h"
#include <MPU6050.h>
#include <Kalman.h>
#include <ArduinoQueue.h>
#include <Tone.h>

#define LED_OUTPUT_PIN 5
#define IMU_INTERRUPT_PIN 2
#define MPU_SAMPLE_RATE 50
#define VIBRATOR_PIN 4
#define FEEDBACK_PLAY_TIME 750
#define KICK_DEBOUNCE_TIME 1000
#define NOTE_DELAY 75
#define BUZZER_PIN 3

MPU6050 mpu;
ArduinoQueue<uint16_t> noteQueue(20);
#define MOVING_AVERAGE_SIZE 10
ArduinoQueue<float> movingAverageQueue(MOVING_AVERAGE_SIZE);
float movingAverage = 0;

unsigned long lastSoundTime = 0;
unsigned long playingFeedbackTime = 0;
bool isKickDetected = false;
bool playingFeedback = false;

const float ACCEL_THRESHOLD = -5.0; // should be in terms of m/s^2
const float KICK_ANGLE = 65;        // should be y-axis
Kalman kalmanY;                     // Kalman filter for Y (pitch)

Tone melody;

void motionDetected();
void detectKick();
void playMotionFeedback();
void playBLEFeedback();

struct CalibrationData
{
  int16_t xoffset;
  int16_t yoffset;
  int16_t zoffset;
  int16_t xgoffset;
  int16_t ygoffset;
  int16_t zgoffset;
};

uint32_t timer;
float accX, accY, accZ, accelZReal;
float gyroX, gyroY, gyroZ;
float roll, pitch;

CalibrationData calibration;

volatile unsigned long lastKickTime = 0;
unsigned long lastSampleTime = 0;

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
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_8);
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);

  mpu.setDHPFMode(MPU6050_DHPF_5);
  mpu.setDLPFMode(MPU6050_DLPF_BW_256);

  calibration = EEPROM.get(0, calibration);
  mpu.setXAccelOffset(calibration.xoffset);
  mpu.setYAccelOffset(calibration.yoffset);
  mpu.setZAccelOffset(calibration.zoffset);
  mpu.setXGyroOffset(calibration.xgoffset);
  mpu.setYGyroOffset(calibration.ygoffset);
  mpu.setZGyroOffset(calibration.zgoffset);

  pinMode(BUZZER_PIN, OUTPUT);
  melody.begin(BUZZER_PIN);

  pinMode(LED_OUTPUT_PIN, OUTPUT);
  pinMode(VIBRATOR_PIN, OUTPUT);
  while (!ic_connect())
    ;
  playBLEFeedback();
  timer = micros();
}

void loop()
{
  // ensure that we are connected even when no kick is being done
  // WARN: might cause a spinlock.
  // @wanlin
  if (communicate())
  {
    playBLEFeedback();
  }

  detectKick();

  if (isKickDetected)
  {
    // push boolean kick detected to the server
    // @wanlin
    ic_push_kick();
    if (communicate())
    {
      playBLEFeedback();
    }
    playMotionFeedback();
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
  if (millis() - lastSoundTime > NOTE_DELAY)
  {
    if (noteQueue.itemCount() > 0)
    {
      uint16_t note = noteQueue.dequeue();
      melody.play(note, 100); // Play note for 50ms
    }
    lastSoundTime = millis();
  }
}

void detectKick()
{
  // Read raw accelerometer and gyroscope data
  int16_t ax, ay, az;
  int16_t gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // Convert to proper units
  accX = (float)ax / 16384.0 / 4.0;
  accY = (float)ay / 16384.0 / 4.0;
  accZ = (float)az / 16384.0 / 4.0;
  accelZReal = ((az / 32767.0) * 8.0 * 9.81);

  // Calculate the angles from the accelerometer
  float pitchAcc = atan2(-accX, sqrt(accY * accY + accZ * accZ)) * 180 / PI;

  float dt = (float)(micros() - timer) / 1000000;
  timer = micros();

  pitch = kalmanY.getAngle(pitchAcc, gyroY, dt);

  if (millis() - lastSampleTime >= MPU_SAMPLE_RATE)
  {
    if (movingAverageQueue.itemCount() == MOVING_AVERAGE_SIZE)
    {
      movingAverage -= movingAverageQueue.dequeue();
      movingAverageQueue.enqueue(accelZReal);
      movingAverage += accelZReal;
      Serial.print("Moving Average: ");
      Serial.println(movingAverage / MOVING_AVERAGE_SIZE);
      Serial.print("Pitch: ");
      Serial.println(pitch);
      if ((accelZReal / MOVING_AVERAGE_SIZE) < ACCEL_THRESHOLD && pitch < KICK_ANGLE)
      {
        // Debounce to avoid multiple detections
        if (millis() - lastKickTime > KICK_DEBOUNCE_TIME)
        {
          isKickDetected = true;
          lastKickTime = millis();
          Serial.println("Kick Detected");
        }
      }
    }
    else
    {
      movingAverageQueue.enqueue(accelZReal);
      movingAverage += accelZReal;
    }
    lastSampleTime = millis();
  }
}

void playMotionFeedback()
{
  noteQueue.enqueue(NOTE_CS6);
  noteQueue.enqueue(NOTE_D6);
  noteQueue.enqueue(NOTE_E6);
}

void playBLEFeedback()
{
  noteQueue.enqueue(NOTE_F6);
  noteQueue.enqueue(NOTE_G6);
  noteQueue.enqueue(NOTE_A6);
}
