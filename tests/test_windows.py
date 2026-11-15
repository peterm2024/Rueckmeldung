"""Tests der Windows-Anbindung, die ohne echte Tastendrücke auskommen: Kürzel-Thread (Ereignis per
Thread-Nachricht simuliert) und Aufnahme eines eigenen Testfensters."""
import queue
import sys
import tkinter as tk
import unittest

import rueckmeldung_kern as kern

if sys.platform == "win32":
    import rueckmeldung_windows as win

# Eine Kombination, die sonst niemand belegt - der Test soll nicht mit einer laufenden Rückmeldung kollidieren
TEST_KUERZEL = "ctrl+alt+shift+f24"


@unittest.skipUnless(sys.platform == "win32", "nur Windows")
class TestKuerzel(unittest.TestCase):
    def test_anmelden_ereignis_abmelden(self):
        q = queue.Queue()
        k = win.Kuerzel(*kern.lies_kuerzel(TEST_KUERZEL), lambda: q.put(1))
        self.assertTrue(k.starte(), k.fehler)
        try:
            k.simuliere()
            self.assertEqual(q.get(timeout=2), 1)
            # Ein zweites Programm mit derselben Kombination bekommt sie nicht (so erkennt ein zweiter Start sich)
            zweit = win.Kuerzel(*kern.lies_kuerzel(TEST_KUERZEL), lambda: None)
            self.assertFalse(zweit.starte())
            self.assertIsNotNone(zweit.fehler)
        finally:
            k.stoppe()
        nachher = win.Kuerzel(*kern.lies_kuerzel(TEST_KUERZEL), lambda: None)   # wieder frei
        self.assertTrue(nachher.starte(), nachher.fehler)
        nachher.stoppe()


@unittest.skipUnless(sys.platform == "win32", "nur Windows")
class TestAufnahme(unittest.TestCase):
    def test_eigenes_fenster(self):
        root = tk.Tk()
        try:
            root.geometry("300x200+120+120")
            root.configure(background="#ff00ff")
            root.update()
            root.after(300)
            root.update()
            hwnd = win.oberstes_fenster(root.winfo_id())
            self.assertTrue(win.gehoert_zu_mir(hwnd))
            root.title("Rückmeldung Testfenster")
            root.update()
            self.assertEqual(win.fenster_titel(hwnd), "Rückmeldung Testfenster")
            self.assertTrue(win.fenster_programm(hwnd).lower().startswith("python"))
            l, o, r, u = win.fensterrahmen(hwnd)
            self.assertGreaterEqual(r - l, 300)
            self.assertGreaterEqual(u - o, 200)
            bild = win.aufnahme(hwnd)
            self.assertEqual(bild.size, (r - l, u - o))
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
