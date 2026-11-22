"""Tests für Konfiguration, Projekt-Zuordnung, Version und Protokoll-Auszug (rueckmeldung_kern)."""
import datetime
import json
import os
import tempfile
import time
import unittest

import rueckmeldung_kern as kern

KID = {"name": "KID",
       "regeln": [{"programm": "DokumentenManager.exe"},
                  {"programm": "python.exe", "fenstertitel": "^Dokumenten-Manager v"}],
       "version": r"v(\d+\.\d+\.\d+)"}
WIZARD = {"name": "Testwizard", "regeln": [{"programm": "python.exe", "fenstertitel": "Manuelle Tests$"}]}


class TestKonfig(unittest.TestCase):
    def test_vorgaben(self):
        k = kern.pruefe_konfig({})
        self.assertEqual(k, {"kuerzel": kern.STANDARD_KUERZEL, "ablage": kern.STANDARD_ABLAGE, "rechner": "",
                             "projekte": []})

    def test_kommentare_erlaubt(self):
        k = kern.pruefe_konfig({"_hinweis": "x", "projekte": [dict(KID, _notiz="y")]})
        self.assertEqual(k["projekte"][0]["name"], "KID")

    def test_fehler_werden_benannt(self):
        faelle = {
            "unbekannt": {"kuerzl": "ctrl+alt+f"},
            "kuerzel": {"kuerzel": "f"},
            "projekte keine Liste": {"projekte": {}},
            "ohne name": {"projekte": [{"regeln": [{"programm": "a.exe"}]}]},
            "ohne regeln": {"projekte": [{"name": "A"}]},
            "leere regel": {"projekte": [{"name": "A", "regeln": [{}]}]},
            "regel unbekannt": {"projekte": [{"name": "A", "regeln": [{"programm": "a", "titel": "x"}]}]},
            "muster kaputt": {"projekte": [{"name": "A", "regeln": [{"fenstertitel": "(("}]}]},
            "version ohne gruppe": {"projekte": [{"name": "A", "regeln": [{"programm": "a"}], "version": r"v\d+"}]},
            "bild_fuer_ki kein bool": {"projekte": [{"name": "A", "regeln": [{"programm": "a"}], "bild_fuer_ki": "ja"}]},
            "protokoll ohne datei": {"projekte": [{"name": "A", "regeln": [{"programm": "a"}], "protokoll": {}}]},
            "zeilen 0": {"projekte": [{"name": "A", "regeln": [{"programm": "a"}],
                                       "protokoll": {"datei": "x", "zeilen": 0}}]},
        }
        for name, daten in faelle.items():
            with self.subTest(name), self.assertRaises(kern.Konfigfehler):
                kern.pruefe_konfig(daten)

    def test_datei(self):
        with tempfile.TemporaryDirectory() as d:
            pfad = os.path.join(d, kern.KONFIG_DATEI)
            self.assertEqual(kern.lade_konfig(pfad)["projekte"], [])           # fehlt -> Vorgaben
            with open(pfad, "w", encoding="utf-8-sig") as f:                  # mit BOM, wie Notepad speichert
                json.dump({"rechner": "Tester-PC", "projekte": [KID]}, f)
            self.assertEqual(kern.lade_konfig(pfad)["rechner"], "Tester-PC")
            with open(pfad, "w", encoding="utf-8") as f:
                f.write('{"rechner": "x",}')
            with self.assertRaises(kern.Konfigfehler):
                kern.lade_konfig(pfad)


