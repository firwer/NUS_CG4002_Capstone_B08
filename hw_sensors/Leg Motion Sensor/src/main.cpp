#include <Wire.h>
#include <MPU6050.h>
#include <EEPROM.h>
#define LED_OUTPUT_PIN 5
#define IMU_INTERRUPT_PIN 2

MPU6050 mpu;

const uint8_t samplingRate = 50; // Sampling interval, 8-bits is sufficient
unsigned long lastSampleTime = 0;
bool isRecording = false;
bool isMotionDetected = false;
bool isKickDetected = false;

int16_t recordedAccel[40][3]; // Sensor outputs 16-bit values
int16_t recordedGyro[40][3];  // Same here
uint8_t recordedPoints = 0;   // Max 40, 8-bits is enough

void motionDetected();
void printResults();
void printArray(int16_t data[40][3], uint8_t index);

unsigned long previousMillis = 0;
const long interval = 100;
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

  CalibrationData storedCalibration;
  EEPROM.get(0, storedCalibration);
  Serial.println("Stored calibration data: ");
  Serial.print("X offset: ");
  Serial.println(storedCalibration.xoffset);
  Serial.print("Y offset: ");
  Serial.println(storedCalibration.yoffset);
  Serial.print("Z offset: ");
  Serial.println(storedCalibration.zoffset);
  Serial.print("XG offset: ");
  Serial.println(storedCalibration.xgoffset);
  Serial.print("YG offset: ");
  Serial.println(storedCalibration.ygoffset);
  Serial.print("ZG offset: ");
  Serial.println(storedCalibration.zgoffset);

  // mpu.setXAccelOffset(storedCalibration.xoffset);
  // mpu.setYAccelOffset(storedCalibration.yoffset);
  // mpu.setZAccelOffset(storedCalibration.zoffset);
  // mpu.setXGyroOffset(storedCalibration.xgoffset);
  // mpu.setYGyroOffset(storedCalibration.ygoffset);
  // mpu.setZGyroOffset(storedCalibration.zgoffset);

  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_16);
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_2000);

  mpu.setDHPFMode(MPU6050_DHPF_5);
  mpu.setDLPFMode(MPU6050_DLPF_BW_42);

  mpu.setMotionDetectionThreshold(135);
  mpu.setMotionDetectionDuration(2);
  mpu.setIntMotionEnabled(true);

  pinMode(IMU_INTERRUPT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(IMU_INTERRUPT_PIN), motionDetected, RISING);
  pinMode(LED_OUTPUT_PIN, OUTPUT);
}

void loop()
{
  unsigned long currentMillis = millis();

  if (isRecording)
  {
    if (millis() - lastSampleTime >= samplingRate && recordedPoints < 40)
    {
      isKickDetected = true;
      lastSampleTime = millis();
      int16_t ax, ay, az;
      int16_t gx, gy, gz;
      mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

      recordedPoints++;

      if (recordedPoints >= 40)
      {
        printResults();
        isRecording = false;
        recordedPoints = 0;
      }
    }
  }
  if (isKickDetected && !isLedOn)
  {
    digitalWrite(LED_OUTPUT_PIN, HIGH);
    previousMillis = currentMillis;
    isLedOn = true;
    isKickDetected = false;
  }

  if (isLedOn && currentMillis - previousMillis >= interval)
  {
    digitalWrite(LED_OUTPUT_PIN, LOW);
    isLedOn = false;
  }
}

void motionDetected()
{
  if (!isRecording)
  {
    isMotionDetected = true;
    isRecording = true;
    isKickDetected = true;
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