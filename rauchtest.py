"""Rauchtest (python rauchtest.py) Rückmeldung Schritt 1 ohne echte Eingaben: App mit Test-Kürzel und Wegwerf-Ablage, ein Zielfenster
(magenta) in einem EIGENEN Prozess als „getestetes Programm“, Erfassungsfenster füllen, Strg+Enter per
event_generate, Dateien prüfen; Esc mit Text fragt nach; eigenes Fenster wird ignoriert."""
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
win.dpi_bewusst()
root = tk.Tk()
root.withdraw()
app = rm.App(root, ablage, "ctrl+alt+shift+f24")
assert app.starte()

ZIEL_CODE = ("import ctypes; ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)); "
             "import tkinter as tk; r=tk.Tk(); r.title('Zielprogramm Test'); r.geometry('400x250+200+200'); "
             "r.configure(background='#ff00ff'); r.after(60000, r.destroy); r.mainloop()")
ziel_proz = subprocess.Popen([sys.executable, "-c", ZIEL_CODE])
ziel_hwnd = 0
for _ in range(50):
    ziel_hwnd = ctypes.windll.user32.FindWindowW(None, "Zielprogramm Test")
    if ziel_hwnd:
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
    print("Erfassung offen:", f is not None, "| Bild:", f.bild.size if f and f.bild else None)
    px = f.bild.getpixel((f.bild.width // 2, f.bild.height // 2))
    print("Bildmitte magenta (Zielfenster unverdeckt?):", px[:3] == (255, 0, 255), px)
    print("Titel:", f.titel, "| Programm:", f.programm)
    f.notiz.insert("1.0", "Testnotiz mit Umlauten äöü")
    f.event_generate("<Alt-Key-2>")
    pumpe(0.2)
    print("Art nach Alt+2:", f.art.get())
    f.notiz.event_generate("<Control-Return>")
    pumpe(0.3)
    print("Fenster zu:", app.fenster is None, "| gespeichert:", len(app.gespeichert))
    kopf, notiz = kern.lies(app.gespeichert[0])
    print("Kopf:", {k: kopf.get(k) for k in ("projekt", "art", "status", "programm", "bilder", "bild_fuer_ki")})
    print("Notiz:", notiz)
    print("Dateien:", sorted(os.listdir(os.path.join(ablage, "Unbekannt"))))

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
    print("Esc leer schließt:", app.fenster is None, "| weiterhin gespeichert:", len(app.gespeichert))

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
