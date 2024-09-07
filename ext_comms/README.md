# NUS_CG4002_Capstone_B08


External Communications
=======================

How to setup the external comms module (Quick Draft)
1. Prepare the environment (install the required packages)
``pip3 install -r requirements.txt``
2. Run the main server ``python main.py``
3. Run the evaluatiion server inside the eval_server folder ``python WebSocketServer.py``
4. Open eval server's index.html in a browser.
5. Enter the Eval Server IP Address (localhost if running on the same machine) and click connect. Select the B08 and enter the password (See config.py)
6. Click "Login"
7. On this screen, you should see ```TCP server waiting for connection from eval_client on port number xxxx```. Take note of the port number
8. Key in the port number in the main server and press enter
9. Now start the relay node by running ``python relay_node.py``