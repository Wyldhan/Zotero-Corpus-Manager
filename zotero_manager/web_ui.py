"""
[TR] Yazılım bilgisi gerektirmeyen, sıfır bağımlılıklı, iki dilli (TR/EN) yerel Görsel Web Arayüzü (Dashboard).
     Üst bardaki 🇹🇷 TR | 🇬🇧 EN düğmesiyle tüm arayüz metinleri anında Türkçe ve İngilizce arasında değiştirilebilir.
[EN] Zero-dependency, bilingual (TR/EN) local Visual Web Dashboard requiring zero coding knowledge.
     All UI labels, messages, and tables can be toggled instantly between Turkish and English via the 🇹🇷 TR | 🇬🇧 EN button.
"""
from __future__ import annotations

import json
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .applier import apply_classification_sqlite, create_backup, list_backups, restore_backup
from .classifier import classify_library, load_rules, DEFAULT_RULES_PATH
from .deduplicator import execute_deduplication, find_duplicate_clusters
from .detector import find_zotero_data_dir, is_zotero_running, start_zotero, stop_zotero_gracefully
from .reader import load_library_snapshot
from .reporter import compute_summary_stats, generate_csv_report, generate_markdown_report

# [TR] Tek dosya içinde gömülü, iki dilli (TR/EN) HTML5 + CSS3 + Vanilla JS Görsel Arayüzü
# [EN] Self-contained, bilingual (TR/EN) HTML5 + CSS3 + Vanilla JS Visual Dashboard
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zotero Derlem & Otomatik Sınıflandırma Yöneticisi | Zotero Corpus & Classification Manager</title>
<style>
  :root {
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #0f172a;
    --muted: #64748b;
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --success: #16a34a;
    --warning: #d97706;
    --danger: #dc2626;
    --border: #e2e8f0;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.5;
  }
  header {
    background: #1e293b; color: #fff; padding: 1.1rem 2rem;
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;
  }
  header h1 { margin: 0; font-size: 1.3rem; display: flex; align-items: center; gap: 0.6rem; }
  .header-right { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
  .status-pill {
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: rgba(255,255,255,0.12); padding: 0.4rem 0.9rem; border-radius: 999px; font-size: 0.85rem;
  }
  .lang-switch {
    background: rgba(255,255,255,0.16); color: #fff; border: 1px solid rgba(255,255,255,0.3);
    padding: 0.38rem 0.85rem; border-radius: 999px; font-size: 0.84rem; font-weight: 700; cursor: pointer;
  }
  .lang-switch:hover { background: rgba(255,255,255,0.28); }
  .dot { width: 10px; height: 10px; border-radius: 50%; background: #22c55e; display: inline-block; }
  .dot.closed { background: #94a3b8; }
  .container { max-width: 1280px; margin: 1.5rem auto; padding: 0 1.5rem; }
  .dir-bar {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 1.25rem; display: flex; align-items: center; gap: 0.8rem; flex-wrap: wrap;
    margin-bottom: 1.25rem; box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }
  .dir-bar input {
    flex: 1; min-width: 260px; padding: 0.55rem 0.8rem; border: 1px solid var(--border);
    border-radius: 6px; font-size: 0.95rem;
  }
  button {
    cursor: pointer; border: none; border-radius: 7px; padding: 0.6rem 1.1rem;
    font-size: 0.92rem; font-weight: 600; transition: all 0.15s; display: inline-flex; align-items: center; gap: 0.4rem;
  }
  .btn-primary { background: var(--primary); color: #fff; }
  .btn-primary:hover { background: var(--primary-hover); }
  .btn-success { background: var(--success); color: #fff; }
  .btn-success:hover { filter: brightness(0.93); }
  .btn-danger { background: var(--danger); color: #fff; }
  .btn-outline { background: #fff; color: var(--text); border: 1px solid var(--border); }
  .btn-outline:hover { background: #f1f5f9; }
  button:disabled { opacity: 0.55; cursor: not-allowed; }
  .tabs {
    display: flex; gap: 0.5rem; border-bottom: 2px solid var(--border); margin-bottom: 1.25rem; flex-wrap: wrap;
  }
  .tab-btn {
    background: transparent; color: var(--muted); border-radius: 8px 8px 0 0;
    padding: 0.75rem 1.25rem; font-weight: 600; border-bottom: 3px solid transparent; margin-bottom: -2px;
  }
  .tab-btn.active { color: var(--primary); border-bottom-color: var(--primary); background: #fff; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }
  .kpi-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;
  }
  .kpi-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 1.1rem 1.25rem;
  }
  .kpi-card .label { color: var(--muted); font-size: 0.85rem; font-weight: 600; }
  .kpi-card .val { font-size: 1.85rem; font-weight: 700; margin-top: 0.25rem; color: var(--text); }
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 1.25rem; margin-bottom: 1.5rem; }
  .card {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }
  .card h3 { margin-top: 0; margin-bottom: 0.9rem; font-size: 1.05rem; border-bottom: 1px solid var(--border); padding-bottom: 0.6rem; }
  .bar-row { margin-bottom: 0.65rem; }
  .bar-label { display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 0.2rem; }
  .bar-track { background: #f1f5f9; height: 9px; border-radius: 99px; overflow: hidden; }
  .bar-fill { background: var(--primary); height: 100%; border-radius: 99px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  th, td { text-align: left; padding: 0.65rem 0.75rem; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { background: #f8fafc; font-weight: 600; color: var(--muted); }
  .badge {
    display: inline-block; padding: 0.15rem 0.5rem; border-radius: 5px; font-size: 0.76rem;
    font-weight: 600; background: #e0e7ff; color: #1e40af; margin: 0.1rem;
  }
  .badge.warn { background: #fef3c7; color: #92400e; }
  .badge.ok { background: #dcfce7; color: #166534; }
  .toast {
    display: none; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1.25rem;
    font-weight: 500; border: 1px solid transparent;
  }
  .toast.info { display: block; background: #eff6ff; color: #1e40af; border-color: #bfdbfe; }
  .toast.success { display: block; background: #f0fdf4; color: #166534; border-color: #bbf7d0; }
  .toast.error { display: block; background: #fef2f2; color: #991b1b; border-color: #fecaca; }
  .check-group { display: flex; gap: 1.25rem; flex-wrap: wrap; margin: 1rem 0; }
  .check-group label { display: flex; align-items: center; gap: 0.45rem; font-size: 0.92rem; cursor: pointer; }
  textarea.code-editor {
    width: 100%; height: 420px; font-family: Consolas, Monaco, monospace; font-size: 0.86rem;
    padding: 0.9rem; border: 1px solid var(--border); border-radius: 8px; background: #0f172a; color: #f8fafc;
  }
</style>
</head>
<body>

<header>
  <h1 data-i18n="app_title">📚 Zotero Derlem & Otomatik Sınıflandırma Yöneticisi</h1>
  <div class="header-right">
    <div class="status-pill">
      <span class="dot" id="zotDot"></span>
      <span id="zotStatusText">Zotero...</span>
    </div>
    <button class="lang-switch" onclick="toggleLang()" id="btnLangSwitch" title="Dili Değiştir / Switch Language">🇹🇷 TR | 🇬🇧 EN</button>
  </div>
</header>

<div class="container">
  <div class="dir-bar">
    <strong data-i18n="zdir_label">Zotero Klasörü:</strong>
    <input type="text" id="zdirInput" placeholder="D:\Zotero">
    <button class="btn-primary" onclick="scanLibrary()" id="btnScan" data-i18n="btn_scan">🔍 Kütüphaneyi Tara</button>
    <button class="btn-outline" onclick="downloadReport('md')" data-i18n="btn_dl_md">📄 Markdown Rapor İndir</button>
    <button class="btn-outline" onclick="downloadReport('csv')" data-i18n="btn_dl_csv">📊 Excel (CSV) İndir</button>
  </div>

  <div id="toastBox" class="toast"></div>

  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('tab-overview', this)" data-i18n="tab_1">1. Genel Bakış & Sınıflandırma</button>
    <button class="tab-btn" onclick="switchTab('tab-dedup', this)" data-i18n="tab_2">2. Akıllı Mükerrer Birleştirici</button>
    <button class="tab-btn" onclick="switchTab('tab-explorer', this)" data-i18n="tab_3">3. Kayıt Gezgini</button>
    <button class="tab-btn" onclick="switchTab('tab-rules', this)" data-i18n="tab_4">4. Kural & Derlem Ayarları</button>
    <button class="tab-btn" onclick="switchTab('tab-backups', this)" data-i18n="tab_5">5. Yedekleme & Geri Yükleme</button>
  </div>

  <!-- TAB 1: OVERVIEW & APPLY CLASSIFICATION -->
  <div id="tab-overview" class="tab-panel active">
    <div class="kpi-grid">
      <div class="kpi-card"><div class="label" data-i18n="kpi_total">Toplam Üst Seviye Kayıt</div><div class="val" id="kpiTotal">-</div></div>
      <div class="kpi-card"><div class="label" data-i18n="kpi_regular">Tam Künyeli Bibliyografik Kayıt</div><div class="val" id="kpiRegular">-</div></div>
      <div class="kpi-card"><div class="label" data-i18n="kpi_standalone">Üst Kaydı Olmayan (Standalone) PDF</div><div class="val" id="kpiStandalone">-</div></div>
      <div class="kpi-card"><div class="label" data-i18n="kpi_zazaki">Zazakî / Kirmanckî Derlemi</div><div class="val" id="kpiZazaki">-</div></div>
      <div class="kpi-card"><div class="label" data-i18n="kpi_kurdish">Kürtçe (Kurmancî / Soranî / Genel)</div><div class="val" id="kpiKurdish">-</div></div>
    </div>

    <div class="card" style="margin-bottom: 1.5rem; border-left: 4px solid var(--primary);">
      <h3 data-i18n="apply_box_title">⚡ Tek Tıkla Otomatik Sınıflandırmayı Zotero'ya Uygula</h3>
      <p style="margin: 0.2rem 0 0.8rem; color: var(--muted); font-size: 0.92rem;" data-i18n="apply_box_desc">
        Kütüphanenizdeki tüm kayıtları dil, hedef derlem, eser türü, araştırma konusu ve kalite kontrol durumuna göre
        otomatik olarak Zotero koleksiyonlarına ayırır, etiketler ve hatalı dil kodlarını düzeltir. İşlem öncesi otomatik yedek alınır.
      </p>
      <div class="check-group">
        <label><input type="checkbox" id="chkCols" checked> <span data-i18n="chk_cols">Koleksiyon ve Alt-Koleksiyon Ağacını Oluştur / Güncelle</span></label>
        <label><input type="checkbox" id="chkTags" checked> <span data-i18n="chk_tags">Otomatik Etiketleri (#dil:, #derlem:, #tur:, #konu:) Ekle</span></label>
        <label><input type="checkbox" id="chkLang" checked> <span data-i18n="chk_lang">Hatalı Dil Kodlarını (zza, kmr, ckb, tr, en) Düzelt</span></label>
        <label><input type="checkbox" id="chkRestart" checked> <span data-i18n="chk_restart">Zotero Açıksa Güvenli Kapatıp İşlem Sonrası Yeniden Başlat</span></label>
      </div>
      <button class="btn-success" onclick="applyClassification()" id="btnApplyClass" data-i18n="btn_apply_class">✅ Sınıflandırmayı Şimdi Zotero'ya Uygula</button>
    </div>

    <div class="grid-2">
      <div class="card"><h3 data-i18n="chart_corpus">1. Derlemler & Hedef Diller (#derlem:...)</h3><div id="barsCorpus"></div></div>
      <div class="card"><h3 data-i18n="chart_lang">2. Metin Diline Göre (#dil:...)</h3><div id="barsLang"></div></div>
      <div class="card"><h3 data-i18n="chart_type">3. Eser Türüne Göre (#tur:...)</h3><div id="barsType"></div></div>
      <div class="card"><h3 data-i18n="chart_topic">4. Konu & Alt Alanlara Göre (#konu:...)</h3><div id="barsTopic"></div></div>
    </div>

    <div class="card">
      <h3 data-i18n="chart_audit">5. Derlem Denetim & Kalite Kontrol Bulguları (#kontrol:...)</h3>
      <div id="barsAudit"></div>
    </div>
  </div>

  <!-- TAB 2: SMART DEDUPLICATOR -->
  <div id="tab-dedup" class="tab-panel">
    <div class="card" style="margin-bottom: 1.25rem;">
      <h3 data-i18n="dedup_title">🧹 Akıllı Mükerrer (Duplicate) Tespit ve Tek Dosyaya İndirme</h3>
      <p style="color: var(--muted); font-size: 0.92rem; margin-top: 0;" data-i18n="dedup_desc">
        SHA-256 PDF dosya özeti, DOI ve normalize edilmiş başlık/yazar kurallarına göre mükerrer kayıtları bulur.
        Her kümede en kapsamlı kaynakçaya sahip olan ana kaydı korur; diğer kopyalardaki eksik künye alanlarını,
        koleksiyonları, notları ve en sağlam tek PDF dosyasını ana kayda bağlayıp geri kalan kopyaları siler.
      </p>
      <div style="display:flex; gap:0.8rem; flex-wrap:wrap; align-items:center;">
        <button class="btn-primary" onclick="scanDuplicates()" id="btnScanDup" data-i18n="btn_scan_dup">🔍 Mükerrerleri ve PDF Kopyalarını Analiz Et</button>
        <button class="btn-danger" onclick="executeDedup()" id="btnExecDup" disabled data-i18n="btn_exec_dup">✨ Tüm Mükerrerleri Birleştir ve Tek Dosyaya İndir</button>
        <span id="dupSummaryBadge" style="font-weight:600; color:var(--muted);"></span>
      </div>
    </div>
    <div class="card">
      <h3 data-i18n="dedup_table_title">Tespit Edilen Mükerrer Kümeleri</h3>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th data-i18n="th_winner">Korunacak Ana Kayıt (En Kapsamlı Kaynakça)</th>
              <th data-i18n="th_losers">Birleştirilip Silinecek Mükerrer Kopyalar</th>
              <th data-i18n="th_pdf">Bağlanacak Tek PDF & Kazanç</th>
            </tr>
          </thead>
          <tbody id="dupTableBody">
            <tr><td colspan="4" style="color:var(--muted);" data-i18n="dedup_empty_hint">Analiz başlatmak için yukarıdaki düğmeye tıklayın.</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 3: ITEM EXPLORER -->
  <div id="tab-explorer" class="tab-panel">
    <div class="card">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap; margin-bottom:1rem;">
        <h3 style="margin:0; border:none; padding:0;" data-i18n="explorer_title">Kayıt Gezgini (İlk 250 Eşleşme)</h3>
        <input type="text" id="searchFilter" placeholder="Başlık, yazar, #derlem:zazaki, #tur:sozluk..." oninput="renderExplorer()" style="min-width:320px; padding:0.5rem 0.8rem; border:1px solid var(--border); border-radius:6px;">
      </div>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Key</th>
              <th data-i18n="th_type">Tür</th>
              <th data-i18n="th_title_author">Başlık & Yazar</th>
              <th data-i18n="th_lang">Dil</th>
              <th data-i18n="th_tags">Derlem & Konu Etiketleri</th>
            </tr>
          </thead>
          <tbody id="explorerBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 4: RULES EDITOR -->
  <div id="tab-rules" class="tab-panel">
    <div class="card">
      <h3 data-i18n="rules_title">⚙️ Sınıflandırma Kuralları (`config/default_rules.json`)</h3>
      <p style="color:var(--muted); font-size:0.9rem; margin-top:0;" data-i18n="rules_desc">
        Yeni bir derlem, dil veya konu anahtar kelimesi eklemek için aşağıdaki JSON yapısını düzenleyip kaydedebilirsiniz.
      </p>
      <textarea id="rulesEditor" class="code-editor"></textarea>
      <div style="margin-top:0.9rem;">
        <button class="btn-success" onclick="saveRules()" data-i18n="btn_save_rules">💾 Kuralları Kaydet ve Yeniden Tara</button>
      </div>
    </div>
  </div>

  <!-- TAB 5: BACKUPS -->
  <div id="tab-backups" class="tab-panel">
    <div class="card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
        <h3 style="margin:0; border:none;" data-i18n="backups_title">💾 Veritabanı Yedekleri (`zotero.sqlite.*.bak`)</h3>
        <button class="btn-primary" onclick="manualBackup()" data-i18n="btn_new_backup">➕ Şimdi Yeni Yedek Al</button>
      </div>
      <table>
        <thead>
          <tr>
            <th data-i18n="th_bak_file">Yedek Dosyası</th>
            <th data-i18n="th_bak_date">Tarih</th>
            <th data-i18n="th_bak_size">Boyut</th>
            <th data-i18n="th_bak_action">İşlem</th>
          </tr>
        </thead>
        <tbody id="backupTableBody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
// [TR] İki dilli (Türkçe & İngilizce) kullanıcı arayüzü sözlüğü
// [EN] Bilingual (Turkish & English) user interface translation dictionary
const I18N = {
  tr: {
    app_title: "📚 Zotero Derlem & Otomatik Sınıflandırma Yöneticisi",
    zdir_label: "Zotero Klasörü:",
    btn_scan: "🔍 Kütüphaneyi Tara",
    btn_dl_md: "📄 Markdown Rapor İndir",
    btn_dl_csv: "📊 Excel (CSV) İndir",
    tab_1: "1. Genel Bakış & Sınıflandırma",
    tab_2: "2. Akıllı Mükerrer Birleştirici",
    tab_3: "3. Kayıt Gezgini",
    tab_4: "4. Kural & Derlem Ayarları",
    tab_5: "5. Yedekleme & Geri Yükleme",
    kpi_total: "Toplam Üst Seviye Kayıt",
    kpi_regular: "Tam Künyeli Bibliyografik Kayıt",
    kpi_standalone: "Üst Kaydı Olmayan (Standalone) PDF",
    kpi_zazaki: "Zazakî / Kirmanckî Derlemi",
    kpi_kurdish: "Kürtçe (Kurmancî / Soranî / Genel)",
    apply_box_title: "⚡ Tek Tıkla Otomatik Sınıflandırmayı Zotero'ya Uygula",
    apply_box_desc: "Kütüphanenizdeki tüm kayıtları dil, hedef derlem, eser türü, araştırma konusu ve kalite kontrol durumuna göre otomatik olarak Zotero koleksiyonlarına ayırır, etiketler ve hatalı dil kodlarını düzeltir. İşlem öncesi otomatik yedek alınır.",
    chk_cols: "Koleksiyon ve Alt-Koleksiyon Ağacını Oluştur / Güncelle",
    chk_tags: "Otomatik Etiketleri (#dil:, #derlem:, #tur:, #konu:) Ekle",
    chk_lang: "Hatalı Dil Kodlarını (zza, kmr, ckb, tr, en) Düzelt",
    chk_restart: "Zotero Açıksa Güvenli Kapatıp İşlem Sonrası Yeniden Başlat",
    btn_apply_class: "✅ Sınıflandırmayı Şimdi Zotero'ya Uygula",
    chart_corpus: "1. Derlemler & Hedef Diller (#derlem:...)",
    chart_lang: "2. Metin Diline Göre (#dil:...)",
    chart_type: "3. Eser Türüne Göre (#tur:...)",
    chart_topic: "4. Konu & Alt Alanlara Göre (#konu:...)",
    chart_audit: "5. Derlem Denetim & Kalite Kontrol Bulguları (#kontrol:...)",
    dedup_title: "🧹 Akıllı Mükerrer (Duplicate) Tespit ve Tek Dosyaya İndirme",
    dedup_desc: "SHA-256 PDF dosya özeti, DOI ve normalize edilmiş başlık/yazar kurallarına göre mükerrer kayıtları bulur. Her kümede en kapsamlı kaynakçaya sahip olan ana kaydı korur; diğer kopyalardaki eksik künye alanlarını, koleksiyonları, notları ve en sağlam tek PDF dosyasını ana kayda bağlayıp geri kalan kopyaları siler.",
    btn_scan_dup: "🔍 Mükerrerleri ve PDF Kopyalarını Analiz Et",
    btn_exec_dup: "✨ Tüm Mükerrerleri Birleştir ve Tek Dosyaya İndir",
    dedup_table_title: "Tespit Edilen Mükerrer Kümeleri",
    th_winner: "Korunacak Ana Kayıt (En Kapsamlı Kaynakça)",
    th_losers: "Birleştirilip Silinecek Mükerrer Kopyalar",
    th_pdf: "Bağlanacak Tek PDF & Kazanç",
    dedup_empty_hint: "Analiz başlatmak için yukarıdaki düğmeye tıklayın.",
    explorer_title: "Kayıt Gezgini (İlk 250 Eşleşme)",
    th_type: "Tür",
    th_title_author: "Başlık & Yazar",
    th_lang: "Dil",
    th_tags: "Derlem & Konu Etiketleri",
    rules_title: "⚙️ Sınıflandırma Kuralları (`config/default_rules.json`)",
    rules_desc: "Yeni bir derlem, dil veya konu anahtar kelimesi eklemek için aşağıdaki JSON yapısını düzenleyip kaydedebilirsiniz.",
    btn_save_rules: "💾 Kuralları Kaydet ve Yeniden Tara",
    backups_title: "💾 Veritabanı Yedekleri (`zotero.sqlite.*.bak`)",
    btn_new_backup: "➕ Şimdi Yeni Yedek Al",
    th_bak_file: "Yedek Dosyası",
    th_bak_date: "Tarih",
    th_bak_size: "Boyut",
    th_bak_action: "İşlem",
    zot_open: "Zotero Açık",
    zot_closed: "Zotero Kapalı",
    no_items: "Kayıt bulunamadı.",
    scanning_msg: "⏳ Zotero veritabanı ve tam metin önbellekleri taranıyor...",
    scan_done: "✅ Tarama tamamlandı:",
    applying_msg: "⏳ Zotero yedekleniyor ve sınıflandırma uygulanıyor...",
    apply_done: "✅ Sınıflandırma başarıyla uygulandı!",
    dup_scanning_msg: "⏳ Tüm PDF dosyalarının SHA-256 özetleri, DOI ve künye başlıkları karşılaştırılıyor...",
    dup_none_left: "🎉 Kütüphanenizde hiç mükerrer kayıt veya kopya PDF kalmadı!",
    dup_confirm: "Mükerrer kayıtlar en kapsamlı kaynakçaya sahip ana kayıtla birleştirilecek, en sağlam tek PDF ana kayda bağlanacak ve geri kalan kopyalar silinecektir (işlem öncesi tam yedek alınır). Onaylıyor musunuz?",
    restore_btn: "⏪ Bu Yedeğe Geri Dön",
    restore_confirm: "Seçilen yedek dosyası aktif Zotero veritabanı olarak geri yüklenecektir. Devam edilsin mi?"
  },
  en: {
    app_title: "📚 Zotero Corpus & Automatic Classification Manager",
    zdir_label: "Zotero Directory:",
    btn_scan: "🔍 Scan Library",
    btn_dl_md: "📄 Download Markdown Report",
    btn_dl_csv: "📊 Download Excel (CSV)",
    tab_1: "1. Overview & Classification",
    tab_2: "2. Smart Deduplicator",
    tab_3: "3. Item Explorer",
    tab_4: "4. Rules & Corpus Settings",
    tab_5: "5. Backup & Restore",
    kpi_total: "Total Top-Level Items",
    kpi_regular: "Full Bibliographic Records",
    kpi_standalone: "Standalone PDFs (No Parent)",
    kpi_zazaki: "Zazaki / Kirmancki Corpus",
    kpi_kurdish: "Kurdish (Kurmanji / Sorani / General)",
    apply_box_title: "⚡ One-Click Apply Automatic Classification to Zotero",
    apply_box_desc: "Automatically organizes all items in your library into Zotero collections, adds structured tags, and fixes wrong ISO language codes based on document language, target corpus, item type, research topic, and quality audit. Creates an automatic backup beforehand.",
    chk_cols: "Create / Update Collection & Subcollection Tree",
    chk_tags: "Add Structured Auto-Tags (#dil:, #derlem:, #tur:, #konu:)",
    chk_lang: "Fix Incorrect ISO Language Codes (zza, kmr, ckb, tr, en)",
    chk_restart: "Safely Close Zotero if Running and Restart Afterwards",
    btn_apply_class: "✅ Apply Classification to Zotero Now",
    chart_corpus: "1. Target Corpora & Languages (#derlem:...)",
    chart_lang: "2. By Document Language (#dil:...)",
    chart_type: "3. By Publication Type (#tur:...)",
    chart_topic: "4. By Research Topic & Subfield (#konu:...)",
    chart_audit: "5. Corpus Audit & Quality Control Findings (#kontrol:...)",
    dedup_title: "🧹 Smart Duplicate Detection & Single-File Consolidation",
    dedup_desc: "Finds duplicate items via SHA-256 PDF file hashes, DOIs, and normalized title/author matching. Preserves the master record with the most comprehensive bibliography in each cluster; merges missing metadata fields, collections, notes, and links the single best physical PDF before deleting redundant copies.",
    btn_scan_dup: "🔍 Analyze Duplicates & Redundant PDFs",
    btn_exec_dup: "✨ Merge All Duplicates & Consolidate to Single File",
    dedup_table_title: "Detected Duplicate Clusters",
    th_winner: "Winning Master Record (Most Comprehensive Bibliography)",
    th_losers: "Duplicate Copies to Merge & Delete",
    th_pdf: "Single Best PDF to Link & Space Saved",
    dedup_empty_hint: "Click the analyze button above to start duplicate detection.",
    explorer_title: "Item Explorer (First 250 Matches)",
    th_type: "Type",
    th_title_author: "Title & Authors",
    th_lang: "Language",
    th_tags: "Corpus & Topic Tags",
    rules_title: "⚙️ Classification Rules (`config/default_rules.json`)",
    rules_desc: "Edit and save the JSON configuration below to add new corpora, languages, or research topic keywords.",
    btn_save_rules: "💾 Save Rules & Rescan Library",
    backups_title: "💾 Database Backups (`zotero.sqlite.*.bak`)",
    btn_new_backup: "➕ Create New Backup Now",
    th_bak_file: "Backup File",
    th_bak_date: "Date Modified",
    th_bak_size: "Size",
    th_bak_action: "Action",
    zot_open: "Zotero Running",
    zot_closed: "Zotero Closed",
    no_items: "No records found.",
    scanning_msg: "⏳ Scanning Zotero database and full-text caches...",
    scan_done: "✅ Scan complete:",
    applying_msg: "⏳ Backing up Zotero and applying classification...",
    apply_done: "✅ Classification applied successfully!",
    dup_scanning_msg: "⏳ Comparing SHA-256 PDF hashes, DOIs, and normalized titles...",
    dup_none_left: "🎉 Zero duplicate records or redundant PDFs remaining in your library!",
    dup_confirm: "Duplicate records will be merged into the master record with the richest bibliography, the single best PDF will be linked, and redundant copies will be deleted (a full backup is created first). Proceed?",
    restore_btn: "⏪ Restore This Backup",
    restore_confirm: "The selected backup file will be restored as the active Zotero database. Continue?"
  }
};

let CUR_LANG = "tr";
let LAST_ZOT_RUNNING = false;
let ALL_ITEMS = [];
let DUP_CLUSTERS = [];

function t(key) {
  return (I18N[CUR_LANG] && I18N[CUR_LANG][key]) || key;
}

function toggleLang() {
  CUR_LANG = CUR_LANG === "tr" ? "en" : "tr";
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (I18N[CUR_LANG][key]) el.textContent = I18N[CUR_LANG][key];
  });
  document.getElementById("zotStatusText").textContent = LAST_ZOT_RUNNING ? t("zot_open") : t("zot_closed");
  loadBackups();
}

function showToast(msg, kind='info') {
  const el = document.getElementById('toastBox');
  el.className = 'toast ' + kind;
  el.innerHTML = msg;
}

function switchTab(tabId, btn) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  btn.classList.add('active');
}

function renderBars(containerId, dataObj, total) {
  const el = document.getElementById(containerId);
  const entries = Object.entries(dataObj || {});
  if (!entries.length) {
    el.innerHTML = `<div style="color:var(--muted);font-size:0.88rem;">${t('no_items')}</div>`;
    return;
  }
  el.innerHTML = entries.map(([k, v]) => {
    const pct = total > 0 ? Math.min(100, Math.round((v / total) * 100)) : 0;
    return `<div class="bar-row">
      <div class="bar-label"><span><strong>${k}</strong></span><span>${v.toLocaleString()} (${pct}%)</span></div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(pct, 2)}%"></div></div>
    </div>`;
  }).join('');
}

async function scanLibrary() {
  const zdir = document.getElementById('zdirInput').value.trim();
  const btn = document.getElementById('btnScan');
  btn.disabled = true;
  showToast(t('scanning_msg'), 'info');
  try {
    const res = await fetch('/api/scan?zdir=' + encodeURIComponent(zdir));
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    document.getElementById('zdirInput').value = data.zdir;
    LAST_ZOT_RUNNING = Boolean(data.zotero_running);
    const dot = document.getElementById('zotDot');
    dot.className = 'dot ' + (LAST_ZOT_RUNNING ? '' : 'closed');
    document.getElementById('zotStatusText').textContent = LAST_ZOT_RUNNING ? t('zot_open') : t('zot_closed');

    const st = data.stats;
    document.getElementById('kpiTotal').textContent = st.total_items.toLocaleString();
    document.getElementById('kpiRegular').textContent = st.regular_items.toLocaleString();
    document.getElementById('kpiStandalone').textContent = st.standalone_pdfs.toLocaleString();
    document.getElementById('kpiZazaki').textContent = (st.by_corpus['zazaki-kirmancki'] || 0).toLocaleString();
    const kurdSum = (st.by_corpus['kurmanci'] || 0) + (st.by_corpus['sorani-gorani'] || 0) + (st.by_corpus['kurdoloji-genel'] || 0);
    document.getElementById('kpiKurdish').textContent = kurdSum.toLocaleString();

    renderBars('barsCorpus', st.by_corpus, st.total_items);
    renderBars('barsLang', st.by_language, st.total_items);
    renderBars('barsType', st.by_type, st.total_items);
    renderBars('barsTopic', st.by_topic, st.total_items);
    renderBars('barsAudit', st.by_audit, st.total_items);

    ALL_ITEMS = data.items || [];
    renderExplorer();
    loadBackups();
    showToast(`${t('scan_done')} <strong>${st.total_items.toLocaleString()}</strong>`, 'success');
  } catch (e) {
    showToast('❌ ' + e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

function renderExplorer() {
  const q = (document.getElementById('searchFilter').value || '').toLowerCase().trim();
  const filtered = ALL_ITEMS.filter(it => {
    if (!q) return true;
    const blob = `${it.key} ${it.title} ${(it.creators||[]).join(' ')} ${(it.auto_tags||[]).join(' ')}`.toLowerCase();
    return blob.includes(q);
  }).slice(0, 250);

  const tbody = document.getElementById('explorerBody');
  tbody.innerHTML = filtered.map(it => `
    <tr>
      <td><code>${it.key}</code></td>
      <td><span class="badge">${it.tur}</span></td>
      <td><strong>${it.title || '(No Title)'}</strong><br><small style="color:var(--muted)">${(it.creators||[]).join('; ')} ${it.date ? '('+it.date+')' : ''}</small></td>
      <td><code>${it.doc_lang} (${it.expected_iso})</code></td>
      <td>${(it.auto_tags||[]).map(t => `<span class="badge ${t.startsWith('#kontrol:')?'warn':''}">${t}</span>`).join(' ')}</td>
    </tr>
  `).join('');
}

async function applyClassification() {
  const zdir = document.getElementById('zdirInput').value.trim();
  const payload = {
    zdir,
    apply_collections: document.getElementById('chkCols').checked,
    apply_tags: document.getElementById('chkTags').checked,
    fix_languages: document.getElementById('chkLang').checked,
    restart_zotero: document.getElementById('chkRestart').checked
  };
  const btn = document.getElementById('btnApplyClass');
  btn.disabled = true;
  showToast(t('applying_msg'), 'info');
  try {
    const res = await fetch('/api/apply-classification', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    const s = data.summary;
    showToast(`${t('apply_done')} (Collections: <strong>${s.created_collections}</strong>, Links: <strong>${s.added_collection_links}</strong>, Tags: <strong>${s.added_item_tags}</strong>, Lang Fixes: <strong>${s.fixed_language_fields}</strong>)`, 'success');
    await scanLibrary();
  } catch (e) {
    showToast('❌ ' + e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function scanDuplicates() {
  const zdir = document.getElementById('zdirInput').value.trim();
  const btn = document.getElementById('btnScanDup');
  btn.disabled = true;
  showToast(t('dup_scanning_msg'), 'info');
  try {
    const res = await fetch('/api/scan-duplicates?zdir=' + encodeURIComponent(zdir));
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    DUP_CLUSTERS = data.clusters || [];
    document.getElementById('dupSummaryBadge').textContent =
      `${DUP_CLUSTERS.length} clusters (${data.total_losers} duplicates, ${data.freed_mb} MB)`;
    document.getElementById('btnExecDup').disabled = DUP_CLUSTERS.length === 0;

    const tbody = document.getElementById('dupTableBody');
    if (!DUP_CLUSTERS.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="color:var(--success);font-weight:600;">${t('dup_none_left')}</td></tr>`;
    } else {
      tbody.innerHTML = DUP_CLUSTERS.map((c, i) => `
        <tr>
          <td>${i+1}</td>
          <td>
            <span class="badge ok">MASTER (${c.winner_type}, Score: ${c.winner_score})</span>
            <code>${c.winner_key}</code><br>
            <strong>${c.winner_title}</strong><br>
            <small style="color:var(--muted)">${(c.winner_creators||[]).join('; ')} ${c.winner_date ? '('+c.winner_date+')' : ''} ${c.winner_doi ? '• DOI: '+c.winner_doi : ''}</small>
          </td>
          <td>
            ${c.loser_keys.map((k, idx) => `<div><span class="badge warn">MERGE & DELETE</span> <code>${k}</code>: ${(c.loser_titles[idx]||'').slice(0,75)}</div>`).join('')}
          </td>
          <td>
            ${c.best_att ? `<span class="badge ok">Keep PDF (${Math.round(c.best_att.size/1024)} KB)</span>` : '<span class="badge">No PDF</span>'}
            ${c.freed_bytes > 0 ? `<br><small style="color:var(--danger)">+${(c.freed_bytes/(1024*1024)).toFixed(2)} MB freed</small>` : ''}
          </td>
        </tr>
      `).join('');
    }
    showToast(`✅ <strong>${DUP_CLUSTERS.length}</strong> clusters found.`, 'success');
  } catch (e) {
    showToast('❌ ' + e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function executeDedup() {
  if (!confirm(t('dup_confirm'))) return;
  const zdir = document.getElementById('zdirInput').value.trim();
  const btn = document.getElementById('btnExecDup');
  btn.disabled = true;
  showToast(t('applying_msg'), 'info');
  try {
    const res = await fetch('/api/execute-dedup', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({zdir, restart_zotero: true})
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    const s = data.summary;
    showToast(`✅ Deduplication complete! Clusters: <strong>${s.clusters_resolved}</strong>, Deleted: <strong>${s.deleted_duplicate_items}</strong>, Linked PDFs: <strong>${s.reparented_standalone_or_child_pdfs}</strong>, Freed: <strong>${s.freed_megabytes} MB</strong>.`, 'success');
    await scanDuplicates();
    await scanLibrary();
  } catch (e) {
    showToast('❌ ' + e.message, 'error');
  }
}

async function loadRules() {
  const res = await fetch('/api/rules');
  const data = await res.json();
  document.getElementById('rulesEditor').value = JSON.stringify(data, null, 2);
}

async function saveRules() {
  try {
    const parsed = JSON.parse(document.getElementById('rulesEditor').value);
    const res = await fetch('/api/rules', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(parsed)
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    await scanLibrary();
  } catch (e) {
    showToast('❌ ' + e.message, 'error');
  }
}

async function loadBackups() {
  const zdir = document.getElementById('zdirInput').value.trim();
  const res = await fetch('/api/backups?zdir=' + encodeURIComponent(zdir));
  const data = await res.json();
  const tbody = document.getElementById('backupTableBody');
  tbody.innerHTML = (data.backups || []).map(b => `
    <tr>
      <td><code>${b.name}</code></td>
      <td>${b.modified}</td>
      <td>${b.size_mb} MB</td>
      <td><button class="btn-outline" onclick="restoreBackup('${b.path.replace(/\\/g, '\\\\')}')">${t('restore_btn')}</button></td>
    </tr>
  `).join('');
}

async function manualBackup() {
  const zdir = document.getElementById('zdirInput').value.trim();
  const res = await fetch('/api/create-backup', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({zdir})
  });
  const data = await res.json();
  if (data.error) { showToast('❌ ' + data.error, 'error'); return; }
  showToast('✅ Backup created: ' + data.backup_file, 'success');
  loadBackups();
}

async function restoreBackup(path) {
  if (!confirm(t('restore_confirm'))) return;
  const zdir = document.getElementById('zdirInput').value.trim();
  const res = await fetch('/api/restore-backup', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({zdir, backup_path: path})
  });
  const data = await res.json();
  if (data.error) { showToast('❌ ' + data.error, 'error'); return; }
  showToast('✅ Restored!', 'success');
  await scanLibrary();
}

function downloadReport(fmt) {
  const zdir = document.getElementById('zdirInput').value.trim();
  window.open(`/api/export?fmt=${fmt}&zdir=${encodeURIComponent(zdir)}`, '_blank');
}

window.addEventListener('DOMContentLoaded', () => {
  scanLibrary();
  loadRules();
});
</script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    """
    [TR] Yerel Görsel Web Arayüzünün HTTP GET ve POST isteklerini karşılayan sunucu sınıfı.
    [EN] HTTP request handler class serving GET and POST endpoints for the local Visual Web Dashboard.
    """

    default_zdir: Path = find_zotero_data_dir()

    def log_message(self, format: str, *args) -> None:
        # [TR] Konsol çıktısını temiz tutmak için standart erişim günlüklerini bastır
        # [EN] Suppress standard access logs to keep terminal output clean
        pass

    def _send_json(self, data: dict | list, status: int = 200) -> None:
        """
        [TR] Veriyi UTF-8 JSON yanıtı olarak tarayıcıya gönderir.
        [EN] Sends data to the browser as a UTF-8 JSON HTTP response.
        """
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_body(self) -> dict:
        """
        [TR] HTTP POST gövdesindeki JSON verisini okur ve sözlüğe dönüştürür.
        [EN] Reads and parses the JSON payload from the HTTP POST request body.
        """
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        """
        [TR] Sayfa görüntüleme, tarama, mükerrer analizi ve rapor indirme isteklerini işler.
        [EN] Handles dashboard page rendering, scanning, duplicate analysis, and report export requests.
        """
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        zdir_str = (qs.get("zdir", [""])[0] or "").strip()
        zdir = find_zotero_data_dir(zdir_str) if zdir_str else self.default_zdir

        try:
            if parsed.path == "/":
                raw = HTML_PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            elif parsed.path == "/api/scan":
                entries = load_library_snapshot(zdir, compute_hashes=False)
                results = classify_library(entries)
                stats = compute_summary_stats(results)
                self._send_json({
                    "zdir": str(zdir),
                    "zotero_running": is_zotero_running(),
                    "stats": stats,
                    "items": list(results.values()),
                })
            elif parsed.path == "/api/scan-duplicates":
                entries = load_library_snapshot(zdir, compute_hashes=True)
                clusters = find_duplicate_clusters(entries)
                total_losers = sum(len(c["loser_ids"]) for c in clusters)
                freed_mb = round(sum(c["freed_bytes"] for c in clusters) / (1024 * 1024), 2)
                self._send_json({
                    "clusters": clusters,
                    "total_losers": total_losers,
                    "freed_mb": freed_mb,
                })
            elif parsed.path == "/api/rules":
                self._send_json(load_rules())
            elif parsed.path == "/api/backups":
                self._send_json({"backups": list_backups(zdir)})
            elif parsed.path == "/api/export":
                fmt = qs.get("fmt", ["md"])[0]
                entries = load_library_snapshot(zdir, compute_hashes=False)
                results = classify_library(entries)
                if fmt == "csv":
                    raw = generate_csv_report(results).encode("utf-8")
                    ctype = "text/csv; charset=utf-8"
                    fname = "zotero_siniflandirma.csv"
                else:
                    raw = generate_markdown_report(zdir, results).encode("utf-8")
                    ctype = "text/markdown; charset=utf-8"
                    fname = "zotero_derlem_raporu.md"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            else:
                self._send_json({"error": "Not found"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def do_POST(self) -> None:
        """
        [TR] Sınıflandırma uygulama, mükerrer birleştirme, kural kaydetme ve yedek geri yükleme işlemlerini yürütür.
        [EN] Executes classification application, duplicate merging, rule saving, and backup restoration.
        """
        parsed = urllib.parse.urlparse(self.path)
        try:
            body = self._read_body()
            zdir_str = (body.get("zdir") or "").strip()
            zdir = find_zotero_data_dir(zdir_str) if zdir_str else self.default_zdir

            if parsed.path == "/api/apply-classification":
                entries = load_library_snapshot(zdir, compute_hashes=False)
                results = classify_library(entries)
                was_running = is_zotero_running()
                restart = bool(body.get("restart_zotero", True))
                if was_running and restart:
                    stop_zotero_gracefully()
                summary = apply_classification_sqlite(
                    zdir,
                    entries,
                    results,
                    apply_collections=bool(body.get("apply_collections", True)),
                    apply_tags=bool(body.get("apply_tags", True)),
                    fix_languages=bool(body.get("fix_languages", True)),
                )
                if was_running and restart:
                    start_zotero()
                self._send_json({"summary": summary})

            elif parsed.path == "/api/execute-dedup":
                entries = load_library_snapshot(zdir, compute_hashes=True)
                clusters = find_duplicate_clusters(entries)
                was_running = is_zotero_running()
                restart = bool(body.get("restart_zotero", True))
                if was_running and restart:
                    stop_zotero_gracefully()
                summary = execute_deduplication(zdir, clusters, entries)
                if was_running and restart:
                    start_zotero()
                self._send_json({"summary": summary})

            elif parsed.path == "/api/rules":
                DEFAULT_RULES_PATH.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
                self._send_json({"ok": True})

            elif parsed.path == "/api/create-backup":
                bak = create_backup(zdir, label="manual")
                self._send_json({"backup_file": str(bak)})

            elif parsed.path == "/api/restore-backup":
                was_running = is_zotero_running()
                if was_running:
                    stop_zotero_gracefully()
                restored = restore_backup(zdir, body["backup_path"])
                if was_running:
                    start_zotero()
                self._send_json({"restored": str(restored)})

            else:
                self._send_json({"error": "Not found"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)


def launch_web_ui(zdir: Path | None = None, port: int = 8765, open_browser: bool = True) -> None:
    """
    [TR] Yerel HTTP sunucusunu başlatır ve varsayılan web tarayıcısında kontrol panelini açar.
    [EN] Starts the local HTTP server and opens the dashboard in the default web browser.
    """
    if zdir:
        DashboardHandler.default_zdir = zdir
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    url = f"http://127.0.0.1:{port}"
    print("======================================================================")
    print(" [TR] Zotero Derlem & Sınıflandırma Yöneticisi Arayüzü Çalışıyor")
    print(" [EN] Zotero Corpus & Classification Manager Web UI is Running")
    print(f" URL / Adres     : {url}")
    print(f" Zotero Path     : {DashboardHandler.default_zdir}")
    print(" [TR] Kapatmak için Ctrl+C tuşlarına basın / [EN] Press Ctrl+C to stop")
    print("======================================================================")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[TR] Sunucu kapatıldı. / [EN] Server stopped.")
        server.server_close()
