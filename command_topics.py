"""
PTIT MQTT Controller — Command Topics & Validation Module
Theo tài liệu: doc2.md (Kiểm thử & Điều khiển KIT-001)

QUY TẮC BẮT BUỘC:
- Mọi payload phải là JSON dict hợp lệ.
- Không tự thêm sequence number, command_id, attempt_id.
- Không chứa K-lock hoặc cmd/magnetic_field.
"""

from typing import Tuple, Dict, Any
from config import (
    TOPIC_RESET, TOPIC_POWER, TOPIC_VOLTAGE, TOPIC_SCALE, TOPIC_RULER, TOPIC_SHUTDOWN,
    FIELD_VOLTAGE, FIELD_SCALE, FIELD_RULER, CONFIRMED_SHUTDOWN_PAYLOAD,
    VALID_VOLTAGES, VALID_SCALES, RULER_MIN_MM, RULER_MAX_MM
)


class CommandBuilder:
    """Xây dựng và kiểm tra tính hợp lệ của topic và payload JSON theo đặc tả doc2.md"""

    # ── Nhóm A: Reset / Vòng đời lượt ─────────────────────────────────────────
    @staticmethod
    def build_reset_cmd(action: str) -> Tuple[str, Dict[str, Any]]:
        action = action.lower().strip()
        if action not in ["start", "stop", "calib"]:
            raise ValueError(f"Hành động reset không hợp lệ: '{action}'. Chỉ chấp nhận 'start', 'stop', 'calib'.")
        return TOPIC_RESET, {"action": action}

    # ── Nhóm B: Power nguồn AC ────────────────────────────────────────────────
    @staticmethod
    def build_power_cmd(action: str) -> Tuple[str, Dict[str, Any]]:
        action = action.lower().strip()
        if action not in ["on", "off"]:
            raise ValueError(f"Hành động nguồn không hợp lệ: '{action}'. Chỉ chấp nhận 'on' hoặc 'off'.")
        return TOPIC_POWER, {"action": action}

    # ── Nhóm C: Điện áp (0, 3, 6, 9, 12 V) ───────────────────────────────────
    @staticmethod
    def build_voltage_cmd(voltage: int) -> Tuple[str, Dict[str, Any]]:
        if not isinstance(voltage, int):
            raise TypeError(f"Giá trị điện áp phải là số nguyên, nhận: {type(voltage).__name__}")
        if voltage not in VALID_VOLTAGES:
            raise ValueError(f"Điện áp {voltage}V không hợp lệ. Miền giá trị cho phép: {VALID_VOLTAGES}")
        # Dùng tên trường từ cấu hình (draft kỹ thuật)
        return TOPIC_VOLTAGE, {FIELD_VOLTAGE: voltage}

    # ── Nhóm D: Thang đo Scale (1.999, 19.99, 199.9) ─────────────────────────
    @staticmethod
    def build_scale_cmd(scale_str: str) -> Tuple[str, Dict[str, Any]]:
        scale_str = str(scale_str).strip()
        if scale_str not in VALID_SCALES:
            raise ValueError(f"Thang đo '{scale_str}' không hợp lệ. Danh sách cho phép: {VALID_SCALES}")
        # Giá trị scale bắt buộc là chuỗi trong JSON, giữ nguyên dấu chấm thập phân
        return TOPIC_SCALE, {FIELD_SCALE: scale_str}

    # ── Nhóm E: Vị trí thước Ruler (0 - 300 mm) ──────────────────────────────
    @staticmethod
    def build_ruler_cmd(pos_raw: Any) -> Tuple[str, Dict[str, Any]]:
        # Không chấp nhận delta như '+1', '-1', 'move_left'
        if isinstance(pos_raw, str):
            pos_raw = pos_raw.strip()
            if not pos_raw.isdigit():
                raise ValueError("Vị trí thước phải là số nguyên tuyệt đối không âm (0 - 300 mm), không chấp nhận chuỗi delta hoặc ký tự lạ.")
            pos_val = int(pos_raw)
        elif isinstance(pos_raw, float):
            if not pos_raw.is_integer():
                raise ValueError(f"Vị trí thước không được là số thập phân ({pos_raw}). Phải là số nguyên mm.")
            pos_val = int(pos_raw)
        elif isinstance(pos_raw, int):
            pos_val = pos_raw
        else:
            raise TypeError("Vị trí thước phải là số nguyên mm.")

        if pos_val < RULER_MIN_MM or pos_val > RULER_MAX_MM:
            raise ValueError(f"Vị trí thước {pos_val} mm nằm ngoài giới hạn cho phép [{RULER_MIN_MM}, {RULER_MAX_MM}] mm.")

        return TOPIC_RULER, {FIELD_RULER: pos_val}

    # ── Nhóm F: Shutdown toàn bộ kit (Admin Draft) ───────────────────────────
    @staticmethod
    def build_shutdown_cmd(admin_enabled: bool) -> Tuple[str, Dict[str, Any]]:
        if not admin_enabled:
            raise PermissionError("Lệnh shutdown chưa được cấp phép. Chỉ admin được kích hoạt khi đã xác nhận giao thức.")
        return TOPIC_SHUTDOWN, dict(CONFIRMED_SHUTDOWN_PAYLOAD)

