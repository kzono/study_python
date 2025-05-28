/*
 
Windows: cl client_win.cpp -o client.exe -lws2_32



*/
// client_win.cpp
#include <iostream>
#include <string>
#include <winsock2.h> // Winsock API
#include <ws2tcpip.h> // for inet_pton
#include <conio.h>    // _kbhit(), _getch()

#pragma comment(lib, "ws2_32.lib") // Winsockライブラリをリンク

// サーバー情報
const std::string HOST = "127.0.0.1";
const int PORT = 65432;

// メイン関数
int main() {
    // 1. Winsockの初期化
    WSADATA wsaData;
    int iResult = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (iResult != 0) {
        std::cerr << "WSAStartup failed: " << iResult << std::endl;
        return 1;
    }

    // 2. ソケットの作成
    SOCKET client_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (client_socket == INVALID_SOCKET) {
        std::cerr << "Error at socket(): " << WSAGetLastError() << std::endl;
        WSACleanup();
        return 1;
    }

    // 3. サーバーアドレスの設定
    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    // IPアドレス変換
    if (inet_pton(AF_INET, HOST.c_str(), &(server_addr.sin_addr)) <= 0) {
        std::cerr << "Invalid address/ Address not supported" << std::endl;
        closesocket(client_socket);
        WSACleanup();
        return 1;
    }

    // 4. サーバーへの接続
    iResult = connect(client_socket, (SOCKADDR*)&server_addr, sizeof(server_addr));
    if (iResult == SOCKET_ERROR) {
        std::cerr << "connect failed with error: " << WSAGetLastError() << std::endl;
        closesocket(client_socket);
        WSACleanup();
        return 1;
    }

    std::cout << "Connected to server. Use arrow keys to move cat. Press 'q' to send QUIT, 'e' to exit." << std::endl;
    std::cout << "(Note: Arrow keys might be less responsive in some console environments.)" << std::endl;

    char recv_buffer[1024];
    std::string command;

    while (true) {
        command = ""; // コマンドをリセット

        if (_kbhit()) { // キー入力があるかチェック
            int key = _getch(); // キーを読み込む
            
            if (key == 224) { // 拡張キーコードのプレフィックス (矢印キーなど)
                key = _getch(); // 次のキーコードを読み込む
                switch (key) {
                    case 72: command = "UP"; break;    // 上矢印
                    case 80: command = "DOWN"; break;  // 下矢印
                    case 75: command = "LEFT"; break;  // 左矢印
                    case 77: command = "RIGHT"; break; // 右矢印
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
            if (bytes_sent == SOCKET_ERROR) {
                std::cerr << "send failed: " << WSAGetLastError() << std::endl;
                break;
            }
            std::cout << "Sent: '" << command << "'" << std::endl;

            // サーバーからの応答受信
            int bytes_received = recv(client_socket, recv_buffer, sizeof(recv_buffer) - 1, 0);
            if (bytes_received > 0) {
                recv_buffer[bytes_received] = '\0'; // ヌル終端
                std::cout << "Received from server: '" << recv_buffer << "'" << std.endl;
            } else if (bytes_received == 0) {
                std::cout << "Server closed the connection." << std::endl;
                break;
            } else {
                std::cerr << "recv failed: " << WSAGetLastError() << std::endl;
                break;
            }

            if (command == "QUIT") {
                std::cout << "Sent QUIT. Disconnecting." << std::endl;
                break;
            }
        }
        // 少し遅延を入れないとCPU使用率が高くなる可能性がある
        // Sleep(10); // Windows
    }

end_loop: // gotoのジャンプ先
    // 6. ソケットとWinsockをクリーンアップ
    closesocket(client_socket);
    WSACleanup();

    std::cout << "Client finished." << std::endl;
    return 0;
}