# 📚 Zotero Corpus & Automatic Classification Manager / Zotero Derlem ve Sınıflandırma Yöneticisi

<p align="center">
  <strong><a href="#-english-documentation">🇬🇧 English Documentation</a></strong> &nbsp;|&nbsp;
  <strong><a href="#-türkçe-dokümantasyon">🇹🇷 Türkçe Dokümantasyon</a></strong>
</p>

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Zero Dependencies](https://img.shields.io/badge/Ba%C4%9F%C4%B1ml%C4%B1l%C4%B1k%20%2F%20Dependencies-S%C4%B1f%C4%B1r%20(Zero)-brightgreen.svg)
![Bilingual TR/EN](https://img.shields.io/badge/Dil%20%2F%20Language-TR%20%7C%20EN-orange.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🇹🇷 Türkçe Dokümantasyon

**Zotero Derlem ve Otomatik Sınıflandırma Yöneticisi**, özellikle dilbilim, Kürdoloji (*Zazakî / Kirmanckî, Kurmancî, Soranî, Goranî*), İrani diller ve Türkoloji çalışan araştırmacıların binlerce kayıttan oluşan Zotero kütüphanelerini **hiçbir yazılım veya komut satırı bilgisi gerektirmeden**, tek tıkla çalışan **iki dilli (TR/EN) Görsel Web Arayüzü (Dashboard)** üzerinden düzenlemek, denetlemek ve mükerrer (duplicate) PDF dosyalarını temizlemek için geliştirilmiş açık kaynaklı bir araçtır.

> 💡 **Sıfır Kurulum Karmaşası:** Bu proje Python standart kütüphanesi dışında **hiçbir harici paket (`pip install ...`) gerektirmez**. İndirip doğrudan `Baslat.bat` dosyasına çift tıklayarak kullanabilirsiniz.

### ✨ Temel Özellikler

1. **🖥️ Yazılım Bilgisi Gerektirmeyen Görsel Web Arayüzü (`🇹🇷 TR | 🇬🇧 EN`):**
   - `Baslat.bat` (Windows) veya `./baslat.sh` (macOS/Linux) dosyasına çift tıkladığınızda tarayıcınızda otomatik olarak modern kontrol paneli açılır.
   - Sağ üstteki **`🇹🇷 TR | 🇬🇧 EN`** düğmesiyle arayüz dilini anında Türkçe ve İngilizce arasında değiştirebilirsiniz.
2. **🗂️ 5 Boyutlu Otomatik Sınıflandırma ve 52 Koleksiyonluk Hiyerarşi:**
   - **1. Hedef Dil & Derlem (`#derlem:...`):** `zazaki-kirmancki`, `kurmanci`, `sorani-gorani`, `kurdoloji-genel`, `irani-diller`, `turkce-turkoloji`, `genel-dilbilim`
   - **2. Metin Dili (`#dil:...`):** Kirmanckî (`zza`), Kurmancî (`kmr`), Soranî (`ckb`), Türkçe (`tr`), İngilizce (`en`), Almanca (`de`), Fransızca (`fr`), Farsça/Arapça (`fa`)
   - **3. Eser Türü (`#tur:...`):** Sözlükler, Gramerler, Tezler (YL/Doktora), Edebi Metinler & Folklor, Dergi/Gazete Sayıları, Kitap & Bölümler, Hakemli Makaleler, Bildiriler, Ön Baskılar
   - **4. Konu & Alt Alan (`#konu:...`):** Morfoloji/Allomorfi/Ergativite, Fonoloji, Sözdizimi (Syntax), Anlambilim/Kip-Zaman, Sözlükbilim/Etimoloji, Derlem Dilbilimi, NLP, Söylem/Toplumdilbilim, Diyalektoloji/Ağızlar, Dil Eğitimi, Edebiyat/Tarih
   - **5. Derlem Denetim & Kalite Kontrol (`#kontrol:...`):** Mükerrer adayları, üst kaydı olmayan (standalone) PDF'ler, fiziksel dosyası eksik kayıtlar, OCR (metin katmanı) gereken taranmış PDF'ler ve dil kodu hatalı (`en` yazılıp Türkçe/Kürtçe/Zazaca olan) eserler.
3. **🧹 Akıllı Mükerrer (Duplicate) Birleştirme ve Tek Dosyaya İndirme:**
   - PDF dosyalarının **SHA-256 kriptografik özetlerini**, **DOI** numaralarını ve **normalize edilmiş başlık/yazar** bilgilerini karşılaştırır.
   - Her mükerrer kümesinde **en kapsamlı kaynakçaya (künyeye) sahip olan kaydı** ana kayıt (*Kazanan*) olarak seçer.
   - Diğer kopyalardaki eksik künye alanlarını, yazarları, etiketleri, koleksiyon üyeliklerini ve kullanıcı notlarını ana kayda aktarır.
   - Üst kaydı olmayan (standalone) veya kopya kayıtlardaki **en sağlam tek PDF dosyasını** (varsa PDF içi vurgulamalarıyla birlikte) ana kayda bağlar ve fazlalık PDF klasörlerini (`storage/<KEY>`) silerek yüzlerce MB disk alanı açar.
4. **🛡️ %100 Veri Güvenliği ve Tek Tıkla Geri Yükleme (Backup & Restore):**
   - Zotero açıkken bile kütüphaneyi geçici kopya üzerinden kilitlenmeden salt-okunur tarayabilir.
   - Veritabanına yapılacak her yazma işleminden önce otomatik olarak tarih-saat damgalı tam yedek (`zotero.sqlite.pre-classify_*.bak` veya `zotero.sqlite.pre-dedup_*.bak`) alır.

### 🚀 Hızlı Başlangıç (Yazılım Bilgisi Olmayanlar İçin)

1. Bu depoyu yeşil **`<> Code` -> `Download ZIP`** düğmesiyle indirin ve bir klasöre çıkartın.
2. Klasörün içindeki **[`Baslat.bat`](file:///D:/Claude/Projects/Zotero-Derlem-Yoneticisi/Baslat.bat)** (Windows) veya **[`baslat.sh`](file:///D:/Claude/Projects/Zotero-Derlem-Yoneticisi/baslat.sh)** (macOS/Linux) dosyasına **çift tıklayın**.
3. Otomatik açılan `http://127.0.0.1:8765` sayfasından kütüphanenizi tarayın, sınıflandırın veya mükerrerleri birleştirin!
   - Ayrıntılı görsel anlatım için **[Adım Adım Kullanım Kılavuzu (`docs/KULLANIM_KILAVUZU.md`)](file:///D:/Claude/Projects/Zotero-Derlem-Yoneticisi/docs/KULLANIM_KILAVUZU.md)** belgesine göz atabilirsiniz.

---

## 🇬🇧 English Documentation

**Zotero Corpus & Automatic Classification Manager** is an open-source, zero-dependency tool designed for linguists and researchers working on Kurdish studies (*Zazaki / Kirmancki, Kurmanji, Sorani, Gorani*), Iranian languages, Turkology, and general linguistics. It organizes, audits, and deduplicates large Zotero libraries through a **one-click bilingual (TR/EN) Visual Web Dashboard** requiring **zero programming or command-line experience**.

> 💡 **Zero Dependency Hassle:** Built 100% on the Python Standard Library (`sqlite3`, `http.server`, `hashlib`, `re`). **No `pip install` is ever required.** Simply download and double-click `Baslat.bat` (Windows) or `./baslat.sh` (macOS/Linux).

### ✨ Key Features

1. **🖥️ No-Code Bilingual Visual Web Dashboard (`🇹🇷 TR | 🇬🇧 EN`):**
   - Double-clicking `Baslat.bat` or `./baslat.sh` automatically detects your Zotero data folder (`D:\Zotero`, `~/Zotero`, or via `prefs.js`) and opens the local dashboard in your browser.
   - Switch the entire UI between **Turkish and English** anytime using the **`🇹🇷 TR | 🇬🇧 EN`** button in the top-right corner.
2. **🗂️ 5-Dimensional Automatic Classification & 52-Collection Hierarchy:**
   - **1. Target Corpus (`#derlem:...`):** `zazaki-kirmancki`, `kurmanci`, `sorani-gorani`, `kurdoloji-genel`, `irani-diller`, `turkce-turkoloji`, `genel-dilbilim`
   - **2. Document Language (`#dil:...`):** Kirmancki (`zza`), Kurmanji (`kmr`), Sorani (`ckb`), Turkish (`tr`), English (`en`), German (`de`), French (`fr`), Persian/Arabic (`fa`)
   - **3. Publication Type (`#tur:...`):** Dictionaries, Grammars, Theses (MA/PhD), Literary & Folklore Texts, Journals/Newspapers, Books & Chapters, Peer-Reviewed Articles, Conference Papers, Preprints
   - **4. Research Topic (`#konu:...`):** Morphology/Allomorphy/Ergativity, Phonology, Syntax & Typology, Semantics/TAM, Lexicography/Etymology, Corpus Linguistics, NLP, Discourse/Sociolinguistics, Dialectology, Language Education, Literature/History
   - **5. Quality Audit (`#kontrol:...`):** Duplicate candidates, standalone PDFs without parent metadata, missing physical files, scanned PDFs requiring OCR, and items with wrong ISO language codes (e.g., marked `en` when written in Turkish, Kurmanji, or Zazaki).
3. **🧹 Smart Duplicate Merging & Single-File Consolidation:**
   - Matches duplicates across **SHA-256 physical file hashes**, **DOIs**, and **normalized titles/authors** (with built-in false-positive guards for shared book-chapter PDFs, book reviews, and university thesis cover headers).
   - Scores every item in a duplicate cluster and keeps the **master record with the most comprehensive bibliography** (*Winner*).
   - Merges any missing metadata fields, creators, collection links, tags, and child notes from duplicate copies into the winning master record.
   - Reparents the **single best physical PDF file** (preserving PDF highlights/annotations) to the winning record and deletes redundant `storage/<KEY>` folders.
4. **🛡️ 100% Data Safety & One-Click Backup/Restore:**
   - Reads your Zotero database safely via a temporary snapshot (`zotero.sqlite` + `-wal` + `-shm`) even while Zotero is open.
   - Automatically creates a timestamped `.bak` backup before every write operation.

---

## 💻 Komut Satırı Kullanımı / Command-Line Interface (CLI)

```bash
# [TR] Görsel Web Arayüzünü başlatır (Varsayılan) / [EN] Launch Visual Web Dashboard (Default)
python -X utf8 zotero_cli.py gui

# [TR] Kütüphaneyi salt-okunur tarar ve rapor üretir / [EN] Read-only scan & export reports (MD, CSV, JSON)
python -X utf8 zotero_cli.py scan

# [TR] Otomatik sınıflandırmayı Zotero'ya uygular / [EN] Apply collections, tags & ISO language fixes
python -X utf8 zotero_cli.py classify

# [TR] Mükerrer birleştirme planını önizler (silme yapmaz) / [EN] Preview duplicate consolidation (dry-run)
python -X utf8 zotero_cli.py dedup --dry-run

# [TR] Mükerrerleri en zengin kaynakçayla birleştirir / [EN] Execute duplicate consolidation & delete redundant PDFs
python -X utf8 zotero_cli.py dedup

# [TR] Veritabanı yedeklerini listeler ve geri yükler / [EN] List and restore database backups
python -X utf8 zotero_cli.py backups
python -X utf8 zotero_cli.py restore "D:\Zotero\zotero.sqlite.pre-dedup_20261107.bak"
```

---

## 📁 Proje Yapısı / Repository Structure

```text
Zotero-Corpus-Manager/
├── Baslat.bat                  # [TR] Windows tek tıkla başlatıcı / [EN] Windows one-click launcher
├── baslat.sh                   # [TR] macOS & Linux başlatıcı / [EN] macOS & Linux launcher
├── zotero_cli.py               # [TR] Ana giriş noktası (GUI & CLI) / [EN] Main entry point
├── config/
│   └── default_rules.json      # [TR/EN] Özelleştirilebilir dil, derlem ve konu kuralları / Customizable rules
├── zotero_manager/
│   ├── __init__.py             # [TR/EN] Paket tanımı / Package metadata
│   ├── detector.py             # [TR/EN] Otomatik Zotero dizini ve süreç tespiti / Auto-detection & process control
│   ├── reader.py               # [TR/EN] Güvenli salt-okunur veritabanı okuyucu / Safe snapshot reader
│   ├── classifier.py           # [TR/EN] 5 boyutlu sınıflandırma motoru / 5D classification engine
│   ├── deduplicator.py         # [TR/EN] Akıllı mükerrer birleştirme motoru / Smart deduplication engine
│   ├── applier.py              # [TR/EN] SQLite yazma ve yedekleme motoru / SQLite writer & backup manager
│   ├── reporter.py             # [TR/EN] İki dilli MD ve Excel CSV rapor üretici / Bilingual report generator
│   └── web_ui.py               # [TR/EN] İki dilli Görsel Web Arayüzü / Bilingual Visual Web Dashboard
├── docs/
│   └── KULLANIM_KILAVUZU.md    # [TR/EN] Adım adım kullanım kılavuzu / Step-by-step user guide
├── reports/
│   └── zotero_derlem_raporu.md # [TR/EN] Örnek denetim raporu / Sample corpus audit report
└── tests/
    └── test_engine.py          # [TR/EN] Birim testleri / Automated unit tests
```

## 🧪 Testler / Running Tests

```bash
python -X utf8 -m unittest discover -s tests -v
```

## 📄 Lisans / License

MIT License — [`LICENSE`](file:///D:/Claude/Projects/Zotero-Derlem-Yoneticisi/LICENSE)
