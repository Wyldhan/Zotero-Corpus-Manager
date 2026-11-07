"""
[TR] Akıllı Mükerrer (Duplicate) Tespit, Künye Birleştirme ve Tek Dosyaya İndirme Motoru.
     SHA-256 dosya özeti, DOI ve normalize edilmiş başlık/yazar eşleşmelerini kullanarak
     mükerrer kayıtları kümeler; en zengin kaynakçaya sahip kaydı "Kazanan" seçer,
     eksik künye alanlarını birleştirir, en sağlam PDF'i ana kayda bağlar ve kopyaları siler.
[EN] Smart Duplicate Detection, Metadata Merging, and Single-File Consolidation Engine.
     Clusters duplicate records using SHA-256 file hashes, DOIs, and normalized title/author
     matching; selects the record with the richest bibliography as the "Winner", merges missing
     metadata fields, attaches the best physical PDF to the master record, and deletes redundant copies.
"""
from __future__ import annotations

import re
import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .applier import create_backup

# [TR] Üniversite tez kapaklarından yanlışlıkla çekilmiş jenerik başlıkları yakalayan Regex
# [EN] Regex matching generic university thesis cover headers mistakenly extracted as titles
RE_BAD_HEADER_TITLE = re.compile(
    r"(thesis\s+submitted\s+to|republic\s+of\s+turkey|t\.?\s*c\.?\s+.*üniversitesi|"
    r"sosyal\s+bilimler\s+enstitüsü|institute\s+of\s+social\s+sciences|"
    r"enstîtuya\s+ziwananê|bingöl\s+üniversitesi\s+yaşayan\s+diller|"
    r"tedeyî\s+ferhengek|no\s+title\s+found|كلية\s+العلوم\s+الإنسانية)",
    re.I,
)

# [TR] Sahte veya şablon yazar adlarını ("Soyadı, Adı" vb.) eleyen Regex
# [EN] Regex filtering out placeholder or invalid author names ("Soyadı, Adı", "Student", etc.)
RE_FAKE_AUTHOR = re.compile(
    r"\b(soyadı|student|masterî|sentaksi|vengî|null|unknown|anonymous)\b",
    re.I,
)


def norm_doi(d: str) -> str:
    """
    [TR] DOI adresini standart küçük harfli formata dönüştürür (https://doi.org/ önekini siler).
    [EN] Normalizes a DOI string to lowercase canonical form (strips https://doi.org/ prefix).
    """
    d = (d or "").strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d.strip()


