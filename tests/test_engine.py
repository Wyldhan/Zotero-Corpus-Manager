"""
[TR] Zotero Sınıflandırma ve Akıllı Mükerrer Birleştirme Motoru Birim Testleri.
[EN] Unit Tests for the Zotero Classification and Smart Deduplication Engine.
"""
import unittest
from zotero_manager.classifier import classify_library
from zotero_manager.deduplicator import find_duplicate_clusters, score_item_metadata


class TestZoteroEngine(unittest.TestCase):
    """
    [TR] Sınıflandırma, tekrar çalıştırılabilirlik (idempotency) ve mükerrer korumalarını doğrular.
    [EN] Verifies classification accuracy, idempotency, and duplicate false-positive guards.
    """

    def test_classification_and_idempotency(self):
        """
        [TR] Kirmanckî/Zazakî metin tespiti, hatalı dil kodu ('en'->'zza') yakalama ve
             '#derlem:' etiketinin yanlışlıkla '#konu:derlem-dilbilimi' üretmemesini test eder.
        [EN] Tests Kirmancki/Zazaki detection, wrong language code ('en'->'zza') audit flagging,
             and ensures '#derlem:' auto-tags do not falsely trigger '#konu:derlem-dilbilimi'.
        """
        entries = {
            1: {
                "itemID": 1,
                "key": "ZZTEST01",
                "itemType": "journalArticle",
                "fields": {
                    "title": "Kirmanckî (Zazakî) de Pêveronayîşê Fekê Çewlîgî û Gimgimî",
                    "abstractNote": "Na xebate de fekê Çewlîgî û Gimgimî hetê morfolojî ra yenê pêveronayene.",
                    "language": "en",
                },
                "creators": [("author", "Baluken", "Yusuf")],
                "collections": [],
                "tags": ["#derlem:zazaki-kirmancki"],
                "attachments": [],
                "notes_count": 0,
            }
        }
        res = classify_library(entries)
        r1 = res[1]
        self.assertEqual(r1["doc_lang"], "kirmancki")
        self.assertEqual(r1["expected_iso"], "zza")
        self.assertIn("zazaki-kirmancki", r1["derlem"])
        self.assertIn("morfoloji-allomorfi", r1["konular"])
        self.assertIn("diyalektoloji-agiz", r1["konular"])
        self.assertIn("dil-kodu-hatali", r1["kontroller"])
        # [TR] Tekrar çalıştırılabilirlik (Idempotency) kontrolü
        # [EN] Idempotency check: #derlem:zazaki-kirmancki tag must NOT trigger #konu:derlem-dilbilimi
        self.assertNotIn("derlem-dilbilimi", r1["konular"])

    def test_dedup_winner_selection_and_guards(self):
        """
        [TR] En kapsamlı kaynakçaya sahip kaydın 'Kazanan' seçildiğini, üst kayıtsız PDF'in
             ona bağlandığını ve farklı yazarlı jenerik tez kapaklarının birleştirilmediğini doğrular.
        [EN] Verifies that the item with the richest bibliography is chosen as 'Winner', the
             standalone PDF is linked to it, and generic thesis headers with different authors are NOT merged.
        """
        items = {
            10: {
                "itemID": 10,
                "key": "RICH0010",
                "itemType": "thesis",
                "fields": {
                    "title": "Zazacanın Sentaksı (Sözdizimi)",
                    "university": "Bingöl Üniversitesi",
                    "date": "2019",
                },
                "creators": [("author", "Sönmez", "Hıdır")],
                "attachments": [],
                "notes_count": 1,
            },
            11: {
                "itemID": 11,
                "key": "POOR0011",
                "itemType": "attachment",
                "fields": {},
                "creators": [],
                "attachments": [
                    {
                        "attID": 11,
                        "attKey": "POOR0011",
                        "parentItemID": None,
                        "contentType": "application/pdf",
                        "path": "storage:Sönmez - 2019 - Zazacanın Sentaksı (Sözdizimi).pdf",
                        "exists": True,
                        "size": 1500000,
                        "sha256": "abc123hash",
                        "indexedChars": 45000,
                        "ann_cnt": 0,
                    }
                ],
                "notes_count": 0,
            },
            # [TR] Farklı yazarlara ait jenerik enstitü başlıkları -> KESİNLİKLE BİRLEŞTİRİLMEMELİ
            # [EN] Different authors with generic university cover page title -> MUST NOT MERGE
            20: {
                "itemID": 20,
                "key": "COV00020",
                "itemType": "journalArticle",
                "fields": {"title": "T.C. Mersin Üniversitesi Sosyal Bilimler Enstitüsü"},
                "creators": [("author", "Yıldız", "İpek")],
                "attachments": [],
                "notes_count": 0,
            },
            21: {
                "itemID": 21,
                "key": "COV00021",
                "itemType": "journalArticle",
                "fields": {"title": "T.C. Mersin Üniversitesi Sosyal Bilimler Enstitüsü"},
                "creators": [("author", "Öz", "Seda")],
                "attachments": [],
                "notes_count": 0,
            },
        }
        self.assertGreater(score_item_metadata(items[10]), score_item_metadata(items[11]))
        clusters = find_duplicate_clusters(items)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["winner_id"], 10)
        self.assertEqual(clusters[0]["loser_ids"], [11])
        self.assertEqual(clusters[0]["best_att"]["attID"], 11)


if __name__ == "__main__":
    unittest.main()
