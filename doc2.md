# PROMPT VIBE CODING — APP 2: PTIT MQTT CONTROLLER

## 1. Mục tiêu

Xây dựng ứng dụng desktop Python có tên **PTIT MQTT Controller** để gửi các lệnh MQTT điều khiển kit `KIT-001`.

Ứng dụng này phục vụ demo và kiểm thử giao thức MQTT. Đây là công cụ điều khiển trực tiếp broker dành cho phát triển, không phải Web UI chính thức của hệ thống. Theo kiến trúc sản phẩm, lệnh điều khiển của sinh viên phải đi qua API server có xác thực, kiểm tra quyền sở hữu và validation trước khi được publish lên MQTT.

Yêu cầu:
- Giao diện trực quan, hiện đại, phù hợp demo trên Windows 10/11.
- Mỗi action điều khiển có nút riêng.
- Bấm nút sẽ publish ngay topic và payload tương ứng.
- Hiển thị trạng thái kết nối, topic, payload và kết quả publish.
- Không có chức năng đăng nhập.
- Không có database, biểu đồ, lưu lịch sử lâu dài hoặc giao diện giám sát telemetry.
- Không triển khai những chức năng không có trong phạm vi bên dưới.

## 2. Công nghệ và cấu trúc

Sử dụng:
- Python.
- Tkinter hoặc CustomTkinter.
- Paho MQTT.
- JSON để tạo payload theo giao thức.
- `threading` hoặc cơ chế bất đồng bộ phù hợp để GUI không bị treo.

Cấu trúc đề xuất:

```text
ptit_mqtt_controller/
├── main.py
├── config.py
├── mqtt_controller.py
├── command_topics.py
├── gui.py
├── requirements.txt
└── README.md
```

Trách nhiệm:
- `main.py`: khởi chạy ứng dụng.
- `config.py`: cấu hình broker, client ID và kit code.
- `mqtt_controller.py`: kết nối, reconnect, publish, xử lý callback.
- `command_topics.py`: định nghĩa topic, payload và validation.
- `gui.py`: giao diện và sự kiện bấm nút.
- `requirements.txt`: dependencies.
- `README.md`: hướng dẫn cài đặt, chạy và kiểm thử.

Có thể điều chỉnh cấu trúc nếu cần, nhưng phải tách giao diện khỏi xử lý MQTT.

## 3. Cấu hình MQTT

Giá trị mặc định cho môi trường demo hiện tại:

- Broker: `mqtt.mysignage.vn`
- Port: `1883`
- Transport: MQTT qua TCP, không TLS, chỉ dùng theo cấu hình demo hiện tại.
- Kit code: `KIT-001`
- Client ID: `KIT-001-python-controller`
- Username/password: không cần giao diện nhập thông tin xác thực; thử kết nối không có credentials và hiển thị lỗi nếu broker từ chối.

Không sử dụng Client ID trùng với Raspberry Pi agent hoặc PTIT MQTT Monitor.

Đưa cấu hình vào `config.py`, không hardcode broker/topic rải rác trong GUI. Cho phép chỉnh broker, port và client ID trong file cấu hình.

Không tuyên bố cấu hình TCP không TLS là cấu hình production an toàn. Nếu môi trường triển khai yêu cầu TLS hoặc ACL, phải thay đổi theo cấu hình broker thực tế.

## 4. Quy tắc chung về giao thức

Prefix topic:

`lab/kit/KIT-001/`

Mỗi lệnh publish tới đúng topic được định nghĩa bên dưới.

**Các command payload được chốt phải là JSON**, không gửi chuỗi đơn như `on`, `off`, `6` hoặc `19.99` khi giao thức yêu cầu JSON.

Không tự thêm:
- `sequence number`
- `command_id`
- `attempt_id`
- `kit_code` vào payload nếu chưa có yêu cầu giao thức
- Trường dữ liệu hoặc topic điều khiển mới

Không tạo bất kỳ topic hay nút điều khiển nào cho K-lock. K-lock đã bị loại bỏ khỏi giao thức hiện hành.

## 5. Nhóm điều khiển A — Reset / vòng đời lượt

