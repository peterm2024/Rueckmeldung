# Rückmeldung

Windows-Werkzeug im Hintergrund: Ein globales Tastenkürzel nimmt das aktive Fenster auf, dazu eine Notiz, gespeichert als Markdown und PNG in einem Ablage-Ordner je Projekt. Angelegt am 2026-11-15 aus einer Idee beim Testen von KID, gebaut nach dem Muster des Testwizards: projektunabhängig, öffentlich, MIT.

Kommunikation, Doku und Code-Kommentare auf Deutsch. Projektübergreifendes (Hardware, Ollama-Server, Konventionen, andere Projekte) steht im Projekte-Wiki `~/Projekte/_Projekte-Wiki/`, Einstieg über `INDEX.md`.

## Zuerst lesen

- `FAHRPLAN.md` für den aktuellen Stand, `KONZEPT.md` für Absicht, Entscheidungen und Bauschritte.
- `FALLSTRICKE_UND_WORKAROUNDS.md` vor jeder Fehlersuche, sobald es sie gibt.

## Befehle

```bash
.venv/Scripts/python rueckmeldung.py                          # starten (Strg+Alt+F, Ablage ~/Rueckmeldungen)
.venv/Scripts/python -m unittest discover -s tests -t .       # Tests
.venv/Scripts/python -m ruff check .                          # Sicherheitsnetz (F, E9, E722)
.venv/Scripts/python build_exe.py                             # dist/Rueckmeldung.exe bauen und prüfen
```

## Release

`VERSION` in `rueckmeldung_kern.py` und `CHANGELOG.md` angleichen, Tests und Ruff grün, `build_exe.py`, EXE kurz starten, committen, `git tag -a vX.Y.Z`, pushen, `gh release create vX.Y.Z dist/Rueckmeldung.exe` mit dem Changelog-Abschnitt als Text. Danach `VERSION` auf `X.Y.Z+dev`.

## Technische Entscheidungen

- Drei Module: `rueckmeldung_kern` (nur Standardbibliothek, kein tkinter, keine Bilder - Logik und Dateiformat), `rueckmeldung_windows` (ctypes: Kürzel, Aufnahme, Fokus), `rueckmeldung` (Tk-Fenster). 2026-11-15.
- Das Kürzel läuft in einem eigenen Thread mit Windows-Nachrichtenschleife und meldet sich nur über eine Queue; Tkinter wird ausschließlich im Haupt-Thread angefasst (`after`-Abholung). 2026-11-15.
- Aufnahme **vor** dem eigenen Fenster, über die DWM-Rahmenmaße, Prozess pro Monitor DPI-bewusst. 2026-11-15.
- Kopfteil der Markdown-Datei mit JSON-Werten (zugleich YAML), Markdown zuletzt und über eine Temp-Datei geschrieben. 2026-11-15.
- Konfiguration `rueckmeldung.json` neben dem Programm, sonst in `~/Rueckmeldungen/` (seit 2026-11-22, weil die EXE aus „Downloads“ lief; Peters Datei liegt in der Ablage, nicht im Repo, Vorlage `rueckmeldung.beispiel.json`); keine gefunden wird sichtbar gemeldet; Unbekannte Schlüssel sind ein Fehler, `_…` sind Kommentare. Projekt-Regeln prüfen alle sichtbaren Fenstertitel des Prozesses, damit Dialoge zum Hauptfenster finden. 2026-11-15.
- Kein Netzwerkzugriff, keine Telemetrie. Bilder mit `bild_fuer_ki: nein` öffnet die KI nicht. Der Haken „Bild für KI freigeben“ ist standardmäßig gesetzt (Peter 2026-11-22: leer wird er übersehen), ein Projekt schaltet ihn mit `"bild_fuer_ki": false` ab.

## Arbeitsweise

- Peter steuert Struktur und Architektur, Claude implementiert. Bei nicht trivialen Änderungen kurz erklären, was und warum.
- Kürzel, Aufnahme und Fenster prüft Peter; Logik gehört in schnelle Kern-Tests. Selbsttests ohne echte Eingaben: Kürzel per `Kuerzel.simuliere()`, Zielfenster in einem eigenen Prozess (das eigene Fenster nimmt das Werkzeug absichtlich nicht auf).
- Echte Tastendrücke oder Mausbewegungen nur mit Peters ausdrücklicher Freigabe. Kein Fokus-Klau in Selbsttests, wenn es sich vermeiden lässt.
- Nach einem gelösten, nicht offensichtlichen Problem einen Eintrag in `FALLSTRICKE_UND_WORKAROUNDS.md` (Problem / Ursache / Lösung).
- Erledigte Punkte im `FAHRPLAN.md` abhaken, mit Datum (JJJJ-MM-TT).
- Ändert sich etwas, das andere Projekte betrifft, das Projekte-Wiki nachziehen.
- Git: kurze deutsche Commit-Messages. Commit erst nach Peters Abnahme. **Das Repo ist öffentlich:** keine echten Namen, Orte, Mail-Adressen, keine festen Benutzerpfade (`~` statt `C:\Users\<name>`), Beispiele neutral („Tester-PC“, „Mein Programm“).
