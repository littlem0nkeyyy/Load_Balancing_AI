import os

# Danh sách 11 chỉ số gốc từ file CSV của bạn
RAW_FEATURES = [
    'requests_total', 'connections_total', 'jobs_processed', 
    'cpu_usage_percent', 'memory_used_percent', 'connections_current', 
    'queue_length', 'avg_latency', 'avg_processing_time', 'request_rate'
]

# Danh sách đầy đủ bao gồm cả Feature do AI tự tạo (Yêu cầu 2)
FEATURES = RAW_FEATURES + ['sensitivity_score']

# Hỗ trợ environment variables cho Docker, mặc định là thư mục gốc
# Get the root directory (parent of AI directory)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(ROOT_DIR, 'Model')

MODEL_FILE = os.path.join(MODEL_DIR, 'ai_model_v2.pkl')
SCALER_FILE = os.path.join(MODEL_DIR, 'scaler_v2.pkl')
MAP_FILE = os.path.join(MODEL_DIR, 'hourly_map_v2.pkl')
THRESHOLDS_FILE = os.path.join(MODEL_DIR, 'auto_thresholds.pkl')
THRESHOLD_STATE_FILE = os.path.join(MODEL_DIR, 'adaptive_threshold.pkl')
DEFAULT_CONFIDENCE = 0.7
MIN_CONFIDENCE = 0.1
MAX_CONFIDENCE = 0.8
ADAPTIVE_STEP = 0.01
TOTAL_SERVERS = 3
DEFAULT_IDLE_THRESHOLD = 5.0
MIN_IDLE_THRESHOLD = 2.0  
MAX_IDLE_THRESHOLD = 15.0   
IDLE_ADAPTIVE_STEP = 0.5

LBS_HOST = os.getenv('LBS_HOST', '127.0.0.1')
LBS_PORT = int(os.getenv('LBS_PORT', 9999))