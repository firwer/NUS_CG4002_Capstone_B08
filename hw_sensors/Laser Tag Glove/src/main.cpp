#include <Arduino.h>
#include <IRremote.hpp>
#include <MPU6050.h>
#include <Tone.h>
#include <ArduinoQueue.h>

// Define I/O pins
#define IMU_INTERRUPT_PIN 2
#define IR_SEND_PIN 5
#define BUTTON_PIN 4
#define BUZZER_PIN 3
#define FLEX_SENSOR_PIN A0
#define FLEX_THRESHOLD 500
#define NOTE_DELAY 50
#define DEBOUNCE_DELAY 50

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
uint8_t bulletState = 6; // No need for 16-bits

uint16_t flexValue = 0; // Flex sensor value can reach up to 1023, use uint16_t
bool isButtonPressed = false;
bool shotBeenFired = false;
uint8_t buttonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long lastSoundTime = 0;

Tone shotFired;

MPU6050 mpu;
const uint8_t samplingRate = 50; // Sampling interval, 8-bits is sufficient
unsigned long lastSampleTime = 0;
bool isRecording = false;
bool isMotionDetected = false;

int16_t recordedAccel[40][3]; // Sensor outputs 16-bit values
int16_t recordedGyro[40][3];  // Same here
uint8_t recordedPoints = 0;   // Max 40, 8-bits is enough

void motionDetected();
void printArray(int16_t data[40][3], uint8_t index);
void printResults();
void detectReload();
void playNoBulletsLeftTone();

void setup()
{
  Serial.begin(115200);
  mpu.initialize();
  if (!mpu.testConnection())
  {
    Serial.println("MPU6050 connection failed");
    while (1)
      ;
  }

  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);

  mpu.setDHPFMode(MPU6050_DHPF_0P63);
  mpu.setDLPFMode(MPU6050_DLPF_BW_20);
  mpu.setMotionDetectionThreshold(15);
  mpu.setMotionDetectionDuration(5);
  mpu.setIntMotionEnabled(true);

  pinMode(IMU_INTERRUPT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(IMU_INTERRUPT_PIN), motionDetected, RISING);
  pinMode(BUZZER_PIN, OUTPUT);
  shotFired.begin(BUZZER_PIN);
  pinMode(FLEX_SENSOR_PIN, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Serial.print(F("Send IR signals at pin "));
  Serial.println(IR_SEND_PIN);
  IrSender.begin(IR_SEND_PIN);
}

void loop()
{
  // For shots
  // detectReload(); //TODO integrate with game engine
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
    // Serial.println(soundQueue.itemCount());
    if (soundQueue.itemCount() > 0)
    {
      uint16_t note = soundQueue.dequeue();
      shotFired.play(note, 50); // Play note for 50ms
    }
    lastSoundTime = millis();
  }

  if (isButtonPressed && !shotBeenFired && flexValue >= FLEX_THRESHOLD)
  {
    if (curr_bulletsLeft > 0)
    {
      IrSender.sendNEC2(PLAYER_1_ADDRESS, 0x23, 0);
      curr_bulletsLeft--;
      soundQueue.enqueue(soundList[curr_bulletsLeft]);
      Serial.print("Bullets left: ");
      Serial.println(curr_bulletsLeft);
      Serial.println("Shot fired");
    }
    else
    {
      Serial.println("No bullets left");
      playNoBulletsLeftTone();
    }
    shotBeenFired = true;
  }

  if (isRecording)
  {
    if (millis() - lastSampleTime >= samplingRate && recordedPoints < 40)
    {
      lastSampleTime = millis();
      int16_t ax, ay, az;
      int16_t gx, gy, gz;
      mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

      recordedAccel[recordedPoints][0] = ax;
      recordedAccel[recordedPoints][1] = ay;
      recordedAccel[recordedPoints][2] = az;

      recordedGyro[recordedPoints][0] = gx;
      recordedGyro[recordedPoints][1] = gy;
      recordedGyro[recordedPoints][2] = gz;
      recordedPoints++;

      if (recordedPoints >= 40)
      {
        printResults();
        isRecording = false;
        recordedPoints = 0;
      }
    }
  }
}

void detectReload()
{
  if (curr_bulletsLeft == 0 && bulletState == 6)
  {
    isReloaded = true;
    curr_bulletsLeft = 6;
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

void motionDetected()
{
  if (!isRecording)
  {
    isMotionDetected = true;
    isRecording = true;
    Serial.println("Motion detected, recording started");
  }
}

void printArray(int16_t data[40][3], uint8_t index)
{
  Serial.print('"');
  Serial.print("[");
  for (uint8_t i = 0; i < 40; i++)
  {
    Serial.print(data[i][index]);
    if (i < 39)
      Serial.print(",");
  }
  Serial.print("]");
  Serial.print('"');
}

void printResults()
{
  printArray(recordedAccel, 0);
  Serial.print(",");
  printArray(recordedAccel, 1);
  Serial.print(",");
  printArray(recordedAccel, 2);
  Serial.print(",");
  printArray(recordedGyro, 0);
  Serial.print(",");
  printArray(recordedGyro, 1);
  Serial.print(",");
  printArray(recordedGyro, 2);
  Serial.print("\n");

  recordedPoints = 0;
  for (uint8_t i = 0; i < 40; i++)
  {
    recordedAccel[i][0] = 0;
    recordedAccel[i][1] = 0;
    recordedAccel[i][2] = 0;
    recordedGyro[i][0] = 0;
    recordedGyro[i][1] = 0;
    recordedGyro[i][2] = 0;
  }
}
