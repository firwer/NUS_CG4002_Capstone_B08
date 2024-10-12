#include <Arduino.h>
#include <IRremote.hpp>
#include <Tone.h>
#include <cppQueue.h>
#include <ArduinoQueue.h>

// Include communication logic
#include "internal.hpp"
#include "packet.h"

#define DECODE_NEC       // Enable NEC protocol. This is the protocol used for the IR receiver
#define IR_RECEIVE_PIN 4 // Define the pin for the IR receiver
#define BUZZER_PIN 3     // Define the pin for the buzzer (PWM pin)
#define NOTE_DELAY 75
#define BULLET_DAMAGE 5
#define VIBRATION_PIN 5
#define PULSE_DURATION 500
#define CRITICAL_VIBRATION_INTERVAL 350 // Interval between critical pulses in ms
#define NOTE_REST 0

const uint16_t PLAYER_1_ADDRESS = 0x23; // Address of player 1
const uint16_t PLAYER_2_ADDRESS = 0x77; // Address of player 2 <--

bool isShot = false;    // to send to game engine
bool isRespawn = false; // to integrate with game engine
unsigned long lastSoundTime = 0;
bool isFullHealthplayed = false;
bool isDeathPlayed = false;
bool isCriticalHealth = false;
bool isDamaged = false;
unsigned long lastCriticalTuneTime = 0;
// Vibration State Variables for Critical Health
bool criticalVibrationActive = false;
unsigned long lastCriticalVibrationTime = 0;
unsigned long lastVibrationTime = 0;
bool vibrationActive = false; // Tracks if a vibration pulse is currently active

int16_t curr_healthValue = 100;   // HARDWARE-side tracker
int16_t incoming_healthState = 0; // INCOMING Game Engine health state

Tone melody;

ArduinoQueue<uint16_t> noteQueue(20);

// Define the healthNotes array with 5 notes per tune
const int healthNotes[19][5] = {
    // Tune 0: Health 95
    {NOTE_F4, NOTE_A4, NOTE_C5, NOTE_A4, NOTE_F4},
    // Tune 1: Health 90
    {NOTE_G4, NOTE_B4, NOTE_D5, NOTE_B4, NOTE_G4},
    // Tune 2: Health 85
    {NOTE_A4, NOTE_C5, NOTE_E5, NOTE_C5, NOTE_A4},
    // Tune 3: Health 80
    {NOTE_B4, NOTE_D5, NOTE_FS5, NOTE_D5, NOTE_B4},
    // Tune 4: Health 75
    {NOTE_C5, NOTE_E5, NOTE_G5, NOTE_E5, NOTE_C5},
    // Tune 5: Health 70
    {NOTE_D5, NOTE_FS5, NOTE_A5, NOTE_FS5, NOTE_D5},
    // Tune 6: Health 65
    {NOTE_E5, NOTE_GS5, NOTE_B5, NOTE_GS5, NOTE_E5},
    // Tune 7: Health 60
    {NOTE_F5, NOTE_A5, NOTE_C6, NOTE_A5, NOTE_F5},
    // Tune 8: Health 55
    {NOTE_G5, NOTE_B5, NOTE_D6, NOTE_B5, NOTE_G5},
    // Tune 9: Health 50
    {NOTE_A5, NOTE_C6, NOTE_E6, NOTE_C6, NOTE_A5},
    // Tune 10: Health 45
    {NOTE_B5, NOTE_D6, NOTE_FS6, NOTE_D6, NOTE_B5},
    // Tune 11: Health 40
    {NOTE_C6, NOTE_E6, NOTE_G6, NOTE_E6, NOTE_C6},
    // Tune 12: Health 35
    {NOTE_D6, NOTE_FS6, NOTE_A6, NOTE_FS6, NOTE_D6},
    // Tune 13: Health 30
    {NOTE_E6, NOTE_GS6, NOTE_B6, NOTE_GS6, NOTE_E6},
    // Tune 14: Health 25
    {NOTE_F6, NOTE_A6, NOTE_C7, NOTE_A6, NOTE_F6},
    // Tune 15: Health 20
    {NOTE_G6, NOTE_B6, NOTE_D7, NOTE_B6, NOTE_G6},
    // Tune 16: Health 15
    {NOTE_A6, NOTE_C7, NOTE_E6, NOTE_C7, NOTE_A6},
    // Tune 17: Health 10
    {NOTE_REST, NOTE_B6, NOTE_D7, NOTE_FS6, NOTE_D7},
    // Tune 18: Health 5 (Adjusted)
    {NOTE_REST, NOTE_C7, NOTE_E6, NOTE_F6, NOTE_E6},
};

