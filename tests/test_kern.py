"""Tests der Logik ohne Fenster (rueckmeldung_kern)."""
import datetime
import os
import tempfile
import unittest

import rueckmeldung_kern as kern

JETZT = datetime.datetime(2026, 11, 15, 21, 4, 12)


class TestKuerzel(unittest.TestCase):
    def test_standard(self):
        mods, vk = kern.lies_kuerzel("ctrl+alt+f")
        self.assertEqual(mods, 0x0002 | 0x0001 | kern.MOD_NOREPEAT)
        self.assertEqual(vk, ord("F"))

    def test_schreibweisen(self):
        self.assertEqual(kern.lies_kuerzel("Strg + Alt + F"), kern.lies_kuerzel("ctrl+alt+f"))
        self.assertEqual(kern.lies_kuerzel("win+shift+f12")[1], 0x7B)
        self.assertEqual(kern.lies_kuerzel("alt+7")[1], ord("7"))

    def test_ungueltig(self):
        for text in ("", "f", "shift+f", "ctrl+alt+enter", "hyper+f", "ctrl+f25"):
            with self.subTest(text=text), self.assertRaises(kern.Kuerzelfehler):
                kern.lies_kuerzel(text)

    def test_anzeige(self):
        self.assertEqual(kern.zeige_kuerzel("ctrl+alt+f"), "Strg+Alt+F")


class TestDateien(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ablage = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_ordnername(self):
        self.assertEqual(kern.ordnername("KID"), "KID")
        self.assertEqual(kern.ordnername('a/b:c*'), "a_b_c_")
        self.assertEqual(kern.ordnername("  "), kern.PROJEKT_UNBEKANNT)
        self.assertEqual(kern.ordnername(None), kern.PROJEKT_UNBEKANNT)

    def test_speichern_und_lesen(self):
        pfad = kern.speichere(self.ablage, "KID", JETZT, "Fehler", "  Reset fehlt.\nZweite Zeile  ",
                              [b"png1", b"png2"], {"fenster": "Dokumenten-Manager v0.9.30", "programm": "x.exe"})
        ordner = os.path.join(self.ablage, "KID")
        self.assertEqual(pfad, os.path.join(ordner, "2026-11-15_210412_fehler.md"))
        self.assertEqual(sorted(os.listdir(ordner)), ["2026-11-15_210412_fehler.md", "2026-11-15_210412_fehler_1.png",
                                                      "2026-11-15_210412_fehler_2.png"])
        with open(os.path.join(ordner, "2026-11-15_210412_fehler_2.png"), "rb") as f:
            self.assertEqual(f.read(), b"png2")
        kopf, notiz = kern.lies(pfad)
        self.assertEqual(notiz, "Reset fehlt.\nZweite Zeile")
        self.assertEqual(kopf["projekt"], "KID")
        self.assertEqual(kopf["art"], "Fehler")
        self.assertEqual(kopf["zeit"], "2026-11-15 21:04:12")
        self.assertEqual(kopf["status"], "offen")
        self.assertEqual(kopf["fenster"], "Dokumenten-Manager v0.9.30")
        self.assertEqual(kopf["bilder"], ["2026-11-15_210412_fehler_1.png", "2026-11-15_210412_fehler_2.png"])
        self.assertIs(kopf["bild_fuer_ki"], False)          # Vorgabe: Bilder nicht für die KI

    def test_kopf_ist_lesbar_ohne_werkzeug(self):
        pfad = kern.speichere(self.ablage, "", JETZT, "Idee", "Text", [], {"fenster": 'Titel mit "Anführung": ja'})
        with open(pfad, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.startswith("---\nprojekt: \"Unbekannt\"\nart: \"Idee\"\n"))
        self.assertIn("bild_fuer_ki: nein\n", text)
        self.assertEqual(kern.lies(pfad)[0]["fenster"], 'Titel mit "Anführung": ja')

    def test_gleiche_sekunde_ueberschreibt_nicht(self):
        a = kern.speichere(self.ablage, "KID", JETZT, "Fehler", "eins", [b"1"])
        b = kern.speichere(self.ablage, "KID", JETZT, "Fehler", "zwei", [b"2"])
        self.assertNotEqual(a, b)
        self.assertTrue(b.endswith("2026-11-15_210412_fehler_2.md"))
        self.assertEqual(kern.lies(a)[1], "eins")
        self.assertEqual(kern.lies(b)[0]["bilder"], ["2026-11-15_210412_fehler_2_1.png"])

    def test_keine_temp_datei_bleibt(self):
        kern.speichere(self.ablage, "KID", JETZT, "Notiz", "x")
        self.assertEqual(os.listdir(os.path.join(self.ablage, "KID")), ["2026-11-15_210412_notiz.md"])

    def test_unbekannte_art(self):
        with self.assertRaises(ValueError):
            kern.speichere(self.ablage, "KID", JETZT, "Lob", "x")
        self.assertFalse(os.path.exists(os.path.join(self.ablage, "KID")))


if __name__ == "__main__":
    unittest.main()
