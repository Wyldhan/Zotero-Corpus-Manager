#!/usr/bin/env bash
# [TR] macOS ve Linux için Tek Tıkla Görsel Web Arayüzü Başlatıcı
# [EN] One-Click Visual Web Dashboard Launcher for macOS and Linux
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[HATA / ERROR] Sisteminizde python3 bulunamadı / python3 was not found on your system."
    exit 1
fi

echo "[TR] Zotero Derlem ve Sınıflandırma Yöneticisi başlatılıyor..."
echo "[EN] Starting Zotero Corpus and Classification Manager..."
python3 zotero_cli.py gui
