# Hướng Dẫn Sử Dụng Load Balancing AI

## 📋 Mô Tả Dự Án

**Load Balancing AI** là hệ thống AI tự động điều khiển cân bằng tải server thông qua Machine Learning. Hệ thống sử dụng mô hình Random Forest để dự đoán tình trạng quá tải của server và tự động ra quyết định mở/đóng server dựa trên các chỉ số hiệu năng thời gian thực.

### Tính Năng Chính

- 🤖 **Dự đoán quá tải thông minh**: Sử dụng AI để phân tích và dự đoán tình trạng quá tải server
- 🔄 **Tự động điều chỉnh ngưỡng**: Hệ thống tự học và điều chỉnh ngưỡng cảnh báo dựa trên phản hồi thực tế
- ⚡ **Phản ứng nhanh**: Chu kỳ ra quyết định mỗi 10 giây
- 📊 **Phân tích theo giờ**: Tính toán độ nhạy cảm theo từng giờ trong ngày
- 🔒 **Thread-safe**: Sử dụng lock để đảm bảo an toàn khi nhiều luồng truy cập AI Brain

## 🏗️ Kiến Trúc Hệ Thống

### Các Thành Phần Chính

1. **AI Engine (`ai_engine.py`)**: 
   - Nạp và quản lý mô hình ML đã được huấn luyện
   - Phân tích metrics của server và đưa ra dự đoán
   - Tự điều chỉnh ngưỡng dựa trên feedback

2. **TCP Advisor (`ai_tcp_advisor.py`)**:
   - Kết nối với Load Balancer Server qua TCP socket
   - Luồng Decision: Ra quyết định mở/đóng server mỗi 10 giây
   - Luồng Adaptive: Tự học và điều chỉnh ngưỡng mỗi 5 phút

3. **Trainer (`trainer.py`)**:
   - Huấn luyện mô hình từ dữ liệu CSV
   - Tự động thiết lập ngưỡng dựa trên phân tích dữ liệu
   - Tạo bản đồ độ nhạy cảm theo giờ

4. **Config (`config.py`)**:
   - Cấu hình các tham số hệ thống
   - Định nghĩa features và thresholds

### Luồng Hoạt Động

```
┌─────────────────┐
│  Load Balancer  │
│     Server      │
└────────┬────────┘
         │ TCP Socket (Port 9999)
         │ GET_STATUS / OPEN_SERVER / CLOSE_SERVER
         ▼
┌─────────────────┐
│  AI TCP Advisor │
│  (2 Threads)    │
├─────────────────┤
│ Decision Cycle  │ ← Chạy mỗi 10s: Ra quyết định
│ Adaptive Cycle  │ ← Chạy mỗi 5min: Tự học
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Engine     │
│  (AI Brain)     │
├─────────────────┤
│ - Load Model    │
│ - Predict       │
│ - Adjust        │
└─────────────────┘
```

## 📦 Yêu Cầu Hệ Thống

### Phần Mềm Cần Thiết

- Python 3.7 trở lên
- Các thư viện Python:
  - `pandas`
  - `scikit-learn`
  - `joblib`

### Cài Đặt Dependencies

```bash
pip install pandas scikit-learn joblib
```

Hoặc tạo file `requirements.txt`:

```txt
pandas>=1.3.0
scikit-learn>=1.0.0
joblib>=1.0.0
```

Sau đó chạy:

```bash
pip install -r requirements.txt
```

## 🚀 Hướng Dẫn Sử Dụng

### Bước 1: Chuẩn Bị Dữ Liệu

Đảm bảo bạn có file `data.csv` chứa dữ liệu huấn luyện với các cột:
- `requests_total`: Tổng số request
- `connections_total`: Tổng số kết nối
- `jobs_processed`: Số job đã xử lý
- `cpu_usage_percent`: Phần trăm sử dụng CPU
- `memory_used_percent`: Phần trăm sử dụng RAM
- `connections_current`: Số kết nối hiện tại
- `queue_length`: Độ dài hàng đợi
- `avg_latency`: Độ trễ trung bình
- `avg_processing_time`: Thời gian xử lý trung bình
- `request_rate`: Tỷ lệ request
- `timestamp`: Thời gian (định dạng HH:MM:SS)

