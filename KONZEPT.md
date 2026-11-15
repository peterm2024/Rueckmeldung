# Konzept: Rückmeldung per Tastenkürzel (eigenes Werkzeug)

Stand 15.11.2026. Idee Peter beim Test von v0.9.30 auf dem Tester-PC: Beim Ausprobieren fällt etwas auf, und bis zur nächsten Sitzung ist die Hälfte vergessen oder nur noch ungenau im Kopf. Ein Tastenkürzel soll den Moment festhalten: Bild vom Fenster, ein Satz dazu, fertig. Die nächste Sitzung liest die gesammelten Rückmeldungen und ordnet sie in den Fahrplan ein.

Entschieden (Peter 15.11.2026):

- **Eigenes Werkzeug**, das im Hintergrund läuft, nicht in KID eingebaut. So funktioniert es mit jedem Programm, auch mit LabVIEW-Anwendungen, und der Kern von KID bleibt unberührt.
- **Nur Peter** gibt Rückmeldung. Das Fenster darf also knapp und tastaturlastig sein, es braucht keine Führung für Ungeübte.
- **Ein Ordner** als Ablage reicht. Peter gibt ihn bei Bedarf im Netz frei, das Werkzeug selbst überträgt nichts.
- **Öffentliches Repo unter MIT**, nach dem Muster des Testwizards: projektunabhängiger Code, Projektwerte in einer JSON-Datei.

Arbeitsname: **Rückmeldung** (`rueckmeldung.py`, Repo `peterm2024/Rueckmeldung`). Entstanden in KID, liegt seit 15.11.2026 hier.

## Ablauf aus Peters Sicht

1. Das Werkzeug läuft seit der Anmeldung unsichtbar mit (Autostart).
2. Im getesteten Programm fällt etwas auf. Peter drückt **Strg+Alt+F**.
3. Das Werkzeug fotografiert **sofort** das aktive Fenster, noch bevor sein eigenes Fenster erscheint. Aufgeklappte Listen, Markierungen und Meldungen bleiben so im Bild.
4. Ein kleines Fenster zeigt das Bild, daneben das Notizfeld mit dem Cursor darin. Darüber steht das erkannte Projekt, etwa „KID v0.9.30“.
5. Peter tippt einen Satz und drückt **Strg+Enter**. Das Fenster schließt sich, das getestete Programm hat wieder den Fokus. **Esc** verwirft.

Zusätze, die im selben Fenster erreichbar sind, aber nie nötig:

- **Art** der Rückmeldung: Fehler, Idee oder Notiz (Alt+1/2/3, Standard Fehler).
- **Rahmen** ins Bild ziehen („hier!“) und Stellen **schwärzen** (rechte Maustaste zieht schwarz).
- **Weiteres Bild:** Ein erneutes Strg+Alt+F, während das Fenster offen ist, hängt ein zweites Bild an dieselbe Rückmeldung (vorher/nachher, Hauptfenster plus Dialog).
- **Ganzer Bildschirm** statt aktivem Fenster (Umschalter im Fenster), für Fälle, in denen die Lage zweier Fenster zueinander das Thema ist.
- **Verzögert aufnehmen** (3 Sekunden), für Zustände, die nur unter der Maus bestehen (Tooltip, Menü).
- **Ohne Bild:** Bild abwählen, dann ist es eine reine Notiz.

## Was gespeichert wird

Je Rückmeldung eine Markdown-Datei und ihre Bilder, in einem Ordner je Projekt:

```
Rueckmeldungen/
  KID/
    2026-11-15_210412_fehler.md
    2026-11-15_210412_fehler_1.png
    erledigt/
  Unbekannt/
```

Die Markdown-Datei:

```markdown
---
projekt: "KID"
art: "Fehler"
zeit: "2026-11-15 21:04:12"
status: "offen"
version: "0.9.30"
fenster: "Dokumenten-Manager v0.9.30 (Build 2026-11-15 15:10)"
programm: "DokumentenManager.exe"
rechner: "Tester-PC"
bildschirm: "1920x1080, Skalierung 125 %"
bilder: ["2026-11-15_210412_fehler_1.png"]
bild_fuer_ki: nein
---
Der Reset-Knopf fehlt, sobald ich das Fenster schmal ziehe.
```

Die Werte im Kopf stehen als JSON (Texte in Anführungszeichen), Wahrheitswerte als ja/nein. Damit ist der Kopf zugleich gültiges YAML und ohne Sonderfälle wieder einlesbar, auch wenn ein Fenstertitel Doppelpunkte oder Anführungszeichen enthält. Gibt es in derselben Sekunde schon eine Rückmeldung derselben Art, hängt das Werkzeug „_2“ an.

