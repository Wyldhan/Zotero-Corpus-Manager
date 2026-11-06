# 📖 Adım Adım Kullanım Kılavuzu (Yazılım Bilgisi Gerektirmez)

Bu kılavuz, hiçbir kodlama veya komut satırı bilgisi olmadan **Zotero Derlem & Otomatik Sınıflandırma Yöneticisi**'ni nasıl kullanacağınızı anlatır.

---

## 1. İlk Hazırlık (Sadece Bir Kez Yapılır)

1. Bu projeyi GitHub sayfasındaki yeşil **`<> Code`** düğmesine tıklayıp **`Download ZIP`** diyerek bilgisayarınıza indirin ve ZIP dosyasını bir klasöre çıkartın.
2. Bilgisayarınızda **Python 3** kurulu değilse [python.org/downloads](https://www.python.org/downloads/) adresinden indirip kurun *(Kurulum ekranında en alttaki **"Add Python to PATH"** kutucuğunu işaretlemeyi unutmayın).*
   - **Ekstra hiçbir kütüphane (`pip install` vb.) kurmanıza gerek yoktur!** Araç tamamen standart Python ile çalışır.

---

## 2. Programı Başlatma (Çift Tıkla Çalıştırma)

- **Windows Kullanıcıları:** Klasörün içindeki **`Baslat.bat`** dosyasına çift tıklayın.
- **Mac / Linux Kullanıcıları:** Klasörün içindeki **`baslat.sh`** dosyasına çift tıklayın (veya çalıştırın).

Program Zotero klasörünüzü (`D:\Zotero`, `C:\Users\Adınız\Zotero` vb.) **otomatik olarak bulur** ve internet tarayıcınızda **Görsel Yönetim Panelini (`http://127.0.0.1:8765`)** açar.

---

## 3. Görsel Yönetim Panelinde Neler Yapabilirsiniz?

### Sekme 1: Genel Bakış & Otomatik Sınıflandırma
1. Sayfa açıldığında kütüphaneniz otomatik taranır ve üst kısımda toplam eser sayınız, bağımsız PDF sayınız ve derlem dağılımınız grafiklerle gösterilir.
2. **`✅ Sınıflandırmayı Şimdi Zotero'ya Uygula`** düğmesine tıkladığınızda:
   - Zotero açıksa güvenli bir şekilde kapatılır,
   - Veritabanınızın otomatik yedeği alınır,
   - Zotero'da 5 ana başlık altında (`1. Derlemler & Hedef Diller`, `2. Metin Diline Göre`, `3. Eser Türüne Göre`, `4. Konu & Alt Alanlara Göre`, `5. Derlem Denetim & Kalite Kontrol`) koleksiyonlar oluşturulur ve eserleriniz ilgili klasörlere yerleştirilir,
   - Her esere `#dil:...`, `#derlem:...`, `#tur:...`, `#konu:...` etiketleri eklenir,
   - Yanlışlıkla İngilizce (`en`) görünürken gerçekte Türkçe, Kirmanckî (Zazakî), Kurmancî, Soranî veya Almanca olan kayıtların `Dil (Language)` alanı düzeltilir,
   - Zotero otomatik olarak yeniden açılır.

### Sekme 2: Akıllı Mükerrer Birleştirici (Tek Dosyaya İndirme)
1. **`🔍 Mükerrerleri ve PDF Kopyalarını Analiz Et`** düğmesine tıklayın.
2. Araç, tüm PDF'lerinizin içerik özetini (SHA-256), DOI numaralarını ve künye başlıklarını karşılaştırır.
3. Tabloda her mükerrer grubu için **Korunacak Ana Kayıt (En Kapsamlı Kaynakça)** yeşil rozetle, birleştirilip silinecek kopyalar sarı rozetle gösterilir.
4. **`✨ Tüm Mükerrerleri Birleştir ve Tek Dosyaya İndir`** düğmesine tıkladığınızda:
   - Kopyalardaki eksik künye bilgileri (DOI, özet, cilt, sayı, sayfa, ISBN) ve notlar en kapsamlı ana kayda aktarılır,
   - En sağlam/okunabilir tek PDF dosyası ana kayda bağlanır (önceden başıboş duran PDF'ler ilgili künyenin alt eki olur),
   - Fazlalık PDF dosyaları ve mükerrer kayıtlar silinerek yüzlerce MB disk alanı boşaltılır.

### Sekme 3: Kayıt Gezgini & Excel Raporu
- Üst bardaki **`📊 Excel (CSV) İndir`** veya **`📄 Markdown Rapor İndir`** düğmeleriyle tüm kütüphanenizin sınıflandırma dökümünü bilgisayarınıza indirebilirsiniz.

### Sekme 4: Kural & Derlem Ayarları
- Kendi çalışma alanınıza özel yeni bir derlem veya konu başlığı eklemek isterseniz **4. Kural & Derlem Ayarları** sekmesinden anahtar kelimeleri düzenleyip **`💾 Kuralları Kaydet ve Yeniden Tara`** düğmesine basmanız yeterlidir.

### Sekme 5: Yedekleme & Geri Yükleme
- Yapılan her işlemden önce otomatik `.bak` yedeği alınır. İstediğiniz zaman **5. Yedekleme & Geri Yükleme** sekmesinden **`⏪ Bu Yedeğe Geri Dön`** düğmesine tıklayarak tek tıkla önceki duruma dönebilirsiniz.
