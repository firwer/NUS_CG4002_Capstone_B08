# Internal Comms

This folder contains all the source code and mocking code for individual subcomponent testing.

**PRE-REQUISITES**:  
You should be on a bluetooth enabled Ubuntu device, or *NIX machine that can support the bluepy library
 

## Components

There are 2 components for Internal Communications.
1. `/beetle`: Firmware for the beetles
2. `/relay`: Software for the relay node

## Testing Internal Comms
For individual subcomponent testing,
1. Using arduino IDE, open the beetle folder
2. Inside internal.cpp, ensure `DEBUG_MODE` is defined as 1
3. Flash your Beetle Bluno with the code
4. Inside `/relay`, modify the mac addresses of the beetles you want to use
5. Re-introduce the commented out code under `getDataToSend` and comment out the live code for the player game for mocking purposes
6. Under the main driver loop, comment out the `externalThread` start and join handles since this is testing locally
7. Run the relay node in `/relay` via `python3 main.py 1` for player 1 beetles or `python3 main.py 2` for player 2 beetles.


## Hardware Integration
To use internal comms, you need to interface with the communication API.

The communication API works with a 'stage and commit' design pattern.  

Data to be sent should be staged with the various `ic_push` handles.  

To actually perform communication, `communicate` or `ic_udp_quicksend` should be called. Note that only `communicate` handle will attempt to retrieve data from the relay.

### Communication API

CONNECTION:  
\> `ic_connect()`
- returns true if connection occurred with relay node
- MUST be called before other APIs can be used (nothing will be sent if there is no connection)

RECEIVING:  
\> `ic_get_state()`
\> Listen for data with `communicate()`

TRANSMITTING:
\> Stage the values to be sent with `ic_push_<data>({your_data})`
\> Commit/transmit the data with `communicate()`
\> For udp data, use `ic_udp_quicksend()` for a lower-latency transmission

For more details, visit `internal.hpp` and read the prototype functions under the "`// hw-ic integration declarations`" comment. 

## Usage for Laser Tag Game

Ensure debug mode is disabled for the beetle code.  

Flash the firmware code to the beetles.

Launch two instances of the relay node process, ideally 1 process per relay node (machine):  
- `python3 main.py 1` player 1
- `python3 main.py 2` player 2
