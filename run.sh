#!/usr/bin/env bash
# Script chạy PTIT MQTT Controller trên Linux / Raspberry Pi OS

# Chuyển về thư mục chứa script
cd "$(dirname "$0")"

# Kiểm tra Python 3
if ! command -v python3 &> /dev/null; then
    echo "[LỖI] Chưa cài đặt python3 trên hệ thống!"
    echo "Cài đặt bằng lệnh: sudo apt update && sudo apt install python3 python3-pip python3-tk -y"
    exit 1
fi

# Chạy ứng dụng
if command -v uv &> /dev/null; then
    uv run --with paho-mqtt --with Pillow main.py
else
    # Cài đặt thư viện nếu chưa có
    python3 -m pip install -q -r requirements.txt 2>/dev/null
    python3 main.py
fi

