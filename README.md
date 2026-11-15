# Rückmeldung

Hält beim Testen einen Moment fest: **Strg+Alt+F** drücken, das aktive Fenster wird sofort fotografiert, einen Satz dazu tippen, **Strg+Enter**. Gespeichert wird eine Markdown-Datei samt Bild in einem Ordner. Von dort liest sie die nächste Arbeitssitzung, ob Mensch oder KI-Assistent, und ordnet sie ein.

Gedacht für Entwickler, die ihr eigenes Programm im Alltag ausprobieren: Was auffällt, ist festgehalten, bevor es vergessen ist, mit Bild und Fenstertitel statt einer ungenauen Erinnerung. Läuft unabhängig vom getesteten Programm, das dafür nichts einbauen muss.

Nichts verlässt den Rechner: Das Werkzeug greift nicht aufs Netz zu.

## Schnellstart

Voraussetzung: Windows, Python 3.11+ mit Tkinter, dazu Pillow.

```bash
python -m pip install -r requirements.txt
python rueckmeldung.py                        # läuft im Hintergrund, Kürzel Strg+Alt+F, Ablage ~/Rueckmeldungen
python rueckmeldung.py --ablage D:/Rueck      # andere Ablage
python rueckmeldung.py --kuerzel ctrl+alt+r   # anderes Kürzel
```

Im Erfassungsfenster:

| Taste | Wirkung |
|---|---|
| Strg+Enter | speichern, zurück ins vorige Programm |
| Esc | verwerfen (mit Rückfrage, wenn schon Text dasteht) |
| Alt+1 / 2 / 3 | Art: Fehler / Idee / Notiz |
| linke Maustaste ziehen | Rahmen, Pfeil oder Schwärzen (Auswahl über dem Bild) |
| Mausrad | Zoom um die Mausposition |
| rechte oder mittlere Maustaste ziehen | Ausschnitt verschieben |
| Strg+Z (nach Klick ins Bild) | letzte Markierung zurücknehmen |

Markierungen werden erst beim Speichern in voller Auflösung ins Bild eingebrannt. Geschwärztes ist danach wirklich weg, die ungeschwärzte Aufnahme liegt nie auf der Platte.

Beenden vorerst mit Strg+C in der Konsole.

## Was gespeichert wird

```
~/Rueckmeldungen/
  Unbekannt/
    2026-11-15_210412_fehler.md
    2026-11-15_210412_fehler_1.png
```

```markdown
---
projekt: "Unbekannt"
art: "Fehler"
zeit: "2026-11-15 21:04:12"
status: "offen"
fenster: "Mein Programm v1.2"
programm: "MeinProgramm.exe"
bilder: ["2026-11-15_210412_fehler_1.png"]
bild_fuer_ki: nein
---
Der Knopf unten rechts fehlt, sobald das Fenster schmal ist.
```

`bild_fuer_ki: nein` ist eine Abmachung mit einem KI-Assistenten, der die Ablage liest: Bilder mit diesem Vermerk öffnet er nicht, weil sie echte Daten zeigen können.

## Stand

Schritte 1 und (größtenteils) 3 von 5, siehe [KONZEPT.md](KONZEPT.md): Kürzel, Aufnahme, Notiz, Speichern, Markieren und Zoomen. Als Nächstes kommen die Zuordnung zu Projekten über eine Konfigurationsdatei und eine EXE.

## Entwicklung

```bash
python -m unittest discover -s tests -t .
python -m ruff check .
```

`rueckmeldung_kern.py` enthält die Logik ohne Fenster (nur Standardbibliothek, schnell getestet), `rueckmeldung_windows.py` die Windows-Aufrufe (Kürzel, Aufnahme, Fokus), `rueckmeldung_bild.py` das Einbrennen der Markierungen (Pillow), `rueckmeldung.py` die Fenster. `rauchtest.py` spielt den ganzen Ablauf ohne echte Eingaben durch.

## Lizenz

MIT, siehe [LICENSE](LICENSE).
