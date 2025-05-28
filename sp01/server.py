# server.py
import socket

HOST = '127.0.0.1'  # ローカルホストを指すIPアドレス
PORT = 65432        # 1024より大きい、未使用のポート番号

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024) # 最大1024バイトのデータを受信
            if not data:
                break
            print(f"Received: {data.decode('utf-8')}")
            conn.sendall(data) # 受信したデータをそのままクライアントに送り返す

print("Server finished.")