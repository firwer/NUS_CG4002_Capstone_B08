// helper.js

/**
 * Sleep function to delay execution
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Disable a button
 * @param {string} elementId - The ID of the button to disable
 */
function disableButton(elementId) {
    const e = document.getElementById(elementId);
    if (e) {
        e.classList.add('disabled');
        e.disabled = true;
    } else {
        console.error(`Element with ID "${elementId}" not found.`);
    }
}

/**
 * Enable a button
 * @param {string} elementId - The ID of the button to enable
 */
function enableButton(elementId) {
    const e = document.getElementById(elementId);
    if (e) {
        e.classList.remove('disabled');
        e.disabled = false;
    } else {
        console.error(`Element with ID "${elementId}" not found.`);
    }
}

/**
 * Function to change the color of player box
 * state:
 *  0: Action matched
 *  1: Action mismatched
 *  2: Neutral (no action)
 */
function changePlayerState(player, state) {
    const targetElement = document.getElementById(player);

    if (targetElement) {
        let colour;
        switch (state) {
            case 0:
                colour = '#93C572'; // Green for match
                break;
            case 1:
                colour = 'Salmon'; // Red for mismatch
                break;
            case 2:
                colour = '#f1f1f1'; // Default color
                break;
            default:
                colour = '#f1f1f1'; // Default color
        }
        targetElement.style.backgroundColor = colour;
    } else {
        console.error(`Element with ID "${player}" not found.`);
    }
}

/**
 * Function to append text to an element
 * @param {string} elementId - The ID of the element to append text to
 * @param {string} text - The text to append
 * @param {boolean} newline - Whether to add a newline before the text
 */
function appendText(elementId, text, newline=true) {
    const targetElement = document.getElementById(elementId);

    if (targetElement) {
        if (newline)
            targetElement.innerHTML += `<br>${text}`;
        else
            targetElement.innerHTML += text;
    } else {
        console.error(`Element with ID "${elementId}" not found.`);
    }
}

/**
 * Function to change the text content of an element
 * @param {string} elementId - The ID of the element to update
 * @param {string} text - The new text content
 */
function changeText(elementId, text) {
    const targetElement = document.getElementById(elementId);

    if (targetElement) {
        targetElement.innerHTML = text;
    } else {
        console.error(`Element with ID "${elementId}" not found.`);
    }
}

/**
 * Function to update the info box with messages
 * @param {string} text - The message text
 * @param {string} type - The type of message (e.g., "error", "yellow")
 * @param {boolean} newline - Whether to add a newline before the text
 */
function updateInfo(text, type="", newline=true) {
    switch (type) {
        case "error":
            appendText("info", `<span style='color:red;'>${text}</span>`, newline);
            break;
        case "yellow":
            appendText("info", `<span style='color:yellow;'>${text}</span>`, newline);
            break;
        default:
            appendText("info", text, newline);
    }

    // Scroll to the bottom of the info box
    const info_box = document.getElementById("info");
    if (info_box) {
        info_box.scrollTop = info_box.scrollHeight;
    }
}

/**
 * Function to specifically update the info box with error messages
 * @param {string} text - The error message text
 */
function updateInfoError(text) {
    updateInfo(text, "error");
}

/**
 * Function to handle the "Next" button click
 */
function next() {
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        // Send the "next" instruction to the server
        window.ws.send("next");
        // Disable the button to prevent multiple clicks
        disableButton("button_next");
    } else {
        updateInfoError("WebSocket is not connected.");
    }
}

/**
 * Function to establish the WebSocket connection
 */
