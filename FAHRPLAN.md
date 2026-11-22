# Fahrplan: Rückmeldung

**Ziel:** Beim Testen eines eigenen Programms hält ein Tastenkürzel den Moment fest (Bild, Notiz, Fenster, Version), und die nächste Arbeitssitzung findet alles geordnet je Projekt vor. Einzelheiten und Begründungen: [KONZEPT.md](KONZEPT.md).

## Schritt 1 – Kern (2026-11-15)

- [x] Globales Kürzel (Strg+Alt+F) in eigenem Thread, ein zweiter Start erkennt das belegte Kürzel
- [x] Aufnahme des aktiven Fensters vor dem eigenen Fenster (DWM-Rahmen, DPI-bewusst)
- [x] Erfassungsfenster: Bild, Art (Alt+1/2/3), Notiz; Strg+Enter speichert, Esc verwirft (fragt bei Text nach), Fokus zurück
- [x] Speichern als Markdown + PNG unter `~/Rueckmeldungen/Unbekannt/`, 12 Unit-Tests, Rauchtest ohne echte Eingaben
- [x] Abnahme durch Peter (2026-11-15, echtes Kürzel über VS Code): „Funktioniert gut :-) Noch Pfeil und Rechteck zum hervorheben ... und Mausrad-Zoom“
- **Meilenstein: Eine echte Rückmeldung liegt im Ordner, das getestete Programm hat danach wieder den Fokus.**

## Schritt 2 – Projekt und Kontext (2026-11-15)

- [x] `rueckmeldung.json`: Kürzel, Ablage, Rechner-Kürzel, Projekte mit Regeln (Programm und/oder Fenstertitel-Muster, auch über ein anderes Fenster desselben Programms - so landen Dialoge beim Projekt ihres Hauptfensters), Version, `bild_fuer_ki`, Protokoll; Unbekanntes wird als Tippfehler gemeldet; Vorlage `rueckmeldung.beispiel.json`
- [x] Bildschirmgröße und Skalierung in den Kopf
- [x] Projekt im Fenster von Hand wählbar, Schalter „Bild für KI freigeben“ und „Protokoll anhängen“ mit den Vorgaben des Projekts
- [x] 41 Unit-Tests, Rauchtest mit Dialog eines fremden Prozesses
- [x] Abnahme durch Peter (2026-11-15): „Passt soweit“, dazu Wunsch: Bild auf einen Ausschnitt beschneiden
- **Meilenstein: Eine Rückmeldung zu KID landet ohne Zutun unter `KID/` mit Version.**

## Schritt 3 – Bild bearbeiten

- [x] Rahmen, Pfeil (Peters Wunsch bei der Abnahme von Schritt 1), Schwärzen - erst beim Speichern in voller Auflösung eingebrannt; Rückgängig (Strg+Z) (2026-11-15)
- [x] Mausrad-Zoom um die Maus, Verschieben mit rechter oder mittlerer Taste, Einpassen; Notizfeld in normaler Schrift statt Schreibmaschinenschrift (2026-11-15)
- [x] Abnahme durch Peter (2026-11-15): „Passt“
- [x] Zuschneiden (Peters Wunsch bei der Abnahme von Schritt 2): letzter gezogener Ausschnitt gilt, außerhalb abgedunkelt, beim Speichern nach dem Einbrennen angewandt; Rückgängig holt den vorigen Ausschnitt (2026-11-15)
- [x] Abnahme Zuschneiden durch Peter (2026-11-15): „passt“
- [ ] Weiteres Bild per erneutem Kürzel, ganzer Bildschirm, verzögert aufnehmen

## Schritt 4 – Einordnen

- [ ] `rueckmeldung.py liste <Projekt>` und `erledigt <datei> "Vermerk"`
- [ ] Satz in der CLAUDE.md von KID, Abschnitt im Projekte-Wiki (Arbeitsweise, Projekt-Vorlage)

## Schritt 5 – Weitergabe

- [x] EXE mit PyInstaller (`build_exe.py` baut und prüft den Inhalt), vorerst mit Konsolenfenster zum Beenden; Version im Kern, CHANGELOG (2026-11-16)
- [x] Erster Release v0.1.0 auf GitHub, auf Peters Wunsch vorgezogen (2026-11-16)
- [ ] Fenster „läuft“ beim zweiten Start (Ordner öffnen, Beenden), danach EXE ohne Konsole
- [ ] Autostart
- **Meilenstein: Läuft auf dem Tester-PC ohne Python.**

## Funde aus der Nutzung (Peter 22.11.2026, sechs Rückmeldungen zu KID)

- [x] **Alles landete in „Unbekannt“:** Peter startete `Downloads\Rueckmeldung.exe`, die `rueckmeldung.json` lag aber nur im Projektordner - die EXE suchte sie nur neben sich und fiel still auf die Vorgaben zurück. Jetzt: erst neben dem Programm, dann in `~/Rueckmeldungen/rueckmeldung.json`; die Startzeile nennt die gefundene Datei bzw. die durchsuchten Orte, das Erfassungsfenster zeigt „ohne rueckmeldung.json“; ein fehlendes `--konfig` ist ein Fehler. Peters Konfiguration liegt seither in der Ablage (2026-11-22)
- [x] **„Bild für die KI“ standardmäßig angehakt** (Peter: „die habe ich nur übersehen anzuhaken. Wir sollten den Haken defaultmäßig angehakt machen“): gesetzt, solange ein Projekt nicht `"bild_fuer_ki": false` sagt, auch bei Unbekannt; in Peters Konfiguration für KID auf `true`; F4 damit entschieden (2026-11-22)
- [x] **„Wie kann ich bestehende Rückmeldungen bearbeiten? Wo finde ich die Rückmeldungen?“** Knopf „Ablage öffnen“ im Erfassungsfenster (Explorer im Ordner des gewählten Projekts, die .md lassen sich mit jedem Editor bearbeiten) (2026-11-22). Nachbearbeiten im Werkzeug selbst kommt mit Schritt 4.
- [x] Abnahme durch Peter (2026-11-23): „passt“, veröffentlicht als v0.2.0
- Die KID-Sitzung hat die sechs KID-Funde bereits von Hand nach `KID/erledigt/` gelegt, mit `status: "erledigt"` und `vermerk` (Commit, Testpunkt) - Vorbild für `erledigt` in Schritt 4.

## Offen (Peter entscheidet)

- F1 Name („Rückmeldung“ ist Arbeitsname), F2 Kürzel (Strg+Alt+F, Kollision mit LabVIEW/Spielen?), F3 Ablageort zu Hause (Vorschlag `~/Rueckmeldungen`), F4 Bilder und KI: entschieden 2026-11-22, Haken standardmäßig gesetzt, ein Projekt kann ihn abschalten. Bis zur Antwort gelten die Vorschläge.

## Ideen (noch nicht entschieden)

- Testwizard anbinden (Prüfpunkt-ID vorbelegen bzw. in der Notiz erkennen), Zustandsdatei des Programms beilegen, kurze Bildfolge für Ruckeln, Symbol im Infobereich, Sammelblick über alle Projekte.
