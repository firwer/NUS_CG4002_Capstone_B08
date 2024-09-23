#include <Arduino.h>
#include <MPU6050.h>
#include <Tone.h>
#include <ArduinoQueue.h>

// Define I/O pins
#define IMU_INTERRUPT_PIN 2
#define BUZZER_PIN 3
#define NOTE_DELAY 100
#define MPU_SAMPLING_RATE 40   // Can be changed to 20. idk what AI model wants.
#define NUM_RECORDED_POINTS 60 // CAN CHANGE TO 40. idk what AI model wants.

// Queue reduced to save memory
ArduinoQueue<uint16_t> soundQueue(10); // Tones are now stored in 16-bit integers
bool isMotionTunePlayed = false;
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

unsigned long lastSoundTime = 0;

Tone shotFired;
bool isFullMagazineTonePlayed = false;

MPU6050 mpu;
const unsigned long SAMPLING_DELAY = 1000 / MPU_SAMPLING_RATE;
unsigned long lastSampleTime = 0;
bool isRecording = false;
bool isMotionDetected = false;
bool hasMotionEnded = false;
void playMotionFeedback();
void playMotionEndFeedback();
void playFullMagazineTone(); // This is also the startup tune
struct MPUData
{
  int16_t ax;
  int16_t ay;
  int16_t az;
  int16_t gx;
  int16_t gy;
  int16_t gz;
} MPUData;

// can use this if the AI model can accept floats
struct MPUData_FLOAT
{
  float accelXreal;
  float accelYreal;
  float accelZreal;
  float gyroXreal;
  float gyroYreal;
  float gyroZreal;
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

// int16_t recordedAccel[60][3];
// int16_t recordedGyro[60][3];
uint8_t recordedPoints = 0;

void motionDetected();
// void printArray(int16_t data[40][3], uint8_t index);
// void printResults();

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

  calibrationData.xoffset = -1060;
  calibrationData.yoffset = -872;
  calibrationData.zoffset = 1611;
  calibrationData.xgoffset = -7;
  calibrationData.ygoffset = -32;
  calibrationData.zgoffset = 27;

  // EEPROM.put(0, calibrationData); //TODO: Store in EEPROM

  mpu.setXAccelOffset(calibrationData.xoffset);
  mpu.setYAccelOffset(calibrationData.yoffset);
  mpu.setZAccelOffset(calibrationData.zoffset);
  mpu.setXGyroOffset(calibrationData.xgoffset);
  mpu.setYGyroOffset(calibrationData.ygoffset);
  mpu.setZGyroOffset(calibrationData.zgoffset);

  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_250);

  mpu.setDHPFMode(MPU6050_DHPF_1P25);
  mpu.setDLPFMode(MPU6050_DLPF_BW_20);
  mpu.setMotionDetectionThreshold(60);
  mpu.setMotionDetectionDuration(5);

  mpu.setIntMotionEnabled(true);

  pinMode(IMU_INTERRUPT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(IMU_INTERRUPT_PIN), motionDetected, RISING);
  pinMode(BUZZER_PIN, OUTPUT);
  shotFired.begin(BUZZER_PIN); // DO NOT DELETE
}

