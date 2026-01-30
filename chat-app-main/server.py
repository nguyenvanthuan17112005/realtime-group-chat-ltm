import socket
import threading
from datetime import datetime

# CẤU HÌNH
HOST = '127.0.0.1'
PORT = 4321
LISTENER_LIMIT = 10  

active_clients = [] # List lưu: (username, client_socket)
clients_lock = threading.Lock() # Khóa để tránh xung đột khi nhiều người vào/ra cùng lúc

def send_message_to_all(message):
    """Gửi tin nhắn đến tất cả client đang online"""
    with clients_lock:
        for user in active_clients:
            try:
                user[1].sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Không thể gửi đến {user[0]}: {e}")

def remove_client(username):
    """Xóa client khỏi danh sách hoạt động một cách an toàn"""
    with clients_lock:
        for user in active_clients:
            if user[0] == username:
                active_clients.remove(user)
                break

def listen_for_message(client, username):
    """Luồng riêng để lắng nghe tin nhắn từ từng client"""
    while True:
        try:
            message = client.recv(2048).decode('utf-8')
            if not message:
                break
            
            time_now = datetime.now().strftime('%H:%M:%S')
            print(f"[{time_now}] {username}: {message}")
            send_message_to_all(f"{username}~{message}")
        except:
            break

    client.close()
    remove_client(username)
    send_message_to_all(f"SERVER~{username} đã rời phòng chat.")
    print(f"[DISCONNECT] {username} đã thoát.")

def client_handler(client):
    """Xử lý giai đoạn đăng nhập của client"""
    try:
        username = client.recv(2048).decode('utf-8')
        
        # 1. Kiểm tra tên trống hoặc trùng
        is_taken = any(user[0] == username for user in active_clients)
        if not username or is_taken:
            client.sendall("SERVER~Tên không hợp lệ hoặc đã tồn tại!".encode('utf-8'))
            client.close()
            return

        # 2. Thêm vào danh sách an toàn với Lock
        with clients_lock:
            active_clients.append((username, client))
        
        time_now = datetime.now().strftime('%H:%M:%S')
        print(f"[{time_now}] [JOIN] {username} đã tham gia.")
        send_message_to_all(f"SERVER~{username} đã vào phòng chat.")

        # 3. Bắt đầu luồng lắng nghe
        threading.Thread(target=listen_for_message, args=(client, username), daemon=True).start()

    except Exception as e:
        print(f"[ERROR] Lỗi handler: {e}")
        client.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server.bind((HOST, PORT))
        server.listen(LISTENER_LIMIT)
        print(f"SERVER ĐANG CHẠY TẠI {HOST}:{PORT}")
        print("Nhấn Ctrl+C để dừng Server an toàn.\n" + "-"*40)

        while True:
            client, address = server.accept()
            # print(f"[CONNECTION] Kết nối mới từ {address}") # Bỏ bớt cho đỡ rối console
            threading.Thread(target=client_handler, args=(client,), daemon=True).start()
            
    except KeyboardInterrupt:
        print("\n Server đang đóng...")
    finally:
        server.close()

if __name__ == "__main__":
    main()