"""Tests für Zoom-Ansicht, Pfeilgeometrie (rueckmeldung_kern) und das Einbrennen (rueckmeldung_bild)."""
import math
import unittest

from PIL import Image

import rueckmeldung_bild as bild
import rueckmeldung_kern as kern


class TestAnsicht(unittest.TestCase):
    def test_einpassen_grosses_bild(self):
        a = kern.Ansicht(2000, 1000)
        a.einpassen(800, 600)
        self.assertAlmostEqual(a.massstab, 0.4)
        self.assertAlmostEqual(a.x0, 0)
        self.assertAlmostEqual(a.y0, -(600 / 0.4 - 1000) / 2)          # senkrecht mittig
        self.assertEqual(a.zu_flaeche(1000, 500), (400, 300))

    def test_kleines_bild_nie_vergroessert_beim_einpassen(self):
        a = kern.Ansicht(200, 100)
        a.einpassen(800, 600)
        self.assertEqual(a.massstab, 1.0)
        self.assertEqual(a.zu_flaeche(100, 50), (400, 300))            # mittig

    def test_zoom_haelt_punkt_unter_der_maus(self):
        a = kern.Ansicht(2000, 1000)
        a.einpassen(800, 400)
        vorher = a.zu_bild(600, 100)
        a.zoome(2.0, 600, 100)
        self.assertAlmostEqual(a.massstab, 0.8)
        for x, y in zip(a.zu_bild(600, 100), vorher):
            self.assertAlmostEqual(x, y)

    def test_zoom_grenzen(self):
        a = kern.Ansicht(2000, 1000)
        a.einpassen(800, 400)
        a.zoome(0.1, 0, 0)
        self.assertAlmostEqual(a.massstab, 0.4)                        # nicht kleiner als eingepasst
        for _ in range(30):
            a.zoome(1.25, 400, 200)
        self.assertEqual(a.massstab, kern.Ansicht.MAX_ZOOM)

    def test_verschieben_ohne_leeren_rand(self):
        a = kern.Ansicht(2000, 1000)
        a.einpassen(800, 400)
        a.zoome(2.5, 0, 0)                                              # Maßstab 1
        a.verschiebe(-5000, -5000)                                      # weit nach rechts unten
        self.assertAlmostEqual(a.x0, 2000 - 800)
        self.assertAlmostEqual(a.y0, 1000 - 400)
        a.verschiebe(5000, 5000)
        self.assertEqual((a.x0, a.y0), (0, 0))

    def test_ausschnitt(self):
        a = kern.Ansicht(2000, 1000)
        a.einpassen(800, 400)
        a.zoome(2.5, 0, 0)
        a.verschiebe(-100, -50)
        (l, o, r, u), (fx, fy) = a.ausschnitt()
        self.assertEqual((l, o), (100, 50))
        self.assertEqual((r, u), (901, 451))
        self.assertEqual((fx, fy), (0, 0))

    def test_eingepasst_bleibt_beim_vergroessern_eingepasst(self):
        a = kern.Ansicht(2000, 1000)
        a.einpassen(800, 400)
        a.neue_flaeche(1000, 500)
        self.assertAlmostEqual(a.massstab, 0.5)
        a.zoome(2, 0, 0)
        a.neue_flaeche(1200, 600)
        self.assertAlmostEqual(a.massstab, 1.0)                        # gezoomt: Maßstab bleibt


class TestPfeil(unittest.TestCase):
    def test_spitze_an_der_maus(self):
        s = kern.pfeilspitze(0, 0, 100, 0, 20)
        self.assertEqual(s[0], (100, 0))
        self.assertAlmostEqual(s[1][0], 80)
        self.assertAlmostEqual(s[2][0], 80)
        self.assertAlmostEqual(abs(s[1][1] - s[2][1]), 2 * 20 * 0.47)

    def test_kurzer_pfeil_kuerzere_spitze(self):
        s = kern.pfeilspitze(0, 0, 0, 10, 20)
        self.assertAlmostEqual(math.dist(s[0], ((s[1][0] + s[2][0]) / 2, (s[1][1] + s[2][1]) / 2)), 5)

    def test_linienbreite(self):
        self.assertEqual(kern.linienbreite(400, 300), 3)
        self.assertEqual(kern.linienbreite(2328, 1440), 5)


