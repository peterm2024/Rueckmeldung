"""Rückmeldung - hält beim Testen einen Moment fest: Tastenkürzel drücken, das aktive Fenster wird fotografiert,
einen Satz dazu tippen, Strg+Enter. Gespeichert wird eine Markdown-Datei samt Bild im Ablage-Ordner, die nächste
Arbeitssitzung liest sie von dort.

    python rueckmeldung.py                       läuft im Hintergrund, Kürzel Strg+Alt+F, Ablage ~/Rueckmeldungen
    python rueckmeldung.py --ablage D:/Rueck     andere Ablage
    python rueckmeldung.py --kuerzel ctrl+alt+r  anderes Kürzel

Beenden (bis es ein eigenes Fenster dafür gibt): Strg+C in der Konsole bzw. die Konsole schließen.
Nichts verlässt den Rechner - kein Netzwerkzugriff.
"""
import argparse
import datetime
import io
import queue
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import rueckmeldung_kern as kern
import rueckmeldung_windows as win

STANDARD_KUERZEL = "ctrl+alt+f"
STANDARD_ABLAGE = "~/Rueckmeldungen"


class App:
    """Unsichtbares Hauptfenster: hält das Kürzel und öffnet bei jedem Druck ein Erfassungsfenster."""

    def __init__(self, root, ablage=STANDARD_ABLAGE, kuerzel=STANDARD_KUERZEL):
        self.root, self.ablage, self.kuerzel_text = root, ablage, kuerzel
        self.ereignisse = queue.Queue()
        self.fenster = None
        self.kuerzel = None
        self.gespeichert = []                    # Pfade dieser Sitzung (für Tests und die Konsolenmeldung)

    def starte(self):
        """Kürzel anmelden. False (mit Meldung), wenn es nicht geht."""
        try:
            mods, taste = kern.lies_kuerzel(self.kuerzel_text)
        except kern.Kuerzelfehler as e:
            messagebox.showerror("Rückmeldung", f"Das Kürzel „{self.kuerzel_text}“ ist nicht lesbar:\n{e}")
            return False
        self.kuerzel = win.Kuerzel(mods, taste, lambda: self.ereignisse.put("kuerzel"))
        if not self.kuerzel.starte():
            messagebox.showerror(
                "Rückmeldung",
                f"Das Kürzel {kern.zeige_kuerzel(self.kuerzel_text)} ist schon belegt "
                f"({self.kuerzel.fehler}).\n\nLäuft die Rückmeldung bereits? Sonst ein anderes Kürzel mit "
                "--kuerzel wählen.")
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
            self.fenster.nach_vorn()             # Schritt 3: hier ein weiteres Bild anhängen
            return
        hwnd = hwnd or win.vordergrund()
        if hwnd and win.gehoert_zu_mir(hwnd):
            return
        bild, titel, programm, rahmen = None, "", "", None
        if hwnd:
            titel, programm, rahmen = win.fenster_titel(hwnd), win.fenster_programm(hwnd), win.fensterrahmen(hwnd)
            try:
                bild = win.aufnahme(hwnd)
            except OSError:
                bild = None
        self.fenster = Erfassung(self, hwnd, bild, titel, programm, rahmen)

    def speichere(self, art, notiz, bild, titel, programm):
        pngs = []
        if bild is not None:
            puffer = io.BytesIO()
            bild.save(puffer, "PNG", optimize=True)
            pngs.append(puffer.getvalue())
        pfad = kern.speichere(self.ablage, kern.PROJEKT_UNBEKANNT, datetime.datetime.now(), art, notiz, pngs,
                              {"fenster": titel, "programm": programm})
        self.gespeichert.append(pfad)
        return pfad