Topic đã chốt:

`lab/kit/KIT-001/cmd/reset`

Tạo ba nút riêng:

| Nút trên GUI | Payload JSON |
|---|---|
| START | `{"action":"start"}` |
| STOP | `{"action":"stop"}` |
| CALIB | `{"action":"calib"}` |

Ý nghĩa:
- `start`: bắt đầu lượt thực hành.
- `stop`: kết thúc lượt thực hành.
- `calib`: yêu cầu hiệu chuẩn trong lượt hiện tại.

Yêu cầu:
- Mỗi nút publish JSON đúng như bảng.
- Không gửi payload rỗng `{}`.
- Không thay `calib` bằng hành động tự đặt từ trường về 0, di chuyển thước hoặc reset mọi thông số.
- Không tự khẳng định ý nghĩa vật lý của các action ngoài nội dung đã xác định.
- Hiển thị cảnh báo xác nhận trước khi gửi STOP nếu phù hợp với trải nghiệm sử dụng.

Đây là công cụ kiểm thử trực tiếp, không tự thực thi các kiểm tra ownership/deadline của API server.

## 6. Nhóm điều khiển B — Power

Topic đã chốt:

`lab/kit/KIT-001/cmd/power`

Tạo hai nút:

| Nút trên GUI | Payload JSON |
|---|---|
| BẬT NGUỒN AC | `{"action":"on"}` |
| TẮT NGUỒN AC | `{"action":"off"}` |

Yêu cầu:
- Nút ON màu xanh lam.
- Nút OFF màu đỏ.
- Hiển thị xác nhận trước khi publish nếu cần.
- Không nhầm OFF nguồn AC với lệnh shutdown toàn bộ kit.
- Không coi việc publish thành công là bằng chứng nguồn AC thực tế đã bật hoặc tắt.

## 7. Nhóm điều khiển C — Voltage

Topic đã chốt:

`lab/kit/KIT-001/cmd/voltage`

Miền giá trị hợp lệ đã chốt: `0`, `3`, `6`, `9`, `12` V.

Tạo năm nút:
- 0 V
- 3 V
- 6 V
- 9 V
- 12 V

Payload mẫu theo draft kỹ thuật:

| Nút | Payload JSON mẫu |
|---|---|
| 0 V | `{"voltage":0}` |
| 3 V | `{"voltage":3}` |
| 6 V | `{"voltage":6}` |
| 9 V | `{"voltage":9}` |
| 12 V | `{"voltage":12}` |

**Lưu ý giao thức:** topic và miền giá trị đã chốt, nhưng tên trường JSON `voltage` vẫn là draft kỹ thuật cần thống nhất với API/firmware. Đặt payload field trong một vị trí cấu hình riêng, ghi chú rõ trạng thái draft và không tự tuyên bố đây là contract đã phê duyệt.

Từ chối giá trị ngoài danh sách. Không gửi các giá trị như 5 V hoặc 15 V.

Không nhầm mức điện áp được yêu cầu với điện áp đo thực tế từ telemetry.

## 8. Nhóm điều khiển D — Scale

Topic draft:

`lab/kit/KIT-001/cmd/scale`

Các giá trị thang đo dự kiến:
- `1.999`
- `19.99`
- `199.9`

Tạo ba nút:
- Scale 1.999
- Scale 19.99
- Scale 199.9

Payload mẫu theo draft kỹ thuật:

| Nút | Payload JSON mẫu |
|---|---|
| 1.999 | `{"scale":"1.999"}` |
| 19.99 | `{"scale":"19.99"}` |
| 199.9 | `{"scale":"199.9"}` |

Quy tắc:
- Giữ giá trị scale dưới dạng chuỗi trong JSON, không chuyển thành float.
- Giữ nguyên dấu chấm thập phân.
- Không tạo topic K-lock hoặc thêm lựa chọn không có trong danh sách.
- Đánh dấu topic và payload của nhóm này là draft, cần đồng bộ với phía kit trước khi dùng trên thiết bị thật.

## 9. Nhóm điều khiển E — Ruler position

Topic draft:

