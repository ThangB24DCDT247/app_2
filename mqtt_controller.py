"""
PTIT MQTT Controller — MQTT Connection & Publishing Engine
Tương thích Paho MQTT v2 (CallbackAPIVersion.VERSION2)
Theo yêu cầu doc2.md:
- Không chặn giao diện (GUI chạy độc lập, MQTT chạy loop_start)
- Không tự động retry lệnh điều khiển sau reconnect
- Thông báo rõ ràng trạng thái ở tầng MQTT (không tự nhận kit đã thực thi)
"""

import json
import random
from typing import Callable, Optional, Dict, Any

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

from config import DEFAULT_QOS, DEFAULT_RETAIN


class MQTTController:
    def __init__(
        self,
        on_status_change: Callable[[str, str], None],
        on_publish_result: Callable[[bool, str, str, str], None]
    ):
        """
        :param on_status_change: callback(status_code: 'connected'|'connecting'|'disconnected'|'error', message)
        :param on_publish_result: callback(success: bool, topic: str, payload_json: str, detail_msg: str)
        """
        self.on_status_change = on_status_change
        self.on_publish_result = on_publish_result

        self.client: Optional[mqtt.Client] = None
        self.is_connected: bool = False
        self._user_requested_disconnect: bool = False
        self._active_config: Dict[str, Any] = {}

    def _cleanup_client(self):
        if self.client:
            try:
                self.client.loop_stop()
            except Exception:
                pass
            try:
                self.client.disconnect()
            except Exception:
                pass
            self.client = None

    def connect(self, host: str, port: int, client_id_base: str, keepalive: int = 60, transport: str = "tcp"):
        """Khởi tạo kết nối MQTT bất đồng bộ tới Broker"""
        if not MQTT_AVAILABLE:
            self.on_status_change("error", "Thư viện paho-mqtt chưa được cài đặt. Vui lòng chạy: pip install paho-mqtt")
            return

        self._user_requested_disconnect = False
        self._cleanup_client()

        # Tạo Client ID duy nhất để tránh xung đột làm broker ngắt kết nối liên tục
        unique_client_id = f"{client_id_base}-{random.randint(1000, 9999)}"
        self._active_config = {
            "host": host,
            "port": port,
            "client_id": unique_client_id,
            "keepalive": keepalive,
            "transport": transport
        }

        self.on_status_change("connecting", f"Đang kết nối tới {host}:{port} …")

        try:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=unique_client_id,
                clean_session=True,
                protocol=mqtt.MQTTv311,
                transport=transport,
            )

            # Tắt tự động reconnect liên tục để tránh hiện tượng nhấp nháy khi broker lỗi
            self.client.reconnect_delay_set(min_delay=86400, max_delay=86400)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish

            self.client.connect_async(host, port, keepalive)
            self.client.loop_start()

        except Exception as e:
            self.is_connected = False
            self.on_status_change("error", f"Lỗi khởi tạo kết nối: {e}")

    def disconnect(self):
        """Ngắt kết nối chủ động bởi người dùng"""
        self._user_requested_disconnect = True
        self.is_connected = False
        self._cleanup_client()
        self.on_status_change("disconnected", "Đã ngắt kết nối với MQTT Broker.")

    def reconnect(self):
        """Kết nối lại với cấu hình đã lưu"""
        if self._active_config:
            self.connect(
                self._active_config["host"],
                self._active_config["port"],
                self._active_config.get("client_id", "KIT-001-python-controller").split("-")[0],
                self._active_config.get("keepalive", 60),
                self._active_config.get("transport", "tcp")
            )

    def publish_command(self, topic: str, payload_dict: Dict[str, Any], qos: int = DEFAULT_QOS, retain: bool = DEFAULT_RETAIN) -> bool:
        """
        Publish command lên MQTT topic:
        1. Kiểm tra trạng thái kết nối
        2. Serialize JSON hợp lệ
        3. Gửi lệnh
        4. Báo cáo kết quả tầng MQTT
        """
        payload_json = json.dumps(payload_dict, ensure_ascii=False)

        if not self.is_connected or not self.client:
            err_msg = "Không thể gửi lệnh: Chưa kết nối tới MQTT Broker!"
            self.on_publish_result(False, topic, payload_json, err_msg)
            return False

        try:
            msg_info = self.client.publish(topic, payload=payload_json, qos=qos, retain=retain)
            # msg_info.rc trong paho v2 có thể là ReasonCode hoặc int
            rc_val = getattr(msg_info.rc, "value", msg_info.rc)

            if rc_val == 0:
                # doc2.md nhấn mạnh: Chỉ ghi nhận thành công ở tầng MQTT, không ghi kit đã thực thi
                success_msg = f"Đã publish thành công ở tầng MQTT (QoS {qos}, Retain: {retain})"
                self.on_publish_result(True, topic, payload_json, success_msg)
                return True
            else:
                fail_msg = f"Lỗi publish tầng MQTT (Mã lỗi: {msg_info.rc})"
                self.on_publish_result(False, topic, payload_json, fail_msg)
                return False

        except Exception as e:
            err_msg = f"Ngoại lệ khi publish: {e}"
            self.on_publish_result(False, topic, payload_json, err_msg)
            return False

    # ── Callbacks Paho MQTT v2 ────────────────────────────────────────────────
    def _on_connect(self, client, userdata, connect_flags, reason_code, properties):
        if reason_code.is_failure:
            self.is_connected = False
            if reason_code.value in (4, 5):
                msg = "Broker từ chối kết nối (Mã 4/5: Không có quyền hoặc sai cấu hình). Liên hệ quản trị viên."
            else:
                msg = f"Kết nối thất bại: {reason_code!s}"
            self.on_status_change("error", msg)
        else:
            self.is_connected = True
            self.on_status_change("connected", f"Đã kết nối thành công tới Broker ✔ | Sẵn sàng gửi lệnh điều khiển.")

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.is_connected = False
        if self._user_requested_disconnect:
            self.on_status_change("disconnected", "Đã ngắt kết nối.")
        elif disconnect_flags.is_disconnect_packet_from_server:
            self.on_status_change("error", f"Broker ngắt kết nối ({reason_code!s}). Nhấn Reconnect để thử lại.")
        else:
            self.on_status_change("error", "Mất kết nối với Broker. Nhấn Reconnect để kết nối lại.")

    def _on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        # Callback xác nhận packet PUBACK/PUBCOMP từ Broker
        pass

