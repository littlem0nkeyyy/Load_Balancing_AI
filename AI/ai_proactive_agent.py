import socket
import json
import struct
import time
import threading
import datetime
from ai_engine import AIBrain
from config import *

class AIProactiveAgent:
    def __init__(self):
        self.brain = AIBrain()
        self.last_action = "STAY"  # Biến chia sẻ để Adaptive biết Decision vừa làm gì
        self.lock = threading.Lock() # Khóa an toàn để tránh xung đột khi 2 luồng cùng truy cập AI Brain

        self.protected_servers = [
            "130.94.65.44:8081"
        ]
    def get_lbs_status_connection(self):

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((LBS_HOST, LBS_PORT))

            # Gửi lệnh lấy dữ liệu
            cmd = json.dumps({"action": "GET_STATUS"}).encode('utf-8')
            s.sendall(struct.pack('>I', len(cmd)) + cmd)

            # Nhận header độ dài (4 bytes)
            raw_len = self.recvall(s, 4)
            if not raw_len: 
                s.close()
                return None, None
            
            # Nhận nội dung JSON
            msglen = struct.unpack('>I', raw_len)[0]
            data_raw = self.recvall(s, msglen).decode('utf-8')
            payload = json.loads(data_raw)

            # Trả về cả payload và socket (để decision_cycle dùng socket này gửi lệnh tiếp nếu cần)
            return payload, s
        
        except Exception as e:
            print(f"[!] Lỗi kết nối LBS: {e}")
            return None, None


    def decision_cycle(self):
        """Luồng chạy liên tục 10s/lần để ra lệnh đóng mở server"""
        print("[*] Luồng Decision (10s) đã khởi động...")
        
        while True:
            # 1. Gọi hàm chung để lấy dữ liệu (Kết nối độc lập A)
            payload, s_conn = self.get_lbs_status_connection()
            
            if payload and s_conn:
                servers_data = payload.get('servers', [])
                current_action = "STAY"

                for s_info in servers_data:
                    s_url = s_info['url']
                    h = s_info['health']

                    # Mapping dữ liệu LBS sang định dạng AI học
                    metrics = [0, 0, 0, h['cpuUsagePercent'], h['memoryUsagePercent'], 
                               h['currConnections'], 0, 0, h['avgProcessingTimeSec'], 0]

                    # --- BẮT ĐẦU VÙNG AN TOÀN (CRITICAL SECTION) ---
                    with self.lock: 
                        # Trong khi đang dự đoán, không cho phép luồng Adaptive thay đổi ngưỡng
                        is_overload, prob = self.brain.analyze_server(metrics)
                        current_idle_threshold = self.brain.idle_threshold
                    # --- KẾT THÚC VÙNG AN TOÀN ---

                    # Logic ra lệnh
                    cmd_action = None

                    if is_overload:
                        cmd_action = "OPEN_SERVER"
                    elif h['cpuUsagePercent'] < current_idle_threshold:
                        is_protected = any(pid in s_url for pid in self.protected_servers)
                        if is_protected:
                            cmd_action = None
                        else: 
                            cmd_action = "CLOSE_SERVER"

                    # Gửi lệnh ngay trên socket đang mở
                    if cmd_action:
                        current_action = cmd_action
                        self.send_command(s_conn, cmd_action, s_url)
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Decision: {cmd_action} -> {s_info['url']}")

                # Cập nhật hành động cuối để luồng Adaptive tham khảo
                self.last_action = current_action
                
                # Đóng kết nối A
                s_conn.close()

            # Ngủ 10 giây
            time.sleep(10)


    def adaptive_cycle(self):
        """Luồng chạy chậm 5 phút/lần để tự điều chỉnh ngưỡng"""
        print("[*] Luồng Adaptive (5min) đã khởi động...")
        
        while True:
            # Ngủ 300 giây (5 phút) trước khi bắt đầu học
            time.sleep(300)
            
            print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] --- BẮT ĐẦU TỰ HỌC ---")
            
            # 1. Gọi hàm chung để lấy dữ liệu (Kết nối độc lập B)
            payload, s_conn = self.get_lbs_status_connection()
            
            if payload:
                servers_data = payload.get('servers', [])
                # Gom dữ liệu hiện tại của toàn bộ server
                all_metrics_now = []
                for s in servers_data:
                    h = s['health']
                    m = [0, 0, 0, h['cpuUsagePercent'], h['memoryUsagePercent'], 
                         h['currConnections'], 0, 0, h['avgProcessingTimeSec'], 0]
                    all_metrics_now.append(m)

                # --- BẮT ĐẦU VÙNG AN TOÀN ---
                with self.lock:
                    # AI tự soi lại: "5 phút trước mình làm 'last_action', giờ hệ thống thế nào?"
                    self.brain.adjust_all_thresholds(all_metrics_now, self.last_action)
                    print(f"[*] Đã học xong. Ngưỡng mới: CONF={self.brain.conf_threshold:.3f}, IDLE={self.brain.idle_threshold:.1f}%")
                # --- KẾT THÚC VÙNG AN TOÀN ---
            
            if s_conn:
                s_conn.close() # Kết nối B chỉ dùng để lấy data học, xong là đóng ngay
            
            print("--- KẾT THÚC TỰ HỌC ---\n")


    def send_command(self, sock, action, url):
        """Gửi lệnh điều khiển"""
        cmd = json.dumps({"action": action, "serverUrl": url}).encode('utf-8')
        sock.sendall(struct.pack('>I', len(cmd)) + cmd)
        # Đọc xác nhận (nếu có) để tránh nghẽn buffer
        r = self.recvall(sock, 4)
        if r: self.recvall(sock, struct.unpack('>I', r)[0])

    def recvall(self, sock, n):
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet: return None
            data.extend(packet)
        return data

    def start(self):
        # Khởi tạo 2 luồng riêng biệt
        t_decision = threading.Thread(target=self.decision_cycle)
        t_adaptive = threading.Thread(target=self.adaptive_cycle)
        
        # Chạy song song
        t_decision.start()
        t_adaptive.start()
        
        # Giữ main thread sống
        t_decision.join()
        t_adaptive.join()

if __name__ == "__main__":
    AIProactiveAgent().start()