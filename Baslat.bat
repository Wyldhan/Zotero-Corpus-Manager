@echo off
REM [TR] Windows icin Tek Tikla Gorsel Web Arayuzu Baslatici
REM [EN] One-Click Visual Web Dashboard Launcher for Windows
chcp 65001 >nul
title Zotero Derlem ve Siniflandirma Yoneticisi / Zotero Corpus Manager
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [HATA / ERROR] Bilgisayarinizda Python 3 bulunamadi! / Python 3 was not found on your system!
    echo [TR] Lutfen https://www.python.org/downloads/ adresinden Python 3 kurun.
    echo [EN] Please install Python 3 from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [TR] Zotero Derlem ve Siniflandirma Yoneticisi baslatiliyor...
echo [EN] Starting Zotero Corpus and Classification Manager...
python -X utf8 zotero_cli.py gui
pause
