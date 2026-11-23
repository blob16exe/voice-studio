# -*- coding: utf-8 -*-
"""
Voice Studio v2 - tool tao giong doc cho video (1 cua so, phong cach pixel).

Sua so voi v1 (theo video test cua Minh sang 11/11/2026):
- Cua so GON lai, khung KET QUA gan o day cua so (luon thay), khong con bi
  tran ra ngoai man hinh.
- Danh sach 20 giong nam trong khung CUON duoc, chia 4 nhom.
- Dong TRANG THAI + thanh tien trinh nam TREN nut TAO GIONG, kem so giay da cho.
- Nut HUY / LAM LAI: pha khoa "dang ban" khi bi ket, khong phai tat tool.
- Edge goi qua tien trinh con co timeout (trong engines.py) - khong treo im nua.
- Moi buoc deu ghi vao output/log.txt.
"""
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkfont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engines

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
OUT_DIR = os.path.join(BASE_DIR, "output")

BG = "#0A0A12"
PANEL = "#141426"
PANEL2 = "#0D0D18"
BORDER = "#3A3A5E"
WHITE = "#E8E8F5"
DIM = "#9696B4"
PURPLE = "#8B7CF0"
YELLOW = "#FFD23F"
GREEN = "#57E389"
CYAN = "#4DD8E6"
BLUE = "#2C78DC"
GREENBG = "#16422A"
REDBG = "#58202A"
ROWSEL = "#1A1A32"
GROUPCOL = {
    "VIỆT — EDGE (CẦN MẠNG)": YELLOW,
    "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)": GREEN,
    "ANH — EDGE (CẦN MẠNG)": CYAN,
    "MÁY BRO — SAPI (GIỌNG SẴN TRONG WINDOWS)": DIM,
}


def _register_bundled_fonts(root):
    if sys.platform.startswith("win"):
        try:
            import ctypes
            for name in ("VT323.ttf", "PressStart2P.ttf"):
                ctypes.windll.gdi32.AddFontResourceExW(
                    os.path.join(FONTS_DIR, name), 0x10, 0)
        except Exception:
            pass
    fams = set(tkfont.families(root))
    vt = "VT323" if "VT323" in fams else "Courier New"
    ps = "Press Start 2P" if "Press Start 2P" in fams else "Courier New"
    return vt, ps


