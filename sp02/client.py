# client.py
import socket
import sys

HOST = '127.0.0.1'  # サーバーのIPアドレス
PORT = 65432        # サーバーのポート番号

print("Connecting to server...")
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}")
        print("Enter one of the following commands: HELLO, STATUS, INFO, QUIT")
        print("Type 'exit' to quit the client.")

        while True:
            try:
                command = input("Enter command: ").strip().upper() # 入力を大文字に変換し、空白を除去

                if command == 'EXIT':
                    print("Exiting client.")
                    break # クライアントを終了

                if not command:
                    print("Command cannot be empty. Please enter a command.")
                    continue

                # コマンドをサーバーに送信
                s.sendall(command.encode('utf-8'))
                print(f"Sent: '{command}'")

                # サーバーからの応答を受信
                data = s.recv(1024)
                if not data:
                    print("Server closed the connection.")
                    break # サーバーが切断した場合

                received_response = data.decode('utf-8')
                print(f"Received from server: '{received_response}'")

                if command == "QUIT":
                    print("Server responded to QUIT. Disconnecting.")
                    break # QUITコマンドを送信したら、クライアントも切断

            except KeyboardInterrupt:
                print("\nClient interrupted. Closing connection.")
                break
            except BrokenPipeError:
                print("Server closed the connection unexpectedly.")
                break
            except ConnectionResetError:
                print("Server forcefully closed the connection.")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

except ConnectionRefusedError:
    print(f"Connection refused. Make sure the server is running on {HOST}:{PORT}.")
except Exception as e:
    print(f"An error occurred while connecting: {e}")

print("Client finished.")