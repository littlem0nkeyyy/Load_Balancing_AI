# Danh sách 11 chỉ số gốc từ file CSV của bạn
RAW_FEATURES = [
    'requests_total', 'connections_total', 'jobs_processed', 
    'cpu_usage_percent', 'memory_used_percent', 'connections_current', 
    'queue_length', 'avg_latency', 'avg_processing_time', 'request_rate'
]

# Danh sách đầy đủ bao gồm cả Feature do AI tự tạo (Yêu cầu 2)
FEATURES = RAW_FEATURES + ['sensitivity_score']

# Hỗ trợ environment variables cho Docker, mặc định là thư mục gốc
MODEL_FILE = 'ai_model_v2.pkl'
SCALER_FILE = 'scaler_v2.pkl'
MAP_FILE = 'hourly_map_v2.pkl'
THRESHOLDS_FILE = 'auto_thresholds.pkl'
THRESHOLD_STATE_FILE = 'adaptive_threshold.pkl'
DEFAULT_CONFIDENCE = 0.4
MIN_CONFIDENCE = 0.1
MAX_CONFIDENCE = 0.8
ADAPTIVE_STEP = 0.01
TOTAL_SERVERS = 3
DEFAULT_IDLE_THRESHOLD = 20.0
MIN_IDLE_THRESHOLD = 10.0  
MAX_IDLE_THRESHOLD = 35.0   
IDLE_ADAPTIVE_STEP = 0.5

LBS_HOST = '127.0.0.1' 
LBS_PORT = 9999