`lab/kit/KIT-001/cmd/ruler`

Giao diện:
- Slider từ 0 đến 300 mm.
- Ô hiển thị giá trị vị trí.
- Nút GỬI VỊ TRÍ.

Payload mẫu theo draft kỹ thuật:

`{"position":120}`

Quy tắc:
- Vị trí là số nguyên tuyệt đối từ 0 đến 300 mm.
- Mỗi bước 1 mm.
- Không dùng delta như `+1`, `-1` hoặc `move_left`.
- Không gửi giá trị âm, lớn hơn 300 hoặc số thập phân.
- Chỉ publish khi người dùng bấm GỬI VỊ TRÍ; không publish liên tục theo từng sự kiện kéo slider.
- Không tự cập nhật giá trị đo thực tế của kit sau khi publish.

Topic `cmd/ruler` và trường payload `position` là draft kỹ thuật, cần thống nhất trước khi coi là contract chính thức.

## 10. Nhóm điều khiển F — Shutdown toàn bộ kit

Topic draft được đề xuất:

`lab/kit/KIT-001/cmd/shutdown`

Nghiệp vụ shutdown toàn bộ kit theo yêu cầu admin đã được xác định, nhưng tên topic và payload cụ thể vẫn cần thống nhất theo giao thức.

Yêu cầu GUI:
- Tạo nút riêng **SHUTDOWN TOÀN BỘ KIT**.
- Nút có màu cảnh báo.
- Khi bấm, hiển thị hộp thoại xác nhận rõ đây là thao tác tắt toàn bộ kit.
- Chỉ gửi sau khi người dùng xác nhận.
- Không dùng topic `cmd/power` thay thế.
- Không dùng topic `cmd/reset` thay thế.
- Không tự gửi thêm lệnh stop, reset hoặc power off nếu chưa có quy trình phối hợp đã được thống nhất.

Vì payload chưa được chốt, hãy:
1. Tạo một cấu hình riêng cho topic shutdown.
2. Không tự phát minh payload rồi coi đó là giao thức chính thức.
3. Mặc định vô hiệu hóa nút shutdown nếu chưa cấu hình payload đã được phía kit xác nhận.
4. Hiển thị ghi chú rằng shutdown chỉ dành cho admin trong hệ thống chính thức.

Không kiểm thử shutdown trên kit thật khi chưa xác nhận giao thức và quyền thực hiện.

## 11. Giao diện

Sắp xếp giao diện theo các khu vực:

### Khu vực 1 — Connection

Hiển thị:
- Broker host.
- Port.
- Client ID.
- Trạng thái `Connecting`, `Connected`, `Disconnected`, `Error`.
- Nút Connect/Disconnect nếu cần.

Cho phép tự kết nối lúc khởi động hoặc bấm Connect. Không làm treo GUI khi broker không phản hồi.

### Khu vực 2 — Reset / Session

Ba nút START, STOP, CALIB.

### Khu vực 3 — Power

Hai nút BẬT NGUỒN AC, TẮT NGUỒN AC.

### Khu vực 4 — Voltage

Năm nút 0 V, 3 V, 6 V, 9 V, 12 V.

### Khu vực 5 — Scale

Ba nút 1.999, 19.99, 199.9.

### Khu vực 6 — Ruler

Slider 0–300, ô giá trị và nút GỬI VỊ TRÍ.

### Khu vực 7 — Admin / Shutdown

Nút shutdown riêng, mặc định disabled khi chưa cấu hình payload đã được xác nhận.

### Khu vực 8 — Publish status

Hiển thị:
- Thời gian thao tác.
- Topic.
- Payload JSON.
- Kết quả publish.
- Thông báo lỗi nếu có.

Không cần lưu log vào database. Có thể giữ 20–50 dòng gần nhất trong RAM cho phiên chạy hiện tại.

## 12. Xử lý MQTT

Triển khai:
- Khởi tạo MQTT client.
- Kết nối broker.
- Chạy network loop theo đúng API Paho MQTT được cài.
- Reconnect khi mất kết nối.
- Xử lý callback đúng phiên bản Paho.
- Kiểm tra kết quả publish.
- Không chặn GUI.
- Xử lý đóng ứng dụng an toàn và dừng MQTT loop.

