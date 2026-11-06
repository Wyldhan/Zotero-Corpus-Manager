"""Zotero Veritabanı Yedekleme, Geri Yükleme ve Sınıflandırma Uygulama Motoru."""
from __future__ import annotations

import random
import re
import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ZOTERO_KEY_CHARS = "23456789ABCDEFGHIJKLMNPQRSTUVWXYZ"


def gen_zotero_key(existing: set[str]) -> str:
    while True:
        k = "".join(random.choice(ZOTERO_KEY_CHARS) for _ in range(8))
        if k not in existing:
            existing.add(k)
            return k


def create_backup(zdir: Path, label: str = "backup", backup_dir: Path | None = None) -> Path:
    """Zotero veritabanının tarih-saat damgalı tam yedeğini alır."""
    db_path = zdir / "zotero.sqlite"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = backup_dir or zdir
    target_dir.mkdir(parents=True, exist_ok=True)
    bak_file = target_dir / f"zotero.sqlite.{label}_{ts}.bak"
    shutil.copy2(db_path, bak_file)
    return bak_file


def list_backups(zdir: Path, backup_dir: Path | None = None) -> list[dict]:
    """Mevcut veritabanı yedeklerini listeler."""
    dirs = [zdir]
    if backup_dir and backup_dir != zdir and backup_dir.exists():
        dirs.append(backup_dir)
    found = []
    seen = set()
    for d in dirs:
        for p in d.glob("zotero.sqlite*.bak"):
            if p.resolve() in seen:
                continue
            seen.add(p.resolve())
            st = p.stat()
            found.append({
                "name": p.name,
                "path": str(p.resolve()),
                "size_mb": round(st.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "mtime": st.st_mtime,
            })
    found.sort(key=lambda x: x["mtime"], reverse=True)
    return found


def restore_backup(zdir: Path, backup_path: str | Path) -> Path:
    """Seçilen yedek dosyasını aktif zotero.sqlite olarak geri yükler."""
    src = Path(backup_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Yedek dosyası bulunamadı: {src}")
    db_path = zdir / "zotero.sqlite"
    create_backup(zdir, label="before_restore")
    for ext in ["-wal", "-shm"]:
        wal = zdir / f"zotero.sqlite{ext}"
        if wal.exists():
            wal.unlink(missing_ok=True)
    shutil.copy2(src, db_path)
    return db_path


def build_collection_plan(
    entries: dict[int, dict],
    results: dict[int, dict],
) -> tuple[list[tuple[str, str | None]], dict[tuple[str, str | None], list[int]]]:
    """Koleksiyon ağacını ve her koleksiyona eklenecek itemID listesini oluşturur."""
    col_defs: list[tuple[str, str | None]] = [
        ("Makaleler", None),
        ("Rojname u kovargeri", "Makaleler"),
        ("TALLIP", "Makaleler"),
        ("Morphology-Kurdî", None),
        ("NLP-Kurdî", None),
        ("Sempozyum-Allomorf", None),
        ("Söylem Analizi", None),
        ("Zazakî-Gramer", None),
        ("01-Gramer, Morfoloji & Sesbilim (Zazakî)", "Zazakî-Gramer"),
        ("02-Sözlük, Sözvarlığı & Etimoloji (Zazakî)", "Zazakî-Gramer"),
        ("03-Diyalektoloji & Ağızlar (Zazakî)", "Zazakî-Gramer"),
        ("04-Edebiyat, Folklor & Toplumdilbilim (Zazakî)", "Zazakî-Gramer"),
        ("05-Kirmanckî Yazılmış Eserler", "Zazakî-Gramer"),
        ("1. Derlemler & Hedef Diller", None),
        ("1.1 Zazakî / Kirmanckî Derlemi", "1. Derlemler & Hedef Diller"),
        ("1.2 Kurmancî Derlemi", "1. Derlemler & Hedef Diller"),
        ("1.3 Soranî, Goranî & Güney Kürtçesi", "1. Derlemler & Hedef Diller"),
        ("1.4 Kürdoloji (Genel & Karşılaştırmalı)", "1. Derlemler & Hedef Diller"),
        ("1.5 İrani Diller & Hint-İran", "1. Derlemler & Hedef Diller"),
        ("1.6 Türkçe & Türkoloji Derlemi", "1. Derlemler & Hedef Diller"),
        ("1.7 Genel Dilbilim & Dünya Dilleri", "1. Derlemler & Hedef Diller"),
        ("2. Metin Diline Göre", None),
        ("Dil: Kirmanckî (Zazakî)", "2. Metin Diline Göre"),
        ("Dil: Kurmancî", "2. Metin Diline Göre"),
        ("Dil: Soranî (Arap-Kürt Alfabesi)", "2. Metin Diline Göre"),
        ("Dil: Türkçe", "2. Metin Diline Göre"),
        ("Dil: İngilizce", "2. Metin Diline Göre"),
        ("Dil: Almanca", "2. Metin Diline Göre"),
        ("Dil: Fransızca", "2. Metin Diline Göre"),
        ("Dil: Farsça & Arapça", "2. Metin Diline Göre"),
        ("3. Eser Türüne Göre", None),
        ("Tür: Sözlükler & Leksikografi", "3. Eser Türüne Göre"),
        ("Tür: Gramer Kitapları & İmla", "3. Eser Türüne Göre"),
        ("Tür: Tezler (YL & Doktora)", "3. Eser Türüne Göre"),
        ("Tür: Edebi Metinler & Folklor", "3. Eser Türüne Göre"),
        ("Tür: Dergi & Gazete Sayıları", "3. Eser Türüne Göre"),
        ("Tür: Akademik Kitap & Bölümler", "3. Eser Türüne Göre"),
        ("Tür: Hakemli Makaleler", "3. Eser Türüne Göre"),
        ("Tür: Sempozyum Bildirileri", "3. Eser Türüne Göre"),
        ("Tür: Ön Baskı (arXiv) & Raporlar", "3. Eser Türüne Göre"),
        ("4. Konu & Alt Alanlara Göre", None),
        ("Konu: Morfoloji, Allomorfi & Ergativite", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Fonoloji, Sesbilim & Morfonoloji", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Sözdizimi (Syntax) & Tipoloji", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Anlambilim, Kip-Zaman & Edat/Zarf", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Sözlükbilim, Sözvarlığı & Etimoloji", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Derlem Dilbilimi (Corpus Linguistics)", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Doğal Dil İşleme (NLP) & Hesaplamalı", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Söylem, Toplumdilbilim & Çeviri", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Diyalektoloji & Ağız Araştırmaları", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Dil Eğitimi & Öğretimi", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Edebiyat, Tarih & Kültür", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Genel Dilbilim & Kuramsal", "4. Konu & Alt Alanlara Göre"),
        ("Konu: Alan Dışı / Diğer Disiplinler", "4. Konu & Alt Alanlara Göre"),
        ("5. Derlem Denetim & Kalite Kontrol", None),
        ("⚠️ 1-Mükerrer (Duplicate) Adayları", "5. Derlem Denetim & Kalite Kontrol"),
        ("⚠️ 2-Üst Kaydı Olmayan (Standalone) PDF'ler", "5. Derlem Denetim & Kalite Kontrol"),
        ("⚠️ 3-Fiziksel Dosyası Eksik Kayıtlar", "5. Derlem Denetim & Kalite Kontrol"),
        ("⚠️ 4-Metin Katmanı Olmayan (OCR Gereken) PDF'ler", "5. Derlem Denetim & Kalite Kontrol"),
        ("⚠️ 5-Dil Kodu Hatalı ('en' yazılıp TR/KU/ZZ olanlar)", "5. Derlem Denetim & Kalite Kontrol"),
    ]

    derlem_col = {
        "zazaki-kirmancki": ("1.1 Zazakî / Kirmanckî Derlemi", "1. Derlemler & Hedef Diller"),
        "kurmanci": ("1.2 Kurmancî Derlemi", "1. Derlemler & Hedef Diller"),
        "sorani-gorani": ("1.3 Soranî, Goranî & Güney Kürtçesi", "1. Derlemler & Hedef Diller"),
        "kurdoloji-genel": ("1.4 Kürdoloji (Genel & Karşılaştırmalı)", "1. Derlemler & Hedef Diller"),
        "irani-diller": ("1.5 İrani Diller & Hint-İran", "1. Derlemler & Hedef Diller"),
        "turkce-turkoloji": ("1.6 Türkçe & Türkoloji Derlemi", "1. Derlemler & Hedef Diller"),
        "genel-dilbilim": ("1.7 Genel Dilbilim & Dünya Dilleri", "1. Derlemler & Hedef Diller"),
    }
    dil_col = {
        "kirmancki": ("Dil: Kirmanckî (Zazakî)", "2. Metin Diline Göre"),
        "kurmanci": ("Dil: Kurmancî", "2. Metin Diline Göre"),
        "sorani": ("Dil: Soranî (Arap-Kürt Alfabesi)", "2. Metin Diline Göre"),
        "turkce": ("Dil: Türkçe", "2. Metin Diline Göre"),
        "ingilizce": ("Dil: İngilizce", "2. Metin Diline Göre"),
        "almanca": ("Dil: Almanca", "2. Metin Diline Göre"),
        "fransizca": ("Dil: Fransızca", "2. Metin Diline Göre"),
        "farsca-arapca": ("Dil: Farsça & Arapça", "2. Metin Diline Göre"),
    }
    tur_col = {
        "sozluk": ("Tür: Sözlükler & Leksikografi", "3. Eser Türüne Göre"),
        "gramer": ("Tür: Gramer Kitapları & İmla", "3. Eser Türüne Göre"),
        "tez": ("Tür: Tezler (YL & Doktora)", "3. Eser Türüne Göre"),
        "edebi-folklor": ("Tür: Edebi Metinler & Folklor", "3. Eser Türüne Göre"),
        "dergi-gazete": ("Tür: Dergi & Gazete Sayıları", "3. Eser Türüne Göre"),
        "kitap-bolum": ("Tür: Akademik Kitap & Bölümler", "3. Eser Türüne Göre"),
        "makale": ("Tür: Hakemli Makaleler", "3. Eser Türüne Göre"),
        "bildiri": ("Tür: Sempozyum Bildirileri", "3. Eser Türüne Göre"),
        "onbaski-rapor": ("Tür: Ön Baskı (arXiv) & Raporlar", "3. Eser Türüne Göre"),
    }
    konu_col = {
        "morfoloji-allomorfi": ("Konu: Morfoloji, Allomorfi & Ergativite", "4. Konu & Alt Alanlara Göre"),
        "fonoloji-sesbilim": ("Konu: Fonoloji, Sesbilim & Morfonoloji", "4. Konu & Alt Alanlara Göre"),
        "sozdizimi-tipoloji": ("Konu: Sözdizimi (Syntax) & Tipoloji", "4. Konu & Alt Alanlara Göre"),
        "anlambilim-kip-zaman": ("Konu: Anlambilim, Kip-Zaman & Edat/Zarf", "4. Konu & Alt Alanlara Göre"),
        "sozlukbilim-etimoloji": ("Konu: Sözlükbilim, Sözvarlığı & Etimoloji", "4. Konu & Alt Alanlara Göre"),
        "derlem-dilbilimi": ("Konu: Derlem Dilbilimi (Corpus Linguistics)", "4. Konu & Alt Alanlara Göre"),
        "nlp-hesaplamali": ("Konu: Doğal Dil İşleme (NLP) & Hesaplamalı", "4. Konu & Alt Alanlara Göre"),
        "soylem-toplumdilbilim": ("Konu: Söylem, Toplumdilbilim & Çeviri", "4. Konu & Alt Alanlara Göre"),
        "diyalektoloji-agiz": ("Konu: Diyalektoloji & Ağız Araştırmaları", "4. Konu & Alt Alanlara Göre"),
        "dil-egitimi": ("Konu: Dil Eğitimi & Öğretimi", "4. Konu & Alt Alanlara Göre"),
        "edebiyat-tarih-kultur": ("Konu: Edebiyat, Tarih & Kültür", "4. Konu & Alt Alanlara Göre"),
        "genel-dilbilim-kuram": ("Konu: Genel Dilbilim & Kuramsal", "4. Konu & Alt Alanlara Göre"),
        "alan-disi": ("Konu: Alan Dışı / Diğer Disiplinler", "4. Konu & Alt Alanlara Göre"),
    }
    kontrol_col = {
        "mukerrer-aday": ("⚠️ 1-Mükerrer (Duplicate) Adayları", "5. Derlem Denetim & Kalite Kontrol"),
        "ust-kayitsiz-pdf": ("⚠️ 2-Üst Kaydı Olmayan (Standalone) PDF'ler", "5. Derlem Denetim & Kalite Kontrol"),
        "eksik-dosya": ("⚠️ 3-Fiziksel Dosyası Eksik Kayıtlar", "5. Derlem Denetim & Kalite Kontrol"),
        "ocr-gerekli": ("⚠️ 4-Metin Katmanı Olmayan (OCR Gereken) PDF'ler", "5. Derlem Denetim & Kalite Kontrol"),
        "dil-kodu-hatali": ("⚠️ 5-Dil Kodu Hatalı ('en' yazılıp TR/KU/ZZ olanlar)", "5. Derlem Denetim & Kalite Kontrol"),
    }

    plan: dict[tuple[str, str | None], list[int]] = defaultdict(list)

    for iid, r in results.items():
        e = entries[iid]
        pub_lower = (e["fields"].get("publicationTitle", "") or "").lower()
        title_lower = r["title"].lower()

        if r["doc_lang"] in dil_col:
            plan[dil_col[r["doc_lang"]]].append(iid)
        for d in r["derlem"]:
            if d in derlem_col:
                plan[derlem_col[d]].append(iid)
        if r["tur"] in tur_col:
            plan[tur_col[r["tur"]]].append(iid)
        for k in r["konular"]:
            if k in konu_col:
                plan[konu_col[k]].append(iid)
        for c in r["kontroller"]:
            if c in kontrol_col:
                plan[kontrol_col[c]].append(iid)

        is_kurdish_or_iranian = any(
            d in ("zazaki-kirmancki", "kurmanci", "sorani-gorani", "kurdoloji-genel", "irani-diller")
            for d in r["derlem"]
        )
        if "zazaki-kirmancki" in r["derlem"]:
            plan[("Zazakî-Gramer", None)].append(iid)
            if r["doc_lang"] == "kirmancki":
                plan[("05-Kirmanckî Yazılmış Eserler", "Zazakî-Gramer")].append(iid)
            if any(k in ("morfoloji-allomorfi", "fonoloji-sesbilim", "sozdizimi-tipoloji", "anlambilim-kip-zaman") for k in r["konular"]) or r["tur"] == "gramer":
                plan[("01-Gramer, Morfoloji & Sesbilim (Zazakî)", "Zazakî-Gramer")].append(iid)
            if "sozlukbilim-etimoloji" in r["konular"] or r["tur"] == "sozluk":
                plan[("02-Sözlük, Sözvarlığı & Etimoloji (Zazakî)", "Zazakî-Gramer")].append(iid)
            if "diyalektoloji-agiz" in r["konular"]:
                plan[("03-Diyalektoloji & Ağızlar (Zazakî)", "Zazakî-Gramer")].append(iid)
            if any(k in ("edebiyat-tarih-kultur", "soylem-toplumdilbilim", "dil-egitimi") for k in r["konular"]) or r["tur"] in ("edebi-folklor", "dergi-gazete"):
                plan[("04-Edebiyat, Folklor & Toplumdilbilim (Zazakî)", "Zazakî-Gramer")].append(iid)

        if is_kurdish_or_iranian and any(k in ("morfoloji-allomorfi", "fonoloji-sesbilim") for k in r["konular"]):
            plan[("Morphology-Kurdî", None)].append(iid)

        if is_kurdish_or_iranian and any(k in ("nlp-hesaplamali", "derlem-dilbilimi") for k in r["konular"]):
            plan[("NLP-Kurdî", None)].append(iid)

        if re.search(
            r"\b(allomorf\w*|allomorph\w*|morfonolo\w*|morphophon\w*|ergativ\w*|ergatîv\w*|hal\s+eki|durum\s+eki|büküm|case\s+marking|inflectional)\b",
            title_lower + " " + (e["fields"].get("abstractNote", "") or "").lower(),
        ):
            plan[("Sempozyum-Allomorf", None)].append(iid)

        if "soylem-toplumdilbilim" in r["konular"]:
            plan[("Söylem Analizi", None)].append(iid)

        if r["tur"] == "dergi-gazete" or re.search(r"\b(rojname\w*|kovar\w*|gazete\w*|journalism|basın|medya|press)\b", title_lower):
            plan[("Rojname u kovargeri", "Makaleler")].append(iid)

        if "tallip" in pub_lower or "asian and low-resource" in pub_lower or "low-resource" in title_lower:
            plan[("TALLIP", "Makaleler")].append(iid)

    return col_defs, plan


def apply_classification_sqlite(
    zdir: Path,
    entries: dict[int, dict],
    results: dict[int, dict],
    apply_collections: bool = True,
    apply_tags: bool = True,
    fix_languages: bool = True,
    backup_dir: Path | None = None,
) -> dict:
    """Sınıflandırma sonuçlarını doğrudan Zotero SQLite veritabanına yazar."""
    db_path = zdir / "zotero.sqlite"
    bak_file = create_backup(zdir, label="pre-classify", backup_dir=backup_dir)

    conn = sqlite3.connect(db_path, timeout=30.0)
    cur = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    existing_keys = {r[0] for r in cur.execute("SELECT key FROM items UNION SELECT key FROM collections")}

    created_cols = 0
    added_col_items = 0
    if apply_collections:
        col_defs, plan = build_collection_plan(entries, results)
        col_id_by_name_parent: dict[tuple[str, int | None], int] = {}
        col_id_by_name_root: dict[str, int] = {}

        for cid, cname, pid in cur.execute("SELECT collectionID, collectionName, parentCollectionID FROM collections WHERE libraryID=1"):
            col_id_by_name_parent[(cname, pid)] = cid
            if pid is None:
                col_id_by_name_root[cname] = cid

        for cname, parent_name in col_defs:
            pid = col_id_by_name_root.get(parent_name) if parent_name else None
            if (cname, pid) not in col_id_by_name_parent:
                new_key = gen_zotero_key(existing_keys)
                cur.execute(
                    """
                    INSERT INTO collections (collectionName, parentCollectionID, clientDateModified, libraryID, key, version, synced, clientVersion)
                    VALUES (?, ?, ?, 1, ?, 0, 0, 0)
                    """,
                    (cname, pid, now_str, new_key),
                )
                cid = cur.lastrowid
                col_id_by_name_parent[(cname, pid)] = cid
                if pid is None:
                    col_id_by_name_root[cname] = cid
                created_cols += 1

        for (cname, parent_name), iids in plan.items():
            pid = col_id_by_name_root.get(parent_name) if parent_name else None
            cid = col_id_by_name_parent[(cname, pid)]
            existing_in_col = {r[0] for r in cur.execute("SELECT itemID FROM collectionItems WHERE collectionID=?", (cid,))}
            max_order = cur.execute("SELECT COALESCE(MAX(orderIndex), 0) FROM collectionItems WHERE collectionID=?", (cid,)).fetchone()[0]
            for iid in dict.fromkeys(iids):
                if iid not in existing_in_col:
                    max_order += 1
                    cur.execute(
                        "INSERT OR IGNORE INTO collectionItems (collectionID, itemID, orderIndex) VALUES (?, ?, ?)",
                        (cid, iid, max_order),
                    )
                    added_col_items += 1
            cur.execute("UPDATE collections SET clientDateModified=?, synced=0 WHERE collectionID=?", (now_str, cid))

    added_tags = 0
    if apply_tags:
        tag_id_map = {r[1]: r[0] for r in cur.execute("SELECT tagID, name FROM tags")}
        for iid, r in results.items():
            for tname in r["auto_tags"]:
                tid = tag_id_map.get(tname)
                if tid is None:
                    cur.execute("INSERT INTO tags (name, nameNormalized) VALUES (?, NULL)", (tname,))
                    tid = cur.lastrowid
                    tag_id_map[tname] = tid
                cur.execute("INSERT OR IGNORE INTO itemTags (itemID, tagID, type) VALUES (?, ?, 0)", (iid, tid))
                added_tags += cur.rowcount

    fixed_langs = 0
    if fix_languages:
        lang_field_id = cur.execute("SELECT fieldID FROM fields WHERE fieldName='language'").fetchone()[0]
        val_id_map = {
            r[1]: r[0]
            for r in cur.execute("SELECT valueID, value FROM itemDataValues WHERE value IN ('en','tr','zza','kmr','ckb','de','fr','fa')")
        }
        for iid, r in results.items():
            if r["itemType"] == "attachment":
                continue
            iso = r["expected_iso"]
            cur_lang = r["current_lang"]
            if not cur_lang or ("dil-kodu-hatali" in r["kontroller"]) or cur_lang in ("en.", 'scheme="iso639-1"', "eng"):
                vid = val_id_map.get(iso)
                if vid is None:
                    cur.execute("INSERT OR IGNORE INTO itemDataValues (value, valueNormalized) VALUES (?, NULL)", (iso,))
                    vid = cur.execute("SELECT valueID FROM itemDataValues WHERE value=?", (iso,)).fetchone()[0]
                    val_id_map[iso] = vid
                cur.execute("INSERT OR REPLACE INTO itemData (itemID, fieldID, valueID) VALUES (?, ?, ?)", (iid, lang_field_id, vid))
                cur.execute("UPDATE items SET clientDateModified=?, synced=0 WHERE itemID=?", (now_str, iid))
                fixed_langs += 1

    conn.commit()
    conn.close()
    return {
        "backup_file": str(bak_file),
        "created_collections": created_cols,
        "added_collection_links": added_col_items,
        "added_item_tags": added_tags,
        "fixed_language_fields": fixed_langs,
    }
