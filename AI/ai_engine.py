import joblib
import datetime
from collections import deque
from config import MODEL_FILE, SCALER_FILE, SENSITIVITY_MAP

class AIBrain:
    def __init__(self):
        self.model = joblib.load(MODEL_FILE)
        self.scaler = joblib.load(SCALER_FILE)
        self.sensitivity_map = joblib.load(SENSITIVITY_MAP)
        self.history = deque(maxlen=5)

    def get_decision(self, metrics):
        current_hour = datetime.datetime.now().hour
        threshold = self.sensitivity_map.get(current_hour, 0.4)
        
        # Dự đoán
        metrics_scaled = self.scaler.transform([metrics])
        prob = self.model.predict_proba(metrics_scaled)[0][1]
        
        vote = 1 if prob > threshold else 0
        self.history.append(vote)
        
        print(f"[{current_hour}h] AI Prob: {prob:.2f} | Ngưỡng: {threshold}")
        
        if sum(self.history) >= 3: return "SCALE_UP"
        if sum(self.history) == 0: return "SCALE_DOWN"
        return "STAY"