void loop()
{
  //==================== BUZZER SUBROUTINE ====================
  if (millis() - lastSoundTime > NOTE_DELAY)
  {
    if (soundQueue.itemCount() > 0)
    {
      uint16_t note = soundQueue.dequeue();
      shotFired.play(note, 100); // Play note for 50ms
    }
    lastSoundTime = millis();
  }
  // START UP BUZZER ROUTINE
  if (!isFullMagazineTonePlayed)
  {
    playFullMagazineTone();
    isFullMagazineTonePlayed = true;
  }

  //==================== MPU6050 SUBROUTINE====================
  if (isRecording)
  {
    if (!isMotionTunePlayed)
    {
      Serial.println("Motion Detected. Displaying raw then corresponding real readings.");
      playMotionFeedback();
      isMotionTunePlayed = true;
      hasMotionEnded = false;
    }
    if (millis() - lastSampleTime >= SAMPLING_DELAY && recordedPoints < NUM_RECORDED_POINTS)
    {
      mpu.getMotion6(&MPUData.ax, &MPUData.ay, &MPUData.az, &MPUData.gx, &MPUData.gy, &MPUData.gz);
      // Take the raw 16bit data, divide by 32767 to get the ratio, multiply by 4g to get the real value,
      // then multiply by 9.81 to get m/s^2
      MPUData_FLOAT.accelXreal = ((MPUData.ax) / 32767.0) * 4.0 * 9.81;
      MPUData_FLOAT.accelYreal = ((MPUData.ay) / 32767.0) * 4.0 * 9.81;
      MPUData_FLOAT.accelZreal = ((MPUData.az) / 32767.0) * 4.0 * 9.81;
      // same for gyroscope scaling
      MPUData_FLOAT.gyroXreal = ((MPUData.gx) / 32767.0) * 250.0;
      MPUData_FLOAT.gyroYreal = ((MPUData.gy) / 32767.0) * 250.0;
      MPUData_FLOAT.gyroZreal = ((MPUData.gz) / 32767.0) * 250.0;

      // REMOVE THESE IF NOT NEEDED

      // Serial.print("RAW Accel & Gyro:\t");

      // Serial.print(MPUData.ax);
      // Serial.print("\t");
      // Serial.print(MPUData.ay);
      // Serial.print("\t");
      // Serial.print(MPUData.az);
      // Serial.print("\t");
      // Serial.print(MPUData.gx);
      // Serial.print("\t");
      // Serial.print(MPUData.gy);
      // Serial.print("\t");
      // Serial.println(MPUData.gz);

      // Serial.print("Real Accel & Gyro:\t");
      // Serial.print(MPUData_FLOAT.accelXreal);
      // Serial.print("\t");
      // Serial.print(MPUData_FLOAT.accelYreal);
      // Serial.print("\t");
      // Serial.print(MPUData_FLOAT.accelZreal);
      // Serial.print("\t");
      // Serial.print(MPUData_FLOAT.gyroXreal);
      // Serial.print("\t");
      // Serial.print(MPUData_FLOAT.gyroYreal);
      // Serial.print("\t");
      // Serial.println(MPUData_FLOAT.gyroZreal);

      lastSampleTime = millis();
      recordedPoints++;

      if (recordedPoints >= NUM_RECORDED_POINTS && !hasMotionEnded)
      {
        // sendIMUData(ax,ay,az,gx,gy,gz); //modify params if needed
        playMotionEndFeedback();
        isRecording = false;
        recordedPoints = 0;
        isMotionTunePlayed = false;
        hasMotionEnded = true;
      }
    }
  }
}

void motionDetected()
{
  if (!isRecording)
  {
    isMotionDetected = true;
    isRecording = true;
  }
}

void playFullMagazineTone()
{
  soundQueue.enqueue(NOTE_C5);
  soundQueue.enqueue(NOTE_A5);
  soundQueue.enqueue(NOTE_C6);
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

// Uncomment for debugging if needed
//  void printArray(int16_t data[40][3], uint8_t index)
//  {
//    Serial.print('"');
//    Serial.print("[");
//    for (uint8_t i = 0; i < 40; i++)
//    {
//      Serial.print(data[i][index]);
//      if (i < 39)
//        Serial.print(",");
//    }
//    Serial.print("]");
//    Serial.print('"');
//  }

// void printResults()
// {
//   printArray(recordedAccel, 0);
//   Serial.print(",");
//   printArray(recordedAccel, 1);
//   Serial.print(",");
//   printArray(recordedAccel, 2);
//   Serial.print(",");
//   printArray(recordedGyro, 0);
//   Serial.print(",");
//   printArray(recordedGyro, 1);
//   Serial.print(",");
//   printArray(recordedGyro, 2);
//   Serial.print("\n");

//   recordedPoints = 0;
//   for (uint8_t i = 0; i < 40; i++)
//   {
//     recordedAccel[i][0] = 0;
//     recordedAccel[i][1] = 0;
//     recordedAccel[i][2] = 0;
//     recordedGyro[i][0] = 0;
//     recordedGyro[i][1] = 0;
//     recordedGyro[i][2] = 0;
//   }
// }
