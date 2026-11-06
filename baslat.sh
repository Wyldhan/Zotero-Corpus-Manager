#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[HATA] Sisteminizde python3 bulunamadı. Lütfen Python 3 kurun."
    exit 1
fi

echo "Zotero Derlem ve Sınıflandırma Yöneticisi başlatılıyor..."
python3 zotero_cli.py gui