function startConnection() {
    // Check if the user is logged in
    if (sessionStorage.getItem("group_name") == null) {
        // Redirect to login page if not logged in
        location.assign("index.html");
        return;
    }

    // Initialize round counter
    window.current_round = 1;

    // Initialize response tracking
    window.round_responses = {};

    // Disable the "Next" button initially
    disableButton('button_next');

    // Construct the server address from session storage
    const server_ip = sessionStorage.getItem("server_ip");
    if (!server_ip) {
        updateInfoError("Server IP not found in session storage.");
        return;
    }
    const server_address = `ws://${server_ip}:8001/`;

    // Check for WebSocket support
    if (!("WebSocket" in window)) {
        alert("WebSocket NOT supported by your Browser. Kindly use a supporting browser!");
        return;
    }

    // Open the WebSocket connection
    const ws = new WebSocket(server_address);

    // Listen for WebSocket errors
    ws.addEventListener("error", (event) => {
        updateInfoError("WebSocket connection Failed.");
        alert("Unable to connect to eval_server");
    });

    // Handle WebSocket open event
    ws.onopen = function() {
        // Create the handshake object
        const handshake = {
            group_name: sessionStorage.getItem("group_name"),
            num_player: sessionStorage.getItem("num_player"),
            password: sessionStorage.getItem("password"),
            no_visualizer: sessionStorage.getItem("no_visualizer")
        };

        updateInfo("Performing Handshake, new connection");

        // Send the handshake to the server
        ws.send(JSON.stringify(handshake));
    };

    // Handle incoming WebSocket messages
    ws.onmessage = function (evt) {
        try {
            var data = JSON.parse(evt.data);
        } catch (e) {
            updateInfoError(`Invalid Json from Server: ${evt.data}`);
            console.error(e);
            return;
        }

        switch (data.type) {
            case "info":
                updateInfo(data.message);
                break;
            case "info_y":
                updateInfo(data.message, "yellow");
                break;
            case "info_wobr":
                updateInfo(data.message, "", false);
                break;
            case "error":
                updateInfo(data.message, "error");
                break;
            case "num_move":
                changeText("num_move", `Move: ${data.message}`);
                break;
            case "position":
                // Wait for 2 seconds before enabling the "Next" button
                sleep(2000).then(() => {
                    enableButton("button_next");
                    // Reset player box colors to neutral
                    changePlayerState("p1", 2);
                    if (sessionStorage.getItem("num_player") != 1) {
                        changePlayerState("p2", 2);
                    }
                    // Update player positions
                    if (sessionStorage.getItem("num_player") == 1) {
                        if (data.pos_1 == 0) {
                            changeText("p1", data.pos_1);
                        }
                    } else {
                        changeText("p1", data.pos_1);
                        changeText("p2", data.pos_2);
                    }
                });
                break;
            case "action":
                // Update actions if necessary
                changeText("p1", data.pos_1);
                if (sessionStorage.getItem("num_player") != 1) {
                    changeText("p2", data.pos_2);
                }
                break;
            case "action_match":
                handleActionMatch(data);
                break;
            case "rainbomb_count":
                // Update rainbomb counts for players
                updateRainbombCounts("p1", data.rainbomb_p1);
                updateRainbombCounts("p2", data.rainbomb_p2);
                break;
            case "statistics":
                // Update mean and median response times for gun and ai actions
                document.getElementById("mean_response_time_gun").textContent = data.mean_response_time_gun.toFixed(3);
                document.getElementById("median_response_time_gun").textContent = data.median_response_time_gun.toFixed(3);
                document.getElementById("mean_response_time_ai").textContent = data.mean_response_time_ai.toFixed(3);
                document.getElementById("median_response_time_ai").textContent = data.median_response_time_ai.toFixed(3);
                break;
            default:
                updateInfoError(`Invalid message type received: ${data.type}`);
        }
    };

    // Handle WebSocket close event
    ws.onclose = function() {
        alert("Connection is closed by the server");
    };

    // Display the team name
    changeText("num_move", `Group: ${sessionStorage.getItem("group_name")}`);

    // Assign the WebSocket to a global variable for access in other functions
    window.ws = ws;
}

/**
 * Handle the "action_match" message type
 * @param {Object} data - The data received from the server
 */
function handleActionMatch(data) {
    let player_id;
    if (data.player_id == 1)
        player_id = "p1";
    else
        player_id = "p2";

    const playerName = player_id === "p1" ? "Player 1" : "Player 2";
    changePlayerState(player_id, data.action_match);
    updateInfo(data.message);

    const num_player = parseInt(sessionStorage.getItem("num_player"), 10);

    if (!window.round_responses[window.current_round]) {
        window.round_responses[window.current_round] = {};
    }

    if (data.response_time !== null && data.response_time !== undefined) {
        window.round_responses[window.current_round][player_id] = {
            playerName: playerName,
            response_time: data.response_time,
            expected_action: data.expected_action,
            user_action: data.user_action
        };
    }

    if (data.game_state_expected && data.game_state_received) {
        window.round_responses[window.current_round][player_id].game_state_expected = data.game_state_expected;
        window.round_responses[window.current_round][player_id].game_state_received = data.game_state_received;
    }

    // Check if all players have responded for the current round
    if (Object.keys(window.round_responses[window.current_round]).length === num_player) {
        // Iterate over each player's response and append to tables
        for (const pid in window.round_responses[window.current_round]) {
            if (!window.round_responses[window.current_round].hasOwnProperty(pid)) continue;
            const resp = window.round_responses[window.current_round][pid];
            appendResponseTime(
                window.current_round,
                resp.playerName,
                resp.response_time,
                resp.expected_action,
                resp.user_action
            );

            if (resp.game_state_expected && resp.game_state_received) {
                appendGameStateComparison(window.current_round, resp.game_state_expected, resp.game_state_received);
            }
        }

        // Increment round counter for the next round
        window.current_round += 1;

        // Clear the responses for the new round
        window.round_responses[window.current_round] = {};
    }
}

