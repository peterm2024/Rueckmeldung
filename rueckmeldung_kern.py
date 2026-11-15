"""Rückmeldung - Logik ohne Fenster: Kürzel lesen, Dateinamen bilden, Rückmeldungen als Markdown schreiben und lesen.

Nur Standardbibliothek, kein tkinter, kein Pillow (Bilder kommen als fertige PNG-Bytes an). Damit lässt sich alles
hier mit schnellen Unit-Tests prüfen; Kürzel, Bildschirmaufnahme und Fenster liegen in rueckmeldung_windows.py
und rueckmeldung.py.

Eine Rückmeldung ist eine Markdown-Datei mit Kopfteil (zwischen zwei Zeilen „---“, je Zeile „schluessel: wert“,
Werte als JSON - damit ist der Kopf zugleich gültiges YAML) und der Notiz darunter. Ihre Bilder liegen daneben
und heißen wie die Datei plus „_1.png“, „_2.png“ ...
"""
import json
import math
import os
import re

ARTEN = ("Fehler", "Idee", "Notiz")
PROJEKT_UNBEKANNT = "Unbekannt"

# Windows-Werte für RegisterHotKey
_MODIFIKATOREN = {"alt": 0x0001, "ctrl": 0x0002, "strg": 0x0002, "shift": 0x0004, "umschalt": 0x0004, "win": 0x0008}
MOD_NOREPEAT = 0x4000


class Kuerzelfehler(ValueError):
    """Die Tastenkombination in der Konfiguration ist nicht lesbar."""


def lies_kuerzel(text):
    """„ctrl+alt+f“ -> (Modifikatoren, virtueller Tastencode) für RegisterHotKey.

    Erlaubt sind Buchstaben, Ziffern und F1-F24, mit mindestens einem Modifikator (ein globales Kürzel ohne
    Strg/Alt/Win würde die Taste in allen Programmen wegnehmen)."""
    teile = [t.strip().lower() for t in (text or "").split("+") if t.strip()]
    if not teile:
        raise Kuerzelfehler("Kein Kürzel angegeben")
    *mods, taste = teile
    wert = 0
    for m in mods:
        if m not in _MODIFIKATOREN:
            raise Kuerzelfehler(f"Unbekannte Taste „{m}“ (erlaubt: ctrl, alt, shift, win)")
        wert |= _MODIFIKATOREN[m]
    if not wert & (0x0001 | 0x0002 | 0x0008):                    # Umschalt allein nähme Großbuchstaben weg
        raise Kuerzelfehler("Das Kürzel braucht mindestens ctrl, alt oder win")
    if re.fullmatch(r"[a-z0-9]", taste):
        vk = ord(taste.upper())
    elif re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", taste):
        vk = 0x70 + int(taste[1:]) - 1
    else:
        raise Kuerzelfehler(f"Unbekannte Taste „{taste}“ (erlaubt: a-z, 0-9, f1-f24)")
    return wert | MOD_NOREPEAT, vk


def zeige_kuerzel(text):
    """„ctrl+alt+f“ -> „Strg+Alt+F“ für Texte im Fenster."""
    namen = {"ctrl": "Strg", "strg": "Strg", "alt": "Alt", "shift": "Umschalt", "umschalt": "Umschalt", "win": "Win"}
    return "+".join(namen.get(t.strip().lower(), t.strip().upper()) for t in text.split("+"))


