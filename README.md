# 📚 Zotero Derlem & Otomatik Sınıflandırma Yöneticisi

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Sıfır Bağımlılık](https://img.shields.io/badge/Ba%C4%9F%C4%B1ml%C4%B1l%C4%B1k-S%C4%B1f%C4%B1r%20(Stdlib)-brightgreen.svg)](#)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](LICENSE)

**Zotero Derlem & Otomatik Sınıflandırma Yöneticisi**, özellikle dilbilim, Kürdoloji (Zazakî/Kirmanckî, Kurmancî, Soranî, Goranî), İrani diller, Türkoloji ve doğal dil işleme (NLP) araştırmacıları için geliştirilmiş; **hiçbir yazılım veya komut satırı bilgisi gerektirmeyen** görsel bir Zotero kütüphane düzenleme, derlem denetleme ve akıllı mükerrer (duplicate) birleştirme aracıdır.

---

## ✨ Temel Özellikler

1. **🖱️ Çift Tıkla Görsel Web Arayüzü (Sıfır Kurulum):**
   - `pip install` veya karmaşık terminal komutları gerektirmez. `Baslat.bat` dosyasına çift tıkladığınızda Zotero veri klasörünüzü (`prefs.js` üzerinden özel sürücülerde olsa bile) otomatik bulur ve tarayıcınızda görsel yönetim panelini açar.
2. **🧠 5 Boyutlu Otomatik Sınıflandırma (Üst Veri + PDF Tam Metin Analizi):**
   - Yalnızca eser başlığına değil, Zotero'nun `.zotero-ft-cache` tam metin indekslerine de bakarak her kaydı 5 boyutta sınıflandırır:
     - **1. Hedef Dil & Derlem (`#derlem:...`):** Zazakî/Kirmanckî, Kurmancî, Soranî/Goranî, Genel Kürdoloji, İrani Diller, Türkçe/Türkoloji, Genel Dilbilim.
     - **2. Gerçek Metin Dili (`#dil:...`):** Otomatik DOI/PDF aktarımlarının yanlışlıkla `en` (İngilizce) olarak işaretlediği Türkçe (`tr`), Kirmanckî (`zza`), Kurmancî (`kmr`), Soranî (`ckb`), Almanca (`de`) ve Farsça/Arapça (`fa`) eserlerin dil kodlarını tespit edip düzeltir.
     - **3. Eser Türü (`#tur:...`):** Sözlük, Gramer Kitabı, Tez, Dergi/Gazete Sayısı, Edebi/Folklorik Metin, Hakemli Makale, Sempozyum Bildirisi, Kitap/Kitap Bölümü, Ön Baskı (arXiv).
     - **4. Araştırma Konusu (`#konu:...`):** Morfoloji & Allomorfi, Fonoloji & Sesbilim, Sözdizimi & Tipoloji, Anlambilim & Kip-Zaman (TAM), Sözlükbilim & Etimoloji, Derlem Dilbilimi, NLP & Hesaplamalı Dilbilim, Söylem & Toplumdilbilim, Diyalektoloji, Dil Eğitimi, Edebiyat & Tarih.
     - **5. Derlem Kalite Kontrol (`#kontrol:...`):** Mükerrer adayları, üst kaydı olmayan (`standalone`) PDF'ler, fiziksel dosyası eksik kayıtlar, metin katmanı olmayan (**OCR gerektiren**) taranmış PDF'ler.
3. **🧹 Akıllı Mükerrer Birleştirici ve Tek Dosyaya İndirme:**
   - **SHA-256 PDF Dosya Özeti**, **DOI** ve **Normalize Başlık/Yazar** eşleşmelerini birlikte kullanır.
   - Her mükerrer kümesinde **en kapsamlı kaynakçaya (üst veriye) sahip olan kaydı** otomatik seçer.
   - Silinecek kopyalardaki eksik künye alanlarını (DOI, özet, dergi, sayı, sayfa, ISBN), koleksiyonları ve notları ana kayda aktarır.
   - Kümedeki PDF'ler arasından **en sağlam tek PDF dosyasını** ana kayda bağlar (başıboş duran PDF'leri ilgili künyenin alt eki yapar) ve fazlalık PDF klasörlerini silerek yüzlerce MB disk alanı kazandırır.
   - **Yanlış Birleştirme Korumaları:** Üniversite tez kapağı başlıklarını (*"T.C. ... Üniversitesi Sosyal Bilimler Enstitüsü"*, *"A Thesis Submitted to..."*), aynı kitaptaki farklı kitap bölümlerini (`bookSection`) ve kitap eleştirilerini (*book review*) birbirine karıştırmaz.
