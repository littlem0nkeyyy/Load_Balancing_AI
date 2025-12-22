import time
import os
from ai_engine import AIBrain
from config import TOTAL_SERVERS

class LoadBalancerManager:
    def __init__(self):
        self.brain = AIBrain()
        self.active_servers = 1

    def run(self):
        print("[System Running] AI Load Balancer đã sẵn sàng...")
        try:
            while True:
                # 1. Thu thập 11 thông số (Giả lập)
                # Trong thực tế, bạn viết hàm lấy stats ở đây
                current_stats = [5500, 0, 220, 5000, 78.0, 65.0, 160, 12, 380, 1024, 280]
                
                # 2. Hỏi ý kiến AI
                action = self.brain.get_decision(current_stats)
                
                # 3. Thực thi
                self.execute(action)
                
                time.sleep(10)
        except KeyboardInterrupt:
            print("[!] Dừng hệ thống.")

    def execute(self, action):
        if action == "SCALE_UP" and self.active_servers < TOTAL_SERVERS:
            self.active_servers += 1
            print(f"==> THỰC THI: Bật server thứ {self.active_servers}")
            # os.system("...") 
        elif action == "SCALE_DOWN" and self.active_servers > 1:
            print(f"==> THỰC THI: Tắt server thứ {self.active_servers}")
            self.active_servers -= 1
            # os.system("...")

if __name__ == "__main__":
    lb_manager = LoadBalancerManager()
    lb_manager.run()