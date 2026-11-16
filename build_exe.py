"""Release-Build: baut `dist/Rueckmeldung.exe` mit PyInstaller und prüft das Ergebnis.

Die EXE läuft vorerst MIT Konsolenfenster: Ein eigenes Fenster zum Beenden gibt es noch nicht (FAHRPLAN Schritt 5),
also beendet man sie wie den Python-Start über die Konsole. Ohne Konsole bliebe nur der Task-Manager.

Nach dem Build wird die EXE gelesen: Jedes Modul des Werkzeugs und Pillow müssen drinstecken. `rueckmeldung_bild`
wird nur innerhalb einer Funktion importiert - fehlt es, merkt man es erst beim ersten Speichern mit Markierung.
Schlägt die Prüfung fehl, endet das Skript mit Exit-Code 1: dann NICHT veröffentlichen.

Aufruf:  python build_exe.py            (baut und prüft)
         python build_exe.py --pruefen  (prüft eine vorhandene dist/Rueckmeldung.exe)
Voraussetzung: python -m pip install -r requirements-build.txt
"""
import os
import subprocess
import sys

PROJEKT = os.path.dirname(os.path.abspath(__file__))
NAME = "Rueckmeldung"
EXE = os.path.join(PROJEKT, "dist", NAME + ".exe")

# Module, die in der EXE stecken müssen (das Hauptskript rueckmeldung.py liegt nicht im Modul-Archiv)
MODULE = ["rueckmeldung_kern", "rueckmeldung_windows", "rueckmeldung_bild", "PIL.Image", "PIL.ImageDraw", "tkinter"]


def baue():
    befehl = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--console", "--name", NAME, "--clean", "--noconfirm",
        "--hidden-import", "rueckmeldung_bild",   # nur in einer Funktion importiert
        "rueckmeldung.py",
    ]
    print("Build:", " ".join(befehl), "\n")
    if subprocess.run(befehl, cwd=PROJEKT).returncode != 0:
        print("\nFEHLER: PyInstaller ist fehlgeschlagen.")
        sys.exit(1)


def pruefe():
    from PyInstaller.archive.readers import CArchiveReader, ZlibArchiveReader

    if not os.path.exists(EXE):
        print(f"FEHLER: {EXE} nicht gefunden.")
        sys.exit(1)
    archiv = CArchiveReader(EXE)
    pyz_name = next(n for n in archiv.toc if n.lower().endswith(".pyz"))
    rohdaten = archiv.extract(pyz_name)
    if not isinstance(rohdaten, (bytes, bytearray)):   # ältere PyInstaller-Versionen: (typ, daten)
        rohdaten = rohdaten[1]
    pyz_datei = os.path.join(PROJEKT, "dist", "_pruef.pyz")
    with open(pyz_datei, "wb") as f:
        f.write(rohdaten)
    try:
        module = set(ZlibArchiveReader(pyz_datei).toc)
    finally:
        os.remove(pyz_datei)

    fehlt = [m for m in MODULE if m not in module]
    if "rueckmeldung" not in archiv.toc:
        fehlt.append("rueckmeldung (Hauptskript)")
    groesse = os.path.getsize(EXE) / (1024 * 1024)
    if fehlt:
        print(f"\nPRÜFUNG FEHLGESCHLAGEN - EXE NICHT veröffentlichen, es fehlt: {', '.join(fehlt)}")
        sys.exit(1)
    print(f"\nPrüfung OK: {len(MODULE)} Module und Hauptskript enthalten ({groesse:.1f} MB): {EXE}")


if __name__ == "__main__":
    if "--pruefen" not in sys.argv:
        baue()
    pruefe()