def ordnername(projekt):
    """Projektname als Ordnername: ohne Zeichen, die Windows in Pfaden verbietet; leer -> „Unbekannt“."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", (projekt or "").strip()).strip(" .")
    return name or PROJEKT_UNBEKANNT


def dateistamm(ordner, jetzt, art):
    """Freier Dateiname ohne Endung, etwa „2026-11-15_210412_fehler“; gibt es ihn schon, „…_fehler_2“ usw.
    Geprüft wird gegen die Markdown-Datei, ihr erstes Bild und ihr Protokoll, damit auch eine halb geschriebene Rückmeldung
    nicht überschrieben wird."""
    basis = f"{jetzt:%Y-%m-%d_%H%M%S}_{(art or ARTEN[0]).lower()}"
    stamm, n = basis, 1
    while any(os.path.exists(os.path.join(ordner, stamm + endung)) for endung in (".md", "_1.png", "_protokoll.txt")):
        n += 1
        stamm = f"{basis}_{n}"
    return stamm


def kopf_text(felder):
    """Kopfteil der Markdown-Datei: jede Zeile „schluessel: <JSON-Wert>“, Wahrheitswerte als ja/nein."""
    zeilen = ["---"]
    for k, v in felder.items():
        if isinstance(v, bool):
            wert = "ja" if v else "nein"
        else:
            wert = json.dumps(v, ensure_ascii=False)
        zeilen.append(f"{k}: {wert}")
    zeilen.append("---")
    return "\n".join(zeilen) + "\n"


def speichere(ablage, projekt, jetzt, art, notiz, bilder=(), felder=None, protokoll=None):
    """Rückmeldung schreiben. bilder = PNG-Bytes, felder = weitere Kopfangaben (Fenster, Programm ...),
    protokoll = Text, der als „…_protokoll.txt“ daneben gelegt wird.

    Erst die Bilder, zuletzt die Markdown-Datei (über eine Temp-Datei), damit ein Absturz mittendrin nie eine
    Markdown-Datei ohne ihre Bilder hinterlässt. Gibt den Pfad der Markdown-Datei zurück."""
    if art not in ARTEN:
        raise ValueError(f"Unbekannte Art: {art}")
    ordner = os.path.join(os.path.expanduser(ablage), ordnername(projekt))
    os.makedirs(ordner, exist_ok=True)
    stamm = dateistamm(ordner, jetzt, art)
    namen = []
    for i, png in enumerate(bilder, start=1):
        name = f"{stamm}_{i}.png"
        with open(os.path.join(ordner, name), "wb") as f:
            f.write(png)
        namen.append(name)
    kopf = {"projekt": ordnername(projekt), "art": art, "zeit": f"{jetzt:%Y-%m-%d %H:%M:%S}", "status": "offen"}
    kopf.update(felder or {})
    kopf["bilder"] = namen
    if protokoll:
        name = f"{stamm}_protokoll.txt"
        with open(os.path.join(ordner, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(protokoll.rstrip("\n") + "\n")
        kopf["protokoll"] = name
    kopf["bild_fuer_ki"] = bool(kopf.pop("bild_fuer_ki", False))     # immer zuletzt, gut sichtbar
    text = kopf_text(kopf) + (notiz or "").strip() + "\n"
    ziel = os.path.join(ordner, stamm + ".md")
    temp = ziel + ".tmp"
    with open(temp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(temp, ziel)
    return ziel


def lies(pfad):
    """Markdown-Datei einer Rückmeldung -> (Kopf als dict, Notiz). Unlesbare Kopfzeilen bleiben als Text stehen."""
    with open(pfad, encoding="utf-8") as f:
        text = f.read()
    kopf, notiz = {}, text
    if text.startswith("---\n"):
        ende = text.find("\n---\n", 4)
        if ende >= 0:
            notiz = text[ende + 5:]
            for zeile in text[4:ende].splitlines():
                k, sep, v = zeile.partition(":")
                if not sep:
                    continue
                v = v.strip()
                if v in ("ja", "nein"):
                    kopf[k.strip()] = v == "ja"
                    continue
                try:
                    kopf[k.strip()] = json.loads(v)
                except ValueError:
                    kopf[k.strip()] = v
    return kopf, notiz.strip()


# --- Bildansicht und Markierungen (Geometrie ohne Pillow und ohne Fenster) ---

MARKIERUNGEN = ("Rahmen", "Pfeil", "Schwärzen")


class Ansicht:
    """Ausschnitt eines Bildes auf einer Zeichenfläche: Maßstab plus die Bildkoordinate der linken oberen Ecke.
    Zoomen hält den Bildpunkt unter der Maus fest; einpassen zeigt das ganze Bild, höchstens 1:1."""

    MAX_ZOOM = 8.0

    def __init__(self, bild_b, bild_h):
        self.bild_b, self.bild_h = bild_b, bild_h
        self.massstab, self.x0, self.y0 = 1.0, 0.0, 0.0
        self.flaeche = (1, 1)

    def passend(self):
        b, h = self.flaeche
        return min(b / self.bild_b, h / self.bild_h, 1.0)

    def einpassen(self, flaeche_b, flaeche_h):
        self.flaeche = (max(1, flaeche_b), max(1, flaeche_h))
        self.massstab = self.passend()
        self._begrenze()

    def neue_flaeche(self, flaeche_b, flaeche_h):
        """Fenstergröße geändert: war das Bild eingepasst, bleibt es eingepasst, sonst bleibt der Maßstab."""
        eingepasst = abs(self.massstab - self.passend()) < 1e-9
        self.flaeche = (max(1, flaeche_b), max(1, flaeche_h))
        if eingepasst:
            self.massstab = self.passend()
        self._begrenze()

    def zoome(self, faktor, cx, cy):
        """Um faktor zoomen, der Bildpunkt unter (cx, cy) auf der Fläche bleibt stehen."""
        bx, by = self.zu_bild(cx, cy)
        self.massstab = min(self.MAX_ZOOM, max(self.passend(), self.massstab * faktor))
        self.x0, self.y0 = bx - cx / self.massstab, by - cy / self.massstab
        self._begrenze()

    def verschiebe(self, dx, dy):
        """Um (dx, dy) Flächen-Pixel verschieben (Ziehen mit der Maus)."""
        self.x0 -= dx / self.massstab
        self.y0 -= dy / self.massstab
        self._begrenze()

    def _begrenze(self):
        """Ist das Bild kleiner als die Fläche, steht es mittig; sonst kein leerer Rand neben dem Bild."""
        for achse, bild, flaeche in (("x0", self.bild_b, self.flaeche[0]), ("y0", self.bild_h, self.flaeche[1])):
            sichtbar = flaeche / self.massstab
            if sichtbar >= bild:
                setattr(self, achse, -(sichtbar - bild) / 2)
            else:
                setattr(self, achse, min(max(getattr(self, achse), 0.0), bild - sichtbar))

    def zu_bild(self, cx, cy):
        return self.x0 + cx / self.massstab, self.y0 + cy / self.massstab

    def zu_flaeche(self, bx, by):
        return (bx - self.x0) * self.massstab, (by - self.y0) * self.massstab

    def ausschnitt(self):
        """Sichtbarer Bildausschnitt (links, oben, rechts, unten) in ganzen Bildpixeln, auf das Bild begrenzt,
        und wohin seine linke obere Ecke auf der Fläche fällt."""
        b, h = self.flaeche
        l, o = max(0, int(self.x0)), max(0, int(self.y0))
        r = min(self.bild_b, int(self.x0 + b / self.massstab) + 1)
        u = min(self.bild_h, int(self.y0 + h / self.massstab) + 1)
        return (l, o, r, u), self.zu_flaeche(l, o)


def linienbreite(bild_b, bild_h):
    """Strichstärke für Rahmen und Pfeil im gespeicherten Bild: gut sichtbar, auch in großen Aufnahmen."""
    return max(3, round(max(bild_b, bild_h) / 450))


def pfeilspitze(x0, y0, x1, y1, laenge):
    """Drei Punkte der Pfeilspitze an (x1, y1), Länge laenge, Öffnung etwa 50°. Bei einem Pfeil, der kürzer ist als
    die Spitze, wird die Spitze auf die halbe Pfeillänge gekürzt."""
    dx, dy = x1 - x0, y1 - y0
    lang = math.hypot(dx, dy)
    if lang < 1e-9:
        return [(x1, y1)] * 3
    laenge = min(laenge, lang / 2) if lang < 2 * laenge else laenge
    ux, uy = dx / lang, dy / lang
    bx, by = x1 - ux * laenge, y1 - uy * laenge                  # Mitte der Grundlinie
    halb = laenge * 0.47
    return [(x1, y1), (bx - uy * halb, by + ux * halb), (bx + uy * halb, by - ux * halb)]


def normiere_rechteck(x0, y0, x1, y1):
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


# --- Konfiguration und Projekt-Zuordnung ---

KONFIG_DATEI = "rueckmeldung.json"
STANDARD_KUERZEL = "ctrl+alt+f"
STANDARD_ABLAGE = "~/Rueckmeldungen"


class Konfigfehler(ValueError):
    """rueckmeldung.json ist nicht lesbar oder enthält Unbekanntes (meist ein Tippfehler)."""


def _pruefe_schluessel(wo, d, erlaubt):
    if not isinstance(d, dict):
        raise Konfigfehler(f"{wo}: erwartet ein Objekt {{…}}")
    falsch = sorted(k for k in d if k not in erlaubt and not k.startswith("_"))
    if falsch:
        raise Konfigfehler(f"{wo}: unbekannt {', '.join(falsch)} (erlaubt: {', '.join(sorted(erlaubt))})")


def _pruefe_muster(wo, muster, gruppe=False):
    if not isinstance(muster, str):
        raise Konfigfehler(f"{wo}: erwartet einen Text")
    try:
        r = re.compile(muster)
    except re.error as e:
        raise Konfigfehler(f"{wo}: kein gültiger regulärer Ausdruck ({e})") from None
    if gruppe and r.groups < 1:
        raise Konfigfehler(f"{wo}: braucht eine Gruppe in Klammern, etwa v(\d+\.\d+\.\d+)")


def pruefe_konfig(daten):
    """Konfiguration prüfen und mit Vorgaben auffüllen. Schlüssel mit „_“ am Anfang sind Kommentare."""
    _pruefe_schluessel("rueckmeldung.json", daten, {"kuerzel", "ablage", "rechner", "projekte"})
    k = {"kuerzel": STANDARD_KUERZEL, "ablage": STANDARD_ABLAGE, "rechner": "", "projekte": []}
    for schluessel in ("kuerzel", "ablage", "rechner"):
        if schluessel in daten:
            if not isinstance(daten[schluessel], str):
                raise Konfigfehler(f"{schluessel}: erwartet einen Text")
            k[schluessel] = daten[schluessel]
    try:
        lies_kuerzel(k["kuerzel"])
    except Kuerzelfehler as e:
        raise Konfigfehler(f"kuerzel: {e}") from None
    projekte = daten.get("projekte", [])
    if not isinstance(projekte, list):
        raise Konfigfehler("projekte: erwartet eine Liste […]")
    for i, p in enumerate(projekte, start=1):
        wo = f"projekte[{i}]"
        _pruefe_schluessel(wo, p, {"name", "regeln", "version", "bild_fuer_ki", "protokoll"})
        if not isinstance(p.get("name"), str) or not p["name"].strip():
            raise Konfigfehler(f"{wo}: name fehlt")
        wo = f"projekte[{i}] ({p['name']})"
        regeln = p.get("regeln")
        if not isinstance(regeln, list) or not regeln:
            raise Konfigfehler(f"{wo}: regeln fehlt (Liste mit programm und/oder fenstertitel)")
        for j, r in enumerate(regeln, start=1):
            _pruefe_schluessel(f"{wo}, regeln[{j}]", r, {"programm", "fenstertitel"})
            if not r.get("programm") and not r.get("fenstertitel"):
                raise Konfigfehler(f"{wo}, regeln[{j}]: braucht programm oder fenstertitel")
            if "fenstertitel" in r:
                _pruefe_muster(f"{wo}, regeln[{j}].fenstertitel", r["fenstertitel"])
        if "version" in p:
            _pruefe_muster(f"{wo}.version", p["version"], gruppe=True)
        if not isinstance(p.get("bild_fuer_ki", False), bool):
            raise Konfigfehler(f"{wo}.bild_fuer_ki: erwartet true oder false")
        if "protokoll" in p:
            pr = p["protokoll"]
            _pruefe_schluessel(f"{wo}.protokoll", pr, {"datei", "zeilen", "vorgabe"})
            if not isinstance(pr.get("datei"), str):
                raise Konfigfehler(f"{wo}.protokoll.datei fehlt")
            if not isinstance(pr.get("zeilen", 40), int) or pr.get("zeilen", 40) < 1:
                raise Konfigfehler(f"{wo}.protokoll.zeilen: erwartet eine Zahl ab 1")
            if not isinstance(pr.get("vorgabe", False), bool):
                raise Konfigfehler(f"{wo}.protokoll.vorgabe: erwartet true oder false")
    k["projekte"] = projekte
    return k


def lade_konfig(pfad):
    """rueckmeldung.json lesen; fehlt die Datei, gelten die Vorgaben (alles nach „Unbekannt“)."""
    if not os.path.exists(pfad):
        return pruefe_konfig({})
    try:
        with open(pfad, encoding="utf-8-sig") as f:
            daten = json.load(f)
    except ValueError as e:
        raise Konfigfehler(f"{os.path.basename(pfad)} ist kein gültiges JSON: {e}") from None
    return pruefe_konfig(daten)


def ordne_zu(konfig, programm, titel):
    """Erstes Projekt, dessen Regel passt, sonst None. titel = Fenstertitel des Prozesses (das aufgenommene
    Fenster zuerst) - so erkennt eine Regel auf den Hauptfenstertitel auch einen Dialog desselben Programms.
    Eine Regel passt, wenn alle ihre Angaben passen: programm (Dateiname, ohne Groß/klein) und fenstertitel
    (regulärer Ausdruck, irgendwo in einem der Titel)."""
    for p in konfig["projekte"]:
        for r in p["regeln"]:
            if r.get("programm") and r["programm"].lower() != (programm or "").lower():
                continue
            if r.get("fenstertitel") and not any(re.search(r["fenstertitel"], t) for t in titel):
                continue
            return p
    return None


def finde_version(projekt, titel):
    """Version aus dem ersten Titel, in dem das Muster des Projekts passt, sonst ""."""
    if not projekt or not projekt.get("version"):
        return ""
    for t in titel:
        m = re.search(projekt["version"], t)
        if m:
            return m.group(1)
    return ""


def protokoll_ende(muster, zeilen):
    """Letzte Zeilen der neuesten Datei, die auf muster passt (~ und * erlaubt). -> (Pfad, Text) oder (None, "")."""
    import glob
    treffer = [p for p in glob.glob(os.path.expanduser(muster)) if os.path.isfile(p)]
    if not treffer:
        return None, ""
    pfad = max(treffer, key=os.path.getmtime)
    groesse = os.path.getsize(pfad)
    lesen = min(groesse, max(65536, zeilen * 400))
    with open(pfad, "rb") as f:
        f.seek(groesse - lesen)
        text = f.read().decode("utf-8", errors="replace")
    teile = text.splitlines()
    if lesen < groesse and teile:
        teile = teile[1:]                                        # erste Zeile ist vermutlich angeschnitten
    return pfad, "\n".join(teile[-zeilen:])
