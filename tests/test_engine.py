import unittest
from zotero_manager.classifier import classify_library
from zotero_manager.deduplicator import find_duplicate_clusters, score_item_metadata


class TestZoteroEngine(unittest.TestCase):
    def test_classification_and_idempotency(self):
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
        # Idempotency check: #derlem:zazaki-kirmancki tag must NOT trigger #konu:derlem-dilbilimi
        self.assertNotIn("derlem-dilbilimi", r1["konular"])

    def test_dedup_winner_selection_and_guards(self):
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
            # Different authors with generic university cover page title -> MUST NOT MERGE
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
