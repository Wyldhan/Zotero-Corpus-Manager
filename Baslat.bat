@echo off
chcp 65001 >nul
title Zotero Derlem ve Otomatik Siniflandirma Yoneticisi
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [HATA] Bilgisayarinizda Python 3 bulunamadi!
    echo Lutfen https://www.python.org/downloads/ adresinden Python 3 kurun.
    pause
    exit /b 1
)

echo Zotero Derlem ve Siniflandirma Yoneticisi baslatiliyor...
python -X utf8 zotero_cli.py gui
pause
