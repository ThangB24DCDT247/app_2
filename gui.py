"""
PTIT MQTT Controller — GUI Module
Giao diện người dùng theo đặc tả tài liệu doc2.md:
- Tông màu thương hiệu PTIT (Đỏ - Trắng)
- Có logo PTIT ở góc trên
- 8 khu vực điều khiển và hiển thị trạng thái publish rõ ràng
- Dialog xác nhận cho các thao tác quan trọng (STOP, Shutdown)
"""

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional

from config import (
    DEFAULT_BROKER, DEFAULT_PORT, DEFAULT_CLIENT_ID, KIT_CODE,
    COLOR_PTIT_RED, COLOR_PTIT_DARK, COLOR_PTIT_LIGHT, COLOR_WHITE,
    COLOR_BG, COLOR_PANEL, COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_MUTED,
    COLOR_GREEN, COLOR_ORANGE, COLOR_BLUE, COLOR_AMBER,
    VALID_VOLTAGES, VALID_SCALES, RULER_MIN_MM, RULER_MAX_MM
)
from command_topics import CommandBuilder
from mqtt_controller import MQTTController


class PTITControllerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PTIT MQTT Controller — KIT-001")
        self.root.geometry("1180x820")
        self.root.minsize(980, 720)
        self.root.configure(bg=COLOR_BG)

        # Trạng thái Admin cho chức năng Shutdown
        self.admin_enabled = tk.BooleanVar(value=False)
        self.auto_scroll   = tk.BooleanVar(value=True)

        # Khởi tạo MQTT Engine
        self.mqtt = MQTTController(
            on_status_change=self._threadsafe_status_update,
            on_publish_result=self._threadsafe_publish_update
        )

        # Xây dựng giao diện
        self._set_app_icon()
        self._build_header()
        self._build_connection_bar()
        self._build_body()
        self._build_footer()

        # Tự động kết nối tới broker khi khởi động
        self.root.after(400, self._on_connect_click)

    # ── Thiết lập Icon & Logo ────────────────────────────────────────────────
    def _set_app_icon(self):
        logo_path = os.path.join(os.path.dirname(__file__), "ptit_logo.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ptit_logo.png")

        if os.path.exists(logo_path):
            try:
                icon_img = tk.PhotoImage(file=logo_path)
                self.root.iconphoto(True, icon_img)
                self._app_icon_ref = icon_img
            except Exception:
                pass

    # ── Header ───────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLOR_PTIT_RED, height=76)
        hdr.pack(fill=tk.X, side=tk.TOP)
        hdr.pack_propagate(False)

        # Logo bên trái
        logo_path = os.path.join(os.path.dirname(__file__), "ptit_logo.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ptit_logo.png")

        self._logo_photo = None
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                pil_img = Image.open(logo_path).resize((54, 54), Image.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(pil_img)
                lbl_logo = tk.Label(hdr, image=self._logo_photo, bg=COLOR_PTIT_RED)
                lbl_logo.pack(side=tk.LEFT, padx=(16, 12), pady=10)
            except Exception:
                pass

        if not self._logo_photo:
            tk.Label(hdr, text="PTIT", font=("Segoe UI", 22, "bold"),
                     fg=COLOR_WHITE, bg=COLOR_PTIT_RED).pack(side=tk.LEFT, padx=(16, 12), pady=10)

        # Tiêu đề ứng dụng
        title_box = tk.Frame(hdr, bg=COLOR_PTIT_RED)
        title_box.pack(side=tk.LEFT, pady=10)

        tk.Label(title_box, text="PTIT MQTT Controller",
                 font=("Segoe UI", 18, "bold"), fg=COLOR_WHITE, bg=COLOR_PTIT_RED).pack(anchor="w")
        tk.Label(title_box, text="Công cụ điều khiển và kiểm thử lệnh trực tiếp cho thiết bị phòng Lab",
                 font=("Segoe UI", 9), fg="#FFD6DA", bg=COLOR_PTIT_RED).pack(anchor="w")

        # Badge Kit Code
        badge = tk.Frame(hdr, bg=COLOR_PTIT_DARK, padx=14, pady=8)
        badge.pack(side=tk.RIGHT, padx=18)
        tk.Label(badge, text=f"Target: {KIT_CODE}", font=("Consolas", 12, "bold"),
                 fg=COLOR_WHITE, bg=COLOR_PTIT_DARK).pack()
        tk.Label(badge, text="Direct Broker Control", font=("Segoe UI", 8),
                 fg="#FFB3B3", bg=COLOR_PTIT_DARK).pack()

    # ── Khu vực 1: Connection Bar ─────────────────────────────────────────────
    def _build_connection_bar(self):
        c_bar = tk.Frame(self.root, bg=COLOR_WHITE, bd=0,
                         highlightthickness=1, highlightbackground=COLOR_BORDER)
        c_bar.pack(fill=tk.X, side=tk.TOP, padx=0, pady=0)

        # Đèn trạng thái
        self._dot = tk.Label(c_bar, text="●", font=("Arial", 16), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE)
        self._dot.pack(side=tk.LEFT, padx=(14, 4), pady=6)

        self._status_var = tk.StringVar(value="Chưa kết nối tới Broker")
        self._status_lbl = tk.Label(c_bar, textvariable=self._status_var,
                                    font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE, anchor="w")
        self._status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)

        # Các trường thông tin kết nối nhỏ gọn
        fields_frame = tk.Frame(c_bar, bg=COLOR_WHITE)
        fields_frame.pack(side=tk.RIGHT, padx=12, pady=6)

        # Host
        tk.Label(fields_frame, text="Host:", font=("Segoe UI", 9), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side=tk.LEFT, padx=(4, 2))
        self._ent_host = tk.Entry(fields_frame, width=18, font=("Consolas", 9), relief="solid", bd=1)
        self._ent_host.insert(0, DEFAULT_BROKER)
        self._ent_host.pack(side=tk.LEFT, padx=(0, 6))

        # Port
        tk.Label(fields_frame, text="Port:", font=("Segoe UI", 9), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side=tk.LEFT, padx=(4, 2))
        self._ent_port = tk.Entry(fields_frame, width=6, font=("Consolas", 9), relief="solid", bd=1)
        self._ent_port.insert(0, str(DEFAULT_PORT))
        self._ent_port.pack(side=tk.LEFT, padx=(0, 8))

        # Nút kết nối
        self._btn_connect = tk.Button(
            fields_frame, text="⚡ Connect", command=self._on_connect_click,
            font=("Segoe UI", 9, "bold"), bg=COLOR_PTIT_RED, fg=COLOR_WHITE,
            activebackground=COLOR_PTIT_DARK, activeforeground=COLOR_WHITE,
            relief="flat", cursor="hand2", padx=10, pady=2
        )
        self._btn_connect.pack(side=tk.LEFT, padx=3)

        self._btn_reconnect = tk.Button(
            fields_frame, text="🔄 Reconnect", command=self._on_reconnect_click,
            font=("Segoe UI", 9, "bold"), bg=COLOR_WHITE, fg=COLOR_PTIT_RED,
            activebackground=COLOR_PTIT_LIGHT, activeforeground=COLOR_PTIT_RED,
            relief="solid", bd=1, cursor="hand2", padx=8, pady=2
        )
        self._btn_reconnect.pack(side=tk.LEFT, padx=3)

        self._btn_disconnect = tk.Button(
            fields_frame, text="✖ Disconnect", command=self._on_disconnect_click,
            font=("Segoe UI", 9, "bold"), bg=COLOR_WHITE, fg=COLOR_TEXT_MUTED,
            activebackground="#F1F5F9", relief="solid", bd=1, cursor="hand2", padx=8, pady=2
        )
        self._btn_disconnect.pack(side=tk.LEFT, padx=3)

    # ── Khu vực chính (Chia 2 cột) ───────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.root, bg=COLOR_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # ── CỘT TRÁI: Các bảng điều khiển (Khu vực 2 -> 7) ─────────────────────
        left_col = tk.Frame(body, bg=COLOR_BG, width=540)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Canvas có thanh cuộn cho cột trái nếu cửa sổ bị thu nhỏ
        canvas = tk.Canvas(left_col, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_col, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLOR_BG)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _configure_canvas_width)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Nhóm A: Reset / Vòng đời lượt
        self._create_group_a_reset(scrollable_frame)

        # Nhóm B: Power nguồn AC
        self._create_group_b_power(scrollable_frame)

        # Nhóm C: Voltage điện áp
        self._create_group_c_voltage(scrollable_frame)

        # Nhóm D: Thang đo Scale
        self._create_group_d_scale(scrollable_frame)

        # Nhóm E: Vị trí thước Ruler
        self._create_group_e_ruler(scrollable_frame)

        # Nhóm F: Shutdown toàn bộ kit (Admin)
        self._create_group_f_shutdown(scrollable_frame)

        # ── CỘT PHẢI: Khu vực 8 — Nhật ký Publish ─────────────────────────────
        right_col = tk.Frame(body, bg=COLOR_PANEL, highlightthickness=1, highlightbackground=COLOR_BORDER)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        self._build_publish_log_panel(right_col)

    # ── KHU VỰC 2: Nhóm A — Reset / Vòng đời lượt ────────────────────────────
    def _create_group_a_reset(self, parent):
        box = self._create_card(parent, "🔄  Nhóm A: Vòng đời lượt (Reset / Session)", "Topic: lab/kit/KIT-001/cmd/reset")

        btn_row = tk.Frame(box, bg=COLOR_PANEL)
        btn_row.pack(fill=tk.X, padx=12, pady=10)

        # START
        btn_start = tk.Button(
            btn_row, text="▶  START\n(Bắt đầu)", font=("Segoe UI", 10, "bold"),
            bg="#ECFDF5", fg=COLOR_GREEN, activebackground="#D1FAE5",
            relief="solid", bd=1, cursor="hand2", height=2,
            command=lambda: self._send_reset_action("start")
        )
        btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # STOP (Có cảnh báo xác nhận)
        btn_stop = tk.Button(
            btn_row, text="⏹  STOP\n(Kết thúc)", font=("Segoe UI", 10, "bold"),
            bg="#FEF2F2", fg=COLOR_PTIT_RED, activebackground="#FEE2E2",
            relief="solid", bd=1, cursor="hand2", height=2,
            command=self._confirm_and_send_stop
        )
        btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # CALIB
        btn_calib = tk.Button(
            btn_row, text="🎯  CALIB\n(Hiệu chuẩn)", font=("Segoe UI", 10, "bold"),
            bg="#F8FAFC", fg=COLOR_TEXT, activebackground="#E2E8F0",
            relief="solid", bd=1, cursor="hand2", height=2,
            command=lambda: self._send_reset_action("calib")
        )
        btn_calib.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

    # ── KHU VỰC 3: Nhóm B — Power nguồn AC ────────────────────────────────────
    def _create_group_b_power(self, parent):
        box = self._create_card(parent, "⚡  Nhóm B: Nguồn AC", "Topic: lab/kit/KIT-001/cmd/power | ON: Xanh lam, OFF: Đỏ")

        btn_row = tk.Frame(box, bg=COLOR_PANEL)
        btn_row.pack(fill=tk.X, padx=12, pady=10)

        # ON: Màu xanh lam (theo đúng yêu cầu doc2.md)
        btn_on = tk.Button(
            btn_row, text="🔌  BẬT NGUỒN AC (ON)", font=("Segoe UI", 10, "bold"),
            bg=COLOR_BLUE, fg=COLOR_WHITE, activebackground="#0369A1", activeforeground=COLOR_WHITE,
            relief="flat", cursor="hand2", height=2,
            command=lambda: self._send_power_action("on")
        )
        btn_on.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # OFF: Màu đỏ (theo đúng yêu cầu doc2.md)
        btn_off = tk.Button(
            btn_row, text="⏻  TẮT NGUỒN AC (OFF)", font=("Segoe UI", 10, "bold"),
            bg=COLOR_PTIT_RED, fg=COLOR_WHITE, activebackground=COLOR_PTIT_DARK, activeforeground=COLOR_WHITE,
            relief="flat", cursor="hand2", height=2,
            command=lambda: self._send_power_action("off")
        )
        btn_off.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

    # ── KHU VỰC 4: Nhóm C — Voltage Điện áp ──────────────────────────────────
    def _create_group_c_voltage(self, parent):
        box = self._create_card(parent, "🔋  Nhóm C: Mức điện áp [DRAFT Field]", "Topic: lab/kit/KIT-001/cmd/voltage | Giá trị: 0, 3, 6, 9, 12 V")

        btn_row = tk.Frame(box, bg=COLOR_PANEL)
        btn_row.pack(fill=tk.X, padx=12, pady=10)

        for v in VALID_VOLTAGES:
            btn = tk.Button(
                btn_row, text=f"{v} V", font=("Segoe UI", 10, "bold"),
                bg=COLOR_WHITE, fg=COLOR_PTIT_RED if v > 0 else COLOR_TEXT,
                activebackground=COLOR_PTIT_LIGHT, relief="solid", bd=1,
                cursor="hand2", width=6, height=2,
                command=lambda val=v: self._send_voltage_action(val)
            )
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

    # ── KHU VỰC 5: Nhóm D — Thang đo Scale ───────────────────────────────────
    def _create_group_d_scale(self, parent):
        box = self._create_card(parent, "📐  Nhóm D: Thang đo Scale [DRAFT]", "Topic: lab/kit/KIT-001/cmd/scale | Chuỗi định dạng thập phân")

        btn_row = tk.Frame(box, bg=COLOR_PANEL)
        btn_row.pack(fill=tk.X, padx=12, pady=10)

        for sc in VALID_SCALES:
            btn = tk.Button(
                btn_row, text=f"Scale {sc}", font=("Segoe UI", 9, "bold"),
                bg=COLOR_WHITE, fg=COLOR_TEXT,
                activebackground="#F1F5F9", relief="solid", bd=1,
                cursor="hand2", height=2,
                command=lambda s=sc: self._send_scale_action(s)
            )
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

    # ── KHU VỰC 6: Nhóm E — Vị trí thước Ruler ───────────────────────────────
    def _create_group_e_ruler(self, parent):
        box = self._create_card(parent, "📏  Nhóm E: Vị trí thước Ruler [DRAFT]", "Topic: lab/kit/KIT-001/cmd/ruler | Số nguyên tuyệt đối 0 - 300 mm")

        content = tk.Frame(box, bg=COLOR_PANEL)
        content.pack(fill=tk.X, padx=14, pady=8)

        # Slider & Value
        slider_frame = tk.Frame(content, bg=COLOR_PANEL)
        slider_frame.pack(fill=tk.X, pady=(2, 8))

        self._ruler_var = tk.IntVar(value=0)

        # Nhãn hiển thị giá trị hiện tại
        lbl_info = tk.Label(slider_frame, text="Vị trí đặt:", font=("Segoe UI", 9), fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL)
        lbl_info.pack(side=tk.LEFT, padx=(0, 8))

        self._lbl_ruler_val = tk.Label(slider_frame, text="0 mm", font=("Consolas", 12, "bold"),
                                       fg=COLOR_PTIT_RED, bg=COLOR_PANEL, width=8, anchor="w")
        self._lbl_ruler_val.pack(side=tk.LEFT)

        # Slider từ 0 tới 300 mm
        self._scale_ruler = ttk.Scale(
            content, from_=RULER_MIN_MM, to=RULER_MAX_MM, orient="horizontal",
            variable=self._ruler_var, command=self._on_ruler_slider_move
        )
        self._scale_ruler.pack(fill=tk.X, pady=(0, 8))

        # Hàng nhập tay + Nút Gửi Vị Trí
        send_row = tk.Frame(content, bg=COLOR_PANEL)
        send_row.pack(fill=tk.X, pady=(0, 4))

        tk.Label(send_row, text="Nhập số mm chính xác:", font=("Segoe UI", 9), fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL).pack(side=tk.LEFT, padx=(0, 6))

        self._ent_ruler = tk.Entry(send_row, width=8, font=("Consolas", 10), relief="solid", bd=1)
        self._ent_ruler.insert(0, "0")
        self._ent_ruler.pack(side=tk.LEFT, padx=(0, 10))

        # Khi người dùng nhập vào Entry, cập nhật slider
        self._ent_ruler.bind("<KeyRelease>", self._on_ruler_entry_change)

        btn_send_ruler = tk.Button(
            send_row, text="🚀  GỬI VỊ TRÍ (0 - 300 mm)", font=("Segoe UI", 9, "bold"),
            bg=COLOR_PTIT_RED, fg=COLOR_WHITE, activebackground=COLOR_PTIT_DARK, activeforeground=COLOR_WHITE,
            relief="flat", cursor="hand2", padx=14, pady=4,
            command=self._send_ruler_action
        )
        btn_send_ruler.pack(side=tk.RIGHT)

    # ── KHU VỰC 7: Nhóm F — Shutdown toàn bộ kit (Admin Draft) ────────────────
    def _create_group_f_shutdown(self, parent):
        box = self._create_card(parent, "⚠️  Nhóm F: Quản trị — Shutdown Toàn Bộ Kit", "Topic: lab/kit/KIT-001/cmd/shutdown | Dành riêng cho Admin phòng Lab")

        content = tk.Frame(box, bg=COLOR_PANEL)
        content.pack(fill=tk.X, padx=14, pady=10)

        # Checkbox mở khóa Admin
        chk_admin = tk.Checkbutton(
            content, text="Xác nhận giao thức & Kích hoạt quyền Admin",
            variable=self.admin_enabled, command=self._toggle_admin_shutdown_button,
            font=("Segoe UI", 9), fg=COLOR_TEXT, bg=COLOR_PANEL, activebackground=COLOR_PANEL
        )
        chk_admin.pack(anchor="w", pady=(0, 8))

        self._btn_shutdown = tk.Button(
            content, text="🛑  SHUTDOWN TOÀN BỘ KIT", font=("Segoe UI", 10, "bold"),
            bg="#94A3B8", fg=COLOR_WHITE, relief="flat", state=tk.DISABLED,
            cursor="arrow", height=2, command=self._confirm_and_send_shutdown
        )
        self._btn_shutdown.pack(fill=tk.X)

    def _toggle_admin_shutdown_button(self):
        if self.admin_enabled.get():
            self._btn_shutdown.config(
                state=tk.NORMAL, bg=COLOR_AMBER, activebackground="#B45309",
                cursor="hand2"
            )
        else:
            self._btn_shutdown.config(
                state=tk.DISABLED, bg="#94A3B8", cursor="arrow"
            )

    # ── KHU VỰC 8: Nhật ký Publish Lệnh ───────────────────────────────────────
    def _build_publish_log_panel(self, parent):
        # Header panel
        lh = tk.Frame(parent, bg=COLOR_PTIT_RED, padx=12, pady=8)
        lh.pack(fill=tk.X)
        tk.Label(lh, text="📋  Nhật ký thao tác Publish Lệnh",
                 font=("Segoe UI", 11, "bold"), fg=COLOR_WHITE, bg=COLOR_PTIT_RED).pack(side=tk.LEFT)

        # Bộ đếm lệnh
        self._lbl_log_counter = tk.Label(lh, text="Đã gửi: 0", font=("Segoe UI", 9), fg="#FFD6DA", bg=COLOR_PTIT_RED)
        self._lbl_log_counter.pack(side=tk.RIGHT)

        # Toolbar
        tb = tk.Frame(parent, bg="#F1F5F9", padx=10, pady=4)
        tb.pack(fill=tk.X)

        tk.Checkbutton(tb, text="Tự cuộn", variable=self.auto_scroll,
                       font=("Segoe UI", 8), bg="#F1F5F9", fg=COLOR_TEXT).pack(side=tk.LEFT)

        tk.Button(tb, text="🗑 Xóa nhật ký", command=self._clear_log,
                  font=("Segoe UI", 8, "bold"), bg=COLOR_WHITE, fg=COLOR_PTIT_RED,
                  relief="solid", bd=1, cursor="hand2", padx=6, pady=1).pack(side=tk.RIGHT)

        # Text feed
        self._feed = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, state=tk.DISABLED,
            font=("Consolas", 9), bg=COLOR_WHITE, fg=COLOR_TEXT,
            relief=tk.FLAT, padx=10, pady=8
        )
        self._feed.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tags màu sắc
        self._feed.tag_configure("time",    foreground=COLOR_TEXT_MUTED, font=("Consolas", 8))
        self._feed.tag_configure("topic",   foreground=COLOR_PTIT_RED,  font=("Consolas", 9, "bold"))
        self._feed.tag_configure("payload", foreground="#0F172A",       font=("Consolas", 9))
        self._feed.tag_configure("ok",      foreground=COLOR_GREEN,     font=("Segoe UI", 9, "bold"))
        self._feed.tag_configure("err",     foreground=COLOR_PTIT_RED,  font=("Segoe UI", 9, "bold"))
        self._feed.tag_configure("sep",     foreground="#CBD5E1")

        self._published_count = 0

    # ── Footer ────────────────────────────────────────────────────────────────
    def _build_footer(self):
        ft = tk.Frame(self.root, bg=COLOR_WHITE, highlightthickness=1, highlightbackground=COLOR_BORDER)
        ft.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(ft, text="⚠ Công cụ thử nghiệm tầng MQTT: Thành công publish chỉ đảm bảo gói tin đã gửi tới Broker.",
                 font=("Segoe UI", 8, "italic"), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side=tk.LEFT, padx=12, pady=4)

        tk.Label(ft, text="© 2026 PTIT — Học viện Công nghệ Bưu chính Viễn thông",
                 font=("Segoe UI", 8), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side=tk.RIGHT, padx=12, pady=4)

    # ── Tiện ích UI: Card ─────────────────────────────────────────────────────
    def _create_card(self, parent, title: str, subtitle: str) -> tk.Frame:
        card = tk.LabelFrame(
            parent, text=f" {title} ", font=("Segoe UI", 9, "bold"),
            fg=COLOR_PTIT_RED, bg=COLOR_PANEL, relief="solid", bd=1
        )
        card.pack(fill=tk.X, padx=4, pady=(0, 10))

        if subtitle:
            tk.Label(card, text=subtitle, font=("Segoe UI", 8),
                     fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL).pack(anchor="w", padx=12, pady=(4, 0))

        return card

    # ── Xử lý Slider & Entry Ruler ───────────────────────────────────────────
    def _on_ruler_slider_move(self, val):
        try:
            int_val = int(float(val))
            self._lbl_ruler_val.config(text=f"{int_val} mm")
            self._ent_ruler.delete(0, tk.END)
            self._ent_ruler.insert(0, str(int_val))
        except Exception:
            pass

    def _on_ruler_entry_change(self, event=None):
        raw = self._ent_ruler.get().strip()
        if raw.isdigit():
            val = int(raw)
            if RULER_MIN_MM <= val <= RULER_MAX_MM:
                self._ruler_var.set(val)
                self._lbl_ruler_val.config(text=f"{val} mm")

    # ── Các sự kiện gửi lệnh ──────────────────────────────────────────────────
    def _send_reset_action(self, action: str):
        try:
            topic, payload = CommandBuilder.build_reset_cmd(action)
            self.mqtt.publish_command(topic, payload)
        except Exception as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))

    def _confirm_and_send_stop(self):
        confirm = messagebox.askyesno(
            "Xác nhận STOP",
            "Bạn có chắc chắn muốn gửi lệnh STOP (kết thúc lượt thực hành)?\nTopic: lab/kit/KIT-001/cmd/reset",
            icon="warning"
        )
        if confirm:
            self._send_reset_action("stop")

    def _send_power_action(self, action: str):
        try:
            topic, payload = CommandBuilder.build_power_cmd(action)
            self.mqtt.publish_command(topic, payload)
        except Exception as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))

    def _send_voltage_action(self, voltage: int):
        try:
            topic, payload = CommandBuilder.build_voltage_cmd(voltage)
            self.mqtt.publish_command(topic, payload)
        except Exception as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))

    def _send_scale_action(self, scale_str: str):
        try:
            topic, payload = CommandBuilder.build_scale_cmd(scale_str)
            self.mqtt.publish_command(topic, payload)
        except Exception as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))

    def _send_ruler_action(self):
        try:
            raw_val = self._ent_ruler.get().strip()
            topic, payload = CommandBuilder.build_ruler_cmd(raw_val)
            self.mqtt.publish_command(topic, payload)
        except Exception as e:
            messagebox.showerror("Lỗi vị trí thước", str(e))

    def _confirm_and_send_shutdown(self):
        confirm = messagebox.askyesno(
            "CẢNH BÁO: SHUTDOWN TOÀN BỘ KIT",
            "THAO TÁC NGUY HIỂM:\nLệnh này sẽ tắt hoàn toàn kit KIT-001 (không phải chỉ tắt nguồn AC)!\n\nBạn có chắc chắn muốn gửi lệnh Shutdown?",
            icon="error"
        )
        if confirm:
            try:
                topic, payload = CommandBuilder.build_shutdown_cmd(self.admin_enabled.get())
                self.mqtt.publish_command(topic, payload)
            except Exception as e:
                messagebox.showerror("Lỗi Shutdown", str(e))

    # ── Xử lý kết nối ────────────────────────────────────────────────────────
    def _on_connect_click(self):
        host = self._ent_host.get().strip() or DEFAULT_BROKER
        try:
            port = int(self._ent_port.get().strip() or DEFAULT_PORT)
        except ValueError:
            messagebox.showerror("Lỗi cấu hình", "Port phải là số nguyên!")
            return
        self.mqtt.connect(host, port, DEFAULT_CLIENT_ID)

    def _on_reconnect_click(self):
        self.mqtt.disconnect()
        self.root.after(400, self._on_connect_click)

    def _on_disconnect_click(self):
        self.mqtt.disconnect()

    # ── Callbacks luồng an toàn ───────────────────────────────────────────────
    def _threadsafe_status_update(self, status: str, message: str):
        self.root.after(0, self._update_status_ui, status, message)

    def _update_status_ui(self, status: str, message: str):
        color_map = {
            "connected":    COLOR_GREEN,
            "connecting":   COLOR_ORANGE,
            "disconnected": COLOR_TEXT_MUTED,
            "error":        COLOR_PTIT_RED,
        }
        c = color_map.get(status, COLOR_TEXT_MUTED)
        self._dot.config(fg=c)
        self._status_var.set(message)
        self._status_lbl.config(fg=c)

    def _threadsafe_publish_update(self, success: bool, topic: str, payload_json: str, detail_msg: str):
        self.root.after(0, self._append_publish_log, success, topic, payload_json, detail_msg)

    def _append_publish_log(self, success: bool, topic: str, payload_json: str, detail_msg: str):
        self._published_count += 1
        self._lbl_log_counter.config(text=f"Đã gửi: {self._published_count}")

        now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        self._feed.config(state=tk.NORMAL)
        self._feed.insert(tk.END, f"[{now_str}] ", "time")
        self._feed.insert(tk.END, f"Topic: {topic}\n", "topic")
        self._feed.insert(tk.END, f"Payload: {payload_json}\n", "payload")

        if success:
            self._feed.insert(tk.END, f"✔ {detail_msg}\n", "ok")
        else:
            self._feed.insert(tk.END, f"✖ {detail_msg}\n", "err")

        self._feed.insert(tk.END, "─" * 56 + "\n", "sep")
        self._feed.config(state=tk.DISABLED)

        if self.auto_scroll.get():
            self._feed.see(tk.END)

    def _clear_log(self):
        self._feed.config(state=tk.NORMAL)
        self._feed.delete("1.0", tk.END)
        self._feed.config(state=tk.DISABLED)
        self._published_count = 0
        self._lbl_log_counter.config(text="Đã gửi: 0")

