import asyncssh
import asyncio
import socket
import config

'''
Purpose: This will allow evaluation client to communicate with evaluation server hosted outside of the Ultra96 board.

It is bloody painful to manually find a free port on the remote machine and bind it to the local evaluation server port
for reverse SSH tunneling each time. This script fully automates the process by finding a free port on the remote machine 
and binding it to the local evaluation server port. The script then runs the game server on the remote machine using the 
bound port.

This script consist of 2 main jobs:
1. Setup Reverse SSH Tunneling based on the port the evaluation server is listening on in your local machine.
2. Run the game server on U96 using the random available port that was bound to the local evaluation server port.

'''


def prompt_user_for_port():
    while True:
        try:
            eval_server_port = int(input("Please provide the port that you see on the eval server UI: "))
            return eval_server_port
        except ValueError:
            print("Invalid input, please enter a valid port number.")


def find_free_port():
    """Find a free port on the local machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


async def reverse_ssh_tunnel(remote_host, remote_user, local_port):
    # Find a free port on the remote machine
    remote_port = find_free_port()
    print(f"Found free port on remote: {remote_port}")

    try:
        async with asyncssh.connect(remote_host, username=remote_user, password=config.ssh_password,
                                    known_hosts=None) as conn:
            # Bind the free remote port to the local evaluation server port
            forwarder = await conn.forward_remote_port('127.0.0.1', remote_port, '127.0.0.1', local_port)
            print(f"Reverse SSH tunnel established: remote {remote_port} -> local {local_port}")

            await run_game_server_on_ultra96(conn, remote_port)
            # Keep the SSH tunnel alive
            await forwarder.wait_closed()

    except (OSError, asyncssh.Error) as exc:
        print(f'Error in SSH tunnel: {str(exc)}')

    return remote_port


async def run_game_server_on_ultra96(conn, remote_port):
    print(f"Running game server on Ultra96 using port {remote_port}...")

    try:
        # Kill any existing active relay node TCP port
        print("Running game server on Ultra96...")
        # Run the game server remotely on the Ultra96
        await conn.run('fuser -KILL -k -n tcp 65001')
        result = await conn.run(f'source /usr/local/share/pynq-venv/bin/activate && python '
                                f'/home/cg4002/ext_comms/main.py {remote_port}', check=True)
        # Print standard output and error
        print("Game server output:")
        print(result.stdout)
        print("Game server errors (if any):")
        print(result.stderr)

    except asyncssh.ProcessError as e:
        print(f"Failed to run the game server on Ultra96: {e}")
        print(f"Error details: {e.stderr}")

async def main():
    local_port = prompt_user_for_port()

    # Set up reverse SSH tunneling and get the remote free port
    remote_host = config.ssh_host
    remote_user = config.ssh_user
    try:
        remote_port = await reverse_ssh_tunnel(remote_host, remote_user, local_port)
        await run_game_server_on_ultra96(remote_port)
    except KeyboardInterrupt as e:
        print("Exiting...")


if __name__ == "__main__":
    asyncio.run(main())
