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
    Geprüft wird gegen die Markdown-Datei und ihr erstes Bild, damit auch eine halb geschriebene Rückmeldung
    nicht überschrieben wird."""
    basis = f"{jetzt:%Y-%m-%d_%H%M%S}_{(art or ARTEN[0]).lower()}"
    stamm, n = basis, 1
    while os.path.exists(os.path.join(ordner, stamm + ".md")) or os.path.exists(os.path.join(ordner, stamm + "_1.png")):
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


def speichere(ablage, projekt, jetzt, art, notiz, bilder=(), felder=None):
    """Rückmeldung schreiben. bilder = PNG-Bytes, felder = weitere Kopfangaben (Fenster, Programm ...).

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
    kopf.setdefault("bild_fuer_ki", False)
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