def play_file(path):
    try:
        if sys.platform.startswith("win"):
            if path.lower().endswith(".wav"):
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                os.startfile(path)
            return True
        import shutil
        for player in (["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
                       ["aplay"], ["afplay"]):
            if shutil.which(player[0]):
                subprocess.Popen(player + [path],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
    except Exception:
        pass
    return False


class VoiceStudioApp:
    def __init__(self, root):
        self.root = root
        root.title("Voice Studio v2.1.2 — Tạo giọng đọc cho video")
        root.configure(bg=BG)
        root.geometry("1180x780")
        root.minsize(1080, 720)
        self.VT, self.PS = _register_bundled_fonts(root)
        self.msg_q = queue.Queue()
        self.busy = False
        self.cancel_event = threading.Event()
        self.gen_started = None
        self.last_progress = (0, 0, "")
        self.voice_var = tk.StringVar(value="kokoro_amadam")
        self.emph_var = tk.BooleanVar(value=True)
        os.makedirs(OUT_DIR, exist_ok=True)
        engines.set_log_path(os.path.join(OUT_DIR, "log.txt"))
        engines.log("=== Voice Studio v2.1.2 khởi động ===")
        self._build()
        self._update_count()
        self.root.after(120, self._poll_queue)
        if not engines.ffmpeg_path():
            self.status_var.set("Lưu ý: chưa thấy ffmpeg trên máy — xem mục "
                                "'Nếu tool báo thiếu ffmpeg' trong README-HUONG-DAN.md")

    def f_vt(self, size, bold=False):
        return (self.VT, size, "bold") if bold else (self.VT, size)

    def f_ps(self, size):
        return (self.PS, size)

    def _panel(self, parent, **kw):
        return tk.Frame(parent, bg=PANEL, highlightbackground=BORDER,
                        highlightthickness=2, **kw)

    # ------------------------------------------------------------------ giao dien
    def _build(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=12, pady=(8, 2))
        cv = tk.Canvas(top, width=46, height=32, bg=BG, highlightthickness=0)
        cv.create_rectangle(2, 12, 11, 21, fill=YELLOW, outline="")
        cv.create_polygon(13, 8, 24, 2, 24, 30, 13, 24, fill=YELLOW, outline="")
        cv.create_rectangle(29, 13, 33, 20, fill=YELLOW, outline="")
        cv.create_rectangle(37, 10, 41, 23, fill=YELLOW, outline="")
        cv.pack(side="left")
        tk.Label(top, text="VOICE STUDIO", font=self.f_ps(14),
                 bg=BG, fg=YELLOW).pack(side="left", padx=(6, 8))
        tk.Label(top, text="v2.1.2 — TOOL TẠO GIỌNG ĐỌC CHO VIDEO", font=self.f_vt(17),
                 bg=BG, fg=DIM).pack(side="left")

        steps = tk.Frame(self.root, bg=BG)
        steps.pack(fill="x", padx=12, pady=2)
        for i, name in enumerate(["DÁN SCRIPT", "CHỌN GIỌNG", "CHỈNH TÔNG",
                                  "TẠO GIỌNG", "GỬI RIO"]):
            cell = tk.Frame(steps, bg=PANEL2, highlightbackground=BORDER,
                            highlightthickness=1)
            cell.pack(side="left", expand=True, fill="x",
                      padx=(0, 6 if i < 4 else 0))
            tk.Label(cell, text=str(i + 1), font=self.f_ps(8),
                     bg=PANEL2, fg=YELLOW).pack(side="left", padx=(7, 3), pady=3)
            tk.Label(cell, text=name, font=self.f_vt(15),
                     bg=PANEL2, fg=WHITE).pack(side="left", pady=3)
            if i < 4:
                tk.Label(steps, text=">", font=self.f_vt(15),
                         bg=BG, fg=DIM).pack(side="left")

        # KET QUA: pack o day TRUOC mid -> luon nam trong cua so
        res = self._panel(self.root)
        res.pack(side="bottom", fill="x", padx=12, pady=(4, 10))
        tk.Label(res, text="KẾT QUẢ — gửi 2 file này cho Rio ráp video (nhật ký: output/log.txt):",
                 font=self.f_vt(16), bg=PANEL, fg=WHITE).pack(
                     anchor="w", padx=10, pady=(4, 1))
        row = tk.Frame(res, bg=PANEL)
        row.pack(fill="x", padx=10, pady=(0, 8))
        chip1 = tk.Frame(row, bg=PANEL2, highlightbackground=CYAN,
                         highlightthickness=1)
        chip1.pack(side="left", expand=True, fill="x", padx=(0, 6))
        tk.Label(chip1, text="voice.mp3", font=self.f_vt(16),
                 bg=PANEL2, fg=CYAN).pack(side="left", padx=8, pady=3)
        self.res_mp3_var = tk.StringVar(value="— chưa tạo")
        tk.Label(chip1, textvariable=self.res_mp3_var, font=self.f_vt(15),
                 bg=PANEL2, fg=DIM).pack(side="left")
        tk.Button(chip1, text="NGHE LẠI", font=self.f_vt(13), bg=PANEL,
                  fg=WHITE, activebackground=BORDER, activeforeground=WHITE,
                  bd=0, padx=8, command=self._play_voice).pack(side="right", padx=4)
        chip2 = tk.Frame(row, bg=PANEL2, highlightbackground=YELLOW,
                         highlightthickness=1)
        chip2.pack(side="left", expand=True, fill="x", padx=(0, 6))
        tk.Label(chip2, text="timings.json", font=self.f_vt(16),
                 bg=PANEL2, fg=YELLOW).pack(side="left", padx=8, pady=3)
        self.res_tim_var = tk.StringVar(value="— chưa tạo")
        tk.Label(chip2, textvariable=self.res_tim_var, font=self.f_vt(15),
                 bg=PANEL2, fg=DIM).pack(side="left")
        tk.Button(row, text="MỞ THƯ MỤC OUTPUT", font=self.f_vt(15, True),
                  bg=PURPLE, fg="#0F0F19", activebackground=PURPLE,
                  activeforeground="#0F0F19", bd=0, padx=12, pady=4,
                  command=self._open_outdir).pack(side="left")

        mid = tk.Frame(self.root, bg=BG)
        mid.pack(fill="both", expand=True, padx=12, pady=4)
        mid.columnconfigure(0, weight=11)
        mid.columnconfigure(1, weight=10)
        mid.rowconfigure(0, weight=1)

        # ---- trai: SCRIPT ----
        left = self._panel(mid)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        hdr = tk.Frame(left, bg=PANEL)
        hdr.pack(fill="x", padx=10, pady=(6, 2))
        tk.Label(hdr, text="SCRIPT", font=self.f_ps(9),
                 bg=PANEL, fg=PURPLE).pack(side="left")
        tk.Label(hdr, text="— mỗi dòng = 1 câu = 1 shot", font=self.f_vt(15),
                 bg=PANEL, fg=DIM).pack(side="left", padx=8)
        bottom = tk.Frame(left, bg=PANEL)
        bottom.pack(side="bottom", fill="x", padx=10, pady=(2, 8))
        self.count_var = tk.StringVar(value="0 câu")
        tk.Label(bottom, textvariable=self.count_var, font=self.f_vt(15),
                 bg=PANEL, fg=DIM).pack(side="left")
        tk.Button(bottom, text="DÁN SCRIPT MỚI", font=self.f_vt(15),
                  bg=PANEL2, fg=WHITE, activebackground=BORDER,
                  activeforeground=WHITE, highlightbackground=PURPLE,
                  highlightthickness=1, bd=0, padx=12, pady=2,
                  command=self._paste_script).pack(side="right")
        txt_wrap = tk.Frame(left, bg=PANEL2, highlightbackground=BORDER,
                            highlightthickness=1)
        txt_wrap.pack(fill="both", expand=True, padx=10, pady=4)
        self.gutter = tk.Text(txt_wrap, width=4, font=self.f_vt(14), bg=PANEL2,
                              fg=CYAN, bd=0, highlightthickness=0, state="disabled",
                              wrap="none")
        self.gutter.pack(side="left", fill="y")
        self.txt = tk.Text(txt_wrap, font=self.f_vt(15), bg=PANEL2, fg=WHITE,
                           insertbackground=GREEN, bd=0, highlightthickness=0,
                           wrap="word", undo=True, padx=6, pady=4)
        self.txt.pack(side="left", fill="both", expand=True)
        self.txt.bind("<<Modified>>", self._on_text_changed)
        self.txt.insert("1.0",
                        "Anthropic vừa đánh bại GPT-6.\n"
                        "Rồi còn cắt giá.\n"
                        "Đây là Claude Fable 5.2.\n"
                        "Sinh ra để viết code, suy luận, và làm agent chạy hàng giờ.")
        self.txt.edit_modified(False)

        # ---- phai ----
        right = tk.Frame(mid, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        # HANH DONG (trang thai + nut TAO GIONG): ghim xuong DAY cot phai
        # va pack TRUOC TIEN — khong bao gio bi cac tang tren day ra khoi
        # cua so (loi tran chieu cao tren Windows o v2.1/v2.1.1).
        act = tk.Frame(right, bg=BG)
        act.pack(side="bottom", fill="x", pady=(8, 0))
        # TRANG THAI + thanh tien trinh: TREN nut, luon nhin thay
        srow = tk.Frame(act, bg=BG)
        srow.pack(fill="x")
        tk.Label(srow, text="TRẠNG THÁI:", font=self.f_vt(16, True),
                 bg=BG, fg=CYAN).pack(side="left")
        self.status_var = tk.StringVar(value="Sẵn sàng.")
        tk.Label(srow, textvariable=self.status_var, font=self.f_vt(16),
                 bg=BG, fg=YELLOW, wraplength=470, justify="left").pack(
                     side="left", padx=(6, 0))
        self.bar_cv = tk.Canvas(act, height=10, bg="#28283F",
                                highlightthickness=0)
        self.bar_cv.pack(fill="x", pady=(3, 0))
        self.bar_rect = self.bar_cv.create_rectangle(0, 0, 0, 10, fill=GREEN,
                                                     outline="")

        brow = tk.Frame(act, bg=BG)
        brow.pack(fill="x", pady=(6, 0))
        self.gen_btn = tk.Button(brow, text="▶  TẠO GIỌNG", font=self.f_vt(21, True),
                                 bg=GREEN, fg="#0F0F19", activebackground=GREEN,
                                 activeforeground="#0F0F19", highlightbackground=GREEN,
                                 highlightthickness=2, bd=0, pady=5,
                                 command=self._generate)
        self.gen_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))
        self.cancel_btn = tk.Button(brow, text="HỦY / LÀM LẠI", font=self.f_vt(16, True),
                                    bg=REDBG, fg=WHITE, activebackground=REDBG,
                                    activeforeground=WHITE,
                                    highlightbackground="#DC5A5A",
                                    highlightthickness=2, bd=0, pady=5, padx=10,
                                    command=self._cancel_or_reset)
        self.cancel_btn.pack(side="left")
        t1 = self._panel(right)
        t1.pack(fill="both", expand=True)
        h1 = tk.Frame(t1, bg=PANEL)
        h1.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(h1, text="TẦNG 1 — CHỌN GIỌNG (50 GIỌNG)",
                 font=self.f_vt(17, True), bg=PANEL, fg=WHITE).pack(side="left", padx=4)
        # khung cuon danh sach giong
        list_wrap = tk.Frame(t1, bg=PANEL)
        list_wrap.pack(fill="both", expand=True, padx=6, pady=(2, 6))
        self.vcanvas = tk.Canvas(list_wrap, bg=PANEL, highlightthickness=0,
                                 height=130)
        vsb = tk.Scrollbar(list_wrap, orient="vertical",
                           command=self.vcanvas.yview)
        self.vcanvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.vcanvas.pack(side="left", fill="both", expand=True)
        self.vinner = tk.Frame(self.vcanvas, bg=PANEL)
        self.vwin = self.vcanvas.create_window((0, 0), window=self.vinner,
                                               anchor="nw")
        self.vinner.bind("<Configure>", lambda e: self.vcanvas.configure(
            scrollregion=self.vcanvas.bbox("all")))
        self.vcanvas.bind("<Configure>", lambda e: self.vcanvas.itemconfig(
            self.vwin, width=e.width))
        self.vcanvas.bind("<Enter>", lambda e: self.vcanvas.bind_all(
            "<MouseWheel>", self._on_wheel))
        self.vcanvas.bind("<Leave>", lambda e: self.vcanvas.unbind_all(
            "<MouseWheel>"))
        self.rows = {}
        last_group = None
        for v in engines.VOICES:
            if v["group"] != last_group:
                last_group = v["group"]
                tk.Label(self.vinner, text=last_group,
                         font=self.f_vt(14, True), bg=PANEL,
                         fg=GROUPCOL.get(last_group, WHITE)).pack(
                             anchor="w", padx=6, pady=(6, 1))
            rowf = tk.Frame(self.vinner, bg=PANEL)
            rowf.pack(fill="x", padx=2, pady=0)
            bar = tk.Frame(rowf, bg=PANEL, width=4)
            bar.pack(side="left", fill="y")
            rb = tk.Radiobutton(rowf, variable=self.voice_var, value=v["id"],
                                bg=PANEL, activebackground=PANEL,
                                selectcolor=PANEL2, highlightthickness=0, bd=0,
                                command=self._highlight_rows)
            rb.pack(side="left")
            tk.Label(rowf, text=v["name"], font=self.f_vt(16),
                     bg=PANEL, fg=WHITE).pack(side="left")
            tk.Button(rowf, text="▶ NGHE 5s", font=self.f_vt(12),
                      bg=BLUE, fg=WHITE, activebackground=BLUE,
                      activeforeground=WHITE, bd=0, padx=7, pady=0,
                      command=lambda vid=v["id"]: self._preview(vid)
                      ).pack(side="right", padx=4, pady=1)
            tk.Label(rowf, text=v["tag"], font=self.f_vt(12),
                     bg=PANEL, fg=DIM).pack(side="right", padx=2)
            self.rows[v["id"]] = (rowf, bar)

        t2 = self._panel(right)
        t2.pack(fill="x", pady=(8, 0))
        h2 = tk.Frame(t2, bg=PANEL)
        h2.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(h2, text="TẦNG 2 — CHỈNH TÔNG", font=self.f_vt(17, True),
                 bg=PANEL, fg=WHITE).pack(side="left", padx=4)
        self.speed_var = tk.DoubleVar(value=125)
        self.pitch_var = tk.DoubleVar(value=100)
        self.pause_var = tk.DoubleVar(value=35)
        self._slider(t2, "TỐC ĐỘ", self.speed_var, 80, 150,
                     lambda v: "%.2fx" % (v / 100.0))
        self._slider(t2, "CAO ĐỘ", self.pitch_var, 85, 115,
                     lambda v: "%.2fx" % (v / 100.0))
        self._slider(t2, "NGHỈ GIỮA CÂU", self.pause_var, 0, 100,
                     lambda v: "%.2fs" % (v / 100.0))
        cb = tk.Checkbutton(t2, text="Tự nhấn chữ *bọc sao* trong script",
                            variable=self.emph_var, font=self.f_vt(14),
                            bg=PANEL, fg=WHITE, activebackground=PANEL,
                            activeforeground=WHITE, selectcolor=PANEL2,
                            highlightthickness=0, bd=0)
        cb.pack(anchor="w", padx=8, pady=(1, 5))

        self._highlight_rows()

    def _on_wheel(self, event):
        try:
            self.vcanvas.yview_scroll(int(-event.delta / 120), "units")
        except Exception:
            pass

    def _slider(self, parent, label, var, lo, hi, fmt):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=10, pady=1)
        tk.Label(row, text=label, font=self.f_vt(15), bg=PANEL,
                 fg=WHITE, width=14, anchor="w").pack(side="left")
        val = tk.Label(row, text=fmt(var.get()), font=self.f_vt(15),
                       bg=PANEL, fg=YELLOW, width=7)
        val.pack(side="right")
        sc = tk.Scale(row, variable=var, from_=lo, to=hi, resolution=1,
                      orient="horizontal", showvalue=False, bg=PANEL,
                      fg=WHITE, troughcolor="#2D2D4B", highlightthickness=0,
                      bd=0, sliderrelief="flat", activebackground=PURPLE,
                      length=180,
                      command=lambda v, val=val, fmt=fmt: val.config(
                          text=fmt(float(v))))
        sc.pack(side="left", expand=True, fill="x", padx=6)
        return sc

    # ------------------------------------------------------------------ text
    def _lines(self):
        raw = self.txt.get("1.0", "end")
        return [ln.strip() for ln in raw.splitlines() if ln.strip()]

    def _update_count(self):
        n = len(self._lines())
        total_lines = int(self.txt.index("end-1c").split(".")[0])
        self.count_var.set("%d câu • mỗi dòng 1 câu" % n)
        self.gutter.config(state="normal")
        self.gutter.delete("1.0", "end")
        self.gutter.insert("1.0", "\n".join(str(i) for i in range(1, total_lines + 1)))
        self.gutter.config(state="disabled")

    def _on_text_changed(self, _evt=None):
        if self.txt.edit_modified():
            self.txt.edit_modified(False)
            self._update_count()

    def _paste_script(self):
        try:
            data = self.root.clipboard_get()
        except Exception:
            messagebox.showwarning(
                "Chưa có gì để dán",
                "Chưa thấy đoạn chữ nào trong clipboard. Hãy copy script Rio "
                "gửi trước (bôi đen đoạn chữ rồi Ctrl+C), rồi bấm lại nút này.")
            return
        if not data.strip():
            return
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", data.strip())
        self.txt.edit_modified(True)
        self._on_text_changed()

    def _highlight_rows(self):
        sel = self.voice_var.get()
        for vid, (rowf, bar) in self.rows.items():
            on = vid == sel
            rowf.config(bg=ROWSEL if on else PANEL)
            bar.config(bg=GREEN if on else PANEL)
            for child in rowf.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=ROWSEL if on else PANEL)

    # ------------------------------------------------------------------ chay viec
    def _tone(self):
        return (self.speed_var.get() / 100.0,
                self.pitch_var.get() / 100.0,
                self.pause_var.get() / 100.0)

    def _set_progress(self, done, total):
        w = self.bar_cv.winfo_width()
        frac = (done / total) if total else 0
        self.bar_cv.coords(self.bar_rect, 0, 0, max(0, w * frac), 10)

    def _preview(self, voice_id):
        if self.busy:
            return
        self.busy = True
        self.cancel_event.clear()
        self.gen_started = time.time()
        self.last_progress = (0, 1, "Đang tạo câu mẫu...")
        name = engines.VOICE_BY_ID[voice_id]["name"]
        self.status_var.set("Đang tạo câu mẫu bằng giọng %s..." % name)

        def work():
            try:
                speed, pitch, _pause = self._tone()
                path = engines.synthesize_preview(
                    voice_id, speed=speed, pitch_mult=pitch,
                    emphasis_on=self.emph_var.get(), outdir=OUT_DIR,
                    cancel_event=self.cancel_event)
                self.msg_q.put(("preview_done", path))
            except engines.GenerationCancelled as e:
                self.msg_q.put(("cancelled", str(e)))
            except Exception as e:  # noqa: BLE001
                engines.log("LỖI nghe thử: %s" % e)
                self.msg_q.put(("error", str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _generate(self):
        if self.busy:
            return
        lines = self._lines()
        if not lines:
            messagebox.showwarning("Chưa có script",
                                   "Ô script đang trống. Dán script Rio gửi "
                                   "vào trước rồi mới bấm TẠO GIỌNG.")
            return
        self.busy = True
        self.cancel_event.clear()
        self.gen_started = time.time()
        self.last_progress = (0, len(lines), "Đang bắt đầu...")
        self.gen_btn.config(state="disabled")
        self.status_var.set("Đang bắt đầu...")
        self._set_progress(0, len(lines))
        speed, pitch, pause = self._tone()
        voice_id = self.voice_var.get()
        emph = self.emph_var.get()

        def prog(done, total, msg):
            self.msg_q.put(("progress", (done, total, msg)))

        def work():
            try:
                res = engines.synthesize_script(
                    lines, voice_id, speed=speed, pitch_mult=pitch,
                    pause_s=pause, emphasis_on=emph, outdir=OUT_DIR,
                    progress=prog, cancel_event=self.cancel_event)
                self.msg_q.put(("gen_done", res))
            except engines.GenerationCancelled as e:
                self.msg_q.put(("cancelled", str(e)))
            except Exception as e:  # noqa: BLE001
                engines.log("LỖI tạo giọng: %s" % e)
                self.msg_q.put(("error", str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _cancel_or_reset(self):
        if self.busy:
            self.cancel_event.set()
            self.status_var.set("Đang hủy... (chờ đoạn đang đọc dở dừng lại)")
            engines.log("Bro bấm HỦY.")
        else:
            self.cancel_event.clear()
            self.last_progress = (0, 0, "")
            self._set_progress(0, 1)
            self.status_var.set("Sẵn sàng.")

    def _finish_busy(self):
        self.busy = False
        self.gen_started = None
        self.gen_btn.config(state="normal")

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.msg_q.get_nowait()
                if kind == "progress":
                    self.last_progress = payload
                    _d, _t, msg = payload
                    self.status_var.set(msg)
                    self._set_progress(_d, _t)
                elif kind == "preview_done":
                    self._finish_busy()
                    self.status_var.set("Đang phát câu mẫu... nghe thử nhé.")
                    if not play_file(payload):
                        self.status_var.set(
                            "Đã tạo file nghe thử trong thư mục output — mở ra nghe nhé.")
                elif kind == "gen_done":
                    self._finish_busy()
                    dur = payload["total_duration"]
                    self.res_mp3_var.set("— %d:%04.1f — nghe lại được" % (
                        int(dur // 60), dur % 60))
                    self.res_tim_var.set("— %d câu — mốc từng câu" % payload["count"])
                    self._set_progress(payload["count"], payload["count"])
                    self.status_var.set(
                        "Xong! Gửi Rio 2 file voice.mp3 + timings.json trong "
                        "thư mục output.")
                elif kind == "cancelled":
                    self._finish_busy()
                    self._set_progress(0, 1)
                    self.status_var.set("Đã hủy. Bấm TẠO GIỌNG để làm lại từ đầu.")
                elif kind == "error":
                    self._finish_busy()
                    self._set_progress(0, 1)
                    self.status_var.set("Có lỗi — xem hộp thoại (chi tiết ở output/log.txt).")
                    messagebox.showerror("Voice Studio — có lỗi", payload)
        except queue.Empty:
            pass
        # cap nhat so giay da cho khi dang ban
        if self.busy and self.gen_started:
            _d, _t, msg = self.last_progress
            if msg:
                el = int(time.time() - self.gen_started)
                self.status_var.set("%s (đã chờ %d giây)" % (msg, el))
        self.root.after(200, self._poll_queue)

    def _play_voice(self):
        wav = os.path.join(OUT_DIR, "voice.wav")
        mp3 = os.path.join(OUT_DIR, "voice.mp3")
        target = wav if os.path.isfile(wav) else mp3
        if os.path.isfile(target):
            if not play_file(target):
                self.status_var.set("Mở thư mục output để nghe file voice.")
        else:
            messagebox.showinfo("Chưa có giọng",
                                "Chưa tạo giọng lần nào. Bấm TẠO GIỌNG trước đã.")

    def _open_outdir(self):
        os.makedirs(OUT_DIR, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(OUT_DIR)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", OUT_DIR])
            else:
                subprocess.Popen(["xdg-open", OUT_DIR])
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Không mở được thư mục", str(e))


def main():
    root = tk.Tk()
    VoiceStudioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
