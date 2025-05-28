# gui_server.py (GUIサーバー - 猫画像移動アニメーション)
import tkinter as tk
from tkinter import scrolledtext
import threading
import socket
import queue
import time
from PIL import Image, ImageTk

# --- 定数 ---
HOST = '127.0.0.1'
PORT = 65432
GUI_UPDATE_INTERVAL_MS = 100 # GUIの更新間隔（ミリ秒）
CAT_IMAGE_PATH = "sleep_animal_cat.png"  # ここに猫の画像ファイルのパスを指定してください (例: cat.png, cat.jpg)
MOVE_STEP = 10              # 猫の移動量 (ピクセル)
INITIAL_X = 150             # 猫の初期X座標
INITIAL_Y = 100             # 猫の初期Y座標
MAX_WIDTH = 600             # ウィンドウの最大幅
MAX_HEIGHT = 400            # ウィンドウの最大高さ

# --- スレッド間でデータをやり取りするためのキュー ---
socket_to_gui_queue = queue.Queue() # ソケット受信 -> GUI表示/制御用

# --- ソケット通信を担当するスレッド（サーバー側） ---
class SocketServerThread(threading.Thread):
    def __init__(self, host, port, incoming_queue):
        super().__init__()
        self.host = host
        self.port = port
        self.incoming_queue = incoming_queue # 受信データをGUIに渡すキュー
        self.server_socket = None
        self.client_conn = None
        self.client_addr = None
        self.running = True

    def run(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 再利用を許可
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1) # 1つのクライアント接続を許可
            self.incoming_queue.put(f"Server: Listening on {self.host}:{self.port}")
            print(f"SocketServerThread: Listening on {self.host}:{self.port}")

            self.server_socket.settimeout(0.5) # acceptにタイムアウトを設定して、停止要求をチェックできるようにする

            while self.running:
                try:
                    self.client_conn, self.client_addr = self.server_socket.accept()
                    self.incoming_queue.put(f"Client connected from {self.client_addr}")
                    print(f"SocketServerThread: Client connected from {self.client_addr}")
                    break # クライアントが接続したらループを抜けて通信フェーズへ
                except socket.timeout:
                    if not self.running: # タイムアウト中に停止フラグが立っていたら終了
                        break
                    continue # タイムアウトしただけなら続行
                except Exception as e:
                    print(f"SocketServerThread: Error during accept: {e}")
                    self.incoming_queue.put(f"Server error: {e}")
                    self.running = False
                    break

            if self.client_conn: # クライアントが接続した場合のみ通信ループへ
                with self.client_conn:
                    while self.running:
                        try:
                            data = self.client_conn.recv(1024)
                            if not data:
                                print(f"SocketServerThread: Client {self.client_addr} disconnected.")
                                self.incoming_queue.put(f"Client {self.client_addr} disconnected.")
                                break # クライアント切断
                            
                            received_command = data.decode('utf-8').strip().upper() # 受信コマンドを大文字に変換
                            print(f"SocketServerThread: Received command: '{received_command}'")

                            # 受信したコマンドをGUIに渡す (dict形式でアクションを指示)
                            if received_command in ["UP", "DOWN", "LEFT", "RIGHT"]:
                                self.incoming_queue.put({"action": "move_cat", "direction": received_command})
                                response = f"Server: Moving cat {received_command}."
                            elif received_command == "QUIT":
                                response = "Server: Goodbye!"
                            else:
                                response = f"Server: Unknown command: '{received_command}'"

                            self.client_conn.sendall(response.encode('utf-8'))

                            if received_command == "QUIT":
                                print(f"SocketServerThread: Client {self.client_addr} sent QUIT. Closing connection.")
                                break # QUITを受信したら通信ループを終了
                            
                        except socket.timeout:
                            pass
                        except (ConnectionResetError, BrokenPipeError):
                            print(f"SocketServerThread: Client {self.client_addr} connection lost.")
                            self.incoming_queue.put(f"Client {self.client_addr} connection lost.")
                            break
                        except Exception as e:
                            print(f"SocketServerThread: Error during communication: {e}")
                            self.incoming_queue.put(f"Communication error: {e}")
                            break
        except Exception as e:
            print(f"SocketServerThread: Server startup error: {e}")
            self.incoming_queue.put(f"Server startup error: {e}")
        finally:
            if self.client_conn:
                self.client_conn.close()
            if self.server_socket:
                self.server_socket.close()
            print("SocketServerThread: Server thread stopped.")
            self.incoming_queue.put("Server: Socket thread stopped.")

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
                self.server_socket.close()
            except OSError:
                pass