/**
 * Append a new row to the response time table
 * @param {number} round - The round number
 * @param {string} player_id - The player identifier ("Player 1" or "Player 2")
 * @param {number} response_time - The response time in seconds
 * @param {string} expected_action - The expected action from the evaluation server
 * @param {string} user_action - The action provided by the user
 */
function appendResponseTime(round, player_id, response_time, expected_action, user_action) {
    const tableBody = document.querySelector("#response_time_table tbody");
    if (!tableBody) {
        console.error("Response Time table body not found.");
        return;
    }

    const row = document.createElement("tr");

    // Determine if the actions match
    const isCorrect = expected_action === user_action;

    // Assign class based on correctness
    if (isCorrect) {
        row.classList.add('response_time_correct');
    } else {
        row.classList.add('response_time_incorrect');
    }

    // Round Number
    const roundCell = document.createElement("td");
    roundCell.textContent = round;
    row.appendChild(roundCell);

    // Player ID
    const playerCell = document.createElement("td");
    playerCell.textContent = player_id;
    row.appendChild(playerCell);

    // Response Time
    const timeCell = document.createElement("td");
    timeCell.textContent = response_time.toFixed(3); // Display up to 3 decimal places
    row.appendChild(timeCell);

    // Expected Action
    const expectedActionCell = document.createElement("td");
    expectedActionCell.textContent = expected_action || "N/A";
    row.appendChild(expectedActionCell);

    // User Provided Action
    const userActionCell = document.createElement("td");
    userActionCell.textContent = user_action || "N/A";
    row.appendChild(userActionCell);

    tableBody.appendChild(row);
}

/**
 * Append a new round section with collapsible game state tables
 * @param {number} round - The round number
 * @param {Object} expected - The expected game state
 * @param {Object} received - The received game state
 */
function appendGameStateComparison(round, expected, received) {
    const gameStateLog = document.getElementById("game_state_log");
    if (!gameStateLog) {
        console.error("Game State Log element not found.");
        return;
    }

    // Create round section
    const roundSection = document.createElement("div");
    roundSection.classList.add("round_section");

    // Create round header
    const roundHeader = document.createElement("div");
    roundHeader.classList.add("round_header");
    roundHeader.textContent = `Round ${round}`;

    // Add toggle indicator
    const toggleIndicator = document.createElement("span");
    toggleIndicator.textContent = "+";
    toggleIndicator.classList.add("toggle_indicator");
    roundHeader.appendChild(toggleIndicator);

    // Create game state tables container
    const tablesContainer = document.createElement("div");
    tablesContainer.classList.add("game_state_tables");
    tablesContainer.style.display = "none"; // Initially collapsed

    // Create Differences Table
    const differences = compareGameStates(expected, received);
    const differencesTable = createDifferencesTable(differences);
    tablesContainer.appendChild(differencesTable);

    // Create Expected Game State Table
    const expectedTable = createGameStateTable("Expected Game State", expected);
    expectedTable.classList.add("game_state_table");
    tablesContainer.appendChild(expectedTable);

    // Create Received Game State Table
    const receivedTable = createGameStateTable("Received Game State", received);
    receivedTable.classList.add("game_state_table");
    tablesContainer.appendChild(receivedTable);

    // Create Toggle Buttons for Game State Tables
    const toggleExpectedBtn = document.createElement("button");
    toggleExpectedBtn.classList.add("toggle_table_btn");
    toggleExpectedBtn.textContent = "Toggle Expected State";
    toggleExpectedBtn.addEventListener("click", () => {
        toggleTableDisplay(expectedTable, toggleExpectedBtn, "Expected");
    });

    const toggleReceivedBtn = document.createElement("button");
    toggleReceivedBtn.classList.add("toggle_table_btn");
    toggleReceivedBtn.textContent = "Toggle Received State";
    toggleReceivedBtn.addEventListener("click", () => {
        toggleTableDisplay(receivedTable, toggleReceivedBtn, "Received");
    });

    tablesContainer.appendChild(toggleExpectedBtn);
    tablesContainer.appendChild(expectedTable);
    tablesContainer.appendChild(toggleReceivedBtn);
    tablesContainer.appendChild(receivedTable);

    // Append header and tables to section
    roundSection.appendChild(roundHeader);
    roundSection.appendChild(tablesContainer);

    // Prepend the round section to the game_state_log
    gameStateLog.prepend(roundSection);

    // Add event listener for collapsing/expanding the round section
    roundHeader.addEventListener("click", (event) => {
        // Prevent triggering toggle when clicking on buttons
        if (event.target.tagName.toLowerCase() === 'button') return;

        const isVisible = tablesContainer.style.display === "block";
        tablesContainer.style.display = isVisible ? "none" : "block";
        toggleIndicator.textContent = isVisible ? "+" : "-";
    });
}

