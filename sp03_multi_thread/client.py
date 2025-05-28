# client.py (CLIクライアント - 矢印キー入力対応)
import socket
import sys
import time

# OSに応じたキー入力モジュールをインポート
try:
    import msvcrt # Windows
except ImportError:
    import termios, tty, select # Linux/macOS

HOST = '127.0.0.1'  # サーバーのIPアドレス
PORT = 65432        # サーバーのポート番号

def get_char_unix():
    """Linux/macOS でキー入力を1文字取得する"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        # 矢印キーはエスケープシーケンスで始まる
        if ch == '\x1b': # ESC
            ch += sys.stdin.read(2) # 次の2文字を読み込む (例: [A, [B, [C, [D)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def get_char_windows():
    """Windows でキー入力を1文字取得する"""
    return msvcrt.getch().decode('utf-8')

# OSに応じたキー入力関数を選択
if sys.platform == "win32":
    get_char = get_char_windows
    KEY_MAP = {
        '\xe0H': 'UP',    # 拡張キーコードのH (↑)
        '\xe0P': 'DOWN',  # 拡張キーコードのP (↓)
        '\xe0K': 'LEFT',  # 拡張キーコードのK (←)
        '\xe0M': 'RIGHT', # 拡張キーコードのM (→)
        'q': 'QUIT',      # Qキーで終了
        'Q': 'QUIT',
        'e': 'EXIT',      # Eキーでクライアント終了
        'E': 'EXIT',
    }
else: # Linux/macOS
    get_char = get_char_unix
    KEY_MAP = {
        '\x1b[A': 'UP',    # ESC [ A (↑)
        '\x1b[B': 'DOWN',  # ESC [ B (↓)
        '\x1b[D': 'LEFT',  # ESC [ D (←)
        '\x1b[C': 'RIGHT', # ESC [ C (→)
        'q': 'QUIT',      # Qキーで終了
        'Q': 'QUIT',
        'e': 'EXIT',      # Eキーでクライアント終了
        'E': 'EXIT',
    }


print("Connecting to GUI Server...")
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}")
        print("Use arrow keys (↑↓←→) to move the cat.")
        print("Press 'q' to send QUIT command to server.")
        print("Press 'e' to exit this client.")
        print("\n(Note: Some terminals may not capture arrow keys directly, try another terminal if issues occur.)")

        while True:
            try:
                char_input = get_char()
                command = KEY_MAP.get(char_input, None) # キーマップからコマンドを取得

                if command == 'EXIT':
                    print("Exiting client.")
                    break

                if command:
                    # コマンドをサーバーに送信
                    s.sendall(command.encode('utf-8'))
                    print(f"Sent: '{command}'")
                    
                    # サーバーからの応答を受信
                    data = s.recv(1024)
                    if not data:
                        print("Server closed the connection.")
                        break

                    received_response = data.decode('utf-8')
                    print(f"Received from server: '{received_response}'")

                    if command == "QUIT":
                        print("Server responded to QUIT. Disconnecting.")
                        break
                else:
                    # 未知のキー入力は表示しない
                    pass

            except Exception as e:
                print(f"An error occurred: {e}")
                break

except ConnectionRefusedError:
    print(f"Connection refused. Make sure the GUI Server is running on {HOST}:{PORT}.")
except Exception as e:
    print(f"An error occurred while connecting: {e}")

print("Client finished.")