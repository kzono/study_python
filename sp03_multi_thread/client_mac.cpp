// client_macos.cpp
#include <iostream>
#include <string>
#include <vector>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h> // close
#include <termios.h> // termios
#include <fcntl.   // fcntl for non-blocking read
#include <map> // for key mapping

// サーバー情報
const std::string HOST = "127.0.0.1";
const int PORT = 65432;

// ターミナル設定を保存する構造体
struct termios old_tio;

// ターミナルをrawモードに設定
void set_terminal_raw_mode() {
    struct termios new_tio;
    tcgetattr(STDIN_FILENO, &old_tio); // 現在の設定を保存
    new_tio = old_tio;
    new_tio.c_lflag &= ~(ICANON | ECHO); // カノニカルモードとエコーを無効に
    new_tio.c_cc[VMIN] = 0;  // 読み取りはブロックしない (最低0文字)
    new_tio.c_cc[VTIME] = 0; // 読み取りのタイムアウトは0 (すぐに戻る)
    tcsetattr(STDIN_FILENO, TCSANOW, &new_tio); // 新しい設定を適用
}

// ターミナル設定を元に戻す
void reset_terminal_mode() {
    tcsetattr(STDIN_FILENO, TCSANOW, &old_tio);
}

// キー入力をノンブロッキングで読み込む
int get_char_non_blocking() {
    char buf[1];
    struct timeval tv;
    fd_set fds;

    tv.tv_sec = 0;
    tv.tv_usec = 0; // タイムアウトを0に設定
    FD_ZERO(&fds);
    FD_SET(STDIN_FILENO, &fds); // 標準入力にセット

    select(STDIN_FILENO + 1, &fds, NULL, NULL, &tv); // selectで読み込み可能かチェック
    if (FD_ISSET(STDIN_FILENO, &fds)) { // 読み込み可能なら
        return read(STDIN_FILENO, buf, 1) == 1 ? (int)buf[0] : -1;
    }
    return -1; // 入力なし
}

// メイン関数
int main() {
    set_terminal_raw_mode(); // ターミナルをrawモードに設定
    std::atexit(reset_terminal_mode); // プログラム終了時にターミナル設定を戻す

    // 1. ソケットの作成
    int client_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (client_socket < 0) {
        std::cerr << "Socket creation failed." << std::endl;
        return 1;
    }

    // 2. サーバーアドレスの設定
    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    // IPアドレス変換
    if (inet_pton(AF_INET, HOST.c_str(), &(server_addr.sin_addr)) <= 0) {
        std::cerr << "Invalid address/ Address not supported" << std::endl;
        close(client_socket);
        return 1;
    }

    // 3. サーバーへの接続
    if (connect(client_socket, (sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        std::cerr << "Connection Failed." << std::endl;
        close(client_socket);
        return 1;
    }

    std::cout << "Connected to server. Use arrow keys to move cat. Press 'q' to send QUIT, 'e' to exit." << std::endl;

    char recv_buffer[1024];
    std::string command;

    while (true) {
        command = ""; // コマンドをリセット
        int key = get_char_non_blocking(); // キーをノンブロッキングで読み込む

        if (key != -1) { // キー入力があった場合
            if (key == 27) { // ESCシーケンス (矢印キーなど)
                int next_char = get_char_non_blocking();
                if (next_char == 91) { // '['
                    next_char = get_char_non_blocking();
                    switch (next_char) {
                        case 65: command = "UP"; break;    // A (↑)
                        case 66: command = "DOWN"; break;  // B (↓)
                        case 68: command = "LEFT"; break;  // D (←)
                        case 67: command = "RIGHT"; break; // C (→)
                    }
                }
            } else { // 通常のキー
                switch (key) {
                    case 'q':
                    case 'Q': command = "QUIT"; break;
                    case 'e':
                    case 'E':
                        std::cout << "Exiting client." << std::endl;
                        goto end_loop; // ループを抜けるためのgoto
                }
            }
        }

        if (!command.empty()) {
            // コマンド送信
            int bytes_sent = send(client_socket, command.c_str(), command.length(), 0);
            if (bytes_sent < 0) {
                std::cerr << "send failed." << std::endl;
                break;
            }
            std::cout << "Sent: '" << command << "'" << std::endl;

            // サーバーからの応答受信
            int bytes_received = recv(client_socket, recv_buffer, sizeof(recv_buffer) - 1, 0);
            if (bytes_received > 0) {
                recv_buffer[bytes_received] = '\0'; // ヌル終端
                std::cout << "Received from server: '" << recv_buffer << "'" << std::endl;
            } else if (bytes_received == 0) {
                std::cout << "Server closed the connection." << std::endl;
                break;
            } else {
                std::cerr << "recv failed." << std::endl;
                break;
            }

            if (command == "QUIT") {
                std::cout << "Sent QUIT. Disconnecting." << std::endl;
                break;
            }
        }
        // usleep(10000); // 10ms delay (macOS)
    }

end_loop: // gotoのジャンプ先
    // 4. ソケットを閉じる
    close(client_socket);

    std::cout << "Client finished." << std::endl;
    return 0;
}