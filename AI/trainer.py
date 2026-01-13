import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from config import *

def train_system_auto(csv_file):
    print(f"[*] Đang nạp dữ liệu: {csv_file}")
    df = pd.read_csv(csv_file)
    df['memory_used_percent'] = pd.to_numeric(df['memory_used_percent'], errors='coerce').fillna(0) 
    # --- YÊU CẦU 2 & 3: AI TỰ SET NGƯỠNG (AUTO-LABELING) ---
    # AI tự lấy mốc 95% cao nhất của từng chỉ số làm ngưỡng "quá tải"
    thresholds = {
        'cpu': df['cpu_usage_percent'].quantile(0.95),
        'latency': df['avg_latency'].quantile(0.95),
        'queue': df['queue_length'].quantile(0.95)
    }

    # Tạo cột target tự động dựa trên ngưỡng vừa học
    df['target'] = (
        (df['cpu_usage_percent'] > thresholds['cpu']) | 
        (df['avg_latency'] > thresholds['latency']) | 
        (df['queue_length'] > thresholds['queue'])
    ).astype(int)

    # --- HỌC PEAK HOUR & SENSITIVITY ---
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%H:%M:%S')
    df['hour'] = df['timestamp'].dt.hour
    hourly_risk = df.groupby('hour')['target'].mean().to_dict()
    df['sensitivity_score'] = df['hour'].map(hourly_risk)

    # --- TRAIN MODEL ---
    scaler = StandardScaler()
    X = df[FEATURES]
    y = df['target']
    scaler.fit(X)
    X_scaled = scaler.transform(X)
    
    model = RandomForestClassifier(n_estimators=200, class_weight='balanced')
    model.fit(X_scaled, y)

    # Lưu tất cả
    joblib.dump(model, MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)
    joblib.dump(hourly_risk, MAP_FILE)
    joblib.dump(thresholds, THRESHOLDS_FILE)
    print("[+] AI đã tự thiết lập ngưỡng và hoàn tất huấn luyện.")

if __name__ == "__main__":
    train_system_auto('data.csv')