class TestEinbrennen(unittest.TestCase):
    def setUp(self):
        self.weiss = Image.new("RGB", (400, 300), "white")

    def test_original_bleibt_unberuehrt(self):
        bild.einbrennen(self.weiss, [("Schwärzen", 10, 10, 100, 100)])
        self.assertEqual(self.weiss.getpixel((50, 50)), (255, 255, 255))

    def test_schwaerzen_deckt_voll(self):
        e = bild.einbrennen(self.weiss, [("Schwärzen", 100, 100, 10, 10)])     # rückwärts gezogen
        for p in ((10, 10), (55, 55), (100, 100)):
            self.assertEqual(e.getpixel(p), (0, 0, 0))
        self.assertEqual(e.getpixel((101, 101)), (255, 255, 255))

    def test_rahmen_nur_rand(self):
        e = bild.einbrennen(self.weiss, [("Rahmen", 50, 50, 250, 200)])
        self.assertEqual(e.getpixel((51, 120)), bild.FARBE)
        self.assertEqual(e.getpixel((150, 120)), (255, 255, 255))

    def test_pfeil(self):
        e = bild.einbrennen(self.weiss, [("Pfeil", 20, 150, 300, 150)])
        self.assertEqual(e.getpixel((100, 150)), bild.FARBE)                 # Schaft
        self.assertEqual(e.getpixel((298, 150)), bild.FARBE)                 # Spitze
        self.assertEqual(e.getpixel((100, 140)), (255, 255, 255))

    def test_spaeter_liegt_oben(self):
        e = bild.einbrennen(self.weiss, [("Rahmen", 50, 50, 250, 200), ("Schwärzen", 40, 40, 60, 210)])
        self.assertEqual(e.getpixel((51, 120)), (0, 0, 0))

    def test_unbekannt(self):
        with self.assertRaises(ValueError):
            bild.einbrennen(self.weiss, [("Kreis", 0, 0, 1, 1)])

    def test_zuschneiden_zuletzt(self):
        # Rahmen reicht über den Ausschnitt hinaus; Ausschnitt rückwärts gezogen
        e = bild.einbrennen(self.weiss, [("Zuschneiden", 300, 250, 100, 50), ("Rahmen", 150, 100, 350, 280)])
        self.assertEqual(e.size, (200, 200))
        self.assertEqual(e.getpixel((51, 100)), bild.FARBE)                   # Rahmen-Kante bei x=150 -> 50
        self.assertEqual(e.getpixel((10, 10)), (255, 255, 255))

    def test_nur_zuschneiden_veraendert_original_nicht(self):
        e = bild.einbrennen(self.weiss, [("Zuschneiden", 0, 0, 10, 10)])
        self.assertEqual(e.size, (10, 10))
        self.assertEqual(self.weiss.size, (400, 300))


class TestZuschnitt(unittest.TestCase):
    def test_letzter_gilt_und_begrenzt(self):
        m = [("Zuschneiden", 10, 10, 50, 50), ("Rahmen", 0, 0, 5, 5), ("Zuschneiden", -20, 280.4, 120.6, 400)]
        self.assertEqual(kern.zuschnitt(m, 400, 300), (0, 280, 121, 300))

    def test_rueckgaengig_holt_vorigen(self):
        m = [("Zuschneiden", 10, 10, 50, 50), ("Zuschneiden", 0, 0, 100, 100)]
        m.pop()
        self.assertEqual(kern.zuschnitt(m, 400, 300), (10, 10, 50, 50))

    def test_keiner_oder_zu_klein(self):
        self.assertIsNone(kern.zuschnitt([("Rahmen", 0, 0, 5, 5)], 400, 300))
        self.assertIsNone(kern.zuschnitt([("Zuschneiden", 10, 10, 11, 50)], 400, 300))
        self.assertIsNone(kern.zuschnitt([("Zuschneiden", 500, 10, 600, 50)], 400, 300))   # ganz außerhalb


if __name__ == "__main__":
    unittest.main()
