# Änderungen

Was sich von Version zu Version für Nutzer ändert. Neueste Version oben. Das
Warum steht in `FAHRPLAN.md` und `KONZEPT.md`.

## Unveröffentlicht

- (noch nichts)

## 0.2.0 - 2026-11-23

Funde aus der ersten Nutzung.

- `rueckmeldung.json` wird auch in der Ablage (`~/Rueckmeldungen/`) gesucht, nicht nur neben dem Programm. So findet eine EXE in „Downloads“ die Einstellungen. Fehlt die Datei, sagen das die Startzeile und das Erfassungsfenster („ohne rueckmeldung.json“), statt still alles nach „Unbekannt“ zu legen.
- „Bild für KI freigeben“ ist standardmäßig angehakt. Ein Projekt schaltet das mit `"bild_fuer_ki": false` ab.
- Knopf „Ablage öffnen“ im Erfassungsfenster: Explorer im Ordner des gewählten Projekts.
- `--konfig` mit einer Datei, die es nicht gibt, ist ein Fehler.

## 0.1.0 - 2026-11-16

Erster Release, als `Rueckmeldung.exe` ohne Python lauffähig.

- Globales Tastenkürzel (Vorgabe Strg+Alt+F) nimmt das aktive Fenster auf, bevor sich das eigene Fenster öffnet. Die Aufnahme beachtet die DPI-Skalierung je Monitor.
- Erfassungsfenster: Art (Fehler/Idee/Notiz, Alt+1/2/3), Notiz, Strg+Enter speichert, Esc verwirft. Danach hat das getestete Programm wieder den Fokus.
- Gespeichert wird eine Markdown-Datei mit Kopfteil samt PNG, je Projekt in einem eigenen Ordner unter `~/Rueckmeldungen`.
- `rueckmeldung.json` ordnet Fenster über Programmname und Fenstertitel Projekten zu (Dialoge landen beim Projekt ihres Hauptfensters). Liest die Version aus dem Fenstertitel und hängt auf Wunsch die letzten Zeilen eines Protokolls an. Tippfehler in der Konfiguration meldet das Werkzeug beim Start.
- Kopfteil mit Bildschirmgröße und Skalierung, Rechner-Kürzel und dem Vermerk `bild_fuer_ki`.
- Bild bearbeiten: Rahmen, Pfeil, Schwärzen und Zuschneiden, Rückgängig mit Strg+Z, Mausrad-Zoom und Verschieben. Markierungen werden erst beim Speichern in voller Auflösung eingebrannt.
- Beenden vorerst über das Konsolenfenster (schließen oder Strg+C).
