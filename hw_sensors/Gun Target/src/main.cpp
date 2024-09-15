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

int16_t curr_healthValue = 100;     // this is the outgoing health value
int16_t incoming_healthState = 100; // To be unpacked from the incoming game_state packet

Tone melody;

ArduinoQueue<uint16_t> noteQueue(14);

// Define the healthNotes array with 5 notes per tune
int healthNotes[10][5] = {
    // Index 0: Health 91-99
    {NOTE_C4, NOTE_D4, NOTE_E4, NOTE_D4, NOTE_C4},
    // Index 1: Health 81-90
    {NOTE_E4, NOTE_G4, NOTE_A4, NOTE_G4, NOTE_E4},
    // Index 2: Health 71-80
    {NOTE_G4, NOTE_A4, NOTE_C5, NOTE_A4, NOTE_G4},
    // Index 3: Health 61-70
    {NOTE_B4, NOTE_D5, NOTE_E5, NOTE_D5, NOTE_B4},
    // Index 4: Health 51-60
    {NOTE_D5, NOTE_F5, NOTE_G5, NOTE_F5, NOTE_D5},
    // Index 5: Health 41-50
    {NOTE_F5, NOTE_A5, NOTE_C6, NOTE_A5, NOTE_F5},
    // Index 6: Health 31-40
    {NOTE_A5, NOTE_C6, NOTE_D6, NOTE_C6, NOTE_A5},
    // Index 7: Health 21-30
    {NOTE_C6, NOTE_E6, NOTE_G6, NOTE_E6, NOTE_C6},
    // Index 8: Health 11-20
    {NOTE_E6, NOTE_G6, NOTE_A6, NOTE_G6, NOTE_E6},
    // Index 9: Health 1-10
    {NOTE_G6, NOTE_B6, NOTE_C7, NOTE_B6, NOTE_G6}};

void playHealthDecrementTune(int16_t health);
void playStartupTune();
void playDeathTune();
void healthSynchronisation(); // TODO: Integrate with internal comms
void handleRespawn();         // TODO: Integrate with internal comms

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
            melody.play(note, 150); // Play note for 100ms
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
            playHealthDecrementTune(curr_healthValue);
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

void playHealthDecrementTune(int16_t health)
{
    if (health >= 100 || health <= 0)
    {
        return; // they have their own tunes
    }
    int8_t index = (100 - health) / 10;

    if (index < 0)
    {
        index = 0;
    }
    if (index > 9)
    {
        index = 9;
    }
    noteQueue.enqueue(healthNotes[index][0]);
    noteQueue.enqueue(healthNotes[index][1]);
    noteQueue.enqueue(healthNotes[index][2]);
    noteQueue.enqueue(healthNotes[index][3]);
    noteQueue.enqueue(healthNotes[index][4]);
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
        isRespawn = false;
    }
}