# --- GUIアプリケーション ---
class Application(tk.Frame):
    def __init__(self, master=None, incoming_queue=None):
        super().__init__(master)
        self.master = master
        self.incoming_queue = incoming_queue
        self.master.title("Cat Mover Server")
        self.pack(fill=tk.BOTH, expand=True)

        self.socket_thread = None

        self.cat_image = None
        self.cat_photo = None # Tkinter PhotoImageオブジェクト
        self.cat_x = INITIAL_X
        self.cat_y = INITIAL_Y

        self.load_cat_image()
        self.create_widgets()
        self.start_socket_thread()
        self.process_incoming_messages() # キューを定期的にチェック

    def load_cat_image(self):
        """猫の画像をロードし、リサイズしてTkinterで表示可能にする"""
        try:
            self.cat_image = Image.open(CAT_IMAGE_PATH)
            # 画像を適切なサイズにリサイズ（任意）
            self.cat_image = self.cat_image.resize((100, 100), Image.Resampling.LANCZOS)
            self.cat_photo = ImageTk.PhotoImage(self.cat_image)
            print(f"GUI: Loaded cat image from '{CAT_IMAGE_PATH}'.")
        except FileNotFoundError:
            print(f"GUI: Error: Cat image file '{CAT_IMAGE_PATH}' not found.")
            self.log_message(f"Error: '{CAT_IMAGE_PATH}' not found. No cat image.")
            self.cat_photo = None
        except Exception as e:
            print(f"GUI: Error loading cat image: {e}")
            self.log_message(f"Error loading cat image: {e}.")
            self.cat_photo = None

    def create_widgets(self):
        # キャンバスを作成して画像を配置
        self.canvas = tk.Canvas(self, width=MAX_WIDTH, height=MAX_HEIGHT, bg="white", borderwidth=2, relief="groove")
        self.canvas.pack(pady=10)
        
        if self.cat_photo:
            self.cat_id = self.canvas.create_image(self.cat_x, self.cat_y, image=self.cat_photo, anchor=tk.CENTER)
        else:
            self.cat_id = None
            self.canvas.create_text(MAX_WIDTH/2, MAX_HEIGHT/2, text="Cat image not loaded!", fill="red")

        # ログ表示エリア
        self.log_label = tk.Label(self, text="Server Log:")
        self.log_label.pack(pady=5)
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=60, height=10, state='disabled')
        self.log_area.pack(pady=5)
        
        # 終了ボタン
        self.quit_button = tk.Button(self, text="Quit Server", fg="red", command=self.on_closing)
        self.quit_button.pack(pady=10)

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log_message(self, message):
        """ログエリアにメッセージを追加するヘルパー関数"""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def start_socket_thread(self):
        """ソケット通信スレッドを開始する"""
        self.socket_thread = SocketServerThread(HOST, PORT, self.incoming_queue)
        self.socket_thread.daemon = True # メインスレッド終了時に一緒に終了させる
        self.socket_thread.start()

    def process_incoming_messages(self):
        """キューから受信メッセージをGUIに表示し、猫の移動を制御する"""
        while not self.incoming_queue.empty():
            try:
                message = self.incoming_queue.get_nowait()
                if isinstance(message, dict) and message.get("action") == "move_cat":
                    direction = message["direction"]
                    self.move_cat(direction)
                    self.log_message(f"Moved cat: {direction}")
                else:
                    self.log_message(str(message))
            except queue.Empty:
                pass

        self.master.after(GUI_UPDATE_INTERVAL_MS, self.process_incoming_messages)

    def move_cat(self, direction):
        """猫画像をCanvas上で移動させる"""
        if not self.cat_id:
            return # 画像がロードされていない場合

        dx, dy = 0, 0
        if direction == "UP":
            dy = -MOVE_STEP
        elif direction == "DOWN":
            dy = MOVE_STEP
        elif direction == "LEFT":
            dx = -MOVE_STEP
        elif direction == "RIGHT":
            dx = MOVE_STEP

        new_x = self.cat_x + dx
        new_y = self.cat_y + dy

        # 画面端での境界チェック
        # 画像の中心がキャンバスの範囲内にあることを保証
        image_width_half = self.cat_image.width // 2 if self.cat_image else 0
        image_height_half = self.cat_image.height // 2 if self.cat_image else 0

        if new_x < image_width_half:
            new_x = image_width_half
        elif new_x > MAX_WIDTH - image_width_half:
            new_x = MAX_WIDTH - image_width_half

        if new_y < image_height_half:
            new_y = image_height_half
        elif new_y > MAX_HEIGHT - image_height_half:
            new_y = MAX_HEIGHT - image_height_half

        self.cat_x = new_x
        self.cat_y = new_y
        
        self.canvas.coords(self.cat_id, self.cat_x, self.cat_y)


    def on_closing(self):
        """GUIが閉じられるときにソケットスレッドを安全に停止する"""
        if self.socket_thread:
            self.socket_thread.stop()
            self.socket_thread.join(timeout=2.0) # スレッドが終了するのを待つ (最大2秒)
            if self.socket_thread.is_alive():
                print("Warning: Socket thread did not terminate cleanly.")
                self.log_message("Warning: Socket thread did not terminate cleanly.")
        self.master.destroy() # GUIを閉じる


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root, incoming_queue=socket_to_gui_queue)
    root.mainloop()