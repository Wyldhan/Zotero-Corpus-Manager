# 📖 Adım Adım Kullanım Kılavuzu / Step-by-Step User Guide

<p align="center">
  <strong><a href="#-türkçe-kullanım-kılavuzu">🇹🇷 Türkçe Kullanım Kılavuzu</a></strong> &nbsp;|&nbsp;
  <strong><a href="#-english-user-guide">🇬🇧 English User Guide</a></strong>
</p>

---

## 🇹🇷 Türkçe Kullanım Kılavuzu

Bu kılavuz, **hiçbir yazılım veya programlama bilgisi olmayan** araştırmacıların Zotero kütüphanelerini birkaç tıklamayla nasıl sınıflandırabileceğini ve mükerrer (çift) dosyaları nasıl temizleyebileceğini anlatır.

### 1. Hazırlık: Bilgisayarınızda Python Var mı?
Bu araç çalışmak için yalnızca standart **Python 3** yorumlayıcısına ihtiyaç duyar (ekstra hiçbir kütüphane kurulumu gerekmez).
- Eğer bilgisayarınızda Python yüklü değilse [python.org/downloads](https://www.python.org/downloads/) adresinden indirip kurarken en alttaki **"Add python.exe to PATH"** kutucuğunu işaretlemeniz yeterlidir.

### 2. Programı Başlatma
1. **Windows Kullanıcıları:** Klasörün içindeki **[`Baslat.bat`](file:///D:/Claude/Projects/Zotero-Derlem-Yoneticisi/Baslat.bat)** dosyasına **çift tıklayın**.
2. **macOS / Linux Kullanıcıları:** Terminalde `./baslat.sh` komutunu çalıştırın.
3. Saniyeler içinde internet tarayıcınızda (Chrome, Edge, Firefox, Safari) **`http://127.0.0.1:8765`** adresinde görsel kontrol paneliniz açılacaktır. *(Program tamamen kendi bilgisayarınızda çalışır, verileriniz internete gönderilmez.)*
4. Sağ üst köşedeki **`🇹🇷 TR | 🇬🇧 EN`** düğmesine tıklayarak arayüz dilini istediğiniz an Türkçe veya İngilizce yapabilirsiniz.

### 3. Sekmelerin Kullanımı

#### 🔹 Sekme 1: Genel Bakış & Otomatik Sınıflandırma
- Sayfa açıldığında Zotero klasörünüz (ör. `D:\Zotero` veya `C:\Users\Adınız\Zotero`) otomatik olarak bulunur ve taranır.
- **"✅ Sınıflandırmayı Şimdi Zotero'ya Uygula"** düğmesine bastığınızda:
  1. Zotero açıksa güvenli şekilde kapatılır.
  2. Veritabanınızın tam yedeği alınır.
  3. 5 ana kategori altında 52 koleksiyon ve alt-koleksiyon oluşturulur, tüm eserler ilgili koleksiyonlara yerleştirilir ve hatalı dil kodları (`zza`, `kmr`, `ckb`, `tr`, `en`) düzeltilir.
  4. Zotero otomatik olarak yeniden başlatılır.

#### 🔹 Sekme 2: Akıllı Mükerrer (Duplicate) Birleştirici
- **"🔍 Mükerrerleri ve PDF Kopyalarını Analiz Et"** düğmesine tıkladığınızda kütüphanenizdeki tüm PDF'lerin içerik özetleri (SHA-256), DOI numaraları ve başlıkları karşılaştırılır.
- Tabloda her mükerrer grubu için **Korunacak Ana Kayıt (En Kapsamlı Kaynakça)** yeşil etiketle, birleştirilip silinecek kopyalar sarı etiketle gösterilir.
- **"✨ Tüm Mükerrerleri Birleştir ve Tek Dosyaya İndir"** düğmesine bastığınızda:
  - Kopyalardaki eksik künye bilgileri (cilt, sayı, sayfa, DOI, özet, notlar) ana kayda aktarılır.
  - En sağlam **tek PDF dosyası** ana kayda bağlanır.
  - Fazlalık kayıtlar ve kopya PDF klasörleri silinerek disk alanı kazanılır.

#### 🔹 Sekme 3, 4 ve 5: Kayıt Gezgini, Kurallar ve Yedekler
- **Kayıt Gezgini:** Kütüphanenizdeki tüm kayıtları `#derlem:zazaki-kirmancki`, `#tur:sozluk`, `#kontrol:ocr-gerekli` gibi etiketlerle anında filtreleyebilirsiniz.
- **Kural & Derlem Ayarları:** [`config/default_rules.json`](file:///D:/Claude/Projects/Zotero-Derlem-Yoneticisi/config/default_rules.json) dosyasındaki anahtar kelimeleri doğrudan tarayıcı üzerinden düzenleyip kaydedebilirsiniz.
- **Yedekleme & Geri Yükleme:** Alınan tüm `.bak` yedeklerini görebilir, **"⏪ Bu Yedeğe Geri Dön"** düğmesiyle istediğiniz tarihteki duruma tek tıkla dönebilirsiniz.

---

## 🇬🇧 English User Guide

This guide explains how researchers with **zero programming knowledge** can automatically classify their Zotero libraries and consolidate duplicate PDF files in just a few clicks.

### 1. Prerequisite: Python 3
This tool uses only the built-in Python 3 Standard Library (no external packages or `pip install` needed).
- If Python is not installed on your computer, download it from [python.org/downloads](https://www.python.org/downloads/) and check **"Add python.exe to PATH"** during installation.

### 2. Launching the Application
1. **Windows Users:** Double-click **[`Baslat.bat`](file:///D:/Claude/Projects/Zotero-Derlem-Yoneticisi/Baslat.bat)**.
2. **macOS / Linux Users:** Run `./baslat.sh` in your terminal.
3. Your default web browser will automatically open **`http://127.0.0.1:8765`**. *(Everything runs 100% locally on your machine; no data ever leaves your computer.)*
4. Click the **`🇹🇷 TR | 🇬🇧 EN`** button in the top-right header at any time to switch the interface between Turkish and English.

### 3. Using the Dashboard Tabs

#### 🔹 Tab 1: Overview & Automatic Classification
- On startup, your Zotero data directory (`D:\Zotero`, `~/Zotero`, etc.) is auto-detected and scanned read-only.
- Clicking **"✅ Apply Classification to Zotero Now"**:
  1. Gracefully closes Zotero if it is currently running.
  2. Creates a timestamped `.bak` backup of `zotero.sqlite`.
  3. Builds the 52-collection hierarchy across 5 dimensions (Corpus, Document Language, Publication Type, Research Topic, Quality Audit), adds structured tags, and fixes incorrect ISO language codes (`zza`, `kmr`, `ckb`, `tr`, `en`).
  4. Automatically restarts Zotero.

#### 🔹 Tab 2: Smart Deduplicator
- Click **"🔍 Analyze Duplicates & Redundant PDFs"** to compare SHA-256 file hashes, DOIs, and normalized titles/authors across your library.
- The table displays the **Winning Master Record (Most Comprehensive Bibliography)** in green alongside the duplicate copies to be merged and removed.
- Click **"✨ Merge All Duplicates & Consolidate to Single File"** to:
  - Merge missing metadata fields (volume, issue, pages, DOI, abstract, notes, tags, collections) into the winning record.
  - Link the **single best physical PDF file** (preserving annotations) to the winning record.
  - Delete redundant duplicate records and duplicate `storage/<KEY>` folders to free disk space.

#### 🔹 Tabs 3, 4, and 5: Item Explorer, Rules & Backups
- **Item Explorer:** Instantly filter your library by title, author, or auto-tags such as `#derlem:zazaki-kirmancki`, `#tur:sozluk`, or `#kontrol:ocr-gerekli`.
- **Rules & Corpus Settings:** Customize [`config/default_rules.json`](file:///D:/Claude/Projects/Zotero-Derlem-Yoneticisi/config/default_rules.json) directly inside the browser and rescan.
- **Backup & Restore:** View all timestamped `zotero.sqlite.*.bak` backups and restore any backup with a single click on **"⏪ Restore This Backup"**.
