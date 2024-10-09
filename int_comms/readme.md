# Internal Comms

## Hardware Integration
How to use the internal comms code for hardware:

CONNECTION:  
Establish connection with relay node: `while(ic_connect());`

RECEIVING:  
\> `ic_get_state()`
\> Listen for data with `communicate()`

TRANSMITTING:
\> Commit the values with `ic_push_<data>()`
\> Send the data with `communicate()`