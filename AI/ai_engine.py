import joblib
import os
import pandas as pd
import datetime
from config import *

class AIBrain:
    def __init__(self):
        self.model = joblib.load(MODEL_FILE) # take 0.1s to predict
        self.scaler = joblib.load(SCALER_FILE) # take 0.1s to predict
        self.hourly_risk_map = joblib.load(MAP_FILE) # take 0.1s to predict

        if os.path.exists(THRESHOLD_STATE_FILE):
            self.conf_threshold = joblib.load(THRESHOLD_STATE_FILE) # take 0.1s to predict
        else:
            self.conf_threshold = DEFAULT_CONFIDENCE # immediately
    
    def load_state(self, filename, default_val):
        if os.path.exists(filename): return joblib.load(filename)
        return default_val

    def analyze_server(self, metrics_10):
        # Lấy nhãn thời gian
        hour = datetime.datetime.now().hour
        s_score = self.hourly_risk_map.get(hour, 0.0)
        
        # Tạo DataFrame đầu vào
        data_dict = dict(zip(RAW_FEATURES, metrics_10))
        data_dict['sensitivity_score'] = s_score
        input_df = pd.DataFrame([data_dict])
        
        # ĐỊNH NGHĨA X_scaled TẠI ĐÂY
        X_scaled = self.scaler.transform(input_df)
        
        # Dự đoán xác suất
        prob = self.model.predict_proba(X_scaled)[0][1] 

        # Predict for 5s
        
        # Quyết định dựa trên ngưỡng thích nghi
        is_overloaded = 1 if prob > self.conf_threshold else 0
        return is_overloaded, prob

    def adjust_all_thresholds(self, metrics_list, last_action):
        """
        Tự điều chỉnh ngưỡng dựa trên kết quả thực tế (Feedback Loop)
        metrics_list: List chứa 3 bộ metrics của 3 server
        """
        # Tính toán trạng thái thực tế của toàn cụm
        avg_cpu = sum(m[3] for m in metrics_list) / len(metrics_list)
        max_cpu = max(m[3] for m in metrics_list)
        
        # 1. ĐIỀU CHỈNH IDLE_THRESHOLD (Dựa trên hành động CLOSE)
        if last_action == "CLOSE_SERVER":
            if max_cpu > 80: # Sai lầm: Đóng xong bị quá tải ngay
                self.idle_threshold = max(MIN_IDLE_THRESHOLD, self.idle_threshold - IDLE_ADAPTIVE_STEP)
            elif max_cpu < 40: # An toàn: Đóng xong vẫn rất rảnh
                self.idle_threshold = min(MAX_IDLE_THRESHOLD, self.idle_threshold + IDLE_ADAPTIVE_STEP)

        # 2. ĐIỀU CHỈNH CONF_THRESHOLD (Dựa trên hành động OPEN)
        if last_action == "OPEN_SERVER":
            if max_cpu < 60: # Sai lầm: Mở thêm máy khi chưa thực sự cần (quá nhạy)
                self.conf_threshold = min(MAX_CONFIDENCE, self.conf_threshold + ADAPTIVE_STEP)
            elif max_cpu > 90: # Chính xác: Mở máy là đúng lúc (có thể nhạy hơn nữa)
                self.conf_threshold = max(MIN_CONFIDENCE, self.conf_threshold - ADAPTIVE_STEP)

        # Lưu lại trạng thái mới
        joblib.dump(self.conf_threshold, 'conf_state.pkl')
        joblib.dump(self.idle_threshold, 'idle_state.pkl')