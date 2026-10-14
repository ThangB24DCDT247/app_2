# 🚀 PTIT MQTT Controller — KIT-001

> **Ứng dụng điều khiển và kiểm thử lệnh trực tiếp qua MQTT cho KIT-001**  
> Tuân thủ đặc tả kỹ thuật trong `doc2.md` và giao thức phòng Lab PTIT.

---

## 1. Mục tiêu ứng dụng

- Phát triển công cụ gửi lệnh MQTT điều khiển thiết bị `KIT-001` dành cho kỹ sư / sinh viên kiểm thử.
- Giao diện đồ họa chuẩn nhận diện thương hiệu **PTIT (Trắng - Đỏ)**, hiển thị logo PTIT sắc nét.
- Mỗi thao tác điều khiển có nút bấm riêng, kiểm tra kết nối và tính hợp lệ trước khi publish.
- Hiển thị trực tiếp lịch sử publish: Thời gian, Topic, JSON Payload, Kết quả tầng MQTT.

---

## 2. Cấu trúc thư mục

```text
controller/
├── config.py           # Cấu hình tập trung (Broker, Port, Topics, DRAFT fields)
├── command_topics.py   # Xây dựng và kiểm tra tính hợp lệ Topic & Payload JSON
├── mqtt_controller.py  # Xử lý kết nối MQTT bất đồng bộ (Paho MQTT v2 API)
├── gui.py              # Giao diện đồ họa Tkinter (Trắng - Đỏ, Logo PTIT)
├── main.py             # Khởi chạy ứng dụng
├── requirements.txt    # Danh sách thư viện phụ thuộc
├── ptit_logo.png       # Logo PTIT
└── README.md           # Hướng dẫn chi tiết
```

---

## 3. Các nhóm lệnh điều khiển

Mọi lệnh gửi lên MQTT đều là **JSON hợp lệ**, tiền tố topic: `lab/kit/KIT-001/`

| Nhóm | Topic | Nút bấm | JSON Payload | Ghi chú |
|---|---|---|---|---|
| **A: Vòng đời (Reset)** | `cmd/reset` | **START** | `{"action":"start"}` | Bắt đầu lượt |
| | | **STOP** | `{"action":"stop"}` | Kết thúc lượt (Có hộp thoại xác nhận) |
| | | **CALIB** | `{"action":"calib"}` | Yêu cầu hiệu chuẩn |
| **B: Nguồn AC** | `cmd/power` | **BẬT NGUỒN AC** | `{"action":"on"}` | Nút màu xanh lam |
| | | **TẮT NGUỒN AC** | `{"action":"off"}` | Nút màu đỏ |
| **C: Mức điện áp** | `cmd/voltage` | **0, 3, 6, 9, 12 V** | `{"voltage": X}` | Chỉ cho phép 5 mức trên. Tên trường `voltage` là [DRAFT] |
| **D: Thang đo** | `cmd/scale` | **Scale 1.999, 19.99, 199.9** | `{"scale":"X"}` | [DRAFT] Giá trị là chuỗi giữ nguyên dấu chấm |
| **E: Vị trí thước** | `cmd/ruler` | **GỬI VỊ TRÍ** | `{"position": Y}` | [DRAFT] Số nguyên tuyệt đối từ 0 tới 300 mm |
| **F: Shutdown toàn bộ** | `cmd/shutdown` | **SHUTDOWN TOÀN BỘ KIT** | `{"action":"shutdown"}` | [DRAFT Admin] Mặc định bị vô hiệu hóa; cần bật quyền Admin và xác nhận |

> ⛔ **Tuyệt đối không có K-lock** và không có topic `cmd/magnetic_field`.

---

## 4. Cách chạy ứng dụng

### Cách 1: Chạy 1-Click bằng file Batch (Khuyên dùng)
Double-click vào file **`app2.bat`** (hoặc `run_controller.bat`) trong thư mục `apppy1`.

### Cách 2: Chạy qua Command Line (uv / python)
```cmd
cd C:\Users\THANG\Desktop\apppy1\controller
uv run --with paho-mqtt --with Pillow main.py
```
Hoặc:
```cmd
pip install -r requirements.txt
python main.py
```

---

## 5. Hướng dẫn kiểm thử bằng Mosquitto Sub

Mở một cửa sổ Command Prompt mới để lắng nghe mọi lệnh được publish lên broker:

```cmd
"C:\Program Files\mosquitto\mosquitto_sub.exe" -h mqtt.mysignage.vn -p 1883 -t "lab/kit/KIT-001/cmd/#" -v
```

Khi bấm các nút trên ứng dụng **PTIT MQTT Controller**, cửa sổ command prompt sẽ hiển thị chính xác topic và payload JSON tương ứng:
- Bấm **START**: `lab/kit/KIT-001/cmd/reset {"action": "start"}`
- Bấm **BẬT NGUỒN AC**: `lab/kit/KIT-001/cmd/power {"action": "on"}`
- Bấm **6 V**: `lab/kit/KIT-001/cmd/voltage {"voltage": 6}`
- Bấm **Scale 19.99**: `lab/kit/KIT-001/cmd/scale {"scale": "19.99"}`
- Kéo thước 150 mm và bấm **GỬI VỊ TRÍ**: `lab/kit/KIT-001/cmd/ruler {"position": 150}`

---

## 6. Lưu ý an toàn & kiến trúc

1. **Tầng MQTT:** Kết quả "✔ Đã publish thành công" thể hiện broker đã nhận gói tin MQTT. Ứng dụng không tự ý thông báo "phần cứng kit đã thực thi" vì giao thức hiện hành chưa có cơ chế ACK thực thi cho từng lệnh.
2. **Không tự động retry:** Khi mất kết nối và phục hồi, ứng dụng không phát lại bất kỳ lệnh điều khiển nguy hiểm nào trong quá khứ.
3. **Shutdown vs Power Off:** Lệnh tắt nguồn AC (`cmd/power`) chỉ tắt nguồn xoay chiều, không phải tắt toàn bộ bo mạch kit. Lệnh Shutdown toàn bộ kit chỉ dành riêng cho Admin trong hệ thống thực tế.

