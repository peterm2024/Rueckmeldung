"""Rückmeldung - hält beim Testen einen Moment fest: Tastenkürzel drücken, das aktive Fenster wird fotografiert,
einen Satz dazu tippen, Strg+Enter. Gespeichert wird eine Markdown-Datei samt Bild im Ablage-Ordner, die nächste
Arbeitssitzung liest sie von dort.

    python rueckmeldung.py                       läuft im Hintergrund (Einstellungen aus rueckmeldung.json)
    python rueckmeldung.py --konfig andere.json  andere Konfiguration
    python rueckmeldung.py --ablage D:/Rueck     andere Ablage
    python rueckmeldung.py --kuerzel ctrl+alt+r  anderes Kürzel

Ohne rueckmeldung.json: Kürzel Strg+Alt+F, Ablage ~/Rueckmeldungen, alles nach „Unbekannt“. Vorlage:
rueckmeldung.beispiel.json.

Beenden (bis es ein eigenes Fenster dafür gibt): Strg+C in der Konsole bzw. die Konsole schließen.
Nichts verlässt den Rechner - kein Netzwerkzugriff.
"""
import argparse
import datetime
import io
import os
import queue
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import rueckmeldung_kern as kern
import rueckmeldung_windows as win

class App:
    """Unsichtbares Hauptfenster: hält das Kürzel und öffnet bei jedem Druck ein Erfassungsfenster."""

    def __init__(self, root, konfig=None):
        self.root = root
        self.konfig = konfig or kern.pruefe_konfig({})
        self.ereignisse = queue.Queue()
        self.fenster = None
        self.kuerzel = None
        self.gespeichert = []                    # Pfade dieser Sitzung (für Tests und die Konsolenmeldung)

    @property
    def projektnamen(self):
        return [p["name"] for p in self.konfig["projekte"]] + [kern.PROJEKT_UNBEKANNT]

    def projekt(self, name):
        return next((p for p in self.konfig["projekte"] if p["name"] == name), None)

    def starte(self):
        """Kürzel anmelden. False (mit Meldung), wenn es nicht geht."""
        text = self.konfig["kuerzel"]
        self.kuerzel = win.Kuerzel(*kern.lies_kuerzel(text), lambda: self.ereignisse.put("kuerzel"))
        if not self.kuerzel.starte():
            messagebox.showerror(
                "Rückmeldung",
                f"Das Kürzel {kern.zeige_kuerzel(text)} ist schon belegt ({self.kuerzel.fehler}).\n\n"
                "Läuft die Rückmeldung bereits? Sonst ein anderes Kürzel in rueckmeldung.json oder mit --kuerzel.")
            return False
        self.root.after(100, self._abholen)
        return True

    def stoppe(self):
        if self.kuerzel:
            self.kuerzel.stoppe()

    def _abholen(self):
        """Kürzel-Ereignisse aus dem Thread abholen - Tkinter nur hier im Haupt-Thread anfassen."""
        try:
            while True:
                self.ereignisse.get_nowait()
                self.ausgeloest()
        except queue.Empty:
            pass
        self.root.after(100, self._abholen)

    def ausgeloest(self, hwnd=None):
        """Kürzel gedrückt: aktives Fenster sofort aufnehmen, dann erst das eigene Fenster zeigen."""
        if self.fenster is not None:
            self.fenster.nach_vorn()             # später: hier ein weiteres Bild anhängen
            return
        hwnd = hwnd or win.vordergrund()
        if hwnd and win.gehoert_zu_mir(hwnd):
            return
        self.fenster = Erfassung(self, self.erfasse(hwnd))

    def erfasse(self, hwnd):
        """Alles über den Moment, was ohne den Nutzer feststeht: Bild, Fenster, Programm, Projekt, Version."""
        m = {"hwnd": hwnd, "bild": None, "titel": "", "programm": "", "rahmen": None, "bildschirm": "",
             "titel_liste": [], "projekt": None, "version": ""}
        if hwnd:
            m["rahmen"] = win.fensterrahmen(hwnd)
            try:
                m["bild"] = win.aufnahme(hwnd)
            except OSError:
                pass
            m["titel"], m["programm"] = win.fenster_titel(hwnd), win.fenster_programm(hwnd)
            m["titel_liste"] = win.prozess_titel(hwnd) or [m["titel"]]
            m["bildschirm"] = win.bildschirm(hwnd)
            m["projekt"] = kern.ordne_zu(self.konfig, m["programm"], m["titel_liste"])
            m["version"] = kern.finde_version(m["projekt"], m["titel_liste"])
        return m

    def speichere(self, art, notiz, bild, moment, projektname, bild_fuer_ki, mit_protokoll):
        pngs = []
        if bild is not None:
            puffer = io.BytesIO()
            bild.save(puffer, "PNG", optimize=True)
            pngs.append(puffer.getvalue())
        projekt = self.projekt(projektname)
        felder = {}
        version = kern.finde_version(projekt, moment["titel_liste"])
        if version:
            felder["version"] = version
        felder["fenster"] = moment["titel"]
        felder["programm"] = moment["programm"]
        if self.konfig["rechner"]:
            felder["rechner"] = self.konfig["rechner"]
        if moment["bildschirm"]:
            felder["bildschirm"] = moment["bildschirm"]
        felder["bild_fuer_ki"] = bool(bild_fuer_ki) and bild is not None
        protokoll = None
        if mit_protokoll and projekt and projekt.get("protokoll"):
            pr = projekt["protokoll"]
            _, protokoll = kern.protokoll_ende(pr["datei"], pr.get("zeilen", 40))
        pfad = kern.speichere(self.konfig["ablage"], projektname, datetime.datetime.now(), art, notiz, pngs, felder,
                              protokoll)
        self.gespeichert.append(pfad)
        return pfad


