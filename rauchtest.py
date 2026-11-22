"""Rauchtest (python rauchtest.py): der ganze Ablauf ohne echte Eingaben.

Ein „getestetes Programm“ läuft in einem EIGENEN Prozess (das Werkzeug nimmt seine eigenen Fenster absichtlich
nicht auf): Hauptfenster „Zielprogramm v7.3.1“ und ein Dialog „Einstellungen“ (magenta). Aufgenommen wird der
Dialog; Projekt und Version müssen trotzdem über den Titel des Hauptfensters erkannt werden. Dann Markierungen
und Zoom per Maus-Ereignis, Strg+Enter, Dateien prüfen (Ordner des Projekts, Kopf, Protokoll, eingebrannte
Markierungen); Esc mit Text fragt nach; Projekt von Hand umstellen; eigenes Fenster wird ignoriert.
Ausgabe: je Prüfung eine Zeile mit True/False. Die Wegwerf-Ablage wird am Ende gelöscht.
"""
import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tkinter as tk
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rueckmeldung as rm  # noqa: E402
import rueckmeldung_kern as kern  # noqa: E402
import rueckmeldung_windows as win  # noqa: E402

ablage = tempfile.mkdtemp(prefix="rm_test_")
log = os.path.join(ablage, "ziel.log")
with open(log, "w", encoding="utf-8") as f:
    f.write("".join(f"Zeile {i}\n" for i in range(1, 101)))
konfig = kern.pruefe_konfig({
    "kuerzel": "ctrl+alt+shift+f24", "ablage": ablage, "rechner": "Test-PC",
    "projekte": [
        {"name": "Andere", "regeln": [{"programm": "gibtsnicht.exe"}]},
        {"name": "Zielprojekt", "regeln": [{"programm": "python.exe", "fenstertitel": "^Zielprogramm v"}],
         "version": r"v(\d+\.\d+\.\d+)", "bild_fuer_ki": True,
         "protokoll": {"datei": os.path.join(ablage, "*.log"), "zeilen": 5, "vorgabe": True}},
    ]})
win.dpi_bewusst()
root = tk.Tk()
root.withdraw()
app = rm.App(root, konfig)
assert app.starte()

ZIEL_CODE = ("import ctypes; ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)); "
             "import tkinter as tk; r=tk.Tk(); r.title('Zielprogramm v7.3.1'); r.geometry('300x200+600+200'); "
             "d=tk.Toplevel(r); d.title('Einstellungen'); d.geometry('400x250+200+200'); "
             "d.configure(background='#ff00ff'); r.after(60000, r.destroy); r.mainloop()")
ziel_proz = subprocess.Popen([sys.executable, "-c", ZIEL_CODE])
ziel_hwnd = 0
for _ in range(50):
    ziel_hwnd = ctypes.windll.user32.FindWindowW(None, "Einstellungen")
    if ziel_hwnd and ctypes.windll.user32.FindWindowW(None, "Zielprogramm v7.3.1"):
        break
    time.sleep(0.2)
time.sleep(1.5)
print("Zielfenster gefunden:", bool(ziel_hwnd))


def pumpe(sek):
    ende = time.time() + sek
    while time.time() < ende:
        root.update()
        time.sleep(0.02)


