"""
[TR] Zotero SQLite veritabanı ve storage tam metin önbelleklerini güvenli (salt-okunur) okur.
[EN] Safely reads (read-only snapshot) the Zotero SQLite database and storage full-text caches.
"""
from __future__ import annotations

import hashlib
import shutil
import sqlite3
import tempfile
from pathlib import Path


def load_library_snapshot(zdir: Path, compute_hashes: bool = False) -> dict[int, dict]:
    """
    [TR] Zotero açık olsa bile WAL dosyalarıyla birlikte geçici kopya üzerinden tüm kayıtları okur.
    [EN] Reads all top-level items via a temporary snapshot (including WAL files) even while Zotero is open.
    """
    db_file = zdir / "zotero.sqlite"
    if not db_file.exists():
        raise FileNotFoundError(
            f"[TR] Zotero veritabanı bulunamadı / [EN] Zotero database not found: {db_file}"
        )

    tmp_dir = Path(tempfile.mkdtemp(prefix="zotero_mgr_"))
    try:
        # [TR] Veritabanı kilidini etkilememek için .sqlite, -wal ve -shm dosyalarını geçici dizine kopyala
        # [EN] Copy .sqlite, -wal, and -shm files to a temp directory to avoid locking the live database
        for ext in ["", "-wal", "-shm"]:
            src = zdir / f"zotero.sqlite{ext}"
            if src.exists():
                shutil.copy2(src, tmp_dir / f"zotero.sqlite{ext}")

        conn = sqlite3.connect(tmp_dir / "zotero.sqlite")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # [TR] 1. Tüm üst seviye kayıtları yükle (bibliyografik kayıtlar + üst kaydı olmayan PDF'ler)
        # [EN] 1. Load all top-level items (regular bibliographic items + standalone PDF attachments)
        entries: dict[int, dict] = {}
        for r in cur.execute("""
            SELECT i.itemID, i.key, it.typeName, i.dateAdded, i.dateModified
            FROM items i
            JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
            LEFT JOIN deletedItems di ON i.itemID = di.itemID
            WHERE di.itemID IS NULL
              AND i.libraryID = 1
              AND it.typeName NOT IN ('note', 'annotation')
              AND i.itemID NOT IN (SELECT itemID FROM itemNotes)
              AND i.itemID NOT IN (
                  SELECT itemID FROM itemAttachments WHERE parentItemID IS NOT NULL
              )
        """):
            entries[r["itemID"]] = {
                "itemID": r["itemID"],
                "key": r["key"],
                "itemType": r["typeName"],
                "dateAdded": r["dateAdded"],
                "dateModified": r["dateModified"],
                "fields": {},
                "creators": [],
                "collections": [],
                "tags": [],
                "attachments": [],
                "notes_count": 0,
            }

        # [TR] 2. Üst veri alanlarını (Başlık, Özet, DOI, Dergi, Tarih, Dil vb.) yükle
        # [EN] 2. Load metadata fields (Title, Abstract, DOI, Publication, Date, Language, etc.)
        for r in cur.execute("""
            SELECT id.itemID, f.fieldName, idv.value
            FROM itemData id
            JOIN fields f ON id.fieldID = f.fieldID
            JOIN itemDataValues idv ON id.valueID = idv.valueID
        """):
            if r["itemID"] in entries:
                entries[r["itemID"]]["fields"][r["fieldName"]] = r["value"]

        # [TR] 3. Yazar ve katkıda bulunanları (creators) sıralı yükle
        # [EN] 3. Load authors and contributors (creators) in order
        for r in cur.execute("""
            SELECT ic.itemID, c.firstName, c.lastName, ct.creatorType
            FROM itemCreators ic
            JOIN creators c ON ic.creatorID = c.creatorID
            JOIN creatorTypes ct ON ic.creatorTypeID = ct.creatorTypeID
            ORDER BY ic.itemID, ic.orderIndex
        """):
            if r["itemID"] in entries:
                entries[r["itemID"]]["creators"].append((r["creatorType"], r["lastName"] or "", r["firstName"] or ""))

        # [TR] 4. Mevcut koleksiyon üyeliklerini yükle
        # [EN] 4. Load existing collection memberships
        col_map = {
            r["collectionID"]: r["collectionName"]
            for r in cur.execute("SELECT collectionID, collectionName FROM collections WHERE libraryID=1")
        }
        for r in cur.execute("SELECT collectionID, itemID FROM collectionItems"):
            if r["itemID"] in entries and r["collectionID"] in col_map:
                entries[r["itemID"]]["collections"].append(col_map[r["collectionID"]])

        # [TR] 5. Mevcut etiketleri (tags) yükle
        # [EN] 5. Load existing item tags
        for r in cur.execute("""
            SELECT itg.itemID, t.name
            FROM itemTags itg
            JOIN tags t ON itg.tagID = t.tagID
        """):
            if r["itemID"] in entries:
                entries[r["itemID"]]["tags"].append(r["name"])

        # [TR] 6. Alt not sayılarını (itemNotes) yükle
        # [EN] 6. Load child note counts (itemNotes)
        for r in cur.execute("""
            SELECT parentItemID, COUNT(*) as cnt
            FROM itemNotes ino
            LEFT JOIN deletedItems di ON ino.itemID = di.itemID
            WHERE di.itemID IS NULL AND parentItemID IS NOT NULL
            GROUP BY parentItemID
        """):
            if r["parentItemID"] in entries:
                entries[r["parentItemID"]]["notes_count"] = r["cnt"]

        # [TR] 7. Ek dosyaları (PDF vb.), fiziksel dosya durumunu, SHA-256 özetini ve tam metin önbelleğini yükle
        # [EN] 7. Load attachments (PDFs, etc.), physical file status, SHA-256 hash, and full-text cache sample
        for r in cur.execute("""
            SELECT ia.itemID as attID, ia.parentItemID, ia.linkMode, ia.contentType, ia.path,
                   i.key as attKey, ft.indexedPages, ft.totalPages, ft.indexedChars,
                   (SELECT COUNT(*) FROM itemAnnotations ian
                    LEFT JOIN deletedItems di2 ON ian.itemID = di2.itemID
                    WHERE ian.parentItemID = ia.itemID AND di2.itemID IS NULL) as ann_cnt
            FROM itemAttachments ia
            JOIN items i ON ia.itemID = i.itemID
            LEFT JOIN deletedItems di ON ia.itemID = di.itemID
            LEFT JOIN fulltextItems ft ON ia.itemID = ft.itemID
            WHERE di.itemID IS NULL
        """):
            target_id = r["parentItemID"] if r["parentItemID"] is not None else r["attID"]
            if target_id not in entries:
                continue
            p_str = r["path"] or ""
            real_path = None
            if p_str.startswith("storage:"):
                real_path = zdir / "storage" / r["attKey"] / p_str[len("storage:"):]
            elif p_str:
                real_path = Path(p_str)
            exists = bool(real_path and real_path.exists() and real_path.is_file())
            size = real_path.stat().st_size if exists else 0
            sha256 = None
            if compute_hashes and exists and size > 0:
                h = hashlib.sha256()
                try:
                    with open(real_path, "rb") as f:
                        while chunk := f.read(65536):
                            h.update(chunk)
                    sha256 = h.hexdigest()
                except Exception:
                    sha256 = None

            cache_file = zdir / "storage" / r["attKey"] / ".zotero-ft-cache"
            ft_text = ""
            if cache_file.exists():
                try:
                    ft_text = cache_file.read_text(encoding="utf-8", errors="ignore")[:4000]
                except Exception:
                    pass

            entries[target_id]["attachments"].append({
                "attID": r["attID"],
                "attKey": r["attKey"],
                "parentItemID": r["parentItemID"],
                "linkMode": r["linkMode"],
                "contentType": r["contentType"],
                "path": p_str,
                "real_path": str(real_path) if real_path else None,
                "exists": exists,
                "size": size,
                "sha256": sha256,
                "indexedChars": r["indexedChars"] or 0,
                "ann_cnt": r["ann_cnt"] or 0,
                "has_ft_cache": cache_file.exists(),
                "ft_sample": ft_text,
            })

        conn.close()
        return entries
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