class TestKonfigSuche(unittest.TestCase):
    """Fund 2026-11-22: Die EXE lief aus „Downloads“, die Konfiguration lag woanders - alles ging nach Unbekannt."""

    def test_reihenfolge_programm_dann_ablage(self):
        orte = kern.konfig_orte(os.path.join("X:", os.sep, "Downloads"))
        self.assertEqual(orte[0], os.path.join("X:", os.sep, "Downloads", kern.KONFIG_DATEI))
        self.assertEqual(orte[1], os.path.normpath(os.path.join(os.path.expanduser(kern.STANDARD_ABLAGE),
                                                                kern.KONFIG_DATEI)))
        self.assertNotIn("/", orte[1])                                           # keine gemischten Trenner

    def test_programm_in_der_ablage_nur_einmal(self):
        ablage = os.path.expanduser(kern.STANDARD_ABLAGE)
        self.assertEqual(len(kern.konfig_orte(ablage)), 1)
        self.assertEqual(len(kern.konfig_orte(ablage.upper())), 1)               # Windows: Groß/klein egal

    def test_erster_vorhandener_gewinnt(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a.json"), os.path.join(d, "b.json")
            self.assertIsNone(kern.finde_konfig([a, b]))
            open(b, "w").close()
            self.assertEqual(kern.finde_konfig([a, b]), b)
            open(a, "w").close()
            self.assertEqual(kern.finde_konfig([a, b]), a)
            self.assertIsNone(kern.finde_konfig([d]))                            # ein Ordner zählt nicht


class TestBildFuerKiVorgabe(unittest.TestCase):
    def test_ohne_angabe_gesetzt(self):
        self.assertTrue(kern.bild_fuer_ki_vorgabe(None))                         # Unbekannt
        self.assertTrue(kern.bild_fuer_ki_vorgabe(KID))                          # Projekt ohne Angabe

    def test_projekt_schaltet_ab(self):
        self.assertFalse(kern.bild_fuer_ki_vorgabe(dict(KID, bild_fuer_ki=False)))
        self.assertTrue(kern.bild_fuer_ki_vorgabe(dict(KID, bild_fuer_ki=True)))

    def test_projektordner(self):
        self.assertEqual(kern.projektordner("~/R", "KID"), os.path.join(os.path.expanduser("~/R"), "KID"))


class TestZuordnung(unittest.TestCase):
    def setUp(self):
        self.k = kern.pruefe_konfig({"projekte": [WIZARD, KID]})

    def test_exe_allein_reicht(self):
        self.assertEqual(kern.ordne_zu(self.k, "dokumentenmanager.EXE", ["Irgendwas"])["name"], "KID")

    def test_python_braucht_titel(self):
        self.assertIsNone(kern.ordne_zu(self.k, "python.exe", ["Anderes Programm"]))
        self.assertEqual(kern.ordne_zu(self.k, "python.exe", ["Dokumenten-Manager v0.9.30 (Build x)"])["name"], "KID")

    def test_dialog_ueber_hauptfenster(self):
        titel = ["Einstellungen", "Dokumenten-Manager v0.9.30 (Build x)"]
        self.assertEqual(kern.ordne_zu(self.k, "python.exe", titel)["name"], "KID")
        self.assertEqual(kern.finde_version(kern.ordne_zu(self.k, "python.exe", titel), titel), "0.9.30")

    def test_reihenfolge_entscheidet(self):
        # Der Testwizard für KID heißt „Dokumenten-Manager - Manuelle Tests“ - steht er vorn, gewinnt er
        titel = ["Dokumenten-Manager - Manuelle Tests"]
        self.assertEqual(kern.ordne_zu(self.k, "python.exe", titel)["name"], "Testwizard")

    def test_version_fehlt(self):
        self.assertEqual(kern.finde_version(KID, ["Dokumenten-Manager"]), "")
        self.assertEqual(kern.finde_version(WIZARD, ["x v1.2.3"]), "")
        self.assertEqual(kern.finde_version(None, ["x v1.2.3"]), "")


class TestProtokoll(unittest.TestCase):
    def test_neueste_datei_letzte_zeilen(self):
        with tempfile.TemporaryDirectory() as d:
            alt = os.path.join(d, "a.log")
            neu = os.path.join(d, "b.log")
            with open(alt, "w", encoding="utf-8") as f:
                f.write("alt\n")
            with open(neu, "w", encoding="utf-8") as f:
                f.write("".join(f"Zeile {i} äöü\n" for i in range(1, 11)))
            jetzt = time.time()
            os.utime(alt, (jetzt - 100, jetzt - 100))
            pfad, text = kern.protokoll_ende(os.path.join(d, "*.log"), 3)
            self.assertEqual(pfad, neu)
            self.assertEqual(text, "Zeile 8 äöü\nZeile 9 äöü\nZeile 10 äöü")

    def test_grosse_datei_nur_das_ende(self):
        with tempfile.TemporaryDirectory() as d:
            pfad = os.path.join(d, "gross.log")
            with open(pfad, "w", encoding="utf-8") as f:
                f.write("".join(f"Zeile {i:06d}\n" for i in range(200000)))
            _, text = kern.protokoll_ende(pfad, 2)
            self.assertEqual(text, "Zeile 199998\nZeile 199999")

    def test_keine_datei(self):
        self.assertEqual(kern.protokoll_ende("~/gibt/es/nicht/*.log", 5), (None, ""))

    def test_speichern_mit_protokoll(self):
        with tempfile.TemporaryDirectory() as d:
            jetzt = datetime.datetime(2026, 11, 15, 22, 0, 0)
            pfad = kern.speichere(d, "KID", jetzt, "Fehler", "x", [], {"bild_fuer_ki": True, "version": "1"},
                                  protokoll="eins\nzwei\n")
            with open(pfad, encoding="utf-8") as f:
                zeilen = f.read().split("\n---\n")[0].splitlines()
            self.assertEqual(zeilen[-1], "bild_fuer_ki: ja")                    # immer zuletzt
            kopf, _ = kern.lies(pfad)
            self.assertEqual(kopf["protokoll"], "2026-11-15_220000_fehler_protokoll.txt")
            with open(os.path.join(d, "KID", kopf["protokoll"]), encoding="utf-8") as f:
                self.assertEqual(f.read(), "eins\nzwei\n")
            # Ein Protokoll ohne Markdown-Datei (abgebrochen) blockiert den Namen
            os.remove(pfad)
            zweit = kern.speichere(d, "KID", jetzt, "Fehler", "y")
            self.assertTrue(zweit.endswith("_fehler_2.md"))


if __name__ == "__main__":
    unittest.main()
