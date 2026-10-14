"""
PTIT MQTT Controller — Main Entry Point
Học viện Công nghệ Bưu chính Viễn thông (PTIT)
Theo tài liệu: doc2.md
"""

import sys
import tkinter as tk
from tkinter import ttk
from gui import PTITControllerGUI


def main():
    root = tk.Tk()

    # Áp dụng ttk theme hiện đại
    try:
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    app = PTITControllerGUI(root)

    # Đóng ứng dụng an toàn: ngắt MQTT loop trước khi thoát
    def on_closing():
        try:
            app.mqtt.disconnect()
        except Exception:
            pass
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