try:
    app.kuerzel.simuliere()
    time.sleep(0.3)
    print("Kürzel-Ereignis in der Queue:", app.ereignisse.qsize() == 1)
    while not app.ereignisse.empty():
        app.ereignisse.get_nowait()                 # nicht das echte Vordergrundfenster aufnehmen
    app.ausgeloest(ziel_hwnd)
    f = app.fenster
    m = f.moment
    print("Erfassung offen:", f is not None, "| Bild:", m["bild"].size if m["bild"] else None)
    px = m["bild"].getpixel((m["bild"].width // 2, m["bild"].height // 2))
    print("Bildmitte magenta (Dialog unverdeckt?):", px[:3] == (255, 0, 255), px)
    print("Dialog über Hauptfenster erkannt - Projekt:", f.projektname.get() == "Zielprojekt",
          "| Version:", m["version"] == "7.3.1", "| Titel:", m["titel_liste"])
    print("Bildschirm:", bool(m["bildschirm"]), m["bildschirm"])
    print("Vorgaben des Projekts - Bild für KI:", f.bild_ki.get(), "| Protokoll:", f.mit_protokoll.get())
    f.notiz.insert("1.0", "Testnotiz mit Umlauten äöü")
    f.event_generate("<Alt-Key-2>")
    pumpe(0.2)
    print("Art nach Alt+2:", f.art.get() == "Idee")

    # Bild bearbeiten: Markierungen per Maus-Ereignis auf der Fläche (Bildkoordinaten -> Fläche umrechnen)
    ed = f.editor
    pumpe(0.3)

    def ziehe(art, x0, y0, x1, y1):
        ed.werkzeug.set(art)
        a0, b0 = ed.ansicht.zu_flaeche(x0, y0)
        a1, b1 = ed.ansicht.zu_flaeche(x1, y1)
        ed.flaeche.event_generate("<ButtonPress-1>", x=int(a0), y=int(b0))
        ed.flaeche.event_generate("<B1-Motion>", x=int((a0 + a1) / 2), y=int((b0 + b1) / 2))
        ed.flaeche.event_generate("<B1-Motion>", x=int(a1), y=int(b1))
        ed.flaeche.event_generate("<ButtonRelease-1>", x=int(a1), y=int(b1))
        pumpe(0.1)

    vorher = ed.ansicht.massstab
    ziehe("Rahmen", 50, 50, 250, 200)
    ziehe("Pfeil", 20, 240, 300, 240)
    ziehe("Schwärzen", 300, 20, 380, 80)
    ziehe("Schwärzen", 10, 10, 11, 11)                      # nur Klick, keine Markierung
    ziehe("Rahmen", 100, 100, 150, 150)
    ed.rueckgaengig()
    ziehe("Zuschneiden", 0, 0, 200, 200)                    # wird vom nächsten Ausschnitt ersetzt
    ziehe("Zuschneiden", 10, 10, 390, 260)
    pumpe(0.2)
    abgedunkelt = [i for i in ed.flaeche.find_withtag("mark") if ed.flaeche.itemcget(i, "stipple") == "gray50"]
    print("Ausschnitt abgedunkelt:", len(abgedunkelt) == 4)
    print("Markierungen (Klick ignoriert, letzte zurückgenommen):",
          [x[0] for x in ed.markierungen] == ["Rahmen", "Pfeil", "Schwärzen", "Zuschneiden", "Zuschneiden"])
    a, b = ed.ansicht.zu_flaeche(200, 140)
    ed.flaeche.event_generate("<MouseWheel>", x=int(a), y=int(b), delta=240)
    pumpe(0.2)
    punkt = [round(v) for v in ed.ansicht.zu_bild(int(a), int(b))]
    print("Mausrad zoomt:", ed.ansicht.massstab > vorher, "| Punkt bleibt:", punkt == [200, 140])
    ed.einpassen()
    pumpe(0.1)
    print("Einpassen:", round(ed.ansicht.massstab, 3) == round(vorher, 3))

    f.notiz.event_generate("<Control-Return>")
    pumpe(0.3)
    print("Fenster zu:", app.fenster is None, "| gespeichert:", len(app.gespeichert) == 1)
    ordner = os.path.join(ablage, "Zielprojekt")
    kopf, notiz = kern.lies(app.gespeichert[0])
    print("Im Projektordner:", os.path.dirname(app.gespeichert[0]) == ordner)
    print("Kopf:", kopf["projekt"] == "Zielprojekt", kopf["art"] == "Idee", kopf.get("version") == "7.3.1",
          kopf.get("rechner") == "Test-PC", kopf.get("fenster") == "Einstellungen", bool(kopf.get("bildschirm")),
          kopf["bild_fuer_ki"] is True)
    print("Notiz:", notiz == "Testnotiz mit Umlauten äöü")
    with open(os.path.join(ordner, kopf["protokoll"]), encoding="utf-8") as p:
        print("Protokoll = letzte 5 Zeilen:", p.read() == "".join(f"Zeile {i}\n" for i in range(96, 101)))
    from PIL import Image
    gespeichert = Image.open(os.path.join(ordner, kopf["bilder"][0])).convert("RGB")
    print("Zugeschnitten auf den letzten Ausschnitt:", gespeichert.size == (380, 250), gespeichert.size)
    print("Eingebrannt (um 10 px verschoben) - Rahmen rot:", gespeichert.getpixel((41, 110)) == (230, 30, 30),
          "| innen magenta:", gespeichert.getpixel((140, 110)) == (255, 0, 255),
          "| Pfeil rot:", gespeichert.getpixel((140, 230)) == (230, 30, 30),
          "| geschwärzt:", gespeichert.getpixel((330, 40)) == (0, 0, 0),
          "| zurückgenommen fehlt:", gespeichert.getpixel((115, 91)) == (255, 0, 255))

    # Zweite Rückmeldung: Projekt von Hand auf „Unbekannt“ -> keine Version, kein Protokoll; Bild für KI ist
    # vorgegeben (seit 2026-11-22) und wird hier von Hand abgewählt
    app.ausgeloest(ziel_hwnd)
    f = app.fenster
    f.projektname.set(kern.PROJEKT_UNBEKANNT)
    f._projekt_gewaehlt()
    print("Von Hand Unbekannt - Bild für KI vorgegeben:", f.bild_ki.get() is True,
          "| Protokoll gesperrt:", str(f._protokoll_knopf.cget("state")) == "disabled")
    f.bild_ki.set(False)
    f.notiz.insert("1.0", "zweite")
    f.event_generate("<Control-Return>")
    pumpe(0.3)
    kopf2, _ = kern.lies(app.gespeichert[1])
    print("Gespeichert unter Unbekannt:", kopf2["projekt"] == "Unbekannt", "version" not in kopf2,
          "protokoll" not in kopf2, kopf2["bild_fuer_ki"] is False)

    app.ausgeloest(ziel_hwnd)
    f = app.fenster
    f.notiz.insert("1.0", "wird verworfen")
    with mock.patch.object(rm.messagebox, "askyesno", return_value=False) as frage:
        f.event_generate("<Escape>")
        pumpe(0.2)
    print("Esc mit Text fragt:", frage.called, "| bleibt offen:", app.fenster is not None)
    f.notiz.delete("1.0", tk.END)
    f.event_generate("<Escape>")
    pumpe(0.2)
    print("Esc leer schließt:", app.fenster is None, "| nichts dazu:", len(app.gespeichert) == 2)

    eigen = tk.Toplevel(root)
    eigen.geometry("200x100+50+50")
    pumpe(0.3)
    app.ausgeloest(win.oberstes_fenster(eigen.winfo_id()))
    print("Eigenes Fenster ignoriert:", app.fenster is None)
finally:
    app.stoppe()
    ziel_proz.terminate()
    root.destroy()
    shutil.rmtree(ablage, ignore_errors=True)
print("Wegwerf-Ablage gelöscht.")
