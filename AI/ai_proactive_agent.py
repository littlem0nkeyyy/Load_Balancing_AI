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
        print("[INIT] Khởi tạo AI Agent...")
        self.brain = AIBrain()
        self.last_action = "STAY"
        self.lock = threading.Lock()

        # DANH SÁCH BẢO VỆ (IP hoặc Port)
        # Bất kỳ URL nào chứa chuỗi này sẽ KHÔNG BAO GIỜ bị tắt
        self.protected_identity = [
            "130.94.65.44:8081",
            "8081" # Bảo vệ thêm port cho chắc
        ]

    # --- HÀM 1: KẾT NỐI (UTILITY) ---
    def get_lbs_status_connection(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((LBS_HOST, LBS_PORT))

            cmd = json.dumps({"action": "GET_STATUS"}).encode('utf-8')
            s.sendall(struct.pack('>I', len(cmd)) + cmd)

            raw_len = self.recvall(s, 4)
            if not raw_len: 
                s.close()
                return None, None
            
            msglen = struct.unpack('>I', raw_len)[0]
            data_raw = self.recvall(s, msglen).decode('utf-8')
            return json.loads(data_raw), s
        except Exception as e:
            # print(f"[!] Kết nối LBS thất bại: {e}")
            return None, None

    # --- HÀM 2: LUỒNG DECISION (10s) ---
    def decision_cycle(self):
        print("[*] Luồng Decision (10s) đã sẵn sàng.")
        
        while True:
            payload, s_conn = self.get_lbs_status_connection()
            
            if payload and s_conn:
                servers_data = payload.get('servers', [])
                current_action = "STAY"
                
                # Tìm danh sách server đang TẮT (để dành cứu viện)
                # Giả định LBS trả về 'isOpen', nếu không có mặc định là False
                standby_servers = [s for s in servers_data if not s['health'].get('isOpen', False)]
                triggered_scale_out = False 

                for s_info in servers_data:
                    s_url = s_info['url']
                    h = s_info['health']
                    
                    # 1. LÀM SẠCH DỮ LIỆU (Tránh lỗi string "8.7%")
                    try:
                        raw_cpu = str(h.get('cpuUsagePercent', 0)).replace('%', '').strip()
                        cpu_val = float(raw_cpu)
                        raw_mem = str(h.get('memoryUsagePercent', 0)).replace('%', '').strip()
                        mem_val = float(raw_mem)
                    except:
                        cpu_val = 0.0
                        mem_val = 0.0

                    # Mapping metrics chuẩn cho AI
                    metrics = [0, 0, 0, cpu_val, mem_val, h.get('currConnections', 0), 0, 0, h.get('avgProcessingTimeSec', 0), 0]

                    # 2. PHÂN TÍCH (EMERGENCY + AI)
                    is_overload = False
                    prob = 0.0
                    current_idle_threshold = 20.0

                    # [LUẬT CỨNG] Nếu CPU > 95% -> Báo động đỏ ngay lập tức
                    if cpu_val >= 95.0:
                        is_overload = True
                        prob = 1.0
                        print(f"[🔥 EMERGENCY] {s_url} CPU {cpu_val}% -> Kích hoạt cứu viện!")
                    else:
                        # [LUẬT MỀM] Hỏi ý kiến AI
                        with self.lock: 
                            is_overload, prob = self.brain.analyze_server(metrics)
                            current_idle_threshold = self.brain.idle_threshold

                    # 3. RA QUYẾT ĐỊNH
                    cmd_action = None
                    target_url = s_url # Mặc định tác động lên chính nó

                    if is_overload:
                        # LOGIC SCALE OUT: Server A quá tải -> Mở Server B (đang tắt)
                        if not triggered_scale_out and len(standby_servers) > 0:
                            savior = standby_servers.pop(0) # Lấy 1 server rảnh
                            cmd_action = "OPEN_SERVER"
                            target_url = savior['url']
                            triggered_scale_out = True # Đánh dấu đã gọi cứu viện trong cycle này
                            print(f"[🚑 SCALE UP] {s_url} quá tải ({prob:.1%}) -> Gọi {target_url} dậy!")
                        elif len(standby_servers) == 0 and not triggered_scale_out:
                            # print(f"[⚠️] {s_url} quá tải nhưng hết server dự phòng!")
                            pass

                    elif cpu_val < current_idle_threshold:
                        # LOGIC SCALE DOWN: Server rảnh -> Tắt bớt (trừ server bảo vệ)
                        is_open = h.get('isOpen', True)
                        if is_open:
                            # Kiểm tra "Thẻ bài miễn tử"
                            is_protected = any(pid in s_url for pid in self.protected_identity)
                            if not is_protected:
                                cmd_action = "CLOSE_SERVER"
                                # print(f"[📉 SCALE DOWN] {s_url} rảnh ({cpu_val}%) -> Tắt.")

                    # 4. THỰC THI
                    if cmd_action:
                        current_action = cmd_action
                        self.send_command(s_conn, cmd_action, target_url)
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] CMD: {cmd_action} -> {target_url} (Prob: {prob:.2f})")

                self.last_action = current_action
                s_conn.close()

            time.sleep(10)

    # --- HÀM 3: LUỒNG ADAPTIVE (5 Phút) ---
    def adaptive_cycle(self):
        print("[*] Luồng Adaptive (5m) đã sẵn sàng.")
        while True:
            time.sleep(300) # 5 Phút
            print(f"\n[AI-LEARNING] Bắt đầu chu kỳ tự học lúc {datetime.datetime.now().strftime('%H:%M:%S')}...")
            
            payload, s_conn = self.get_lbs_status_connection()
            if payload:
                servers_data = payload.get('servers', [])
                all_metrics_now = []
                
                for s in servers_data:
                    h = s['health']
                    # Clean data trước khi học
                    try:
                        c = float(str(h.get('cpuUsagePercent',0)).replace('%',''))
                    except: c = 0.0
                    
                    m = [0, 0, 0, c, 0, h.get('currConnections',0), 0, 0, 0, 0]
                    all_metrics_now.append(m)

                with self.lock:
                    self.brain.adjust_all_thresholds(all_metrics_now, self.last_action)
                    print(f"[AI-LEARNING] Xong. Conf={self.brain.conf_threshold:.3f}, Idle={self.brain.idle_threshold:.1f}%")
            
            if s_conn: s_conn.close()
            print("[AI-LEARNING] Kết thúc.\n")

    # --- UTILS ---
    def send_command(self, sock, action, url):
        cmd = json.dumps({"action": action, "serverUrl": url}).encode('utf-8')
        sock.sendall(struct.pack('>I', len(cmd)) + cmd)
        r = self.recvall(sock, 4) # Đọc confirm
        if r: self.recvall(sock, struct.unpack('>I', r)[0])

    def recvall(self, sock, n):
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet: return None
            data.extend(packet)
        return data

    def start(self):
        t1 = threading.Thread(target=self.decision_cycle)
        t2 = threading.Thread(target=self.adaptive_cycle)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

if __name__ == "__main__":
    AIProactiveAgent().start()