"""Rückmeldung - Logik ohne Fenster: Kürzel lesen, Dateinamen bilden, Rückmeldungen als Markdown schreiben und lesen.

Nur Standardbibliothek, kein tkinter, kein Pillow (Bilder kommen als fertige PNG-Bytes an). Damit lässt sich alles
hier mit schnellen Unit-Tests prüfen; Kürzel, Bildschirmaufnahme und Fenster liegen in rueckmeldung_windows.py
und rueckmeldung.py.

Eine Rückmeldung ist eine Markdown-Datei mit Kopfteil (zwischen zwei Zeilen „---“, je Zeile „schluessel: wert“,
Werte als JSON - damit ist der Kopf zugleich gültiges YAML) und der Notiz darunter. Ihre Bilder liegen daneben
und heißen wie die Datei plus „_1.png“, „_2.png“ ...
"""
import json
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
