"""Markdown, Excel uyumlu CSV ve JSON Rapor Üretici."""
from __future__ import annotations

import csv
import io
import json
from collections import Counter
from pathlib import Path


def compute_summary_stats(results: dict[int, dict]) -> dict:
    """Web arayüzü ve raporlar için özet istatistikleri hesaplar."""
    total = len(results)
    standalone = sum(1 for r in results.values() if r["itemType"] == "attachment")
    regular = total - standalone

    c_dil = Counter(r["doc_lang"] for r in results.values())
    c_derlem = Counter(d for r in results.values() for d in r["derlem"])
    c_tur = Counter(r["tur"] for r in results.values())
    c_konu = Counter(k for r in results.values() for k in r["konular"])
    c_kontrol = Counter(c for r in results.values() for c in r["kontroller"])

    return {
        "total_items": total,
        "regular_items": regular,
        "standalone_pdfs": standalone,
        "by_language": dict(c_dil.most_common()),
        "by_corpus": dict(c_derlem.most_common()),
        "by_type": dict(c_tur.most_common()),
        "by_topic": dict(c_konu.most_common()),
        "by_audit": dict(c_kontrol.most_common()),
    }


def generate_markdown_report(zdir: Path, results: dict[int, dict]) -> str:
    stats = compute_summary_stats(results)
    lines = [
        "# Zotero Kütüphanesi Otomatik Sınıflandırma ve Derlem Denetim Raporu",
        "",
        f"- **Veritabanı Konumu**: `{zdir / 'zotero.sqlite'}`",
        f"- **Toplam Üst Seviye Kayıt**: **{stats['total_items']:,}** (`{stats['regular_items']:,}` bibliyografik kayıt + `{stats['standalone_pdfs']:,}` üst kaydı olmayan PDF)",
        "",
        "## 1. Hedef Dil ve Derlem Dağılımı (`1. Derlemler & Hedef Diller`)",
        "",
        "| Derlem / Hedef Dil Grubu | Etiket | Kayıt Sayısı |",
        "|---|---|---:|",
    ]
    for k, v in stats["by_corpus"].items():
        lines.append(f"| **{k}** | `#derlem:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 2. Metin Diline Göre Dağılım (`2. Metin Diline Göre`)",
        "",
        "| Metin Dili | Etiket | Kayıt Sayısı |",
        "|---|---|---:|",
    ])
    for k, v in stats["by_language"].items():
        lines.append(f"| **{k.title()}** | `#dil:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 3. Eser Türüne Göre Dağılım (`3. Eser Türüne Göre`)",
        "",
        "| Eser Türü | Etiket | Kayıt Sayısı |",
        "|---|---|---:|",
    ])
    for k, v in stats["by_type"].items():
        lines.append(f"| **{k}** | `#tur:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 4. Konu ve Alt Alan Dağılımı (`4. Konu & Alt Alanlara Göre`)",
        "",
        "| Konu / Alt Alan | Etiket | Kayıt Sayısı |",
        "|---|---|---:|",
    ])
    for k, v in stats["by_topic"].items():
        lines.append(f"| **{k}** | `#konu:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 5. Derlem Denetim & Kalite Kontrol Bulguları (`5. Derlem Denetim & Kalite Kontrol`)",
        "",
        "| Kontrol Kategorisi | Etiket | Tespit Edilen Kayıt |",
        "|---|---|---:|",
    ])
    for k, v in stats["by_audit"].items():
        lines.append(f"| **{k}** | `#kontrol:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 6. Metin Katmanı Olmayan (OCR Gereken) PDF'ler",
        "",
        "| Zotero Key | Derlem | Başlık |",
        "|---|---|---|",
    ])
    for r in results.values():
        if "ocr-gerekli" in r["kontroller"]:
            lines.append(f"| `{r['key']}` | `{', '.join(r['derlem'])}` | {r['title'].replace('|', '/')[:95]} |")

    return "\n".join(lines) + "\n"


def generate_csv_report(results: dict[int, dict]) -> str:
    """Excel ile doğrudan açılabilen UTF-8 BOM'lu CSV raporu üretir."""
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow([
        "Zotero Key",
        "Kayıt Türü",
        "Başlık",
        "Yazarlar",
        "Tarih",
        "DOI",
        "Metin Dili",
        "ISO Kodu",
        "Hedef Derlemler",
        "Eser Türü",
        "Konular",
        "Kalite Kontrolleri",
    ])
    for r in results.values():
        writer.writerow([
            r["key"],
            r["itemType"],
            r["title"],
            "; ".join(r.get("creators", [])),
            r.get("date", ""),
            r.get("DOI", ""),
            r["doc_lang"],
            r["expected_iso"],
            ", ".join(r["derlem"]),
            r["tur"],
            ", ".join(r["konular"]),
            ", ".join(r["kontroller"]),
        ])
    return buf.getvalue()