class Erfassung(tk.Toplevel):
    """Das Fenster nach dem Kürzel: Projekt, Bild, Art, Notiz; Strg+Enter speichert, Esc verwirft."""

    def __init__(self, app, moment):
        super().__init__(app.root)
        self.withdraw()                                          # unsichtbar aufbauen, dann an Ort und Stelle zeigen
        self.app, self.moment, self.vorher = app, moment, moment["hwnd"]
        bild = moment["bild"]
        self.title("Rückmeldung")
        self.protocol("WM_DELETE_WINDOW", self.verwerfen)
        faktor = self.winfo_fpixels("1i") / 96.0

        def px(n):
            return int(n * faktor)

        rand = ttk.Frame(self, padding=px(10))
        rand.pack(fill=tk.BOTH, expand=True)

        knoepfe = ttk.Frame(rand)                                # vor dem dehnbaren Inhalt, damit sie nie verschwinden
        knoepfe.pack(side=tk.BOTTOM, fill=tk.X, pady=(px(8), 0))
        ttk.Button(knoepfe, text="Verwerfen (Esc)", command=self.verwerfen).pack(side=tk.RIGHT)
        ttk.Button(knoepfe, text="Speichern (Strg+Enter)", command=self.speichern).pack(side=tk.RIGHT, padx=px(6))
        self.bild_ki = tk.BooleanVar()
        self.mit_protokoll = tk.BooleanVar()
        self._ki_knopf = ttk.Checkbutton(knoepfe, text="Bild für KI freigeben", variable=self.bild_ki)
        self._ki_knopf.pack(side=tk.LEFT)
        self._protokoll_knopf = ttk.Checkbutton(knoepfe, variable=self.mit_protokoll)
        self._protokoll_knopf.pack(side=tk.LEFT, padx=(px(12), 0))

        self.notiz = tk.Text(rand, width=64, height=4, wrap=tk.WORD, undo=True, font="TkDefaultFont")
        self.notiz.pack(side=tk.BOTTOM, fill=tk.X, pady=(px(6), 0))

        projektzeile = ttk.Frame(rand)
        projektzeile.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(projektzeile, text="Projekt:").pack(side=tk.LEFT)
        self.projektname = tk.StringVar(value=moment["projekt"]["name"] if moment["projekt"]
                                        else kern.PROJEKT_UNBEKANNT)
        self.projektwahl = ttk.Combobox(projektzeile, textvariable=self.projektname, values=app.projektnamen,
                                        state="readonly", width=max(12, max(len(n) for n in app.projektnamen) + 2))
        self.projektwahl.pack(side=tk.LEFT, padx=(px(6), px(12)))
        self.projektwahl.bind("<<ComboboxSelected>>", lambda e: self._projekt_gewaehlt())
        self._angaben = ttk.Label(projektzeile, foreground="#666666")
        self._angaben.pack(side=tk.LEFT)

        kopf = moment["titel"] or "(kein Fenster erkannt)"
        if moment["programm"]:
            kopf += f"   —   {moment['programm']}"
        ttk.Label(rand, text=kopf if len(kopf) <= 110 else kopf[:107] + "...").pack(side=tk.TOP, anchor=tk.W,
                                                                                   pady=(px(4), 0))

        self.mit_bild = tk.BooleanVar(value=bild is not None)
        bildzeile = ttk.Frame(rand)
        bildzeile.pack(side=tk.BOTTOM, fill=tk.X, pady=(px(6), 0))
        self.editor = None
        if bild is not None:
            b = min(px(900), int(self.winfo_screenwidth() * 0.7))
            h = min(px(520), int(self.winfo_screenheight() * 0.55))
            self.editor = BildEditor(rand, bild, px, b, h)
            self.editor.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(px(6), 0))
        ttk.Checkbutton(bildzeile, text=f"Bild anhängen ({bild.width} × {bild.height})" if bild is not None
                        else "Kein Bild (Fenster nicht aufnehmbar)", variable=self.mit_bild,
                        state=tk.NORMAL if bild is not None else tk.DISABLED).pack(side=tk.LEFT)
        self.art = tk.StringVar(value=kern.ARTEN[0])
        for i, a in enumerate(reversed(kern.ARTEN)):
            ttk.Radiobutton(bildzeile, text=f"{a} (Alt+{len(kern.ARTEN) - i})", value=a,
                            variable=self.art).pack(side=tk.RIGHT, padx=(px(6), 0))
        self._projekt_gewaehlt()

        self.bind("<Control-Return>", lambda e: (self.speichern(), "break")[1])
        self.notiz.bind("<Control-Return>", lambda e: (self.speichern(), "break")[1])
        self.bind("<Escape>", lambda e: self.verwerfen())
        for i, a in enumerate(kern.ARTEN, start=1):
            self.bind(f"<Alt-Key-{i}>", lambda e, a=a: (self.art.set(a), "break")[1])

        self.update_idletasks()
        self._platzieren(moment["rahmen"])
        self.deiconify()
        self.nach_vorn()

    def _projekt_gewaehlt(self):
        """Vorgaben des gewählten Projekts übernehmen: Version, Bild für die KI, Protokoll anhängen."""
        p = self.app.projekt(self.projektname.get())
        version = kern.finde_version(p, self.moment["titel_liste"])
        angaben = [f"Version {version}" if version else "", self.moment["bildschirm"]]
        self._angaben.configure(text="   ·   ".join(a for a in angaben if a))
        p = p or {}
        self.bild_ki.set(bool(p.get("bild_fuer_ki")) and self.moment["bild"] is not None)
        self._ki_knopf.configure(state=tk.NORMAL if self.moment["bild"] is not None else tk.DISABLED)
        pr = p.get("protokoll")
        if pr:
            self.mit_protokoll.set(bool(pr.get("vorgabe")))
            self._protokoll_knopf.configure(text=f"Protokoll anhängen (letzte {pr.get('zeilen', 40)} Zeilen)",
                                            state=tk.NORMAL)
        else:
            self.mit_protokoll.set(False)
            self._protokoll_knopf.configure(text="Protokoll anhängen", state=tk.DISABLED)

    def _platzieren(self, rahmen):
        """Mittig über das aufgenommene Fenster, sonst mittig auf den Bildschirm - und nie über den Rand."""
        b, h = self.winfo_reqwidth(), self.winfo_reqheight()
        if rahmen:
            mx, my = (rahmen[0] + rahmen[2]) // 2, (rahmen[1] + rahmen[3]) // 2
        else:
            mx, my = self.winfo_screenwidth() // 2, self.winfo_screenheight() // 2
        x = max(self.winfo_vrootx(), mx - b // 2)
        y = max(self.winfo_vrooty(), my - h // 2)
        self.geometry(f"+{x}+{y}")

    def nach_vorn(self):
        """Nach vorn und Fokus ins Notizfeld - erlaubt, weil der Nutzer gerade das Kürzel gedrückt hat."""
        self.lift()
        win.in_den_vordergrund(win.oberstes_fenster(self.winfo_id()))
        self.focus_force()
        self.notiz.focus_set()

    def speichern(self):
        text = self.notiz.get("1.0", tk.END).strip()
        bild = self.editor.ergebnis() if self.editor is not None and self.mit_bild.get() else None
        if not text and bild is None:
            self.schliessen()
            return
        try:
            self.app.speichere(self.art.get(), text, bild, self.moment, self.projektname.get(),
                               self.bild_ki.get(), self.mit_protokoll.get())
        except OSError as e:
            messagebox.showerror("Rückmeldung", f"Speichern fehlgeschlagen:\n{e}", parent=self)
            return
        self.schliessen()

    def verwerfen(self):
        gemacht = self.notiz.get("1.0", tk.END).strip() or (self.editor is not None and self.editor.markierungen)
        if gemacht and not messagebox.askyesno("Rückmeldung", "Notiz und Markierungen verwerfen?", parent=self):
            self.notiz.focus_set()
            return
        self.schliessen()

    def schliessen(self):
        self.app.fenster = None
        self.destroy()
        win.in_den_vordergrund(self.vorher)                     # zurück ins getestete Programm


class BildEditor(ttk.Frame):
    """Aufnahme mit Zoom (Mausrad, um die Maus herum), Verschieben (rechte oder mittlere Taste ziehen) und
    Markierungen (linke Taste ziehen: Rahmen, Pfeil oder Schwärzen). Die Markierungen liegen in Bildpixeln vor und
    werden erst beim Speichern in voller Auflösung eingebrannt (rueckmeldung_bild)."""

    def __init__(self, parent, bild, px, breite, hoehe):
        super().__init__(parent)
        self.bild = bild.convert("RGB")
        self.px = px
        self.markierungen = []                                   # [(art, x0, y0, x1, y1)] in Bildpixeln
        self.ansicht = kern.Ansicht(*self.bild.size)
        self._foto = None
        self._geplant = None
        self._ziehen = None                                      # (art, Bild-x, Bild-y, Canvas-Element) beim Zeichnen
        self._schieben = None                                    # letzte Mausposition beim Verschieben

        leiste = ttk.Frame(self)
        leiste.pack(side=tk.TOP, fill=tk.X)
        self.werkzeug = tk.StringVar(value=kern.MARKIERUNGEN[0])
        for art, zeichen in zip(kern.MARKIERUNGEN, ("▭", "➜", "■")):
            ttk.Radiobutton(leiste, text=f"{zeichen} {art}", value=art, variable=self.werkzeug).pack(
                side=tk.LEFT, padx=(0, px(10)))
        ttk.Button(leiste, text="Rückgängig (Strg+Z)", command=self.rueckgaengig).pack(side=tk.LEFT, padx=(px(6), 0))
        ttk.Button(leiste, text="Einpassen", command=self.einpassen).pack(side=tk.LEFT, padx=(px(6), 0))
        self.zoom_text = ttk.Label(leiste, foreground="#666666")
        self.zoom_text.pack(side=tk.RIGHT)

        self.flaeche = tk.Canvas(self, width=breite, height=hoehe, background="#7a7a7a", highlightthickness=0,
                                 cursor="crosshair")
        self.flaeche.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(px(4), 0))
        self.ansicht.einpassen(breite, hoehe)

        f = self.flaeche
        f.bind("<Configure>", self._groesse)
        f.bind("<MouseWheel>", self._rad)
        f.bind("<ButtonPress-1>", self._zeichnen_start)
        f.bind("<B1-Motion>", self._zeichnen_weiter)
        f.bind("<ButtonRelease-1>", self._zeichnen_ende)
        for taste in (2, 3):
            f.bind(f"<ButtonPress-{taste}>", self._schieben_start)
            f.bind(f"<B{taste}-Motion>", self._schieben_weiter)
        f.bind("<Control-z>", lambda e: (self.rueckgaengig(), "break")[1])
        self._planen()

    # --- Darstellung ---

    def _planen(self):
        """Neu zeichnen, aber höchstens einmal je Leerlauf - Rad und Ziehen feuern viele Ereignisse."""
        if self._geplant is None:
            self._geplant = self.after_idle(self._zeichnen)

    def _zeichnen(self):
        from PIL import Image, ImageTk
        self._geplant = None
        f, a = self.flaeche, self.ansicht
        f.delete("bild", "mark")
        (l, o, r, u), (fx, fy) = a.ausschnitt()
        if r > l and u > o:
            ziel = (max(1, round((r - l) * a.massstab)), max(1, round((u - o) * a.massstab)))
            verfahren = Image.Resampling.NEAREST if a.massstab >= 2 else Image.Resampling.BILINEAR
            teil = self.bild.crop((l, o, r, u)).resize(ziel, verfahren)
            self._foto = ImageTk.PhotoImage(teil, master=self)
            f.create_image(round(fx), round(fy), image=self._foto, anchor=tk.NW, tags="bild")
        for m in self.markierungen:
            self._zeichne_markierung(*m)
        self.zoom_text.configure(text=f"{a.massstab * 100:.0f} %   ·   Rad: Zoom   ·   rechte Taste: verschieben")

    def _zeichne_markierung(self, art, x0, y0, x1, y1, element=None):
        """Markierung (Bildkoordinaten) auf die Fläche zeichnen bzw. ein vorhandenes Element nachführen."""
        a0, b0 = self.ansicht.zu_flaeche(x0, y0)
        a1, b1 = self.ansicht.zu_flaeche(x1, y1)
        f = self.flaeche
        if element is not None:
            f.coords(element, a0, b0, a1, b1)
            return element
        breite = max(2, round(kern.linienbreite(*self.bild.size) * self.ansicht.massstab))
        if art == "Schwärzen":
            return f.create_rectangle(a0, b0, a1, b1, fill="black", outline="black", tags="mark")
        if art == "Rahmen":
            return f.create_rectangle(a0, b0, a1, b1, outline="#e61e1e", width=breite, tags="mark")
        spitze = breite * 5
        return f.create_line(a0, b0, a1, b1, fill="#e61e1e", width=breite, arrow=tk.LAST,
                             arrowshape=(spitze, spitze, spitze * 0.47), tags="mark")

    def _groesse(self, ereignis):
        self.ansicht.neue_flaeche(ereignis.width, ereignis.height)
        self._planen()

    # --- Bedienung ---

    def _rad(self, ereignis):
        self.ansicht.zoome(1.25 ** (ereignis.delta / 120), ereignis.x, ereignis.y)
        self._planen()

    def einpassen(self):
        self.ansicht.einpassen(self.flaeche.winfo_width(), self.flaeche.winfo_height())
        self._planen()

    def _schieben_start(self, ereignis):
        self._schieben = (ereignis.x, ereignis.y)

    def _schieben_weiter(self, ereignis):
        if self._schieben:
            self.ansicht.verschiebe(ereignis.x - self._schieben[0], ereignis.y - self._schieben[1])
            self._schieben = (ereignis.x, ereignis.y)
            self._planen()

    def _zeichnen_start(self, ereignis):
        self.flaeche.focus_set()                                 # damit Strg+Z hier rückgängig macht
        bx, by = self.ansicht.zu_bild(ereignis.x, ereignis.y)
        art = self.werkzeug.get()
        self._ziehen = (art, bx, by, self._zeichne_markierung(art, bx, by, bx, by), ereignis.x, ereignis.y)

    def _zeichnen_weiter(self, ereignis):
        if self._ziehen:
            art, bx, by, element, _, _ = self._ziehen
            self._zeichne_markierung(art, bx, by, *self._begrenzt(ereignis), element=element)

    def _zeichnen_ende(self, ereignis):
        if not self._ziehen:
            return
        art, bx, by, element, sx, sy = self._ziehen
        self._ziehen = None
        if abs(ereignis.x - sx) < self.px(5) and abs(ereignis.y - sy) < self.px(5):
            self.flaeche.delete(element)                         # nur geklickt, nicht gezogen
            return
        self.markierungen.append((art, bx, by, *self._begrenzt(ereignis)))
        self._planen()

    def _begrenzt(self, ereignis):
        """Mausposition als Bildkoordinate, auf das Bild begrenzt (Ziehen über den Rand hinaus)."""
        bx, by = self.ansicht.zu_bild(ereignis.x, ereignis.y)
        return min(max(bx, 0), self.bild.width), min(max(by, 0), self.bild.height)

    def rueckgaengig(self):
        if self.markierungen:
            self.markierungen.pop()
            self._planen()

    def ergebnis(self):
        """Das Bild zum Speichern: Original oder Kopie mit eingebrannten Markierungen."""
        if not self.markierungen:
            return self.bild
        import rueckmeldung_bild
        return rueckmeldung_bild.einbrennen(self.bild, self.markierungen)


def konfig_pfad():
    """rueckmeldung.json neben dem Programm (bei der EXE neben der EXE)."""
    ordner = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
    return os.path.join(ordner, kern.KONFIG_DATEI)


def main(argv=None):
    p = argparse.ArgumentParser(description="Rückmeldung per Tastenkürzel festhalten")
    p.add_argument("--konfig", default=None, help=f"Konfigurationsdatei (Standard {kern.KONFIG_DATEI} neben dem Programm)")
    p.add_argument("--ablage", default=None, help=f"Ablage-Ordner (überschreibt die Konfiguration, Standard {kern.STANDARD_ABLAGE})")
    p.add_argument("--kuerzel", default=None, help=f"Tastenkürzel (überschreibt die Konfiguration, Standard {kern.STANDARD_KUERZEL})")
    args = p.parse_args(argv)
    win.dpi_bewusst()
    root = tk.Tk()
    root.withdraw()
    pfad = args.konfig or konfig_pfad()
    try:
        konfig = kern.lade_konfig(pfad)
        if args.ablage:
            konfig["ablage"] = args.ablage
        if args.kuerzel:
            kern.lies_kuerzel(args.kuerzel)
            konfig["kuerzel"] = args.kuerzel
    except (kern.Konfigfehler, kern.Kuerzelfehler) as e:
        messagebox.showerror("Rückmeldung", f"Konfiguration nicht lesbar:\n{e}\n\n{pfad}")
        root.destroy()
        return 1
    app = App(root, konfig)
    if not app.starte():
        root.destroy()
        return 1
    projekte = ", ".join(x["name"] for x in konfig["projekte"]) or "keine (alles nach Unbekannt)"
    print(f"Rückmeldung läuft: {kern.zeige_kuerzel(konfig['kuerzel'])} hält das aktive Fenster fest, "
          f"Ablage {konfig['ablage']}, Projekte: {projekte}. Beenden mit Strg+C.", flush=True)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        app.stoppe()
    return 0


if __name__ == "__main__":
    sys.exit(main())