### Bước 2: Huấn Luyện Mô Hình

Chạy script huấn luyện để tạo các file model:

```bash
cd AI
python trainer.py
```

Script sẽ:
- Đọc dữ liệu từ `data.csv` (ở thư mục gốc)
- Tự động thiết lập ngưỡng quá tải (95th percentile)
- Tạo bản đồ độ nhạy cảm theo giờ
- Huấn luyện mô hình Random Forest
- Lưu các file:
  - `ai_model_v2.pkl`: Mô hình đã huấn luyện
  - `scaler_v2.pkl`: Scaler để chuẩn hóa dữ liệu
  - `hourly_map_v2.pkl`: Bản đồ độ nhạy cảm theo giờ
  - `auto_thresholds.pkl`: Ngưỡng tự động

**Lưu ý**: Các file model sẽ được lưu ở thư mục gốc của project.

### Bước 3: Cấu Hình Kết Nối

Chỉnh sửa file `AI/config.py` để cấu hình kết nối với Load Balancer Server:

```python
LBS_HOST = '127.0.0.1'  # Địa chỉ IP của Load Balancer Server
LBS_PORT = 9999          # Port của Load Balancer Server
```

### Bước 4: Chạy Hệ Thống AI

Đảm bảo Load Balancer Server đã chạy và lắng nghe trên port đã cấu hình, sau đó:

```bash
cd AI
python ai_tcp_advisor.py
```

Hệ thống sẽ:
- Kết nối với Load Balancer Server
- Bắt đầu luồng Decision (ra quyết định mỗi 10 giây)
- Bắt đầu luồng Adaptive (tự học mỗi 5 phút)
- Hiển thị log các hành động và quyết định

## ⚙️ Cấu Hình Chi Tiết

### Các Tham Số Trong `config.py`

#### Ngưỡng Confidence (Xác Suất Quá Tải)
- `DEFAULT_CONFIDENCE = 0.4`: Ngưỡng mặc định
- `MIN_CONFIDENCE = 0.1`: Ngưỡng tối thiểu
- `MAX_CONFIDENCE = 0.8`: Ngưỡng tối đa
- `ADAPTIVE_STEP = 0.01`: Bước điều chỉnh

#### Ngưỡng Idle (Server Rảnh)
- `DEFAULT_IDLE_THRESHOLD = 20.0`: Ngưỡng mặc định (%)
- `MIN_IDLE_THRESHOLD = 10.0`: Ngưỡng tối thiểu
- `MAX_IDLE_THRESHOLD = 35.0`: Ngưỡng tối đa
- `IDLE_ADAPTIVE_STEP = 0.5`: Bước điều chỉnh

#### Kết Nối
- `LBS_HOST`: Địa chỉ Load Balancer Server
- `LBS_PORT`: Port của Load Balancer Server
- `TOTAL_SERVERS = 3`: Số lượng server trong hệ thống

## 🔍 Cách Hệ Thống Hoạt Động

### Luồng Decision (10 giây/lần)

1. Kết nối với Load Balancer Server qua TCP
2. Gửi lệnh `GET_STATUS` để lấy thông tin các server
3. Với mỗi server:
   - Thu thập metrics (CPU, RAM, connections, processing time)
   - Gửi metrics vào AI Engine để phân tích
   - Nhận xác suất quá tải và ngưỡng hiện tại
   - Ra quyết định:
     - Nếu `prob > conf_threshold` → Gửi lệnh `OPEN_SERVER`
     - Nếu `CPU < idle_threshold` → Gửi lệnh `CLOSE_SERVER`
     - Ngược lại → `STAY` (không làm gì)
4. Đợi 10 giây và lặp lại

### Luồng Adaptive (5 phút/lần)

