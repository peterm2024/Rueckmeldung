"""Rückmeldung - Windows-Anbindung über ctypes: globales Kürzel, aktives Fenster, Bildschirmaufnahme, Fokus.

Kein tkinter hier. Das Kürzel läuft in einem eigenen Thread mit Windows-Nachrichtenschleife und meldet sich nur
über einen Rückruf, der thread-sicher sein muss (rueckmeldung.py legt dafür eine Queue hin, die das Fenster per
after() abholt - Tkinter darf nie aus diesem Thread angefasst werden).
"""
import ctypes
import ctypes.wintypes as wt
import os
import threading

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
dwmapi = ctypes.windll.dwmapi

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
DWMWA_EXTENDED_FRAME_BOUNDS = 9

user32.GetForegroundWindow.restype = wt.HWND
user32.GetParent.restype = wt.HWND
user32.GetParent.argtypes = [wt.HWND]
user32.GetAncestor.restype = wt.HWND
user32.GetAncestor.argtypes = [wt.HWND, wt.UINT]


def dpi_bewusst():
    """Prozess als „pro Monitor DPI-bewusst“ melden - VOR dem ersten Fenster aufrufen. Sonst rechnet Windows bei
    125 % die Fensterkoordinaten um, und die Aufnahme schneidet daneben bzw. das eigene Fenster wird unscharf."""
    try:
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):   # PER_MONITOR_AWARE_V2
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        user32.SetProcessDPIAware()


def vordergrund():
    """Handle des aktiven Fensters (0, wenn keins)."""
    return user32.GetForegroundWindow() or 0


def oberstes_fenster(hwnd):
    """Zum Handle eines Tk-Fensters (winfo_id) das Fenster der obersten Ebene, wie Windows es kennt."""
    return user32.GetAncestor(hwnd, 2) or hwnd       # GA_ROOT


def gehoert_zu_mir(hwnd):
    """Gehört das Fenster zu diesem Prozess? (Kürzel im eigenen Fenster nimmt nicht sich selbst auf.)"""
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(wt.HWND(hwnd), ctypes.byref(pid))
    return pid.value == os.getpid()


def fenster_titel(hwnd):
    n = user32.GetWindowTextLengthW(wt.HWND(hwnd))
    puffer = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(wt.HWND(hwnd), puffer, n + 1)
    return puffer.value


def fenster_programm(hwnd):
    """Dateiname des Programms, dem das Fenster gehört (etwa „DokumentenManager.exe“), sonst ""."""
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(wt.HWND(hwnd), ctypes.byref(pid))
    h = kernel32.OpenProcess(0x1000, False, pid.value)          # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    try:
        puffer, n = ctypes.create_unicode_buffer(1024), wt.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(h, 0, puffer, ctypes.byref(n)):
            return os.path.basename(puffer.value)
        return ""
    finally:
        kernel32.CloseHandle(h)


def fensterrahmen(hwnd):
    """Sichtbarer Rahmen (links, oben, rechts, unten) in Bildschirm-Pixeln. Unter Windows 10/11 liefert
    GetWindowRect den unsichtbaren Schatten-Rand mit, darum zuerst DWM fragen."""
    r = wt.RECT()
    if dwmapi.DwmGetWindowAttribute(wt.HWND(hwnd), DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(r), ctypes.sizeof(r)) != 0:
        if not user32.GetWindowRect(wt.HWND(hwnd), ctypes.byref(r)):
            return None
    if r.right - r.left < 2 or r.bottom - r.top < 2:
        return None
    return r.left, r.top, r.right, r.bottom


def aufnahme(hwnd=None):
    """PIL-Bild des Fensters (bzw. aller Bildschirme bei hwnd=None); None, wenn das Fenster keine Fläche hat
    (minimiert). Aufgenommen wird, was auf dem Bildschirm zu sehen ist - auch darüber liegende Fenster."""
    from PIL import ImageGrab
    if hwnd is None:
        return ImageGrab.grab(all_screens=True)
    rahmen = fensterrahmen(hwnd)
    if rahmen is None:
        return None
    return ImageGrab.grab(bbox=rahmen, all_screens=True)


def in_den_vordergrund(hwnd):
    """Fenster nach vorn holen. Gelingt nur, solange dieser Prozess das Recht dazu hat - nach einem Kürzel
    (WM_HOTKEY) gibt Windows es ihm."""
    if hwnd and user32.IsWindow(wt.HWND(hwnd)):
        user32.SetForegroundWindow(wt.HWND(hwnd))


class Kuerzel:
    """Globales Tastenkürzel in eigenem Thread. rueckruf() wird bei jedem Druck im Kürzel-Thread aufgerufen."""

    _ID = 0x5246                                                 # beliebig, nur innerhalb des Threads eindeutig

    def __init__(self, modifikatoren, taste, rueckruf):
        self.modifikatoren, self.taste, self.rueckruf = modifikatoren, taste, rueckruf
        self._thread = None
        self._thread_id = None
        self._bereit = threading.Event()
        self.fehler = None

    def starte(self, warte=5.0):
        """Thread starten und auf die Anmeldung warten. True, wenn das Kürzel gilt; sonst steht in fehler warum
        (meist: ein anderes Programm - oder eine zweite Rückmeldung - hat dieselbe Kombination)."""
        self._thread = threading.Thread(target=self._schleife, name="Kuerzel", daemon=True)
        self._thread.start()
        self._bereit.wait(warte)
        return self.fehler is None and self._thread_id is not None

    def _schleife(self):
        self._thread_id = kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, self._ID, self.modifikatoren, self.taste):
            self.fehler = f"Windows-Fehler {ctypes.GetLastError()}"
            self._bereit.set()
            return
        self._bereit.set()
        msg = wt.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY and msg.wParam == self._ID:
                    self.rueckruf()
        finally:
            user32.UnregisterHotKey(None, self._ID)

    def simuliere(self):
        """Für Tests: ein Kürzel-Ereignis in die Schleife legen, ohne eine Taste zu drücken."""
        user32.PostThreadMessageW(self._thread_id, WM_HOTKEY, self._ID, 0)

    def stoppe(self):
        if self._thread_id is not None and self._thread and self._thread.is_alive():
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            self._thread.join(2)
