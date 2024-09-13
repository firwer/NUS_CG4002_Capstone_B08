#include <Arduino.h>
#include <IRremote.hpp>
#include <Tone.h>
#include <cppQueue.h>
#include <ArduinoQueue.h>

#define DECODE_NEC       // Enable NEC protocol. This is the protocol used for the IR receiver
#define IR_RECEIVE_PIN 4 // Define the pin for the IR receiver
#define BUZZER_PIN 3     // Define the pin for the buzzer (PWM pin)
#define NOTE_DELAY 50
#define BULLET_DAMAGE 5

const uint16_t PLAYER_1_ADDRESS = 0x23; // Address of player 1
const uint16_t PLAYER_2_ADDRESS = 0x77; // Address of player 2 <--

bool isShot = false;    // to send to game engine
bool isRespawn = false; // to integrate with game engine
unsigned long lastSoundTime = 0;
bool isFullHealthplayed = false;
bool isDeathPlayed = false;

uint16_t curr_healthValue = 100;     // this is the outgoing health value
uint16_t incoming_healthState = 100; // To be unpacked from the incoming game_state packet

Tone melody;

ArduinoQueue<uint16_t> noteQueue(14);

int soundList[14]{
    NOTE_C4,
    NOTE_E4,
    NOTE_G4,
    NOTE_C5,
    NOTE_E5,
    NOTE_G3,
    NOTE_E3,
    NOTE_A3,
    NOTE_B3,
    NOTE_GS3,
    NOTE_AS3,
    NOTE_A4,
    NOTE_B4,
    NOTE_D5,
};

enum
{
    SOUND_C4,
    SOUND_E4,
    SOUND_G4,
    SOUND_C5,
    SOUND_E5,
    SOUND_G3,
    SOUND_E3,
    SOUND_A3,
    SOUND_B3,
    SOUND_GS3,
    SOUND_AS3,
    SOUND_A4,
    SOUND_B4,
    SOUND_D5,
};

void playhealthDecrementTune()
{
    // NOTE_E5, NOTE_C5
    noteQueue.enqueue(soundList[SOUND_E5]);
    noteQueue.enqueue(soundList[SOUND_C5]);
}
void playStartupTune()
{
    // NOTE_C4, NOTE_E4, NOTE_G4, NOTE_C5
    noteQueue.enqueue(soundList[SOUND_C4]);
    noteQueue.enqueue(soundList[SOUND_E4]);
    noteQueue.enqueue(soundList[SOUND_G4]);
    noteQueue.enqueue(soundList[SOUND_C5]);
}
void playDeathTune()
{
    // NOTE_C4, NOTE_G3, NOTE_E3, NOTE_A3, NOTE_B3, NOTE_A3, NOTE_GS3, NOTE_AS3
    noteQueue.enqueue(soundList[SOUND_C4]);
    noteQueue.enqueue(soundList[SOUND_G3]);
    noteQueue.enqueue(soundList[SOUND_E3]);
    noteQueue.enqueue(soundList[SOUND_A3]);
    noteQueue.enqueue(soundList[SOUND_B3]);
    noteQueue.enqueue(soundList[SOUND_A3]);
    noteQueue.enqueue(soundList[SOUND_GS3]);
    noteQueue.enqueue(soundList[SOUND_AS3]);
}
void playRespawnTune()
{
    // NOTE_G4, NOTE_A4, NOTE_B4, NOTE_D5
    noteQueue.enqueue(soundList[SOUND_G4]);
    noteQueue.enqueue(soundList[SOUND_A4]);
    noteQueue.enqueue(soundList[SOUND_B4]);
    noteQueue.enqueue(soundList[SOUND_D5]);
}

/*
Game engine handles health calculation for non-bullet damage.
This function will handle the health agreement between the game engine and the hardware.
*/
void healthSynchronisation()
{
    if (curr_healthValue != incoming_healthState)
    {
        curr_healthValue = incoming_healthState;
    }
}

/*
This function will give feedback that the player has respawned.
*/
void handleRespawn()
{
    if (isRespawn)
    {
        curr_healthValue = 100; // reset health to 100
        Serial.print(F("Player 1 respawned! Health: "));
        Serial.println(curr_healthValue);
        playRespawnTune();
        isRespawn = false;
    }
}

void setup()
{
    Serial.begin(115200);
    while (!Serial)
        ; // Wait for Serial to become available.

    // Start the receiver and enable feedback on the built-in LED
    melody.begin(BUZZER_PIN);

    IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK);
    // IrReceiver.start();
    Serial.print(F("Ready to receive IR signals of protocols: "));
    printActiveIRProtocols(&Serial);
    // Set up the built-in LED pin as output
    pinMode(LED_BUILTIN, OUTPUT);
}

void loop()
{
    if (millis() - lastSoundTime > NOTE_DELAY)
    {
        // Serial.println(soundQueue.itemCount());
        if (noteQueue.itemCount() > 0)
        {
            uint16_t note = noteQueue.dequeue();
            melody.play(note, 50); // Play note for 50ms
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

    // Handle IR remote input
    if (IrReceiver.decode())
    {
        Serial.println(F("IR signal received:"));
        Serial.println(IrReceiver.decodedIRData.address, HEX);

        if (IrReceiver.decodedIRData.protocol == UNKNOWN)
        {
            Serial.println(F("Received noise or an unknown (or not yet enabled) protocol"));
            // Print extended info for unknown protocols
            IrReceiver.printIRResultRawFormatted(&Serial, true);
        }
        else
        {
            IrReceiver.printIRResultShort(&Serial);
            IrReceiver.printIRSendUsage(&Serial);
        }
        Serial.println();

        if (IrReceiver.decodedIRData.address == PLAYER_1_ADDRESS)
        {
            digitalWrite(LED_BUILTIN, HIGH);
            curr_healthValue -= BULLET_DAMAGE;
            isFullHealthplayed = false;
            playhealthDecrementTune();
            Serial.print(F("Player 1 shot! Health: "));
            Serial.println(curr_healthValue);
        }
        IrReceiver.resume(); // Receive the next value
    }

    // Play death tune if health is 0 or less
    if (curr_healthValue <= 0 && !isDeathPlayed)
    {
        playDeathTune();
        isDeathPlayed = true;
        Serial.println(F("Player 1 is dead!"));
    }

    // handleRespawn(); //TODO: Integrate with internal comms
}
