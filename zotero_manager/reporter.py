"""
[TR] İki Dilli (TR/EN) Markdown, Excel uyumlu CSV ve JSON Rapor Üretici.
[EN] Bilingual (TR/EN) Markdown, Excel-compatible CSV, and JSON Report Generator.
"""
from __future__ import annotations

import csv
import io
from collections import Counter
from pathlib import Path


def compute_summary_stats(results: dict[int, dict]) -> dict:
    """
    [TR] Web arayüzü ve raporlar için 5 boyutlu özet istatistikleri hesaplar.
    [EN] Computes 5-dimensional summary statistics for the Web UI and reports.
    """
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
    """
    [TR] Kütüphanenin iki dilli (TR / EN) kapsamlı Markdown denetim raporunu üretir.
    [EN] Generates a comprehensive bilingual (TR / EN) Markdown audit report of the library.
    """
    stats = compute_summary_stats(results)
    lines = [
        "# Zotero Kütüphanesi Otomatik Sınıflandırma ve Derlem Denetim Raporu / Zotero Library Classification & Corpus Audit Report",
        "",
        f"- **Veritabanı Konumu / Database Path**: `{zdir / 'zotero.sqlite'}`",
        f"- **Toplam Üst Seviye Kayıt / Total Top-Level Items**: **{stats['total_items']:,}** (`{stats['regular_items']:,}` bibliyografik kayıt / bibliographic items + `{stats['standalone_pdfs']:,}` üst kayıtsız PDF / standalone PDFs)",
        "",
        "## 1. Hedef Dil ve Derlem Dağılımı / Target Language & Corpus Distribution (`1. Derlemler & Hedef Diller`)",
        "",
        "| Derlem / Target Corpus | Etiket / Tag | Kayıt Sayısı / Count |",
        "|---|---|---:|",
    ]
    for k, v in stats["by_corpus"].items():
        lines.append(f"| **{k}** | `#derlem:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 2. Metin Diline Göre Dağılım / Distribution by Document Language (`2. Metin Diline Göre`)",
        "",
        "| Metin Dili / Document Language | Etiket / Tag | Kayıt Sayısı / Count |",
        "|---|---|---:|",
    ])
    for k, v in stats["by_language"].items():
        lines.append(f"| **{k.title()}** | `#dil:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 3. Eser Türüne Göre Dağılım / Distribution by Item Type (`3. Eser Türüne Göre`)",
        "",
        "| Eser Türü / Item Type | Etiket / Tag | Kayıt Sayısı / Count |",
        "|---|---|---:|",
    ])
    for k, v in stats["by_type"].items():
        lines.append(f"| **{k}** | `#tur:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 4. Konu ve Alt Alan Dağılımı / Distribution by Research Topic (`4. Konu & Alt Alanlara Göre`)",
        "",
        "| Konu / Research Topic | Etiket / Tag | Kayıt Sayısı / Count |",
        "|---|---|---:|",
    ])
    for k, v in stats["by_topic"].items():
        lines.append(f"| **{k}** | `#konu:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 5. Derlem Denetim & Kalite Kontrol Bulguları / Quality Audit Findings (`5. Derlem Denetim & Kalite Kontrol`)",
        "",
        "| Kontrol Kategorisi / Audit Category | Etiket / Tag | Tespit Edilen Kayıt / Count |",
        "|---|---|---:|",
    ])
    for k, v in stats["by_audit"].items():
        lines.append(f"| **{k}** | `#kontrol:{k}` | **{v:,}** |")

    lines.extend([
        "",
        "## 6. Metin Katmanı Olmayan (OCR Gereken) PDF'ler / Scanned PDFs Requiring OCR",
        "",
        "| Zotero Key | Derlem / Corpus | Başlık / Title |",
        "|---|---|---|",
    ])
    for r in results.values():
        if "ocr-gerekli" in r["kontroller"]:
            lines.append(f"| `{r['key']}` | `{', '.join(r['derlem'])}` | {r['title'].replace('|', '/')[:95]} |")

    return "\n".join(lines) + "\n"


def generate_csv_report(results: dict[int, dict]) -> str:
    """
    [TR] Excel ile doğrudan açılabilen UTF-8 BOM'lu iki dilli CSV raporu üretir.
    [EN] Generates an Excel-compatible UTF-8 with BOM CSV report with bilingual column headers.
    """
    buf = io.StringIO()
    # [TR] Microsoft Excel'in Türkçe/Kürtçe karakterleri doğru açması için UTF-8 BOM ekle
    # [EN] Write UTF-8 BOM so Microsoft Excel opens Turkish/Kurdish characters properly
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow([
        "Zotero Key",
        "Kayıt Türü / Item Type",
        "Başlık / Title",
        "Yazarlar / Creators",
        "Tarih / Date",
        "DOI",
        "Metin Dili / Language",
        "ISO Kodu / ISO Code",
        "Hedef Derlemler / Target Corpora",
        "Eser Türü / Publication Type",
        "Konular / Topics",
        "Kalite Kontrolleri / Quality Audit",
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