Was das Werkzeug von selbst dazulegt:

- **Fenstertitel und Programmname** des aktiven Fensters, daraus Projekt und Version (siehe Konfiguration).
- **Bildschirmgröße und Skalierung.** Bei KID hängen mehrere gelöste Fehler genau daran (FALLSTRICKE #77).
- **Rechner** als frei gewähltes Kürzel aus der Konfiguration, nicht der echte Rechnername.
- Auf Wunsch je Projekt die **letzten Zeilen einer Protokolldatei** (Häkchen im Fenster, Vorgabe je Projekt einstellbar).

## Datenschutz

Rückmeldungen entstehen oft an echten Daten. Darum:

- **Nichts verlässt den Rechner.** Kein Netzwerkzugriff im Code, keine Telemetrie, keine Aktualisierungsprüfung. Wer den Ordner teilt, tut das außerhalb des Werkzeugs.
- **Geschwärztes ist wirklich weg:** Das Bild wird erst beim Speichern geschrieben, mit den schwarzen Flächen eingebrannt. Die ungeschwärzte Aufnahme liegt nie auf der Platte.
- **`bild_fuer_ki`:** Je Projekt legt die Konfiguration fest, ob Bilder für die KI freigegeben sind. Bei Projekten mit echten Daten (KID an einer echten Sammlung) ist die Vorgabe **nein**: Die Sitzung liest dann nur den Text, das Bild ist für Peter. Im Fenster lässt sich das je Rückmeldung umstellen, etwa wenn das Bild nur die Test-Sammlung zeigt oder alles Heikle geschwärzt ist.
- **Protokollzeilen** können Dateinamen enthalten. Für solche Projekte ist das Anhängen in der Vorgabe aus.
- Verworfene Rückmeldungen (Esc) hinterlassen nichts.

Diese Regel muss in die Arbeitsanweisung der Projekte (CLAUDE.md): Bilder mit `bild_fuer_ki: nein` werden nicht geöffnet.

## Konfiguration

`rueckmeldung.json` neben dem Programm, nach dem Muster von `testwizard.json`:

```json
{
  "kuerzel": "ctrl+alt+f",
  "ablage": "~/Rueckmeldungen",
  "rechner": "Tester-PC",
  "projekte": [
    {
      "name": "KID",
      "programm": ["DokumentenManager.exe", "python.exe"],
      "fenstertitel": "^Dokumenten-Manager",
      "version": "v(\\d+\\.\\d+\\.\\d+)",
      "bild_fuer_ki": false,
      "protokoll": {"datei": "…/dokumenten_manager.log", "zeilen": 40, "vorgabe": false}
    }
  ]
}
```

- Ein Projekt passt, wenn Programmname und Fenstertitel-Muster stimmen (jedes für sich optional). Passt keines, landet die Rückmeldung unter `Unbekannt`, das Projekt lässt sich im Fenster von Hand wählen.
- Ohne Konfigurationsdatei läuft das Werkzeug mit Vorgaben: alles nach `Unbekannt`, Bilder nicht für die KI.

## Wie die Rückmeldungen in die Arbeit kommen

- **Zu Sitzungsbeginn** sieht die KI im Ordner des Projekts nach (ein Satz in der CLAUDE.md des Projekts, in KID neben dem Verweis auf den FAHRPLAN). `python rueckmeldung.py liste KID` gibt die offenen Einträge als Text aus: Zeit, Art, Version, Notiz, Zahl der Bilder und ob sie freigegeben sind.
- Die KI ordnet jeden Eintrag ein: sofort beheben, in den FAHRPLAN, zu „Zurückgestellt“ oder als Frage zurück an Peter. Die Spielregel des Fahrplans gilt weiter, eine Rückmeldung zieht keine Arbeit an der Reihenfolge vorbei.
- `python rueckmeldung.py erledigt <datei> "Vermerk"` setzt `status: erledigt`, schreibt den Vermerk (Fahrplan-Stelle oder Commit) darunter und schiebt Datei samt Bildern nach `erledigt/`. So bleibt nachvollziehbar, was aus einer Rückmeldung wurde.
- **Zwei Rechner:** Auf dem Tester-PC sammelt der Ordner, Peter gibt ihn frei oder nimmt ihn mit. Zu Hause genügt es, die Dateien in den eigenen Rückmeldungs-Ordner zu legen. Die Dateinamen tragen Datum und Uhrzeit, es gibt keine Datenbank und nichts abzugleichen.

## Technik

- **Python mit tkinter und Pillow**, sonst nur Standardbibliothek. Windows zuerst (dort wird getestet), die Windows-Aufrufe liegen in einem eigenen Modul.
- **Globales Kürzel** über `RegisterHotKey`. Ist die Kombination vergeben, meldet das Werkzeug das beim Start, statt still nichts zu tun.
- **Aufnahme** des aktiven Fensters über seine echten Rahmenmaße (`DwmGetWindowAttribute`), sonst schneidet Windows 11 Schatten und Ränder falsch. Das Werkzeug erklärt sich als DPI-bewusst, damit Bilder bei 125 % nicht verschoben oder unscharf sind.
- **Fokus:** Das Fenster merkt sich das zuvor aktive Fenster und gibt ihm nach dem Speichern den Fokus zurück.
- **Eine Instanz:** Ein zweiter Start zeigt ein kleines Fenster „läuft, Kürzel Strg+Alt+F“ mit „Ordner öffnen“ und „Beenden“. Das ersetzt fürs Erste ein Symbol im Infobereich.
- **EXE** für Rechner ohne Python (PyInstaller, wie bei KID), Konfiguration daneben, Autostart als Verknüpfung, die das Werkzeug auf Wunsch selbst anlegt.
- **Aufteilung wie beim Testwizard:** Die Logik ohne Fenster (Projekt zuordnen, Dateinamen, Markdown schreiben und lesen, Schwärzen, `liste`, `erledigt`) ist ein eigenes Modul mit schnellen Unit-Tests. Kürzel, Aufnahme und Fenster prüft Peter.

## Bauschritte

1. **Kern:** Kürzel, Aufnahme des aktiven Fensters, Fenster mit Bild und Notiz, Speichern als Markdown und PNG, Fokus zurück. Läuft aus dem Quelltext auf Peters Rechner. Abnahme: eine Rückmeldung zu KID an der Test-Sammlung.
2. **Projekt und Kontext:** `rueckmeldung.json`, Zuordnung, Version, Bildschirmgröße und Skalierung, `bild_fuer_ki`, Protokollzeilen.
3. **Bild bearbeiten:** Rahmen, Schwärzen, weiteres Bild, ganzer Bildschirm, verzögert.
4. **Einordnen:** `liste` und `erledigt`, Satz in der CLAUDE.md von KID, Abschnitt im Projekte-Wiki (Arbeitsweise, Projekt-Übersicht, Projekt-Vorlage).
5. **Weitergabe:** Eine Instanz, EXE, Autostart, README, erster Release im öffentlichen Repo. Abnahme auf dem Tester-PC.

Nach Schritt 1 ist das Werkzeug schon benutzbar, jeder weitere Schritt ist für sich abnehmbar.

## Weitere Einfälle, bewusst nicht im ersten Wurf

- **Testwizard anbinden:** Im Wizard ein Knopf „Rückmeldung“, der die ID des gerade offenen Prüfpunkts vorbelegt. Umgekehrt erkennt `liste` eine ID wie `T10g.64` in der Notiz und nennt den Prüfpunkt.
- **Zustand vom Programm:** Ein Projekt kann in der Konfiguration eine Zustandsdatei nennen, die sein Programm ohnehin schreibt. Das Werkzeug legt sie bei. Für KID vorerst unnötig, Fenstertitel und Protokoll reichen.
- **Kurze Aufzeichnung** (einige Sekunden als Bildfolge) für Ruckeln und Flackern. Lohnt erst, wenn solche Rückmeldungen wirklich vorkommen.
- **Symbol im Infobereich** mit Zähler der offenen Rückmeldungen.
- **Sammelblick für Peter:** `liste` über alle Projekte, als Erinnerung, was noch nirgends eingeordnet ist.

## Offen (Peter entscheidet)

- **F1 Name:** „Rückmeldung“ ist ein Arbeitsname. Kürzer und als Programmname griffiger wäre etwa „Merker“.
- **F2 Kürzel:** Strg+Alt+F als Vorgabe. Zu prüfen, ob es mit einem der getesteten Programme kollidiert (LabVIEW, Spiele).
- **F3 Ablageort zu Hause:** `~/Rueckmeldungen` als gemeinsamer Ordner für alle Projekte (Vorschlag), oder je Projekt ein Ordner neben dem Repo.
- **F4 Bilder und KI:** Vorschlag wie oben: je Projekt eine Vorgabe, bei KID „nein“, im Fenster je Rückmeldung umstellbar.