void playHealthDecrementTune(int16_t health);
void playStartupTune();
void playDeathTune();
void healthSynchronisation(int16_t curr_healthValue, int16_t incoming_healthState); // TODO: Integrate with internal comms
void handleRespawn(bool isRespawn);                                                 // TODO: Integrate with internal comms
void playCriticalHealthTune();                                                      // TODO: Integrate with internal comms

void setup()
{
    Serial.begin(115200);
    while (!Serial)
        ; // Wait for Serial to become available.

    // Start the receiver and enable feedback on the built-in LED
    melody.begin(BUZZER_PIN);

    IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK);
    // IrReceiver.start();
    // Serial.print(F("Ready to receive IR signals of protocols: "));
    // printActiveIRProtocols(&Serial);
    // Set up the built-in LED pin as output
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(VIBRATION_PIN, OUTPUT);

    while (ic_connect())
        ;
    melody.play(NOTE_A7, 100);
}

packet_gamestate_t pkt;
void loop()
{
    //==========================Game Engine SubRoutine =====================
    //@wanlin
    communicate();
    pkt = ic_get_state();
    incoming_healthState = pkt.health_num;
    if (incoming_healthState != curr_healthValue)
        healthSynchronisation(curr_healthValue, incoming_healthState);
    handleRespawn(isRespawn);
    digitalWrite(VIBRATION_PIN, HIGH);

    //==========================Buzzer and Health Update SubRoutine ==========================
    if (millis() - lastSoundTime > NOTE_DELAY)
    {
        // Serial.println(soundQueue.itemCount());
        if (noteQueue.itemCount() > 0)
        {
            uint16_t note = noteQueue.dequeue();
            melody.play(note, 100); // Play note for 200ms
        }
        else if (noteQueue.itemCount() == 0)
        {
            IrReceiver.restartTimer();
        }
        lastSoundTime = millis();
    }

    if (curr_healthValue == 100 && !isFullHealthplayed)
    {
        playStartupTune();
        isFullHealthplayed = true;
    }
    else if (curr_healthValue < 100 && isDamaged)
    {
        playHealthDecrementTune(curr_healthValue);
        if (isDamaged && !vibrationActive)
        {
            digitalWrite(VIBRATION_PIN, HIGH);
            vibrationActive = true;
            lastVibrationTime = millis();
        }

        isDamaged = false;
    }
    else if (curr_healthValue <= 10 && !isCriticalHealth && curr_healthValue > 0)
    {
        isCriticalHealth = true;
        lastCriticalTuneTime = millis();
    }
    else if ((curr_healthValue > 10 && isCriticalHealth) || (curr_healthValue <= 0 && isCriticalHealth))
    {
        isCriticalHealth = false;
    }
    else if (curr_healthValue <= 0 && !isDeathPlayed)
    {
        playDeathTune();
        isDeathPlayed = true;
        // Serial.println(F("Player 1 is dead!"));
    }
    if (isCriticalHealth)
    {
        if (millis() - lastCriticalTuneTime >= 750)
        {
            playCriticalHealthTune();
            lastCriticalTuneTime = millis();
        }
    }
    if (vibrationActive && (millis() - lastVibrationTime >= PULSE_DURATION))
    {
        digitalWrite(VIBRATION_PIN, LOW);
        vibrationActive = false;
    }

    if (isCriticalHealth)
    {
        if (millis() - lastCriticalTuneTime >= 750)
        {
            playCriticalHealthTune();
            lastCriticalTuneTime = millis();
        }
    }
    if (isCriticalHealth)
    {
        // Start a new critical vibration pulse if interval has passed
        if (!criticalVibrationActive && (millis() - lastCriticalVibrationTime >= CRITICAL_VIBRATION_INTERVAL))
        {
            digitalWrite(VIBRATION_PIN, HIGH);
            criticalVibrationActive = true;
            lastCriticalVibrationTime = millis();
        }

        // End the critical vibration pulse after PULSE_DURATION
        if (criticalVibrationActive && (millis() - lastCriticalVibrationTime >= PULSE_DURATION))
        {
            digitalWrite(VIBRATION_PIN, LOW);
            criticalVibrationActive = false;
            // Set up for the next pulse interval
            lastCriticalVibrationTime = millis();
        }
    }
    //==========================IR Receiver SubRoutine ==========================
    if (IrReceiver.decode())
    {
        // Serial.println(F("IR signal received:"));
        // Serial.println(IrReceiver.decodedIRData.address, HEX);

        if (IrReceiver.decodedIRData.protocol == UNKNOWN)
        {
            // Serial.println(F("Received noise or an unknown (or not yet enabled) protocol"));
            // Print extended info for unknown protocols
            // IrReceiver.printIRResultRawFormatted(&Serial, true);
        }
        else
        {
            // IrReceiver.printIRResultShort(&Serial);
            // IrReceiver.printIRSendUsage(&Serial);
        }

        if (IrReceiver.decodedIRData.address == PLAYER_1_ADDRESS)
        {
            digitalWrite(LED_BUILTIN, HIGH);
            curr_healthValue -= BULLET_DAMAGE;
            isFullHealthplayed = false;
            isDamaged = true;
            // Serial.print(F("Player 1 shot! Health: "));
            // Serial.println(curr_healthValue);

            // @wanlin
            ic_push_health(curr_healthValue);
            communicate();
        }
        IrReceiver.resume(); // Receive the next value
    }
}
void playHealthDecrementTune(int16_t health)
{
    int8_t index = (95 - health) / 5;

    if (index < 0)
    {
        index = 0;
    }
    if (index > 18)
    {
        index = 18;
    }

    for (int i = 0; i < 5; i++)
    {
        noteQueue.enqueue(healthNotes[index][i]);
    }
}