1. Đợi 5 phút
2. Thu thập metrics hiện tại của tất cả server
3. Phân tích kết quả của hành động trước đó:
   - Nếu đã `CLOSE_SERVER`:
     - CPU > 80% → Giảm `idle_threshold` (đóng quá sớm)
     - CPU < 40% → Tăng `idle_threshold` (có thể đóng sớm hơn)
   - Nếu đã `OPEN_SERVER`:
     - CPU < 60% → Tăng `conf_threshold` (mở quá sớm)
     - CPU > 90% → Giảm `conf_threshold` (cần nhạy hơn)
4. Lưu ngưỡng mới vào file
5. Lặp lại sau 5 phút

### AI Engine - Phân Tích Server

1. Nhận metrics từ server (10 giá trị)
2. Lấy giờ hiện tại và tra cứu `sensitivity_score` từ hourly map
3. Chuẩn hóa dữ liệu bằng scaler
4. Dự đoán xác suất quá tải bằng Random Forest
5. So sánh với `conf_threshold` để quyết định

## 📊 Định Dạng Dữ Liệu

### Input từ Load Balancer Server

Hệ thống mong đợi JSON response từ Load Balancer Server:

```json
{
  "servers": [
    {
      "url": "http://server1:8080",
      "health": {
        "cpuUsagePercent": 75.5,
        "memoryUsagePercent": 60.2,
        "currConnections": 150,
        "avgProcessingTimeSec": 0.5
      }
    }
  ]
}
```

### Metrics được sử dụng

Hệ thống mapping dữ liệu từ LBS sang format AI học:
- `metrics[3]` = `cpuUsagePercent`
- `metrics[4]` = `memoryUsagePercent`
- `metrics[5]` = `currConnections`
- `metrics[8]` = `avgProcessingTimeSec`

## 🐛 Xử Lý Lỗi

### Lỗi Kết Nối

Nếu không kết nối được với Load Balancer Server:
- Kiểm tra `LBS_HOST` và `LBS_PORT` trong `config.py`
- Đảm bảo Load Balancer Server đang chạy
- Kiểm tra firewall và network

### Lỗi Thiếu File Model

Nếu thiếu các file `.pkl`:
- Chạy lại `trainer.py` để tạo model
- Đảm bảo file `data.csv` tồn tại và có dữ liệu hợp lệ

### Lỗi Thread Safety

Hệ thống sử dụng `threading.Lock()` để đảm bảo:
- Luồng Decision và Adaptive không xung đột khi truy cập AI Brain
- Ngưỡng được cập nhật an toàn

## 📝 Log và Monitoring

Hệ thống hiển thị các log:
- `[*] Luồng Decision (10s) đã khởi động...`
- `[*] Luồng Adaptive (5min) đã khởi động...`
- `[HH:MM:SS] Decision: OPEN_SERVER -> http://server1:8080`
- `[HH:MM:SS] --- BẮT ĐẦU TỰ HỌC ---`
- `[*] Đã học xong. Ngưỡng mới: CONF=0.450, IDLE=22.5%`

## 🔄 Tự Động Hóa

### Chạy như Service (Linux)

Tạo file `/etc/systemd/system/load-balancing-ai.service`:

```ini
[Unit]
Description=Load Balancing AI Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/Load_Balancing_AI/AI
ExecStart=/usr/bin/python3 ai_tcp_advisor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Khởi động service:
```bash
sudo systemctl enable load-balancing-ai
sudo systemctl start load-balancing-ai
```

## 📚 Tài Liệu Tham Khảo

- **Mô hình**: Random Forest Classifier với 200 estimators
- **Features**: 11 features gốc + 1 feature sensitivity_score
- **Auto-labeling**: Sử dụng 95th percentile làm ngưỡng quá tải
- **Adaptive Learning**: Điều chỉnh ngưỡng dựa trên feedback mỗi 5 phút

## 🤝 Đóng Góp

Để cải thiện hệ thống:
1. Thu thập thêm dữ liệu training
2. Điều chỉnh các tham số trong `config.py`
3. Tối ưu hóa mô hình ML
4. Thêm các metrics khác vào phân tích

## 📄 License

Dự án này được phát triển cho mục đích học tập và nghiên cứu.
