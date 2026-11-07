#!/usr/bin/env python3
"""
[TR] Zotero Derlem ve Sınıflandırma Yöneticisi — Ana Giriş Noktası (Görsel Web Arayüzü & CLI).
     Argümansız çalıştırıldığında (veya `python zotero_cli.py gui` ile) yazılım bilgisi
     gerektirmeyen iki dilli (TR/EN) görsel Web Arayüzünü başlatır.
[EN] Zotero Corpus & Classification Manager — Main Entry Point (Visual Web UI & CLI).
     When executed without arguments (or via `python zotero_cli.py gui`), launches the
     zero-coding-required bilingual (TR/EN) Visual Web Dashboard.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from zotero_manager.applier import apply_classification_sqlite, create_backup, list_backups, restore_backup
from zotero_manager.classifier import classify_library
from zotero_manager.deduplicator import execute_deduplication, find_duplicate_clusters
from zotero_manager.detector import find_zotero_data_dir, is_zotero_running, start_zotero, stop_zotero_gracefully
from zotero_manager.reader import load_library_snapshot
from zotero_manager.reporter import compute_summary_stats, generate_csv_report, generate_markdown_report
from zotero_manager.web_ui import launch_web_ui


def main() -> None:
    """
    [TR] Komut satırı argümanlarını ayrıştırır ve ilgili modülü (gui, scan, classify, dedup, backups, restore) çalıştırır.
    [EN] Parses command-line arguments and dispatches the requested command (gui, scan, classify, dedup, backups, restore).
    """
    ap = argparse.ArgumentParser(
        description=(
            "[TR] Zotero Otomatik Sınıflandırma, Derlem Denetimi ve Akıllı Mükerrer Birleştirici | "
            "[EN] Zotero Automatic Classification, Corpus Auditing & Smart Deduplication Tool"
        )
    )
    ap.add_argument(
        "--zdir",
        type=Path,
        default=None,
        help="[TR] Zotero veri dizini (varsayılan: otomatik tespit) / [EN] Zotero data directory (default: auto-detect)",
    )
    sub = ap.add_subparsers(dest="cmd")

    # 1. GUI (Web Dashboard)
    p_gui = sub.add_parser(
        "gui",
        help="[TR] Görsel Web Arayüzünü başlatır (Varsayılan) / [EN] Launch Visual Web Dashboard (Default)",
    )
    p_gui.add_argument("--port", type=int, default=8765, help="[TR] Port (8765) / [EN] Server port (8765)")
    p_gui.add_argument("--no-browser", action="store_true", help="[TR] Tarayıcıyı otomatik açma / [EN] Do not open browser")

    # 2. Scan (Read-Only Audit & Reports)
    p_scan = sub.add_parser(
        "scan",
        help="[TR] Kütüphaneyi salt-okunur tarar ve rapor üretir / [EN] Scan library read-only and generate reports",
    )
    p_scan.add_argument("--out-md", type=Path, default=Path("reports/zotero_derlem_raporu.md"))
    p_scan.add_argument("--out-csv", type=Path, default=Path("reports/zotero_siniflandirma.csv"))
    p_scan.add_argument("--out-json", type=Path, default=Path("reports/zotero_siniflandirma.json"))

    # 3. Classify (Apply Collections, Tags & ISO Language Fixes)
    p_cls = sub.add_parser(
        "classify",
        help="[TR] Koleksiyon, etiket ve dil düzeltmelerini uygular / [EN] Apply collections, tags, and language fixes",
    )
    p_cls.add_argument("--no-collections", action="store_true", help="[TR] Koleksiyonları atla / [EN] Skip collections")
    p_cls.add_argument("--no-tags", action="store_true", help="[TR] Etiketleri atla / [EN] Skip tags")
    p_cls.add_argument("--no-lang-fix", action="store_true", help="[TR] Dil düzeltmeyi atla / [EN] Skip language fixes")
    p_cls.add_argument("--no-restart", action="store_true", help="[TR] Zotero'yu kapatıp açma / [EN] Do not restart Zotero")

    # 4. Dedup (Smart Duplicate Merging & Single-File Consolidation)
    p_dedup = sub.add_parser(
        "dedup",
        help="[TR] Mükerrerleri en zengin kaynakçayla birleştirir / [EN] Merge duplicates into richest bibliography & single PDF",
    )
    p_dedup.add_argument("--dry-run", action="store_true", help="[TR] Sadece planı göster / [EN] Dry-run preview only")
    p_dedup.add_argument("--no-restart", action="store_true", help="[TR] Zotero'yu kapatıp açma / [EN] Do not restart Zotero")

    # 5. Backups & Restore
    sub.add_parser("backups", help="[TR] Mevcut veritabanı yedeklerini listeler / [EN] List database backups")

    p_rest = sub.add_parser("restore", help="[TR] Yedek dosyasını geri yükler / [EN] Restore a .bak database backup")
    p_rest.add_argument("backup_file", type=Path, help="[TR] .bak dosya yolu / [EN] Path to .bak file")

    args = ap.parse_args()
    zdir = find_zotero_data_dir(args.zdir)

    if not args.cmd or args.cmd == "gui":
        port = getattr(args, "port", 8765)
        open_br = not getattr(args, "no_browser", False)
        launch_web_ui(zdir=zdir, port=port, open_browser=open_br)
        return

    if args.cmd == "scan":
        print(f"[1/2] [TR] Zotero kütüphanesi taranıyor / [EN] Scanning Zotero library ({zdir})...")
        entries = load_library_snapshot(zdir, compute_hashes=False)
        results = classify_library(entries)
        stats = compute_summary_stats(results)
        print(json.dumps(stats, ensure_ascii=False, indent=2))

        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(generate_markdown_report(zdir, results), encoding="utf-8")
        args.out_csv.write_text(generate_csv_report(results), encoding="utf-8")
        args.out_json.write_text(json.dumps(list(results.values()), ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            f"[2/2] [TR] Raporlar kaydedildi / [EN] Reports saved:\n"
            f"  - {args.out_md}\n  - {args.out_csv}\n  - {args.out_json}"
        )

    elif args.cmd == "classify":
        entries = load_library_snapshot(zdir, compute_hashes=False)
        results = classify_library(entries)
        was_running = is_zotero_running()
        if was_running and not args.no_restart:
            print("[TR] Zotero güvenli şekilde kapatılıyor... / [EN] Stopping Zotero gracefully...")
            stop_zotero_gracefully()
        summary = apply_classification_sqlite(
            zdir,
            entries,
            results,
            apply_collections=not args.no_collections,
            apply_tags=not args.no_tags,
            fix_languages=not args.no_lang_fix,
        )
        print("[TR] Sınıflandırma tamamlandı / [EN] Classification complete:", json.dumps(summary, ensure_ascii=False, indent=2))
        if was_running and not args.no_restart:
            start_zotero()

    elif args.cmd == "dedup":
        entries = load_library_snapshot(zdir, compute_hashes=True)
        clusters = find_duplicate_clusters(entries)
        total_losers = sum(len(c["loser_ids"]) for c in clusters)
        freed_mb = round(sum(c["freed_bytes"] for c in clusters) / (1024 * 1024), 2)
        print(
            f"[TR] Tespit edilen mükerrer küme: {len(clusters)} (Kopya: {total_losers}, Alan: {freed_mb} MB) / "
            f"[EN] Duplicate clusters found: {len(clusters)} (Copies: {total_losers}, Space: {freed_mb} MB)"
        )
        if args.dry_run or not clusters:
            return
        was_running = is_zotero_running()
        if was_running and not args.no_restart:
            print("[TR] Zotero güvenli şekilde kapatılıyor... / [EN] Stopping Zotero gracefully...")
            stop_zotero_gracefully()
        summary = execute_deduplication(zdir, clusters, entries)
        print("[TR] Mükerrer birleştirme tamamlandı / [EN] Deduplication complete:", json.dumps(summary, ensure_ascii=False, indent=2))
        if was_running and not args.no_restart:
            start_zotero()

    elif args.cmd == "backups":
        for b in list_backups(zdir):
            print(f"{b['modified']} | {b['size_mb']:6.2f} MB | {b['path']}")

    elif args.cmd == "restore":
        was_running = is_zotero_running()
        if was_running:
            stop_zotero_gracefully()
        restored = restore_backup(zdir, args.backup_file)
        print(f"[TR] Yedek geri yüklendi / [EN] Backup restored: {restored}")
        if was_running:
            start_zotero()


if __name__ == "__main__":
    main()