class Erfassung(tk.Toplevel):
    """Das Fenster nach dem Kürzel: Bild, Art, Notiz; Strg+Enter speichert, Esc verwirft."""

    def __init__(self, app, vorher, bild, titel, programm, rahmen):
        super().__init__(app.root)
        self.withdraw()                                          # unsichtbar aufbauen, dann an Ort und Stelle zeigen
        self.app, self.vorher, self.bild, self.titel, self.programm = app, vorher, bild, titel, programm
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

        kopf = titel or "(kein Fenster erkannt)"
        if programm:
            kopf += f"   —   {programm}"
        ttk.Label(rand, text=kopf if len(kopf) <= 110 else kopf[:107] + "...").pack(side=tk.TOP, anchor=tk.W)

        self.mit_bild = tk.BooleanVar(value=bild is not None)
        self._vorschau = None
        if bild is not None:
            from PIL import ImageTk
            klein = bild.copy()
            klein.thumbnail((px(560), px(340)))
            self._vorschau = ImageTk.PhotoImage(klein, master=self)
            ttk.Label(rand, image=self._vorschau, relief=tk.SOLID, borderwidth=1).pack(side=tk.TOP, pady=px(6))
        bildzeile = ttk.Frame(rand)
        bildzeile.pack(side=tk.TOP, fill=tk.X)
        ttk.Checkbutton(bildzeile, text=f"Bild anhängen ({bild.width} × {bild.height})" if bild is not None
                        else "Kein Bild (Fenster nicht aufnehmbar)", variable=self.mit_bild,
                        state=tk.NORMAL if bild is not None else tk.DISABLED).pack(side=tk.LEFT)
        self.art = tk.StringVar(value=kern.ARTEN[0])
        for i, a in enumerate(reversed(kern.ARTEN)):
            ttk.Radiobutton(bildzeile, text=f"{a} (Alt+{len(kern.ARTEN) - i})", value=a,
                            variable=self.art).pack(side=tk.RIGHT, padx=(px(6), 0))

        self.notiz = tk.Text(rand, width=64, height=5, wrap=tk.WORD, undo=True)
        self.notiz.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(px(6), 0))

        self.bind("<Control-Return>", lambda e: (self.speichern(), "break")[1])
        self.notiz.bind("<Control-Return>", lambda e: (self.speichern(), "break")[1])
        self.bind("<Escape>", lambda e: self.verwerfen())
        for i, a in enumerate(kern.ARTEN, start=1):
            self.bind(f"<Alt-Key-{i}>", lambda e, a=a: (self.art.set(a), "break")[1])

        self.update_idletasks()
        self._platzieren(rahmen)
        self.deiconify()
        self.nach_vorn()

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
        bild = self.bild if self.mit_bild.get() else None
        if not text and bild is None:
            self.schliessen()
            return
        try:
            self.app.speichere(self.art.get(), text, bild, self.titel, self.programm)
        except OSError as e:
            messagebox.showerror("Rückmeldung", f"Speichern fehlgeschlagen:\n{e}", parent=self)
            return
        self.schliessen()

    def verwerfen(self):
        if self.notiz.get("1.0", tk.END).strip() and not messagebox.askyesno(
                "Rückmeldung", "Die Notiz verwerfen?", parent=self):
            self.notiz.focus_set()
            return
        self.schliessen()

    def schliessen(self):
        self.app.fenster = None
        self.destroy()
        win.in_den_vordergrund(self.vorher)                     # zurück ins getestete Programm


def main(argv=None):
    p = argparse.ArgumentParser(description="Rückmeldung per Tastenkürzel festhalten")
    p.add_argument("--ablage", default=STANDARD_ABLAGE, help=f"Ablage-Ordner (Standard {STANDARD_ABLAGE})")
    p.add_argument("--kuerzel", default=STANDARD_KUERZEL, help=f"Tastenkürzel (Standard {STANDARD_KUERZEL})")
    args = p.parse_args(argv)
    win.dpi_bewusst()
    root = tk.Tk()
    root.withdraw()
    app = App(root, args.ablage, args.kuerzel)
    if not app.starte():
        root.destroy()
        return 1
    print(f"Rückmeldung läuft: {kern.zeige_kuerzel(args.kuerzel)} hält das aktive Fenster fest, "
          f"Ablage {args.ablage}. Beenden mit Strg+C.", flush=True)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        app.stoppe()
    return 0


if __name__ == "__main__":
    sys.exit(main())
