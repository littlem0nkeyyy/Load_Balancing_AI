import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from config import FEATURES, MODEL_FILE, SCALER_FILE, SENSITIVITY_MAP

def train_system(csv_file):
    print(f"[*] Khởi động quá trình học tập từ: {csv_file}")
    df = pd.read_csv(csv_file)
    
    # 1. Học quy luật Peak Hour từ Timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    
    hourly_map = {}
    prob_per_hour = df.groupby('hour')['target'].mean()
    for h in range(24):
        p = prob_per_hour.get(h, 0)
        # Tự động gán độ nhạy dựa trên xác suất quá tải lịch sử
        if p > 0.6: hourly_map[h] = 0.2
        elif p > 0.3: hourly_map[h] = 0.3
        else: hourly_map[h] = 0.5
    
    # 2. Huấn luyện Model
    scaler = StandardScaler()
    X = df[FEATURES]
    y = df['target']
    
    X_scaled = scaler.fit_transform(X)
    model = RandomForestClassifier(n_estimators=200, class_weight={0: 1, 1: 5}, random_state=42)
    model.fit(X_scaled, y)
    
    # 3. Lưu trữ
    joblib.dump(model, MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)
    joblib.dump(hourly_map, SENSITIVITY_MAP)
    print("[+] Đã lưu tất cả bộ não AI vào file!")

if __name__ == "__main__":
    train_system('du_lieu_cua_ban.csv')