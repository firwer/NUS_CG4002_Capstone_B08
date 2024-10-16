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
#define NOTE_REST 0
#define MAX_HEALTH 100

const uint16_t PLAYER_1_ADDRESS = 0x23; // Address of player 1
const uint16_t PLAYER_2_ADDRESS = 0x77; // Address of player 2 <--

bool isShot = false;    // to send to game engine
bool isRespawn = false; // to integrate with game engine
unsigned long lastSoundTime = 0;
bool isFullHealthplayed = false;

unsigned long lastCriticalTuneTime = 0;
// Vibration State Variables for Critical Health
unsigned long lastVibrationTime = 0;
uint16_t pulseDuration = 100;

uint8_t curr_healthValue = 100; // HARDWARE-side tracker

Tone melody;

typedef struct
{
    bool vibrationActive;
    uint16_t duration;
} vibrationState;

ArduinoQueue<vibrationState> vibrationQueue(10);

ArduinoQueue<uint16_t>
    noteQueue(20);

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

void playHealthDecrementTune(uint8_t health);
void playStartupTune();
void playDeathTune();
void healthSynchronisation(uint8_t incoming_healthState); // TODO: Integrate with internal comms
void playCriticalHealthTune();                            // TODO: Integrate with internal comms
void playVibration(uint16_t duration);

void setup()
{
    Serial.begin(115200);
    while (!Serial)
        ; // Wait for Serial to become available.

    // Start the receiver and enable feedback on the built-in LED
    melody.begin(BUZZER_PIN);
    IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK);
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(VIBRATION_PIN, OUTPUT);

    while (!ic_connect())
        ;
    playStartupTune();
}

packet_gamestate_t pkt;
void loop()
{
    //==========================Game Engine SubRoutine =====================
    //@wanlin
    communicate();
    pkt = ic_get_state();
    if (pkt.packet_type == PACKET_DATA_GAMESTATE && pkt.health_num != curr_healthValue)
    {
        healthSynchronisation(pkt.health_num);
    }
    // digitalWrite(VIBRATION_PIN, HIGH);

    //==========================Buzzer and Health Update SubRoutine ==========================
    if (millis() - lastSoundTime > NOTE_DELAY)
    {
        if (noteQueue.itemCount() > 0)
        {
            uint16_t note = noteQueue.dequeue();
            melody.play(note, 100); // Play note for 200ms
        }
        else if (noteQueue.itemCount() == 0)
        {
            IrReceiver.restartTimer();
            communicate();
        }
        lastSoundTime = millis();
    }

    //==========================Vibration SubRoutine ==========================
    if (millis() - lastVibrationTime >= pulseDuration)
    {
        if (vibrationQueue.itemCount() > 0)
        {
            vibrationState newvibestate = vibrationQueue.dequeue();
            digitalWrite(VIBRATION_PIN, newvibestate.vibrationActive);
            pulseDuration = newvibestate.duration;
            lastVibrationTime = millis();
        }
    }

    //==================== CRITICAL HEALTH SUBROUTINE=======================
    if (curr_healthValue <= 10 && curr_healthValue > 0)
    {
        if (millis() - lastCriticalTuneTime >= 500)
        {
            playCriticalHealthTune();
            playVibration(800);
            lastCriticalTuneTime = millis();
        }
    }

    //==========================IR Receiver SubRoutine ==========================
    if (IrReceiver.decode())
    {
        if (IrReceiver.decodedIRData.address == PLAYER_1_ADDRESS)
        {
            digitalWrite(LED_BUILTIN, HIGH);
            curr_healthValue -= BULLET_DAMAGE;
            isFullHealthplayed = false;

            // @wanlin
            ic_push_health(curr_healthValue);
            playHealthDecrementTune(curr_healthValue);
            playVibration(1000);
            communicate();
        }
        IrReceiver.resume(); // Receive the next value
    }
}

void playVibration(uint16_t duration)
{
    vibrationState newvibestate;
    newvibestate.vibrationActive = true;
    newvibestate.duration = duration;
    vibrationQueue.enqueue(newvibestate);
    newvibestate.vibrationActive = false;
    newvibestate.duration = 100;
    vibrationQueue.enqueue(newvibestate);
}

void playHealthDecrementTune(uint8_t health)
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
void healthSynchronisation(uint8_t incoming_healthState)
{
    // CASE 1: Health is decremented
    if (incoming_healthState < curr_healthValue)
    {
        playHealthDecrementTune(incoming_healthState);
        playVibration(1000);
    }
    // either respawn or revive and damaged (in the case of rain bomb)
    else if (incoming_healthState > curr_healthValue)
    {
        if (incoming_healthState == MAX_HEALTH)
        {
            playStartupTune();
        }
        else
        {
            // CASE 3: If health from update is more but its less than max health then play revive + damage

            playStartupTune();
            playHealthDecrementTune(incoming_healthState);
        }
    }
    curr_healthValue = incoming_healthState;
}
