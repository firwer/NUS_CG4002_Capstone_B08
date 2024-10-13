import paramiko
import threading
import socket
import sys
import time
import select
import config


def prompt_user_for_port():
    while True:
        try:
            eval_server_port = int(input("Please provide the port that you see on the eval server UI: "))
            return eval_server_port
        except ValueError:
            print("Invalid input, please enter a valid port number.")


def find_remote_free_port(client):
    stdin, stdout, stderr = client.exec_command(
        "python3 -c 'import socket; s=socket.socket(); s.bind((\"\",0)); print(s.getsockname()[1]); s.close()'")
    remote_port_str = stdout.read().decode().strip()
    if not remote_port_str.isdigit():
        print(f"Could not find a free port on remote host: {remote_port_str}")
        sys.exit(1)
    remote_port = int(remote_port_str)
    return remote_port


def reverse_forward_tunnel(remote_port, local_host, local_port, transport):
    """
    Create a reverse tunnel from the remote server port to the specified local host and port.
    """
    try:
        transport.request_port_forward('', remote_port)
        print(f"Reverse SSH tunnel established: remote {remote_port} -> local {local_port}")
    except Exception as e:
        print(f"Failed to establish reverse SSH tunnel: {e}")
        return

    while True:
        chan = transport.accept(1000)
        if chan is None:
            continue
        # Open a connection to the local host and port
        sock = socket.socket()
        try:
            sock.connect((local_host, local_port))
        except Exception as e:
            print(f"Forwarding request to {local_host}:{local_port} failed: {e}")
            chan.close()
            continue
        # Start a thread to forward data between the channels
        threading.Thread(target=handler, args=(chan, sock)).start()


def handler(chan, sock):
    while True:
        r, w, x = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.sendall(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.sendall(data)
    chan.close()
    sock.close()


def run_game_server_on_ultra96(client, remote_port):
    print(f"Running game server on Ultra96 using port {remote_port}...")

    try:
        # Kill any existing active relay node TCP port
        print("Killing any existing process on port 65001...")
        client.exec_command('fuser -KILL -k -n tcp 65001', timeout=10)

        # Run the game server remotely on the Ultra96
        command = f'source /usr/local/share/pynq-venv/bin/activate && python /home/xilinx/ext_comms/main.py {remote_port}'
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)

        # Start threads to read stdout and stderr
        threading.Thread(target=read_stream, args=(stdout, "STDOUT")).start()
        threading.Thread(target=read_stream, args=(stderr, "STDERR")).start()

    except Exception as e:
        print(f"Failed to run the game server on Ultra96: {e}")


def read_stream(stream, stream_name):
    for line in iter(lambda: stream.readline(2048), ""):
        if line:
            print(f"[REMOTE {stream_name}] {line}", end='')
        else:
            break


def main():
    local_port = prompt_user_for_port()
    local_host = '127.0.0.1'

    # Set up reverse SSH tunneling and get the remote free port
    remote_host = config.ssh_host
    remote_user = config.ssh_user
    ssh_password = config.ssh_password

    try:
        # Create SSH client and connect
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(remote_host, username=remote_user, password=ssh_password)

        # Find a free port on the remote host
        remote_port = find_remote_free_port(client)
        print(f"Found free port on remote: {remote_port}")

        transport = client.get_transport()

        # Start reverse port forwarding in a separate thread
        reverse_tunnel_thread = threading.Thread(target=reverse_forward_tunnel,
                                                 args=(remote_port, local_host, local_port, transport))
        reverse_tunnel_thread.daemon = True
        reverse_tunnel_thread.start()

        # Run the game server on the remote host
        run_game_server_on_ultra96(client, remote_port)

        # Keep the main thread alive to maintain the SSH connection
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
