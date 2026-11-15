"""Rückmeldung - Markierungen ins Bild einbrennen (Pillow, ohne Fenster).

Eine Markierung ist (art, x0, y0, x1, y1) in Bildpixeln, art aus rueckmeldung_kern.MARKIERUNGEN. Eingebrannt wird
in eine Kopie in voller Auflösung; Schwärzen deckt die Fläche vollständig ab, das Original darunter wird nirgends
gespeichert. „Zuschneiden“ wird zuletzt angewandt (der zuletzt gezogene Ausschnitt), damit Rahmen und Pfeile, die
über den Rand des Ausschnitts reichen, sauber abgeschnitten werden.
"""
from PIL import ImageDraw

import rueckmeldung_kern as kern

FARBE = (230, 30, 30)


def einbrennen(bild, markierungen):
    """Kopie des Bildes mit allen Markierungen in Reihenfolge (spätere liegen oben)."""
    ergebnis = bild.convert("RGB")                        # convert liefert immer eine Kopie
    zeichne = ImageDraw.Draw(ergebnis)
    breite = kern.linienbreite(*ergebnis.size)
    for art, x0, y0, x1, y1 in markierungen:
        if art == "Zuschneiden":
            continue
        if art == "Schwärzen":
            l, o, r, u = kern.normiere_rechteck(x0, y0, x1, y1)
            zeichne.rectangle((l, o, r, u), fill=(0, 0, 0))
        elif art == "Rahmen":
            l, o, r, u = kern.normiere_rechteck(x0, y0, x1, y1)
            zeichne.rectangle((l, o, r, u), outline=FARBE, width=breite)
        elif art == "Pfeil":
            spitze = kern.pfeilspitze(x0, y0, x1, y1, breite * 5)
            grund = ((spitze[1][0] + spitze[2][0]) / 2, (spitze[1][1] + spitze[2][1]) / 2)
            zeichne.line((x0, y0, grund[0], grund[1]), fill=FARBE, width=breite)
            zeichne.polygon(spitze, fill=FARBE)
        else:
            raise ValueError(f"Unbekannte Markierung: {art}")
    ausschnitt = kern.zuschnitt(markierungen, *ergebnis.size)
    return ergebnis.crop(ausschnitt) if ausschnitt else ergebnis