def norm_title_strict(s: str) -> str:
    """
    [TR] Başlığı karşılaştırma için temizler (dosya uzantıları, tez ibareleri ve noktalamaları siler).
    [EN] Cleans and normalizes a title for strict comparison (strips file extensions, thesis tags, punctuation).
    """
    s = (s or "").replace("Ġ", "İ").replace("ġ", "ş").lower()
    s = re.sub(r"\[#\d+\]-\d+", "", s)
    s = re.sub(r"\(\d+\)\s*(\.pdf)?$", "", s)
    s = re.sub(r"\.pdf$", "", s)
    s = re.sub(r"libgen\.li", "", s)
    s = re.sub(r"\s*\[\s*(doktora|yüksek\s+lisans)\s+tezi\s*\]?", "", s)
    s = re.sub(r"[^\w\u0600-\u06FF]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_standalone_title(s: str) -> str:
    """
    [TR] Zotero'nun 'Yazar - Yıl - Başlık.pdf' formatındaki üst kayıtsız PDF adlarından asıl başlığı ayıklar.
    [EN] Extracts the core title from Zotero standalone PDF filenames formatted as 'Author - Year - Title.pdf'.
    """
    s = (s or "").replace("storage:", "")
    s = re.sub(r"\.pdf$", "", s, flags=re.I)
    m = re.match(r"^[^-]+-\s*(?:19\d\d|20\d\d)\s*-\s*(.+)$", s)
    if m:
        return norm_title_strict(m.group(1))
    m2 = re.match(r"^[^-]+-\s*(.+)$", s)
    if m2 and len(m2.group(1)) > 15:
        return norm_title_strict(m2.group(1))
    return norm_title_strict(s)


def norm_author_token(s: str) -> str:
    """
    [TR] Yazar soyadlarını/adlarını aksan ve diakritiklerden arındırarak karşılaştırılabilir hale getirir.
    [EN] Strips diacritics and accents from author names for cross-encoding comparison.
    """
    s = (s or "").lower().replace("i̇", "i")
    s = s.translate(str.maketrans("ığüşöçîêûáéíóúàèìòùäëïöü’'", "igusocieuadminaeiouaeiou  "))
    return re.sub(r"[^a-z\u0600-\u06FF]+", "", s)


def author_tokens(it: dict) -> set[str]:
    """
    [TR] Kaydın geçerli yazarlarının normalize edilmiş isim parçalarını küme olarak döndürür.
    [EN] Returns a set of normalized name tokens for all valid creators of an item.
    """
    out = set()
    for _, last, first in it["creators"]:
        if RE_FAKE_AUTHOR.search(f"{last} {first}"):
            continue
        for part in (last + " " + first).split():
            tok = norm_author_token(part)
            if len(tok) >= 3:
                out.add(tok)
    return out


def title_words(s: str) -> set[str]:
    """
    [TR] Başlıktaki anlamlı kelimeleri (en az 4 harfli) küme olarak döndürür.
    [EN] Returns the set of meaningful words (length >= 4) in a title.
    """
    nt = norm_title_strict(s)
    return {
        w
        for w in nt.split()
        if len(w) >= 4 and w not in ("with", "from", "that", "this", "study", "analysis", "based", "üzerine", "inceleme")
    }


def score_item_metadata(it: dict) -> int:
    """
    [TR] En kapsamlı kaynakçaya (bibliyografik künyeye) sahip olan kaydı seçmek için puanlama yapar.
         Akademik kayıt türü, temiz başlık, gerçek yazar sayısı, DOI, dergi/yayınevi, tarih, özet,
         cilt/sayı/sayfa/ISBN ve kullanıcı notları puanı artırır; üst kayıtsız PDF veya bozuk kapak
         başlıkları puanı düşürür.
    [EN] Scores an item's metadata completeness to select the record with the most comprehensive bibliography.
         Academic item types, clean titles, valid authors, DOI, publication venue, date, abstract,
         volume/issue/pages/ISBN, and user notes increase the score; standalone PDFs or corrupted
         thesis cover-page titles decrease the score.
    """
    itype = it["itemType"]
    if itype == "attachment":
        return -500

    type_scores = {
        "book": 120,
        "thesis": 120,
        "journalArticle": 115,
        "bookSection": 115,
        "conferencePaper": 115,
        "encyclopediaArticle": 110,
        "preprint": 85,
        "document": 75,
        "presentation": 75,
        "webpage": 60,
    }
    score = type_scores.get(itype, 70)
    f = it["fields"]
    title = f.get("title", "") or ""

    if not title or len(title.strip()) < 5:
        score -= 100
    elif RE_BAD_HEADER_TITLE.search(title):
        score -= 90
    elif title.endswith(".pdf") or "_" in title:
        score -= 30
    else:
        score += 25

    valid_creators = [c for c in it["creators"] if not RE_FAKE_AUTHOR.search(f"{c[1]} {c[2]}")]
    score += min(len(valid_creators) * 12, 36)
    for _, last, first in valid_creators:
        if len(first.strip()) >= 2 and not first.strip().endswith("."):
            score += 4

    if f.get("DOI"):
        score += 18
    pub = f.get("publicationTitle") or f.get("bookTitle") or f.get("university") or f.get("publisher") or ""
    if pub and pub.strip().lower() != "null":
        score += 15
    if f.get("date"):
        score += 12
    if f.get("abstractNote") and len(f["abstractNote"]) > 30:
        score += 14
    for k, pts in [
        ("volume", 5),
        ("issue", 5),
        ("pages", 6),
        ("ISBN", 8),
        ("ISSN", 6),
        ("place", 5),
        ("series", 5),
        ("url", 4),
        ("language", 3),
    ]:
        val = f.get(k, "")
        if val and val.strip().lower() != "null":
            score += pts

    score += it.get("notes_count", 0) * 5
    return score


def find_duplicate_clusters(items: dict[int, dict]) -> list[dict]:
    """
    [TR] SHA-256 dosya özeti, DOI ve Başlık/Yazar kurallarına göre mükerrer kümelerini tespit eder.
         Yanlış birleştirmeleri (false-positive) önlemek için 3 özel koruma içerir:
         1. Aynı kitabın farklı bölümleri (bookSection) aynı PDF'i paylaşsa bile birleştirilmez.
         2. Jenerik tez kapak başlıkları (RE_BAD_HEADER_TITLE) yazarları aynı değilse birleştirilmez.
         3. Bir kitap ile o kitabın başka bir yazar tarafından yazılmış incelemesi (book review) birleştirilmez.
    [EN] Identifies duplicate clusters using SHA-256 file hashes, DOIs, and Title/Author matching rules.
         Includes 3 dedicated false-positive guards:
         1. Distinct chapters of the same book (bookSection) sharing a full-book PDF are never merged.
         2. Generic thesis cover-page headers (RE_BAD_HEADER_TITLE) are never merged unless authors match.
         3. A book and a journal book-review written by a different author are never merged.
    """
    parent = {iid: iid for iid in items}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # ------------------------------------------------------------------
    # 1. [TR] Birebir aynı fiziksel dosya (SHA-256 eşleşmesi)
    #    [EN] Identical physical file content (SHA-256 hash match)
    # ------------------------------------------------------------------
    hash_groups = defaultdict(list)
    for iid, it in items.items():
        for a in it["attachments"]:
            if a.get("sha256"):
                hash_groups[a["sha256"]].append(iid)

    for h, iids in hash_groups.items():
        u_iids = list(dict.fromkeys(iids))
        if len(u_iids) > 1:
            types = {items[x]["itemType"] for x in u_iids}
            titles = {norm_title_strict(items[x]["fields"].get("title", "")) for x in u_iids}
            # [TR] Farklı başlıklara sahip kitap bölümlerini birleştirme
            # [EN] Do not merge distinct book chapters sharing the same book PDF
            if types == {"bookSection"} and len(titles) > 1:
                continue
            for x in u_iids[1:]:
                union(u_iids[0], x)

    # ------------------------------------------------------------------
    # 2. [TR] Aynı DOI (başlık/yazar doğrulamasıyla)
    #    [EN] Identical DOI (verified with title/author overlap)
    # ------------------------------------------------------------------
    doi_groups = defaultdict(list)
    for iid, it in items.items():
        d = norm_doi(it["fields"].get("DOI", ""))
        if d and len(d) > 5:
            doi_groups[d].append(iid)

    for d, iids in doi_groups.items():
        u_iids = list(dict.fromkeys(iids))
        if len(u_iids) > 1:
            base = u_iids[0]
            base_words = title_words(items[base]["fields"].get("title", ""))
            base_auth = author_tokens(items[base])
            for x in u_iids[1:]:
                if "bookSection" in (items[base]["itemType"], items[x]["itemType"]):
                    if norm_title_strict(items[base]["fields"].get("title", "")) != norm_title_strict(
                        items[x]["fields"].get("title", "")
                    ):
                        continue
                x_words = title_words(items[x]["fields"].get("title", ""))
                x_auth = author_tokens(items[x])
                if len(base_words & x_words) >= 2 or (base_auth and x_auth and (base_auth & x_auth)):
                    union(base, x)

    # ------------------------------------------------------------------
    # 3. [TR] Normalize edilmiş başlık eşleşmesi (tez kapağı ve farklı yazar korumalı)
    #    [EN] Normalized title match (guarded against thesis headers & disjoint authors)
    # ------------------------------------------------------------------
    title_groups = defaultdict(list)
    for iid, it in items.items():
        raw_t = it["fields"].get("title", "")
        if not raw_t and it["attachments"]:
            raw_t = it["attachments"][0]["path"]
        nt = norm_title_strict(raw_t)
        if len(nt) >= 12 and nt not in ("null", "introduction", "book review", "editorial", "front matter", "back matter"):
            title_groups[nt].append(iid)
        if it["itemType"] == "attachment":
            nst = norm_standalone_title(raw_t)
            if len(nst) >= 15 and nst != nt:
                title_groups[nst].append(iid)

    for t, iids in title_groups.items():
        u_iids = list(dict.fromkeys(iids))
        if len(u_iids) <= 1:
            continue
        is_bad_header = bool(RE_BAD_HEADER_TITLE.search(t))
        for i in range(len(u_iids)):
            for j in range(i + 1, len(u_iids)):
                a_id, b_id = u_iids[i], u_iids[j]
                it_a, it_b = items[a_id], items[b_id]
                auth_a, auth_b = author_tokens(it_a), author_tokens(it_b)

                if is_bad_header:
                    if auth_a and auth_b and (auth_a & auth_b):
                        union(a_id, b_id)
                    continue

                types_pair = {it_a["itemType"], it_b["itemType"]}
                if types_pair in ({"book", "journalArticle"}, {"book", "bookSection"}):
                    if auth_a and auth_b and not (auth_a & auth_b):
                        continue

                if auth_a and auth_b and not (auth_a & auth_b):
                    if len(t.split()) <= 5:
                        continue
                    if "koroglu" not in (auth_a | auth_b) and "veisi" not in (auth_a | auth_b) and "haig" not in (auth_a | auth_b):
                        continue

                union(a_id, b_id)

    raw_clusters = defaultdict(list)
    for iid in items:
        raw_clusters[find(iid)].append(iid)

    # [TR] Her küme için en yüksek puanlı "Kazanan" kaydı ve en sağlam fiziksel PDF'i seç
    # [EN] Select the highest-scoring "Winner" item and the best physical PDF for each cluster
    plan_clusters = []
    for c_iids in raw_clusters.values():
        if len(c_iids) <= 1:
            continue
        ranked = sorted(c_iids, key=lambda x: (score_item_metadata(items[x]), -x), reverse=True)
        winner_id = ranked[0]
        loser_ids = ranked[1:]

        all_atts = [a for x in ranked for a in items[x]["attachments"]]
        existing_atts = [a for a in all_atts if a["exists"]]
        best_att = None
        if existing_atts:
            existing_atts.sort(
                key=lambda a: (
                    a["contentType"] == "application/pdf",
                    a["ann_cnt"],
                    a["indexedChars"],
                    a["size"],
                    a["parentItemID"] == winner_id,
                ),
                reverse=True,
            )
            best_att = existing_atts[0]
        elif all_atts:
            best_att = all_atts[0]

        redundant_atts = [a for a in all_atts if best_att is None or a["attID"] != best_att["attID"]]
        w_item = items[winner_id]
        w_title = w_item["fields"].get("title", "")
        if not w_title and w_item["attachments"]:
            w_title = w_item["attachments"][0]["path"].replace("storage:", "")

        plan_clusters.append({
            "winner_id": winner_id,
            "winner_key": w_item["key"],
            "winner_type": w_item["itemType"],
            "winner_title": w_title,
            "winner_creators": [f"{c[1]}, {c[2]}".strip(", ") for c in w_item["creators"]],
            "winner_date": w_item["fields"].get("date", ""),
            "winner_doi": w_item["fields"].get("DOI", ""),
            "winner_score": score_item_metadata(w_item),
            "loser_ids": loser_ids,
            "loser_keys": [items[x]["key"] for x in loser_ids],
            "loser_titles": [
                items[x]["fields"].get("title") or (items[x]["attachments"][0]["path"] if items[x]["attachments"] else "")
                for x in loser_ids
            ],
            "best_att": best_att,
            "redundant_atts": redundant_atts,
            "freed_bytes": sum(a["size"] for a in redundant_atts if a["exists"]),
        })

    return plan_clusters


def execute_deduplication(
    zdir: Path,
    clusters: list[dict],
    items: dict[int, dict],
    backup_dir: Path | None = None,
) -> dict:
    """
    [TR] Seçilen mükerrer kümelerini birleştirir, en sağlam PDF'i ana kayda bağlar ve kopyaları siler.
         İşlem öncesi otomatik olarak tarih damgalı '.pre-dedup_*.bak' yedeği alır.
    [EN] Merges duplicate clusters, links the best PDF to the winning master record, and removes redundant copies.
         Automatically creates a timestamped '.pre-dedup_*.bak' database backup before modifying anything.
    """
    db_path = zdir / "zotero.sqlite"
    bak_file = create_backup(zdir, label="pre-dedup", backup_dir=backup_dir)

    conn = sqlite3.connect(db_path, timeout=30.0)
    cur = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    item_type_id_map = {r[0]: r[1] for r in cur.execute("SELECT itemID, itemTypeID FROM items")}
    valid_type_fields = defaultdict(set)
    for r in cur.execute("SELECT itemTypeID, fieldID FROM itemTypeFields"):
        valid_type_fields[r[0]].add(r[1])

    merged_fields_cnt = 0
    merged_creators_cnt = 0
    reparented_atts_cnt = 0
    moved_annotations_cnt = 0
    moved_notes_cnt = 0
    deleted_att_records = 0
    deleted_storage_dirs = 0
    deleted_bytes = 0
    deleted_items_cnt = 0

    for cl in clusters:
        wid = cl["winner_id"]
        lids = list(cl["loser_ids"])
        best_att = cl["best_att"]
        red_atts = list(cl["redundant_atts"])

        # [TR] Eğer kazananın kendisi de üst kayıtsız bir PDF ise, en sağlam PDF'i kazanan yap
        # [EN] If the winner itself is a standalone attachment, promote the best physical PDF as winner
        if items[wid]["itemType"] == "attachment":
            if best_att and best_att["attID"] != wid:
                old_wid = wid
                wid = best_att["attID"]
                lids = [x for x in ([old_wid] + lids) if x != wid]
                red_atts = [a for a in ([best_att] + red_atts) if a["attID"] != wid]

        w_type_id = item_type_id_map.get(wid)
        allowed_fids = valid_type_fields.get(w_type_id, set())

        # 1. [TR] Eksik bibliyografik alanları silinecek kopyalardan kazanana aktar
        #    [EN] Merge missing metadata fields from duplicate items into the winner
        w_existing_fields = {
            r[0]: r[1]
            for r in cur.execute("SELECT fieldID, valueID FROM itemData WHERE itemID=?", (wid,))
        }
        for lid in lids:
            for fid, vid in cur.execute("SELECT fieldID, valueID FROM itemData WHERE itemID=?", (lid,)).fetchall():
                if fid in allowed_fids and fid not in w_existing_fields:
                    val_str = cur.execute("SELECT value FROM itemDataValues WHERE valueID=?", (vid,)).fetchone()[0]
                    if val_str and str(val_str).strip().lower() != "null":
                        cur.execute("INSERT OR IGNORE INTO itemData (itemID, fieldID, valueID) VALUES (?, ?, ?)", (wid, fid, vid))
                        w_existing_fields[fid] = vid
                        merged_fields_cnt += 1

        # 2. [TR] Kazananda hiç yazar yoksa kopyadaki yazar listesini aktar
        #    [EN] If winner has no creators, copy creator list from duplicate item
        w_creator_cnt = cur.execute("SELECT COUNT(*) FROM itemCreators WHERE itemID=?", (wid,)).fetchone()[0]
        if w_creator_cnt == 0 and items[wid]["itemType"] != "attachment":
            for lid in lids:
                l_creators = cur.execute(
                    "SELECT creatorID, creatorTypeID, orderIndex FROM itemCreators WHERE itemID=? ORDER BY orderIndex",
                    (lid,),
                ).fetchall()
                if l_creators:
                    for cid, ctid, oidx in l_creators:
                        cur.execute(
                            "INSERT OR IGNORE INTO itemCreators (itemID, creatorID, creatorTypeID, orderIndex) VALUES (?, ?, ?, ?)",
                            (wid, cid, ctid, oidx),
                        )
                    merged_creators_cnt += len(l_creators)
                    break

        # 3. [TR] Koleksiyon üyeliklerini ve etiketleri kazanana birleştir
        #    [EN] Consolidate collection memberships and tags onto the winner
        for lid in lids:
            for (col_id,) in cur.execute("SELECT collectionID FROM collectionItems WHERE itemID=?", (lid,)).fetchall():
                cur.execute(
                    "INSERT OR IGNORE INTO collectionItems (collectionID, itemID, orderIndex) VALUES (?, ?, 0)",
                    (col_id, wid),
                )
            for (tag_id, ttype) in cur.execute("SELECT tagID, type FROM itemTags WHERE itemID=?", (lid,)).fetchall():
                cur.execute(
                    "INSERT OR IGNORE INTO itemTags (itemID, tagID, type) VALUES (?, ?, ?)",
                    (wid, tag_id, ttype),
                )

        # 4. [TR] Alt notları (itemNotes) kazanana taşı
        #    [EN] Move child notes (itemNotes) to the winner
        if items[wid]["itemType"] != "attachment":
            for lid in lids:
                moved = cur.execute("UPDATE itemNotes SET parentItemID=? WHERE parentItemID=?", (wid, lid)).rowcount
                moved_notes_cnt += moved

        # 5. [TR] En sağlam fiziksel PDF'i kazanana bağla ve PDF içi vurgulamaları (annotations) koru
        #    [EN] Reparent the best physical PDF to the winner and preserve PDF annotations
        if best_att and items[wid]["itemType"] != "attachment":
            best_att_id = best_att["attID"]
            if best_att["parentItemID"] != wid:
                cur.execute("DELETE FROM collectionItems WHERE itemID=?", (best_att_id,))
                cur.execute("UPDATE itemNotes SET parentItemID=? WHERE parentItemID=?", (wid, best_att_id))
                cur.execute("UPDATE itemAttachments SET parentItemID=? WHERE itemID=?", (wid, best_att_id))
                cur.execute("UPDATE items SET clientDateModified=?, synced=0 WHERE itemID=?", (now_str, best_att_id))
                reparented_atts_cnt += 1
                if best_att_id in lids:
                    lids.remove(best_att_id)

            for ra in red_atts:
                ra_id = ra["attID"]
                if ra_id == best_att_id:
                    continue
                moved_ann = cur.execute("UPDATE itemAnnotations SET parentItemID=? WHERE parentItemID=?", (best_att_id, ra_id)).rowcount
                moved_annotations_cnt += moved_ann

        # 6. [TR] Gereksiz ek (attachment) kayıtlarını ve diskteki kopya storage/<KEY> klasörlerini sil
        #    [EN] Delete redundant attachment records and their duplicate storage/<KEY> folders on disk
        for ra in red_atts:
            ra_id = ra["attID"]
            if best_att and ra_id == best_att["attID"]:
                continue
            cur.execute("DELETE FROM collectionItems WHERE itemID=?", (ra_id,))
            cur.execute("DELETE FROM itemAnnotations WHERE parentItemID=?", (ra_id,))
            cur.execute("DELETE FROM fulltextItems WHERE itemID=?", (ra_id,))
            cur.execute("DELETE FROM itemAttachments WHERE itemID=?", (ra_id,))
            cur.execute("DELETE FROM items WHERE itemID=?", (ra_id,))
            deleted_att_records += 1

            att_folder = zdir / "storage" / ra["attKey"]
            if att_folder.exists() and (not best_att or ra["attKey"] != best_att["attKey"]):
                for fpath in att_folder.rglob("*"):
                    if fpath.is_file():
                        deleted_bytes += fpath.stat().st_size
                shutil.rmtree(att_folder, ignore_errors=True)
                deleted_storage_dirs += 1

        # 7. [TR] Kaybeden mükerrer bibliyografik kayıtları sil
        #    [EN] Delete losing duplicate bibliographic items
        for lid in lids:
            cur.execute("DELETE FROM collectionItems WHERE itemID=?", (lid,))
            cur.execute("DELETE FROM itemTags WHERE itemID=?", (lid,))
            cur.execute("DELETE FROM itemData WHERE itemID=?", (lid,))
            cur.execute("DELETE FROM itemCreators WHERE itemID=?", (lid,))
            cur.execute("DELETE FROM itemNotes WHERE parentItemID=? OR itemID=?", (lid, lid))
            cur.execute("DELETE FROM items WHERE itemID=?", (lid,))
            deleted_items_cnt += 1

        cur.execute("UPDATE items SET clientDateModified=?, synced=0 WHERE itemID=?", (now_str, wid))

    # [TR] Eski mükerrer-aday etiketlerini ve denetim koleksiyonunu temizle
    # [EN] Clear stale duplicate-candidate tags and audit collection links
    cur.execute("DELETE FROM itemTags WHERE tagID IN (SELECT tagID FROM tags WHERE name='#kontrol:mukerrer-aday')")
    cur.execute("DELETE FROM collectionItems WHERE collectionID IN (SELECT collectionID FROM collections WHERE collectionName LIKE '%1-Mükerrer%')")

    conn.commit()
    conn.close()

    return {
        "backup_file": str(bak_file),
        "clusters_resolved": len(clusters),
        "deleted_duplicate_items": deleted_items_cnt,
        "deleted_redundant_attachment_records": deleted_att_records,
        "deleted_storage_folders": deleted_storage_dirs,
        "freed_megabytes": round(deleted_bytes / (1024 * 1024), 2),
        "merged_metadata_fields": merged_fields_cnt,
        "merged_creator_lists": merged_creators_cnt,
        "reparented_standalone_or_child_pdfs": reparented_atts_cnt,
        "preserved_annotations": moved_annotations_cnt,
        "preserved_notes": moved_notes_cnt,
    }