void playStartupTune()
{

    noteQueue.enqueue(NOTE_E5);
    noteQueue.enqueue(NOTE_G5);
    noteQueue.enqueue(NOTE_E6);
    noteQueue.enqueue(NOTE_C6);
    noteQueue.enqueue(NOTE_D6);
    noteQueue.enqueue(NOTE_G6);
}
void playDeathTune()
{
    noteQueue.enqueue(NOTE_C5);
    noteQueue.enqueue(NOTE_B4);
    noteQueue.enqueue(NOTE_A4);
    noteQueue.enqueue(NOTE_G4);
    noteQueue.enqueue(NOTE_F4);
    noteQueue.enqueue(NOTE_E4);
    noteQueue.enqueue(NOTE_D4);
    noteQueue.enqueue(NOTE_C4);
}

void playCriticalHealthTune()
{
    noteQueue.enqueue(NOTE_D6);
    noteQueue.enqueue(NOTE_A5);
    noteQueue.enqueue(NOTE_REST);
}

/*
Game engine handles health calculation for non-bullet damage.
This function will handle the health agreement between the game engine and the hardware.
*/
void healthSynchronisation(int16_t curr_healthValue, int16_t incoming_healthState)
{
    if (curr_healthValue != incoming_healthState && incoming_healthState < curr_healthValue)
    {
        curr_healthValue = incoming_healthState;
        isDamaged = true;
    }
    else if (curr_healthValue == 0 && incoming_healthState == 100)
    {
        curr_healthValue = 100;
        isRespawn = true;
    }
}

/*
This function will give feedback that the player has respawned.
*/
void handleRespawn(bool isRespawn)
{
    if (isRespawn)
    {
        curr_healthValue = 100; // reset health to 100
        playStartupTune();
        // Serial.print(F("Player 1 respawned! Health: "));
        // Serial.println(curr_healthValue);
        isRespawn = false;
    }
}