4. **💾 Otomatik Yedekleme ve Tek Tıkla Geri Yükleme:**
   - Veritabanına dokunan her işlemden önce tarih damgalı `.bak` yedeği alır; arayüzden tek tıkla istediğiniz yedeğe geri dönebilirsiniz.

---

## 🚀 Hızlı Başlangıç (Yazılım Bilgisi Olmayanlar İçin)

1. Bu sayfanın sağ üst kısmındaki yeşil **`<> Code`** düğmesine tıklayıp **`Download ZIP`** seçeneğiyle projeyi indirin ve klasöre çıkartın.
2. Klasörün içindeki **`Baslat.bat`** (Windows) veya **`baslat.sh`** (macOS / Linux) dosyasına çift tıklayın.
3. Tarayıcınızda açılan yönetim panelinden:
   - **`✅ Sınıflandırmayı Şimdi Zotero'ya Uygula`** düğmesiyle tüm koleksiyon ve etiketleri oluşturun.
   - **`2. Akıllı Mükerrer Birleştirici`** sekmesinden mükerrer kayıtları ve kopya PDF'leri tek dosyaya indirin.

> 📘 Daha detaylı açıklamalar için **[Adım Adım Kullanım Kılavuzu](docs/KULLANIM_KILAVUZU.md)** sayfasına göz atabilirsiniz.

---

## 💻 İleri Seviye (Komut Satırı / CLI) Kullanımı

Aracı komut satırından veya otomasyon betiklerinizden de çalıştırabilirsiniz:

```bash
# 1. Görsel Web Arayüzünü başlat (Varsayılan)
python zotero_cli.py gui

# 2. Salt-okunur tarama yap ve Markdown / Excel (CSV) / JSON raporları üret
python zotero_cli.py scan

# 3. Otomatik sınıflandırmayı, koleksiyon ağacını ve dil düzeltmelerini uygula
python zotero_cli.py classify

# 4. Mükerrer birleştirme planını önizle (hiçbir şeyi silmez)
python zotero_cli.py dedup --dry-run

# 5. Mükerrerleri en kapsamlı kaynakçayla birleştir ve tek dosyaya indir
python zotero_cli.py dedup

# 6. Alınan veritabanı yedeklerini listele ve geri yükle
python zotero_cli.py backups
python zotero_cli.py restore "D:\Zotero\zotero.sqlite.pre-dedup_20261106.bak"
```

---

## 🗂️ Proje Mimarisi

```text
Zotero-Derlem-Yoneticisi/
├── Baslat.bat                  # Windows için çift tıkla görsel arayüz başlatıcı
├── baslat.sh                   # macOS / Linux için başlatıcı
├── zotero_cli.py               # Birleşik CLI ve GUI giriş noktası
├── config/
│   └── default_rules.json      # Kod yazmadan düzenlenebilir dil, derlem ve konu kuralları
├── zotero_manager/
│   ├── __init__.py
│   ├── detector.py             # Zotero veri dizini (prefs.js) ve süreç tespiti
│   ├── reader.py               # Salt-okunur güvenli SQLite + .zotero-ft-cache okuyucu
│   ├── classifier.py           # 5 boyutlu sınıflandırma motoru
│   ├── deduplicator.py         # SHA-256, DOI ve Başlık/Yazar tabanlı mükerrer birleştirici
│   ├── applier.py              # Yedekleme, geri yükleme ve SQLite işlem motoru
│   ├── reporter.py             # Markdown, Excel (UTF-8 BOM CSV) ve JSON rapor üreteci
│   └── web_ui.py               # Sıfır bağımlılıklı yerel Görsel Web Arayüzü
├── docs/
│   └── KULLANIM_KILAVUZU.md    # Son kullanıcılar için adım adım kılavuz
├── tests/
│   └── test_engine.py          # Otomatik birim testleri
├── pyproject.toml              # Standart Python paket yapılandırması
└── LICENSE                     # MIT Lisansı
```

---

## 🧪 Testleri Çalıştırma

```bash
python -m unittest discover -s tests -v
```

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında açık kaynaklı olarak sunulmaktadır.
