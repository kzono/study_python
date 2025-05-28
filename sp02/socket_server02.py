# server.py
import socket

HOST = '127.0.0.1'  # ローカルホスト
PORT = 65432        # ポート番号

def handle_client(conn, addr):
    """個々のクライアント接続を処理する関数"""
    print(f"Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"Client {addr} disconnected.")
                break

            received_message = data.decode('utf-8').strip() # 受信したデータを文字列として解釈し、改行などを除去

            print(f"Received from {addr}: '{received_message}'")

            response_message = ""
            if received_message == "HELLO":
                response_message = "Hi there! How can I help you?"
            elif received_message == "STATUS":
                response_message = "Server status: OK."
            elif received_message == "INFO":
                response_message = "This is a simple echo server with predefined responses."
            elif received_message == "QUIT":
                response_message = "Goodbye! Disconnecting."
                conn.sendall(response_message.encode('utf-8'))
                print(f"Client {addr} requested QUIT. Closing connection.")
                break # QUITを受信したら接続を閉じる
            else:
                response_message = f"Unknown command: '{received_message}'. Please send HELLO, STATUS, INFO, or QUIT."

            conn.sendall(response_message.encode('utf-8'))

    except ConnectionResetError:
        print(f"Client {addr} forcefully disconnected.")
    except Exception as e:
        print(f"An error occurred with client {addr}: {e}")
    finally:
        conn.close()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        try:
            conn, addr = s.accept() # クライアントからの接続を待機
            # ここではシンプルに逐次処理していますが、複数クライアントを同時に扱う場合は
            # スレッドや非同期I/O (asyncio) を使うのが一般的です。
            handle_client(conn, addr)
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            break
        except Exception as e:
            print(f"Error accepting connection: {e}")

print("Server finished.")