"""
PTIT MQTT Controller — Configuration Module
Theo tài liệu: doc2.md (Kiểm thử & Điều khiển KIT-001)
"""

# ─── Cấu hình kết nối MQTT mặc định ──────────────────────────────────────────
DEFAULT_BROKER     = "mqtt.mysignage.vn"
DEFAULT_PORT       = 1883
DEFAULT_TRANSPORT  = "tcp"
DEFAULT_KEEPALIVE  = 60
KIT_CODE           = "KIT-001"
DEFAULT_CLIENT_ID  = "KIT-001-python-controller"

# Cấu hình Publish (khuyến nghị kỹ thuật - không retained)
DEFAULT_QOS        = 1
DEFAULT_RETAIN     = False

# Prefix topic chuẩn
TOPIC_PREFIX       = f"lab/kit/{KIT_CODE}/"

# ─── Định nghĩa các topic điều khiển ─────────────────────────────────────────
# Nhóm A: Reset / Vòng đời (Chính thức)
TOPIC_RESET        = f"{TOPIC_PREFIX}cmd/reset"

# Nhóm B: Nguồn AC (Chính thức)
TOPIC_POWER        = f"{TOPIC_PREFIX}cmd/power"

# Nhóm C: Điện áp (Topic chính thức, tên trường JSON đang là draft kỹ thuật)
TOPIC_VOLTAGE      = f"{TOPIC_PREFIX}cmd/voltage"
FIELD_VOLTAGE      = "voltage"     # [DRAFT] Cần thống nhất với API/firmware

# Nhóm D: Thang đo (Draft kỹ thuật)
TOPIC_SCALE        = f"{TOPIC_PREFIX}cmd/scale"
FIELD_SCALE        = "scale"       # [DRAFT] Chuỗi ký tự có dấu chấm thập phân

# Nhóm E: Vị trí thước (Draft kỹ thuật)
TOPIC_RULER        = f"{TOPIC_PREFIX}cmd/ruler"
FIELD_RULER        = "position"    # [DRAFT] Số nguyên tuyệt đối 0 - 300 mm

# Nhóm F: Shutdown toàn bộ kit (Draft quản trị - Admin only)
TOPIC_SHUTDOWN     = f"{TOPIC_PREFIX}cmd/shutdown"
# Payload shutdown chưa chốt chính thức, mặc định không gửi nếu chưa xác nhận
CONFIRMED_SHUTDOWN_PAYLOAD = {"action": "shutdown"}

# ─── Miền giá trị hợp lệ ────────────────────────────────────────────────────
VALID_VOLTAGES     = [0, 3, 6, 9, 12]       # Chỉ chấp nhận 5 mức này
VALID_SCALES       = ["1.999", "19.99", "199.9"] # Chuỗi ký tự giữ nguyên dấu chấm
RULER_MIN_MM       = 0
RULER_MAX_MM       = 300

# ─── Bảng màu thương hiệu PTIT ───────────────────────────────────────────────
COLOR_PTIT_RED     = "#C8102E"  # Đỏ PTIT chính
COLOR_PTIT_DARK    = "#9B0B22"  # Đỏ đậm
COLOR_PTIT_LIGHT   = "#FDECEA"  # Đỏ nhạt
COLOR_WHITE        = "#FFFFFF"
COLOR_BG           = "#F8F9FA"  # Nền sáng
COLOR_PANEL        = "#FFFFFF"  # Nền khối
COLOR_BORDER       = "#E2E8F0"  # Viền xám nhạt
COLOR_TEXT         = "#1E293B"  # Chữ đen
COLOR_TEXT_MUTED   = "#64748B"  # Chữ xám
COLOR_GREEN        = "#16A34A"  # Connected / Success
COLOR_ORANGE       = "#D97706"  # Connecting / Warning
COLOR_BLUE         = "#0284C7"  # Nút Bật nguồn AC (xanh lam)
COLOR_AMBER        = "#D97706"  # Admin warning