/**
 * Toggle the display of a table and update the button text accordingly
 * @param {HTMLElement} table - The table element to toggle
 * @param {HTMLElement} button - The button element controlling the toggle
 * @param {string} label - Label indicating which table is being toggled
 */
function toggleTableDisplay(table, button, label) {
    if (table.style.display === "none" || table.style.display === "") {
        table.style.display = "table";
        button.textContent = `Hide ${label} State`;
    } else {
        table.style.display = "none";
        button.textContent = `Show ${label} State`;
    }
}

/**
 * Compare two game states and return the differences.
 * @param {Object} expected - The expected game state from the server.
 * @param {Object} received - The received game state from the user.
 * @returns {Array} - An array of difference objects.
 */
function compareGameStates(expected, received) {
    const differences = [];

    // Check for missing players in received
    for (const player in expected) {
        if (!received.hasOwnProperty(player)) {
            differences.push({
                player,
                attribute: 'Player Status',
                expected: 'Exists',
                received: 'Missing',
                status: 'missing'
            });
            continue;
        }

        // Check for missing attributes and discrepancies
        for (const attr in expected[player]) {
            if (!received[player].hasOwnProperty(attr)) {
                differences.push({
                    player,
                    attribute: attr,
                    expected: expected[player][attr],
                    received: 'Missing',
                    status: 'missing'
                });
                continue;
            }

            const expectedValue = expected[player][attr];
            const receivedValue = received[player][attr];

            // Numeric comparison
            if (typeof expectedValue === 'number' && typeof receivedValue === 'number') {
                if (receivedValue > expectedValue) {
                    differences.push({
                        player,
                        attribute: attr,
                        expected: expectedValue,
                        received: receivedValue,
                        status: 'over'
                    });
                } else if (receivedValue < expectedValue) {
                    differences.push({
                        player,
                        attribute: attr,
                        expected: expectedValue,
                        received: receivedValue,
                        status: 'under'
                    });
                }
            }
            // String or other type comparison
            else if (expectedValue !== receivedValue) {
                differences.push({
                    player,
                    attribute: attr,
                    expected: expectedValue,
                    received: receivedValue,
                    status: 'mismatch'
                });
            }
        }
    }

    // Check for extra players in received
    for (const player in received) {
        if (!expected.hasOwnProperty(player)) {
            differences.push({
                player,
                attribute: 'Player Status',
                expected: 'Missing',
                received: 'Exists',
                status: 'extra'
            });
        }
    }

    return differences;
}

/**
 * Create a table to display differences between expected and received game states
 * @param {Array} differences - Array of difference objects from compareGameStates
 * @returns {HTMLElement} - The differences table element
 */
