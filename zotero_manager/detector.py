"""
[TR] Zotero veri dizinini, yürütülebilir dosyasını ve çalışma durumunu otomatik tespit eder.
[EN] Automatically detects the Zotero data directory, executable binary, and running process state.
"""
from __future__ import annotations

import os
import platform
import re
import socket
import subprocess
import time
from pathlib import Path


def find_zotero_data_dir(custom_path: str | Path | None = None) -> Path:
    """
    [TR] Kullanıcının Zotero veri dizinini (zotero.sqlite'ın bulunduğu klasör) otomatik bulur.
    [EN] Automatically locates the user's Zotero data directory (folder containing zotero.sqlite).
    """
    if custom_path:
        p = Path(custom_path).expanduser().resolve()
        if (p / "zotero.sqlite").exists():
            return p

    env_path = os.environ.get("ZOTERO_DATA_DIR")
    if env_path:
        p = Path(env_path).expanduser().resolve()
        if (p / "zotero.sqlite").exists():
            return p

    # [TR] 1. Zotero profilindeki prefs.js dosyasından özel veri dizinini (extensions.zotero.dataDir) oku
    # [EN] 1. Read custom data directory (extensions.zotero.dataDir) from Zotero profile's prefs.js
    home = Path.home()
    profile_roots = [
        home / "AppData" / "Roaming" / "Zotero" / "Zotero" / "Profiles",
        home / "Library" / "Application Support" / "Zotero" / "Profiles",
        home / ".zotero" / "zotero",
    ]
    for proot in profile_roots:
        if proot.exists():
            for prefs in proot.rglob("prefs.js"):
                try:
                    txt = prefs.read_text(encoding="utf-8", errors="ignore")
                    m = re.search(r'user_pref\("extensions\.zotero\.dataDir",\s*"([^"]+)"\);', txt)
                    if m:
                        raw_dir = m.group(1).replace("\\\\", "\\")
                        cand = Path(raw_dir)
                        if (cand / "zotero.sqlite").exists():
                            return cand
                except Exception:
                    pass

    # [TR] 2. Yaygın varsayılan dizinleri kontrol et
    # [EN] 2. Check common default directories across drives and user home
    candidates = [
        Path(r"D:\Zotero"),
        Path(r"C:\Zotero"),
        home / "Zotero",
        home / "Documents" / "Zotero",
    ]
    for cand in candidates:
        if (cand / "zotero.sqlite").exists():
            return cand

    return home / "Zotero"


def find_zotero_executable() -> Path | None:
    """
    [TR] İşletim sistemine göre Zotero.exe / Zotero.app yolunu bulur.
    [EN] Locates the Zotero executable binary based on the current operating system.
    """
    sys_name = platform.system().lower()
    if sys_name == "windows":
        candidates = [
            Path(r"C:\Program Files\Zotero\zotero.exe"),
            Path(r"C:\Program Files (x86)\Zotero\zotero.exe"),
            Path.home() / "AppData" / "Local" / "Zotero" / "zotero.exe",
        ]
    elif sys_name == "darwin":
        candidates = [Path("/Applications/Zotero.app/Contents/MacOS/zotero")]
    else:
        candidates = [
            Path("/usr/bin/zotero"),
            Path("/usr/local/bin/zotero"),
            Path("/snap/bin/zotero-snap"),
            Path.home() / ".local" / "bin" / "zotero",
        ]
    for c in candidates:
        if c.exists():
            return c
    return None


def is_zotero_running() -> bool:
    """
    [TR] Zotero'nun şu anda açık olup olmadığını kontrol eder (Port 23119 ve süreç kontrolü).
    [EN] Checks whether Zotero is currently running (via local port 23119 and OS process table).
    """
    # [TR] Önce Zotero yerel sunucu portu 23119 kontrolü
    # [EN] First check Zotero local HTTP connector port 23119
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.35)
    try:
        if s.connect_ex(("127.0.0.1", 23119)) == 0:
            return True
    except Exception:
        pass
    finally:
        s.close()

    sys_name = platform.system().lower()
    try:
        if sys_name == "windows":
            res = subprocess.run(["tasklist", "/FI", "IMAGENAME eq zotero.exe"], capture_output=True, text=True)
            return "zotero.exe" in res.stdout.lower()
        else:
            res = subprocess.run(["pgrep", "-f", "zotero"], capture_output=True, text=True)
            return res.returncode == 0
    except Exception:
        return False


def stop_zotero_gracefully(timeout_sec: float = 10.0) -> bool:
    """
    [TR] Zotero açıksa veritabanı kilidini güvenli şekilde bırakması için kapatır.
    [EN] Gracefully closes Zotero if running so SQLite database locks and WAL files are flushed.
    """
    if not is_zotero_running():
        return True
    sys_name = platform.system().lower()
    if sys_name == "windows":
        subprocess.run(["taskkill", "/IM", "zotero.exe"], check=False, capture_output=True)
    else:
        subprocess.run(["pkill", "-TERM", "-f", "zotero"], check=False, capture_output=True)

    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if not is_zotero_running():
            time.sleep(0.4)
            return True
        time.sleep(0.4)

    # [TR] Zaman aşımında zorla kapatma (Yedek koruma)
    # [EN] Force kill on timeout (Fallback protection)
    if sys_name == "windows":
        subprocess.run(["taskkill", "/F", "/IM", "zotero.exe"], check=False, capture_output=True)
    else:
        subprocess.run(["pkill", "-KILL", "-f", "zotero"], check=False, capture_output=True)
    time.sleep(0.8)
    return not is_zotero_running()


def start_zotero() -> bool:
    """
    [TR] Zotero'yu arka planda yeniden başlatır.
    [EN] Relaunches the Zotero desktop application in the background.
    """
    exe = find_zotero_executable()
    if exe and exe.exists():
        try:
            subprocess.Popen([str(exe)], close_fds=True)
            return True
        except Exception:
            return False
    return False
