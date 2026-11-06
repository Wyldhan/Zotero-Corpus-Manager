"""5 Boyutlu Zotero Otomatik Sınıflandırma ve Koleksiyon Planlama Motoru."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

DEFAULT_RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "default_rules.json"

RE_TR_CHARS = re.compile(r"[ğĞşŞıİ]")
RE_AR_SCRIPT = re.compile(r"[\u0600-\u06FF]")
RE_SORANI_CHARS = re.compile(r"[ڵڕێۆەڤگچپژ]")
AUTO_TAG_PREFIXES = ("#dil:", "#derlem:", "#tur:", "#konu:", "#kontrol:")


def clean_text(s: str) -> str:
    return (s or "").replace("Ġ", "İ").replace("ġ", "ş").replace("_", " ")


def normalize_title_key(s: str) -> str:
    s = clean_text(s).lower()
    s = re.sub(r"\[#\d+\]-\d+", "", s)
    s = re.sub(r"\(\d+\)$", "", s)
    s = re.sub(r"libgen\.li", "", s)
    s = re.sub(r"[^\w\u0600-\u06FF]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_rules(rules_path: Path | None = None) -> dict:
    p = rules_path or DEFAULT_RULES_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def _compile_kw_list(keywords: list[str]) -> re.Pattern | None:
    if not keywords:
        return None
    joined = "|".join(keywords)
    return re.compile(rf"\b({joined})\b", re.I)


def classify_library(entries: dict[int, dict], rules: dict | None = None) -> dict[int, dict]:
    """Tüm kütüphane kayıtlarını 5 boyutta (dil, derlem, tür, konu, kontrol) sınıflandırır."""
    if rules is None:
        rules = load_rules()

    lang_compiled = {}
    iso_map = {}
    for lcfg in rules.get("languages", []):
        lid = lcfg["id"]
        iso_map[lid] = lcfg.get("iso", "en")
        lang_compiled[lid] = _compile_kw_list(lcfg.get("keywords", []))

    corpus_compiled = {
        ccfg["id"]: _compile_kw_list(ccfg.get("keywords", []))
        for ccfg in rules.get("corpora", [])
        if ccfg.get("keywords")
    }
    topic_compiled = {
        tcfg["id"]: _compile_kw_list(tcfg.get("keywords", []))
        for tcfg in rules.get("topics", [])
        if tcfg.get("keywords")
    }

    # Mükerrer ön kontrolü (başlık ve dosya boyutu tabanlı)
    title_groups: dict[str, list[int]] = defaultdict(list)
    size_groups: dict[int, list[int]] = defaultdict(list)
    for iid, e in entries.items():
        raw_t = e["fields"].get("title", "")
        if not raw_t and e["attachments"]:
            raw_t = e["attachments"][0].get("path", "").replace("storage:", "")
        nt = normalize_title_key(raw_t)
        if len(nt) >= 12 and nt not in ("null", "introduction", "book review", "editorial"):
            title_groups[nt].append(iid)
        for a in e["attachments"]:
            if a["exists"] and a["size"] > 20_000:
                size_groups[a["size"]].append(iid)

    dup_iids = set()
    for iids in title_groups.values():
        if len(set(iids)) > 1:
            dup_iids.update(iids)
    for iids in size_groups.values():
        if len(set(iids)) > 1:
            dup_iids.update(iids)

    results: dict[int, dict] = {}
    re_zz = lang_compiled.get("kirmancki")
    re_ku = lang_compiled.get("kurmanci")
    re_tr = lang_compiled.get("turkce")
    re_de = lang_compiled.get("almanca")
    re_fr = lang_compiled.get("fransizca")

    for iid, e in entries.items():
        f = e["fields"]
        raw_title = f.get("title", "")
        if not raw_title and e["attachments"]:
            raw_title = e["attachments"][0].get("path", "").replace("storage:", "")
        title = clean_text(raw_title)
        abstract = clean_text(f.get("abstractNote", ""))
        pub = clean_text(f.get("publicationTitle", "") or f.get("bookTitle", "") or f.get("series", ""))
        lang_field = (f.get("language", "") or "").strip().lower()
        ft_samples = clean_text(" ".join(a.get("ft_sample", "")[:2500] for a in e["attachments"]))

        # Kendi ürettiğimiz otomatik etiketleri (#derlem:... vb.) metin havuzuna dahil etme (Idempotency)
        user_tags = [t for t in e["tags"] if not t.startswith(AUTO_TAG_PREFIXES)]
        meta_blob = f"{title} {abstract} {pub} {' '.join(user_tags)}"
        full_blob = f"{meta_blob} {ft_samples}"

        # 1. Metin Dili (#dil:...)
        ar_chars_title = len(RE_AR_SCRIPT.findall(title + " " + abstract))
        ar_chars_full = len(RE_AR_SCRIPT.findall(full_blob))
        if ar_chars_title > 8 or ar_chars_full > 120:
            if len(RE_SORANI_CHARS.findall(full_blob)) >= 3 or "کورد" in full_blob or "زمانی" in full_blob:
                doc_lang = "sorani"
            else:
                doc_lang = "farsca-arapca"
        elif re_zz and (len(re_zz.findall(title + " " + abstract)) >= 1 or len(re_zz.findall(ft_samples)) >= 4):
            doc_lang = "kirmancki"
        elif re_ku and (len(re_ku.findall(title + " " + abstract)) >= 1 or len(re_ku.findall(ft_samples)) >= 4):
            doc_lang = "kurmanci"
        elif (
            (re_tr and len(re_tr.findall(title + " " + pub)) >= 1)
            or len(RE_TR_CHARS.findall(title)) >= 2
            or (re_tr and len(re_tr.findall(abstract + " " + ft_samples[:1200])) >= 4)
            or lang_field.startswith("tr")
        ):
            doc_lang = "turkce"
        elif lang_field.startswith("de") or (re_de and len(re_de.findall(title)) >= 2):
            doc_lang = "almanca"
        elif lang_field.startswith("fr") or (re_fr and len(re_fr.findall(title)) >= 2):
            doc_lang = "fransizca"
        elif lang_field.startswith("zza") or lang_field.startswith("diq"):
            doc_lang = "kirmancki"
        elif lang_field.startswith("ku") or lang_field.startswith("kmr"):
            doc_lang = "kurmanci"
        elif lang_field.startswith("ckb"):
            doc_lang = "sorani"
        else:
            doc_lang = "ingilizce"

        # 2. Hedef Dil / Derlem (#derlem:...)
        derlem = []
        if (corpus_compiled.get("zazaki-kirmancki") and corpus_compiled["zazaki-kirmancki"].search(meta_blob)) or doc_lang == "kirmancki" or "Zazakî-Gramer" in e["collections"]:
            derlem.append("zazaki-kirmancki")
        if (corpus_compiled.get("kurmanci") and corpus_compiled["kurmanci"].search(meta_blob)) or doc_lang == "kurmanci":
            derlem.append("kurmanci")
        if (corpus_compiled.get("sorani-gorani") and corpus_compiled["sorani-gorani"].search(meta_blob)) or doc_lang == "sorani":
            derlem.append("sorani-gorani")
        if corpus_compiled.get("kurdoloji-genel") and corpus_compiled["kurdoloji-genel"].search(meta_blob) and not derlem:
            derlem.append("kurdoloji-genel")
        if corpus_compiled.get("irani-diller") and corpus_compiled["irani-diller"].search(meta_blob):
            derlem.append("irani-diller")
        if corpus_compiled.get("turkce-turkoloji") and corpus_compiled["turkce-turkoloji"].search(meta_blob) and not derlem:
            derlem.append("turkce-turkoloji")

        if not derlem:
            if corpus_compiled.get("zazaki-kirmancki") and corpus_compiled["zazaki-kirmancki"].search(ft_samples[:1500]):
                derlem.append("zazaki-kirmancki")
            elif corpus_compiled.get("kurdoloji-genel") and corpus_compiled["kurdoloji-genel"].search(ft_samples[:1500]):
                derlem.append("kurdoloji-genel")
            elif doc_lang == "turkce" and re.search(r"\b(türkçe|türk\s+dili|ağız|ekler|fiil|cümle|sözlük|kelime)\b", meta_blob, re.I):
                derlem.append("turkce-turkoloji")
            else:
                derlem.append("genel-dilbilim")

        # 3. Eser Türü (#tur:...)
        itype = e["itemType"]
        if re.search(r"\b(sözlük\w*|sözlüğü|ferheng\w*|dictionary|lexicon|glossary|îdyom\w*|deyimler)\b", title, re.I):
            tur = "sozluk"
        elif re.search(r"\b(gramer\w*|dilbilgisi|grammar|rêziman\w*|rastnuştiş\w*|imla|orthograph\w*|reference\s+book)\b", title, re.I) and itype in ("book", "document", "attachment"):
            tur = "gramer"
        elif re.search(r"\b(kovar\w*|rojname\w*|hûmar[ae]|sayı\s*\d|dergisi\s+sayı)\b", title, re.I):
            tur = "dergi-gazete"
        elif re.search(r"\b(hikaye\w*|öykü\w*|roman\b|şiir\w*|masal\w*|folklor\w*|destan\w*|antoloji\w*|sanik\w*|kılam\w*|atasöz\w*|metinler\w*)\b", title, re.I):
            tur = "edebi-folklor"
        elif itype == "thesis" or re.search(r"\b(tez[i]?|thesis|dissertation|doktora\s+tezi|yüksek\s+lisans\s+tezi|ماجستير|دكتوراه)\b", meta_blob, re.I):
            tur = "tez"
        elif itype == "conferencePaper" or re.search(r"\b(sempozyum\w*|bildiri\w*|proceedings|conference|workshop\s+on|toplantısı)\b", pub + " " + title, re.I):
            tur = "bildiri"
        elif itype in ("book", "bookSection"):
            tur = "kitap-bolum"
        elif itype == "preprint" or "arxiv" in meta_blob.lower():
            tur = "onbaski-rapor"
        else:
            tur = "makale"

        # 4. Konu / Alt Alan (#konu:...)
        konular = []
        for tid, pat in topic_compiled.items():
            if pat and pat.search(meta_blob):
                konular.append(tid)

        if not konular:
            if re.search(
                r"\b(liderlik|yönetim|işletme|muhasebe|turizm|hemşirelik|tıp\b|hastalık|cerrahi|"
                r"inşaat|beton|elektrik|tarım|fındık|finans|pazarlama|homotetik|geometri|"
                r"malware|android|spam\s+detection|visual\s+processing|connectivity\s+in\s+africa)\b",
                meta_blob,
                re.I,
            ):
                konular.append("alan-disi")
            else:
                konular.append("genel-dilbilim-kuram")

        # 5. Teknik / Derlem Kontrol (#kontrol:...)
        kontroller = []
        if iid in dup_iids:
            kontroller.append("mukerrer-aday")
        if itype == "attachment":
            kontroller.append("ust-kayitsiz-pdf")
        if any(a["path"] and not a["exists"] for a in e["attachments"]):
            kontroller.append("eksik-dosya")
        if any(
            a["contentType"] == "application/pdf"
            and a["exists"]
            and not a["has_ft_cache"]
            and a["indexedChars"] < 50
            for a in e["attachments"]
        ):
            kontroller.append("ocr-gerekli")
        expected_iso = iso_map.get(doc_lang, "en")
        if lang_field and lang_field.startswith("en") and expected_iso != "en":
            kontroller.append("dil-kodu-hatali")

        tags_to_add = (
            [f"#dil:{doc_lang}"]
            + [f"#derlem:{d}" for d in derlem]
            + [f"#tur:{tur}"]
            + [f"#konu:{k}" for k in konular]
            + [f"#kontrol:{c}" for c in kontroller]
        )

        results[iid] = {
            "itemID": iid,
            "key": e["key"],
            "title": title,
            "itemType": itype,
            "creators": [f"{c[1]}, {c[2]}".strip(", ") for c in e["creators"]],
            "date": f.get("date", ""),
            "DOI": f.get("DOI", ""),
            "doc_lang": doc_lang,
            "expected_iso": expected_iso,
            "current_lang": lang_field,
            "derlem": derlem,
            "tur": tur,
            "konular": konular,
            "kontroller": kontroller,
            "auto_tags": tags_to_add,
        }

    return results
