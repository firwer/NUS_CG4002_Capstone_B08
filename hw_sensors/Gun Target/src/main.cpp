#include <Arduino.h>
#include <IRremote.hpp>
#include <Tone.h>
#include <cppQueue.h>
#include <ArduinoQueue.h>

#define DECODE_NEC       // Enable NEC protocol. This is the protocol used for the IR receiver
#define IR_RECEIVE_PIN 4 // Define the pin for the IR receiver
#define BUZZER_PIN 3     // Define the pin for the buzzer (PWM pin)
#define NOTE_DELAY 75
#define BULLET_DAMAGE 5

const uint16_t PLAYER_1_ADDRESS = 0x23; // Address of player 1
const uint16_t PLAYER_2_ADDRESS = 0x77; // Address of player 2 <--

bool isShot = false;    // to send to game engine
bool isRespawn = false; // to integrate with game engine
unsigned long lastSoundTime = 0;
bool isFullHealthplayed = false;
bool isDeathPlayed = false;
bool isCriticalHealth = false;
unsigned long lastCriticalTuneTime = 0;

int16_t curr_healthValue = 100;     // this is the outgoing health value
int16_t incoming_healthState = 100; // To be unpacked from the incoming game_state packet

Tone melody;

ArduinoQueue<uint16_t> noteQueue(20);

// Define the healthNotes array with 5 notes per tune
int healthNotes[19][5] = {
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
void healthSynchronisation(); // TODO: Integrate with internal comms
void handleRespawn();
void playCriticalHealthTune(); // TODO: Integrate with internal comms

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
            melody.play(note, 150); // Play note for 200ms
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
            if (curr_healthValue > 0)
            {
                playHealthDecrementTune(curr_healthValue);
            }
            // Update critical health status
            if (curr_healthValue <= 10 && !isCriticalHealth && curr_healthValue > 0)
            {
                isCriticalHealth = true;
                lastCriticalTuneTime = millis();
            }
            else if ((curr_healthValue > 10 && isCriticalHealth) || (curr_healthValue <= 0 && isCriticalHealth))
            {
                isCriticalHealth = false;
            }
            Serial.print(F("Player 1 shot! Health: "));
            Serial.println(curr_healthValue);
        }
        IrReceiver.resume(); // Receive the next value
    }

    if (isCriticalHealth)
    {
        if (millis() - lastCriticalTuneTime >= 750)
        {
            playCriticalHealthTune();
            lastCriticalTuneTime = millis();
        }
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
        playStartupTune();
        Serial.print(F("Player 1 respawned! Health: "));
        Serial.println(curr_healthValue);
        isRespawn = false;
    }
}