Khi bấm nút:
1. Kiểm tra trạng thái kết nối.
2. Nếu chưa kết nối, thông báo lỗi và không báo đã gửi.
3. Kiểm tra payload theo loại lệnh.
4. Serialize payload thành JSON hợp lệ.
5. Publish lên đúng topic.
6. Hiển thị kết quả publish và thông tin lệnh.

Nếu publish thành công, chỉ ghi nhận **đã gửi/publish thành công ở tầng MQTT**. Không ghi “kit đã thực thi thành công” vì giao thức hiện tại chưa định nghĩa ACK xác nhận thực thi cho từng lệnh.

Không tự retry một lệnh điều khiển nguy hiểm sau reconnect. Không gửi lại lệnh cũ cho kit sau khi kết nối phục hồi.

## 13. QoS và retain

Có thể cấu hình QoS cho command là 1 và retain là false theo đề xuất trong guide, nhưng ghi chú đây là khuyến nghị kỹ thuật cần xác nhận cùng phía kit.

Không tuyên bố QoS 1 đảm bảo lệnh chỉ thực hiện đúng một lần. Không dùng retained command cho các lệnh điều khiển.

Không tự tạo ACK topic, sequence number hoặc cơ chế command ID nếu chưa có contract thống nhất.

## 14. Kiểm thử

Dùng `mosquitto_sub` để quan sát các lệnh publish:

```cmd
"C:\Program Files\mosquitto\mosquitto_sub.exe" -h mqtt.mysignage.vn -p 1883 -t "lab/kit/KIT-001/cmd/#" -v
```

Kiểm thử từng trường hợp:

1. Kết nối broker thành công.
2. Broker từ chối kết nối.
3. Publish START, STOP và CALIB lên `cmd/reset` với đúng JSON.
4. Publish ON/OFF lên `cmd/power`.
5. Publish năm mức voltage với payload JSON.
6. Publish ba giá trị scale theo draft.
7. Publish ruler position 0, 120, 300.
8. Từ chối ruler position -1, 301 và 120.5.
9. Không gửi lệnh khi chưa kết nối.
10. GUI vẫn phản hồi khi broker mất kết nối.
11. Reconnect không làm phát lại lệnh cũ.
12. Shutdown không gửi nếu chưa được cấu hình payload đã xác nhận.

Khi kiểm thử, kiểm tra cả topic và payload thực tế trong cửa sổ `mosquitto_sub`.

Nếu broker từ chối kết nối, hiển thị nguyên nhân phù hợp. Không giả định anonymous access luôn được cho phép.

## 15. Những nội dung tuyệt đối không được làm

- Không thêm K-lock.
- Không thêm `cmd/magnetic_field`.
- Không gửi chuỗi đơn `on`, `off`, `6` hoặc `19.99` cho những command yêu cầu JSON.
- Không nhầm shutdown toàn bộ kit với OFF nguồn AC.
- Không coi topic/payload draft là giao thức đã phê duyệt.
- Không tạo API server giả để tuyên bố hoàn tất luồng chính thức.
- Không tuyên bố publish thành công đồng nghĩa phần cứng đã thực thi lệnh.
- Không tự thêm chức năng ngoài yêu cầu.

## 16. Đầu ra cần cung cấp

Hãy tạo ứng dụng hoàn chỉnh, có thể chạy trên Windows, bao gồm:
- Toàn bộ source code.
- `requirements.txt`.
- README hướng dẫn cài đặt và chạy.
- Cấu hình MQTT tập trung.
- Giao diện điều khiển đầy đủ.
- Xử lý lỗi và reconnect.
- Kiểm thử các topic/payload bằng Mosquitto.
- Ghi chú rõ các trường/topic còn draft.

Trước khi hoàn thành, hãy đối chiếu lại từng nút, topic và JSON payload với tài liệu MQTT Integration Guide v2.2. Không được để K-lock xuất hiện ở bất kỳ vị trí nào trong code hoặc giao diện.