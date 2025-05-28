# client.py
import socket

HOST = '127.0.0.1'  # サーバーのIPアドレス
PORT = 65432        # サーバーのポート番号

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    message = "Hello, server!"
    s.sendall(message.encode('utf-8')) # 文字列をバイトデータにエンコードして送信
    data = s.recv(1024) # サーバーからの応答を受信

print(f"Sent: {message}")
print(f"Received from server: {data.decode('utf-8')}")

print("Client finished.")