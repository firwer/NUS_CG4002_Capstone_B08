#include <Wire.h>
#include <MPU6050.h>
#include <EEPROM.h>
#define LED_OUTPUT_PIN 5
#define IMU_INTERRUPT_PIN 2
#define MPU_SAMPLE_RATE 20

MPU6050 mpu;
struct MPUData
{
  int16_t ax;
  int16_t ay;
  int16_t az;
  int16_t gx;
  int16_t gy;
  int16_t gz;
} MPUData;

const unsigned long SAMPLING_DELAY = 1000 / MPU_SAMPLE_RATE; // Sampling interval, 8-bits is sufficient
unsigned long lastSampleTime = 0;
bool isRecording = false;
bool isMotionDetected = false;
bool isKickDetected = false;

uint8_t recordedPoints = 0; // Max 40, 8-bits is enough

void motionDetected();
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

  mpu.setXAccelOffset(storedCalibration.xoffset);
  mpu.setYAccelOffset(storedCalibration.yoffset);
  mpu.setZAccelOffset(storedCalibration.zoffset);
  mpu.setXGyroOffset(storedCalibration.xgoffset);
  mpu.setYGyroOffset(storedCalibration.ygoffset);
  mpu.setZGyroOffset(storedCalibration.zgoffset);

  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_16);
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_2000);

  mpu.setDHPFMode(MPU6050_DHPF_5);
  mpu.setDLPFMode(MPU6050_DLPF_BW_10);

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
    if (millis() - lastSampleTime >= SAMPLING_DELAY && recordedPoints < 40)
    {
      isKickDetected = true;
      lastSampleTime = millis();
      mpu.getMotion6(&MPUData.ax, &MPUData.ay, &MPUData.az, &MPUData.gx, &MPUData.gy, &MPUData.gz);
      Serial.print("Accel/Gyra:\t");
      Serial.print(MPUData.ax);
      Serial.print("\t");
      Serial.print(MPUData.ay);
      Serial.print("\t");
      Serial.print(MPUData.az);
      Serial.print("\t");
      Serial.print(MPUData.gx);
      Serial.print("\t");
      Serial.print(MPUData.gy);
      Serial.print("\t");
      Serial.println(MPUData.gz);
      lastSampleTime = millis();
      recordedPoints++;

      if (recordedPoints >= 40)
      {

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
