# NUS_CG4002_Capstone_B08


External Communications
=======================

How to setup the external comms module
1. Prepare the environment (install the required packages)
``pip3 install -r requirements.txt``
2. Run the evaluation server inside the real_eval_server subfolder ``python WebSocketServer.py``
3. Open eval server's index.html in a browser.
4. Enter the Eval Server IP Address (localhost if running on the same machine) and click connect. Select the B08 and enter the password (See config.py)
5. Click "Login"
6. On this screen, you should see ```TCP server waiting for connection from eval_client on port number xxxx```. Take note of the port number
7. Run one-click-deploy ``python one_click_deploy.py``
8. Key in the port number in the deployment script and press enter
9. Now start the relay node by running ``python relay_node.py``

## For Relay Node (Internal Comms Side)
- If you wish to run the mocker (for testing purposes in the absence of hardware), go to /int_comms/relay/ and run ``python external_p1.py`` for player 1 relay node and ``python external_p2.py`` for player 2 relay node.
- If you wish to run the actual relay node, go to /int_comms/relay/ and run ``python main.py <player_number>`` where player_number is either 1 or 2.