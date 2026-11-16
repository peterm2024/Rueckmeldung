# Rückmeldung

Hält beim Testen einen Moment fest: **Strg+Alt+F** drücken, das aktive Fenster wird sofort fotografiert, einen Satz dazu tippen, **Strg+Enter**. Gespeichert wird eine Markdown-Datei samt Bild in einem Ordner. Von dort liest sie die nächste Arbeitssitzung, ob Mensch oder KI-Assistent, und ordnet sie ein.

Gedacht für Entwickler, die ihr eigenes Programm im Alltag ausprobieren: Was auffällt, ist festgehalten, bevor es vergessen ist, mit Bild und Fenstertitel statt einer ungenauen Erinnerung. Läuft unabhängig vom getesteten Programm, das dafür nichts einbauen muss.

Nichts verlässt den Rechner: Das Werkzeug greift nicht aufs Netz zu.

## Download

Unter [Releases](https://github.com/peterm2024/Rueckmeldung/releases) liegt `Rueckmeldung.exe`, eine einzelne Datei, die ohne Python läuft. In einen eigenen Ordner legen, starten, fertig. Die `rueckmeldung.json` (siehe unten) gehört neben die EXE.

Die EXE öffnet vorerst ein Konsolenfenster. Solange es offen ist, läuft das Werkzeug, Schließen beendet es. Windows SmartScreen und manche Virenscanner warnen beim ersten Start vor einem unbekannten Herausgeber, weil die EXE nicht signiert ist. Wer dem nicht trauen mag, startet aus dem Quellcode (Schnellstart).

## Schnellstart

Aus dem Quellcode. Voraussetzung: Windows, Python 3.11+ mit Tkinter, dazu Pillow.

```bash
python -m pip install -r requirements.txt
python rueckmeldung.py                        # läuft im Hintergrund, Einstellungen aus rueckmeldung.json
python rueckmeldung.py --konfig andere.json   # andere Konfiguration
python rueckmeldung.py --ablage D:/Rueck      # andere Ablage (überschreibt die Konfiguration)
python rueckmeldung.py --kuerzel ctrl+alt+r   # anderes Kürzel (überschreibt die Konfiguration)
```

Ohne `rueckmeldung.json` gelten Strg+Alt+F und `~/Rueckmeldungen`, und alles landet unter `Unbekannt`.

## Projekte zuordnen

`rueckmeldung.json` neben `rueckmeldung.py` bzw. `Rueckmeldung.exe` (Vorlage: [rueckmeldung.beispiel.json](rueckmeldung.beispiel.json)) sagt, welches Fenster zu welchem Projekt gehört:

```json
{
  "kuerzel": "ctrl+alt+f",
  "ablage": "~/Rueckmeldungen",
  "rechner": "Entwickler-PC",
  "projekte": [
    {
      "name": "MeinProgramm",
      "regeln": [
        {"programm": "MeinProgramm.exe"},
        {"programm": "python.exe", "fenstertitel": "^Mein Programm v"}
      ],
      "version": "v(\\d+\\.\\d+\\.\\d+)",
      "bild_fuer_ki": false,
      "protokoll": {"datei": "~/MeinProgramm/*.log", "zeilen": 40, "vorgabe": false}
    }
  ]
}
```

- **Regeln:** Das erste Projekt mit einer passenden Regel gewinnt. Eine Regel passt, wenn alle ihre Angaben passen: `programm` ist der Dateiname des Programms, `fenstertitel` ein regulärer Ausdruck. Er darf auch auf ein anderes Fenster desselben Programms passen, so landet ein Dialog wie „Einstellungen“ beim Projekt seines Hauptfensters.
- **version:** regulärer Ausdruck mit einer Gruppe, angewandt auf die Fenstertitel des Programms.
- **bild_fuer_ki:** Vorgabe für den Schalter „Bild für KI freigeben“ (siehe unten).
- **protokoll:** Die letzten Zeilen der neuesten passenden Datei kommen auf Wunsch als `…_protokoll.txt` dazu. `vorgabe` sagt, ob der Schalter dafür anfangs gesetzt ist.
- **rechner:** freies Kürzel für den Kopf der Rückmeldung (statt des echten Rechnernamens).
- Schlüssel, die mit `_` beginnen, sind Kommentare. Alles andere Unbekannte meldet das Werkzeug beim Start als Fehler, damit Tippfehler nicht still wirkungslos bleiben.

Im Erfassungsfenster steht das erkannte Projekt oben und lässt sich von Hand umstellen.

Im Erfassungsfenster:

| Taste | Wirkung |
|---|---|
| Strg+Enter | speichern, zurück ins vorige Programm |
| Esc | verwerfen (mit Rückfrage, wenn schon Text dasteht) |
| Alt+1 / 2 / 3 | Art: Fehler / Idee / Notiz |
| linke Maustaste ziehen | Rahmen, Pfeil, Schwärzen oder Zuschneiden (Auswahl über dem Bild) |
| Mausrad | Zoom um die Mausposition |
| rechte oder mittlere Maustaste ziehen | Ausschnitt verschieben |
| Strg+Z (nach Klick ins Bild) | letzte Markierung zurücknehmen |

Beim Zuschneiden gilt der zuletzt gezogene Ausschnitt, außerhalb davon ist das Bild abgedunkelt. Markierungen werden erst beim Speichern in voller Auflösung ins Bild eingebrannt, danach wird zugeschnitten. Geschwärztes ist danach wirklich weg, die ungeschwärzte Aufnahme liegt nie auf der Platte.

Beenden vorerst mit Strg+C in der Konsole oder durch Schließen des Konsolenfensters.

## Was gespeichert wird

```
~/Rueckmeldungen/
  MeinProgramm/
    2026-11-15_210412_fehler.md
    2026-11-15_210412_fehler_1.png
    2026-11-15_210412_fehler_protokoll.txt
  Unbekannt/
```

```markdown
---
projekt: "MeinProgramm"
art: "Fehler"
zeit: "2026-11-15 21:04:12"
status: "offen"
version: "1.2.0"
fenster: "Mein Programm v1.2.0"
programm: "MeinProgramm.exe"
rechner: "Entwickler-PC"
bildschirm: "2560x1440, Skalierung 125 %"
bilder: ["2026-11-15_210412_fehler_1.png"]
protokoll: "2026-11-15_210412_fehler_protokoll.txt"
bild_fuer_ki: nein
---
Der Knopf unten rechts fehlt, sobald das Fenster schmal ist.
```

`bild_fuer_ki: nein` ist eine Abmachung mit einem KI-Assistenten, der die Ablage liest: Bilder mit diesem Vermerk öffnet er nicht, weil sie echte Daten zeigen können.

## Stand

Version 0.1.0, Schritte 1, 2 und (größtenteils) 3 von 5, siehe [KONZEPT.md](KONZEPT.md) und [CHANGELOG.md](CHANGELOG.md): Kürzel, Aufnahme, Notiz, Speichern, Projekte zuordnen, Markieren, Zuschneiden und Zoomen, als EXE ohne Python. Als Nächstes kommen `liste`/`erledigt` zum Einordnen und ein Fenster zum Beenden.

## Entwicklung

```bash
python -m unittest discover -s tests -t .
python -m ruff check .
python -m pip install -r requirements-build.txt   # einmalig, für die EXE
python build_exe.py                              # baut dist/Rueckmeldung.exe und prüft ihren Inhalt
```

`rueckmeldung_kern.py` enthält die Logik ohne Fenster (nur Standardbibliothek, schnell getestet), `rueckmeldung_windows.py` die Windows-Aufrufe (Kürzel, Aufnahme, Fokus), `rueckmeldung_bild.py` das Einbrennen der Markierungen (Pillow), `rueckmeldung.py` die Fenster. `rauchtest.py` spielt den ganzen Ablauf ohne echte Eingaben durch.

## Lizenz

MIT, siehe [LICENSE](LICENSE).
