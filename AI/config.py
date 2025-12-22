# Danh sách 11 chỉ số đầu vào
FEATURES = [
    'total_requests', 'total_errors', 'total_connections', 'jobs_processed',
    'cpu_usage', 'ram_usage', 'current_connections', 'queue_length',
    'request_latency', 'response_size', 'processing_time'
]

# File lưu trữ
MODEL_FILE = 'final_lb_model.pkl'
SCALER_FILE = 'final_scaler.pkl'
SENSITIVITY_MAP = 'sensitivity_map.pkl'

# Cấu hình hạ tầng
TOTAL_SERVERS = 5