function createDifferencesTable(differences) {
    const table = document.createElement("table");
    table.classList.add("differences_table");

    // Create table header
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    const th1 = document.createElement("th");
    th1.textContent = "Player";
    const th2 = document.createElement("th");
    th2.textContent = "Attribute";
    const th3 = document.createElement("th");
    th3.textContent = "Expected";
    const th4 = document.createElement("th");
    th4.textContent = "Received";
    const th5 = document.createElement("th");
    th5.textContent = "Status";

    headerRow.appendChild(th1);
    headerRow.appendChild(th2);
    headerRow.appendChild(th3);
    headerRow.appendChild(th4);
    headerRow.appendChild(th5);
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement("tbody");

    differences.forEach(diff => {
        const row = document.createElement("tr");
        row.classList.add(`status_${diff.status}`); // For styling based on status

        const tdPlayer = document.createElement("td");
        tdPlayer.textContent = diff.player.toUpperCase();
        const tdAttribute = document.createElement("td");
        tdAttribute.textContent = diff.attribute;
        const tdExpected = document.createElement("td");
        tdExpected.textContent = diff.expected;
        const tdReceived = document.createElement("td");
        tdReceived.textContent = diff.received;
        const tdStatus = document.createElement("td");
        tdStatus.textContent = formatStatus(diff.status);

        // Add tooltip based on status
        let tooltipText = "";
        switch(diff.status) {
            case 'over':
                tooltipText = `${diff.attribute} is higher than expected by ${diff.received - diff.expected}`;
                break;
            case 'under':
                tooltipText = `${diff.attribute} is lower than expected by ${diff.expected - diff.received}`;
                break;
            case 'mismatch':
                tooltipText = `${diff.attribute} does not match the expected value.`;
                break;
            case 'missing':
                tooltipText = `${diff.attribute} is missing in the ${diff.expected === 'Exists' ? 'received' : 'expected'} game state.`;
                break;
            case 'extra':
                tooltipText = `Extra player present in the received game state.`;
                break;
            default:
                tooltipText = "";
        }

        row.title = tooltipText; // Set tooltip

        row.appendChild(tdPlayer);
        row.appendChild(tdAttribute);
        row.appendChild(tdExpected);
        row.appendChild(tdReceived);
        row.appendChild(tdStatus);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    return table;
}

/**
 * Format the status for display
 * @param {string} status - The status identifier
 * @returns {string} - Formatted status with icons
 */
function formatStatus(status) {
    switch(status) {
        case 'over':
            return 'Over ▲'; // Using an upward arrow
        case 'under':
            return 'Under ▼'; // Using a downward arrow
        case 'mismatch':
            return 'Mismatch ❌';
        case 'missing':
            return 'Missing ❓';
        case 'extra':
            return 'Extra ➕';
        default:
            return status;
    }
}

/**
 * Create a game state table
 * @param {string} title - The title of the table
 * @param {Object} gameState - The game state object
 * @returns {HTMLElement} - The game state table element
 */
function createGameStateTable(title, gameState) {
    const table = document.createElement("table");
    table.classList.add("game_state_table");

    // Create table header with title
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const th = document.createElement("th");
    th.colSpan = 3;
    th.textContent = title;
    headerRow.appendChild(th);
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create sub-header
    const subHeader = document.createElement("thead");
    const subHeaderRow = document.createElement("tr");
    const thPlayer = document.createElement("th");
    thPlayer.textContent = "Player";
    const thAttribute = document.createElement("th");
    thAttribute.textContent = "Attribute";
    const thValue = document.createElement("th");
    thValue.textContent = "Value";

    subHeaderRow.appendChild(thPlayer);
    subHeaderRow.appendChild(thAttribute);
    subHeaderRow.appendChild(thValue);
    subHeader.appendChild(subHeaderRow);
    table.appendChild(subHeader);

    // Create table body
    const tbody = document.createElement("tbody");

    for (const player in gameState) {
        if (!gameState.hasOwnProperty(player)) continue;

        for (const attr in gameState[player]) {
            if (!gameState[player].hasOwnProperty(attr)) continue;

            const row = document.createElement("tr");

            const tdPlayer = document.createElement("td");
            tdPlayer.textContent = player.toUpperCase();
            const tdAttribute = document.createElement("td");
            tdAttribute.textContent = attr;
            const tdValue = document.createElement("td");
            tdValue.textContent = gameState[player][attr];

            row.appendChild(tdPlayer);
            row.appendChild(tdAttribute);
            row.appendChild(tdValue);

            tbody.appendChild(row);
        }
    }

    table.appendChild(tbody);
    return table;
}

/**
 * Update rainbomb counts for a player
 * @param {string} player - The player identifier ('p1' or 'p2')
 * @param {Object} counts - An object with quadrants as keys and counts as values
 */
function updateRainbombCounts(player, counts) {
    const rainbombList = document.getElementById(`rainbomb_${player}`);
    if (rainbombList) {
        for (let quadrant = 1; quadrant <= 4; quadrant++) {
            const li = rainbombList.querySelector(`li:nth-child(${quadrant}) span`);
            if (li) {
                li.textContent = counts[quadrant] || 0;
            }
        }
    } else {
        console.error(`Rainbomb list for ${player} not found.`);
    }
}
