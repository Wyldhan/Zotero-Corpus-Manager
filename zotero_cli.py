#!/usr/bin/env python3
"""Zotero Derlem ve Sınıflandırma Yöneticisi — Ana Giriş Noktası (GUI & CLI).

Argümansız çalıştırıldığında (veya `python zotero_cli.py gui` ile) yazılım bilgisi
gerektirmeyen görsel Web Arayüzünü başlatır.
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
    ap = argparse.ArgumentParser(
        description="Zotero Otomatik Sınıflandırma, Derlem Denetimi ve Akıllı Mükerrer Birleştirici"
    )
    ap.add_argument("--zdir", type=Path, default=None, help="Zotero veri dizini (varsayılan: otomatik tespit)")
    sub = ap.add_subparsers(dest="cmd")

    p_gui = sub.add_parser("gui", help="Görsel Web Arayüzünü (Dashboard) başlatır (Varsayılan)")
    p_gui.add_argument("--port", type=int, default=8765, help="Web sunucu portu (varsayılan: 8765)")
    p_gui.add_argument("--no-browser", action="store_true", help="Tarayıcıyı otomatik açma")

    p_scan = sub.add_parser("scan", help="Kütüphaneyi salt-okunur tarar ve rapor üretir")
    p_scan.add_argument("--out-md", type=Path, default=Path("reports/zotero_derlem_raporu.md"))
    p_scan.add_argument("--out-csv", type=Path, default=Path("reports/zotero_siniflandirma.csv"))
    p_scan.add_argument("--out-json", type=Path, default=Path("reports/zotero_siniflandirma.json"))

    p_cls = sub.add_parser("classify", help="Otomatik koleksiyon, etiket ve dil düzeltmelerini Zotero'ya uygular")
    p_cls.add_argument("--no-collections", action="store_true", help="Koleksiyonları güncelleme")
    p_cls.add_argument("--no-tags", action="store_true", help="Etiketleri ekleme")
    p_cls.add_argument("--no-lang-fix", action="store_true", help="Dil kodlarını düzeltme")
    p_cls.add_argument("--no-restart", action="store_true", help="Zotero'yu otomatik kapatıp açma")

    p_dedup = sub.add_parser("dedup", help="Mükerrer kayıtları en kapsamlı kaynakçayla birleştirir ve tek dosyaya indirir")
    p_dedup.add_argument("--dry-run", action="store_true", help="Sadece birleştirme planını göster, silme yapma")
    p_dedup.add_argument("--no-restart", action="store_true", help="Zotero'yu otomatik kapatıp açma")

    sub.add_parser("backups", help="Mevcut veritabanı yedeklerini listeler")

    p_rest = sub.add_parser("restore", help="Belirtilen yedek dosyasını geri yükler")
    p_rest.add_argument("backup_file", type=Path, help="Geri yüklenecek .bak dosyası")

    args = ap.parse_args()
    zdir = find_zotero_data_dir(args.zdir)

    if not args.cmd or args.cmd == "gui":
        port = getattr(args, "port", 8765)
        open_br = not getattr(args, "no_browser", False)
        launch_web_ui(zdir=zdir, port=port, open_browser=open_br)
        return

    if args.cmd == "scan":
        print(f"[1/2] Zotero kütüphanesi taranıyor ({zdir})...")
        entries = load_library_snapshot(zdir, compute_hashes=False)
        results = classify_library(entries)
        stats = compute_summary_stats(results)
        print(json.dumps(stats, ensure_ascii=False, indent=2))

        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(generate_markdown_report(zdir, results), encoding="utf-8")
        args.out_csv.write_text(generate_csv_report(results), encoding="utf-8")
        args.out_json.write_text(json.dumps(list(results.values()), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[2/2] Raporlar kaydedildi:\n  - {args.out_md}\n  - {args.out_csv}\n  - {args.out_json}")

    elif args.cmd == "classify":
        entries = load_library_snapshot(zdir, compute_hashes=False)
        results = classify_library(entries)
        was_running = is_zotero_running()
        if was_running and not args.no_restart:
            print("Zotero güvenli şekilde kapatılıyor...")
            stop_zotero_gracefully()
        summary = apply_classification_sqlite(
            zdir,
            entries,
            results,
            apply_collections=not args.no_collections,
            apply_tags=not args.no_tags,
            fix_languages=not args.no_lang_fix,
        )
        print("Sınıflandırma tamamlandı:", json.dumps(summary, ensure_ascii=False, indent=2))
        if was_running and not args.no_restart:
            start_zotero()

    elif args.cmd == "dedup":
        entries = load_library_snapshot(zdir, compute_hashes=True)
        clusters = find_duplicate_clusters(entries)
        total_losers = sum(len(c["loser_ids"]) for c in clusters)
        freed_mb = round(sum(c["freed_bytes"] for c in clusters) / (1024 * 1024), 2)
        print(f"Tespit edilen mükerrer küme: {len(clusters)} (Silinecek kopya: {total_losers}, Kazanılacak alan: {freed_mb} MB)")
        if args.dry_run or not clusters:
            return
        was_running = is_zotero_running()
        if was_running and not args.no_restart:
            print("Zotero güvenli şekilde kapatılıyor...")
            stop_zotero_gracefully()
        summary = execute_deduplication(zdir, clusters, entries)
        print("Mükerrer birleştirme tamamlandı:", json.dumps(summary, ensure_ascii=False, indent=2))
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
        print(f"Yedek geri yüklendi: {restored}")
        if was_running:
            start_zotero()


if __name__ == "__main__":
    main()
