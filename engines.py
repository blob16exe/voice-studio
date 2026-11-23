# -*- coding: utf-8 -*-
"""
Voice Studio v2 - engine sinh giong (khong phu thuoc giao dien).

Thay doi lon so voi v1:
- Giong Edge goi qua TIEN TRINH CON (python -m edge_tts) co TIMEOUT 40s/cau,
  tu thu lai toi da 3 lan. Treo la bi giet + bao loi ro rang, khong dung im nua.
  (Day cung la duong file .bat sinh giong Reel 26 da chay tot tren laptop Minh.)
- Ho tro HUY giua chung (cancel_event) o moi engine.
- Ghi nhat ky vao output/log.txt (set_log_path).
- Mo khoa du 11 giong Kokoro + them 4 giong Edge Anh (Guy/Andrew/Brian/Eric).

Quy trinh: sinh TUNG CAU rieng -> do thoi luong that -> chen khoang lang ->
ghep thanh voice.wav + voice.mp3 -> ghi timings.json.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KOKORO_DIR = os.path.join(BASE_DIR, "models", "kokoro-en-v0_19")
TARGET_SR = 24000  # moi giong deu chuan hoa ve 24kHz mono truoc khi ghep
EDGE_TIMEOUT_S = int(os.environ.get("VS_EDGE_TIMEOUT", "40"))
EDGE_TRIES = int(os.environ.get("VS_EDGE_TRIES", "3"))


class GenerationCancelled(Exception):
    """Nguoi dung bam HUY giua chung."""


# ---------------------------------------------------------------- nhat ky
_LOG_PATH = None


def set_log_path(path):
    global _LOG_PATH
    _LOG_PATH = path


def log(msg):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), msg)
    try:
        print(line, flush=True)
    except Exception:
        pass
    if _LOG_PATH:
        try:
            os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
            with open(_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def _check_cancel(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise GenerationCancelled("Đã hủy theo yêu cầu của bro.")


# ---------------------------------------------------------------- danh sach giong
# group: nhom hien thi tren giao dien. sample: cau mau cho nut NGHE 5s.
_VI_SAMPLE = "Xin chào, tôi là Blob. Hôm nay AI lại làm ra trò gì nữa đây?"
_EN_SAMPLE = ("Anthropic just shipped a model that writes code for hours. "
              "And it costs less than lunch.")

VOICES = [
    # --- Viet, Edge ---
    {"id": "edge_namminh", "name": "Edge — Nam Minh", "tag": "NAM",
     "group": "VIỆT — EDGE (CẦN MẠNG)",
     "engine": "edge", "voice": "vi-VN-NamMinhNeural", "lang": "vi",
     "sample": _VI_SAMPLE},
    {"id": "edge_hoaimy", "name": "Edge — Hoài My", "tag": "NỮ",
     "group": "VIỆT — EDGE (CẦN MẠNG)",
     "engine": "edge", "voice": "vi-VN-HoaiMyNeural", "lang": "vi",
     "sample": _VI_SAMPLE},
    # --- Kokoro: du 11 giong trong model v0_19 ---
    {"id": "kokoro_amadam", "name": "Kokoro — am_adam", "tag": "GIỌNG KÊNH",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 5, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_ammichael", "name": "Kokoro — am_michael", "tag": "NAM MỸ",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 6, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_bmgeorge", "name": "Kokoro — bm_george", "tag": "NAM ANH",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 9, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_bmlewis", "name": "Kokoro — bm_lewis", "tag": "NAM ANH",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 10, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_afbella", "name": "Kokoro — af_bella", "tag": "NỮ MỸ",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 1, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_afsarah", "name": "Kokoro — af_sarah", "tag": "NỮ MỸ",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 3, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_afnicole", "name": "Kokoro — af_nicole", "tag": "NỮ MỸ",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 2, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_afsky", "name": "Kokoro — af_sky", "tag": "NỮ MỸ",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 4, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_af", "name": "Kokoro — af", "tag": "NỮ MỸ",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 0, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_bfemma", "name": "Kokoro — bf_emma", "tag": "NỮ ANH",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 7, "lang": "en", "sample": _EN_SAMPLE},
    {"id": "kokoro_bfisabella", "name": "Kokoro — bf_isabella", "tag": "NỮ ANH",
     "group": "ANH — KOKORO (CHẠY TRÊN MÁY, THƯƠNG MẠI OK)",
     "engine": "kokoro", "sid": 8, "lang": "en", "sample": _EN_SAMPLE},
    # --- Anh, Edge ---
    {"id": "edge_guy", "name": "Edge — Guy", "tag": "NAM • LỬA",
     "group": "ANH — EDGE (CẦN MẠNG)",
     "engine": "edge", "voice": "en-US-GuyNeural", "lang": "en",
     "sample": _EN_SAMPLE},
    {"id": "edge_andrew", "name": "Edge — Andrew", "tag": "NAM • ẤM",
     "group": "ANH — EDGE (CẦN MẠNG)",
     "engine": "edge", "voice": "en-US-AndrewNeural", "lang": "en",
     "sample": _EN_SAMPLE},
    {"id": "edge_brian", "name": "Edge — Brian", "tag": "NAM • THÂN THIỆN",
     "group": "ANH — EDGE (CẦN MẠNG)",
     "engine": "edge", "voice": "en-US-BrianNeural", "lang": "en",
     "sample": _EN_SAMPLE},
    {"id": "edge_eric", "name": "Edge — Eric", "tag": "NAM • TIN TỨC",
     "group": "ANH — EDGE (CẦN MẠNG)",
     "engine": "edge", "voice": "en-US-EricNeural", "lang": "en",
     "sample": _EN_SAMPLE},
    {"id": "edge_christopher", "name": "Edge — Christopher", "tag": "NAM",
     "group": "ANH — EDGE (CẦN MẠNG)",
     "engine": "edge", "voice": "en-US-ChristopherNeural", "lang": "en",
     "sample": _EN_SAMPLE},
    {"id": "edge_jenny", "name": "Edge — Jenny", "tag": "NỮ",
     "group": "ANH — EDGE (CẦN MẠNG)",
     "engine": "edge", "voice": "en-US-JennyNeural", "lang": "en",
     "sample": _EN_SAMPLE},
    # --- SAPI ---
    {"id": "sapi_david_zira", "name": "SAPI — David / Zira", "tag": "MÁY BRO",
     "group": "MÁY BRO — SAPI (GIỌNG SẴN TRONG WINDOWS)",
     "engine": "sapi", "lang": "en", "sample": _EN_SAMPLE},
]
VOICE_BY_ID = {v["id"]: v for v in VOICES}


def ffmpeg_path():
    return shutil.which("ffmpeg")


def require_ffmpeg():
    if not ffmpeg_path():
        raise RuntimeError(
            "Chưa thấy ffmpeg trên máy này. ffmpeg là phần mềm ghép/xuất âm thanh "
            "mà tool bắt buộc phải có. Cách cài: xem file README-HUONG-DAN.md, "
            "mục 'Nếu tool báo thiếu ffmpeg'."
        )


# ---------------------------------------------------------------- chia doan nhan manh
_EMPH_RE = re.compile(r"\*([^*]+)\*")


def parse_segments(text, emphasis_on):
    if not emphasis_on:
        return [(_EMPH_RE.sub(r"\1", text), False)]
    segs = []
    pos = 0
    for m in _EMPH_RE.finditer(text):
        if m.start() > pos:
            segs.append((text[pos:m.start()], False))
        segs.append((m.group(1), True))
        pos = m.end()
    if pos < len(text):
        segs.append((text[pos:], False))
    segs = [(s, e) for (s, e) in segs if s.strip()]
    return segs or [(_EMPH_RE.sub(r"\1", text), False)]


def clean_text(text):
    return _EMPH_RE.sub(r"\1", text)


# ---------------------------------------------------------------- tien ich am thanh
def _run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError("Lệnh xử lý âm thanh lỗi: " + " ".join(cmd[:2]) +
                           "\n" + r.stderr.decode("utf-8", "ignore")[-400:])
    return r


def _normalize_to_24k(src_wav, dst_wav):
    _run([ffmpeg_path(), "-y", "-v", "error", "-i", src_wav,
          "-ar", str(TARGET_SR), "-ac", "1", dst_wav])


def _pitch_shift(wav_in, wav_out, mult):
    if abs(mult - 1.0) < 0.005:
        shutil.copyfile(wav_in, wav_out)
        return
    try:
        _run([ffmpeg_path(), "-y", "-v", "error", "-i", wav_in,
              "-af", "asetrate=%d,aresample=%d,atempo=%.5f" % (
                  int(TARGET_SR * mult), TARGET_SR, 1.0 / mult),
              "-ar", str(TARGET_SR), "-ac", "1", wav_out])
    except Exception:
        shutil.copyfile(wav_in, wav_out)


def _read_wav(path):
    import numpy as np
    import soundfile as sf
    data, sr = sf.read(path, dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data[:, 0]
    if sr != TARGET_SR:
        n = int(round(len(data) * TARGET_SR / sr))
        data = np.interp(np.linspace(0, len(data) - 1, n),
                         np.arange(len(data)), data).astype(np.float32)
    return data


# ---------------------------------------------------------------- edge tts (tien trinh con + timeout)
def _edge_run_once(text, voice, rate_pct, pitch_hz, mp3_path, cancel_event):
    """1 lan goi edge-tts bang tien trinh con. Tra ve (ok, thong diep loi)."""
    with tempfile.TemporaryDirectory() as td:
        txt = os.path.join(td, "seg.txt")
        with open(txt, "w", encoding="utf-8") as f:
            f.write(text)
        cmd = [sys.executable, "-m", "edge_tts",
               "--voice", voice,
               "--rate", "%+d%%" % int(round(rate_pct)),
               "--pitch", "%+dHz" % int(round(pitch_hz)),
               "--file", txt,
               "--write-media", mp3_path]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        t0 = time.time()
        while True:
            try:
                _out, err = proc.communicate(timeout=1.0)
                break
            except subprocess.TimeoutExpired:
                if cancel_event is not None and cancel_event.is_set():
                    proc.kill()
                    raise GenerationCancelled("Đã hủy theo yêu cầu của bro.")
                if time.time() - t0 > EDGE_TIMEOUT_S:
                    proc.kill()
                    try:
                        _out, err = proc.communicate(timeout=5)
                    except Exception:
                        err = b""
                    return False, "quá %d giây không trả tiếng (bị treo)" % EDGE_TIMEOUT_S
        if proc.returncode != 0:
            msg = (err or b"").decode("utf-8", "ignore").strip()[-300:]
            return False, "edge-tts báo lỗi: " + (msg or "không rõ")
        if not os.path.isfile(mp3_path) or os.path.getsize(mp3_path) == 0:
            return False, "edge-tts trả về file rỗng (Microsoft hay chập chờn)"
        return True, ""


def synth_edge_segment(text, voice, speed, pitch_hz, out_wav, cancel_event=None):
    """Sinh 1 doan bang Edge TTS -> wav 24k. Co timeout + thu lai 3 lan."""
    require_ffmpeg()
    rate_pct = (speed - 1.0) * 100.0
    last_err = ""
    with tempfile.TemporaryDirectory() as td:
        mp3 = os.path.join(td, "seg.mp3")
        for attempt in range(1, EDGE_TRIES + 1):
            _check_cancel(cancel_event)
            log("Edge: gọi giọng %s, lần %d/%d, chữ: %s..." %
                (voice, attempt, EDGE_TRIES, text[:40]))
            ok, err = _edge_run_once(text, voice, rate_pct, pitch_hz, mp3,
                                     cancel_event)
            if ok:
                _normalize_to_24k(mp3, out_wav)
                log("Edge: xong 1 đoạn.")
                return
            last_err = err
            log("Edge: lần %d hỏng (%s)" % (attempt, err))
            if attempt < EDGE_TRIES:
                time.sleep(1.5)
    raise RuntimeError(
        "Giọng Edge không đọc được sau %d lần thử. Lỗi cuối: %s. "
        "Thường là do mạng chập chờn hoặc Microsoft bóp kết nối tạm thời. "
        "Cách xử lý: kiểm tra mạng rồi bấm TẠO GIỌNG lại, hoặc đổi sang giọng "
        "Kokoro (chạy ngay trên máy, không cần mạng)." % (EDGE_TRIES, last_err))


# ---------------------------------------------------------------- kokoro (sherpa-onnx)
_kokoro_tts = None


def _get_kokoro():
    global _kokoro_tts
    if _kokoro_tts is not None:
        return _kokoro_tts
    import sherpa_onnx
    d = KOKORO_DIR
    if not os.path.isfile(os.path.join(d, "model.onnx")):
        raise RuntimeError("Thiếu file model Kokoro ở thư mục models/kokoro-en-v0_19. "
                           "Hãy giải nén lại trọn gói Voice Studio.")
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=os.path.join(d, "model.onnx"),
                voices=os.path.join(d, "voices.bin"),
                tokens=os.path.join(d, "tokens.txt"),
                data_dir=os.path.join(d, "espeak-ng-data"),
            ),
            num_threads=4, debug=False, provider="cpu",
        ),
        max_num_sentences=10,
    )
    _kokoro_tts = sherpa_onnx.OfflineTts(cfg)
    return _kokoro_tts


def synth_kokoro_segment(text, sid, speed, pitch_mult, out_wav):
    import numpy as np
    import soundfile as sf
    tts = _get_kokoro()
    audio = tts.generate(text, sid=sid, speed=float(speed))
    samples = np.array(audio.samples, dtype=np.float32)
    if len(samples) == 0:
        raise RuntimeError("Kokoro không tạo được tiếng cho đoạn này.")
    if audio.sample_rate != TARGET_SR:
        n = int(round(len(samples) * TARGET_SR / audio.sample_rate))
        samples = np.interp(np.linspace(0, len(samples) - 1, n),
                            np.arange(len(samples)), samples).astype(np.float32)
    if abs(pitch_mult - 1.0) >= 0.005 and ffmpeg_path():
        with tempfile.TemporaryDirectory() as td:
            raw = os.path.join(td, "raw.wav")
            sf.write(raw, samples, TARGET_SR)
            _pitch_shift(raw, out_wav, pitch_mult)
    else:
        sf.write(out_wav, samples, TARGET_SR)


# ---------------------------------------------------------------- SAPI (pyttsx3, Windows)
def synth_sapi_segment(text, speed, out_wav):
    if not sys.platform.startswith("win"):
        raise RuntimeError("Giọng SAPI chỉ chạy trên Windows (laptop của bro).")
    import pyttsx3
    eng = pyttsx3.init()
    try:
        voices = eng.getProperty("voices") or []
        chosen = None
        for want in ("david", "zira"):
            for v in voices:
                if want in (getattr(v, "name", "") or "").lower():
                    chosen = v
                    break
            if chosen:
                break
        if chosen:
            eng.setProperty("voice", chosen.id)
        eng.setProperty("rate", int(200 * float(speed)))
        with tempfile.TemporaryDirectory() as td:
            raw = os.path.join(td, "sapi.wav")
            eng.save_to_file(text, raw)
            eng.runAndWait()
            if not os.path.isfile(raw):
                raise RuntimeError("SAPI không tạo được file tiếng.")
            if ffmpeg_path():
                _normalize_to_24k(raw, out_wav)
            else:
                shutil.copyfile(raw, out_wav)
    finally:
        try:
            eng.stop()
        except Exception:
            pass


def _write_result(full, timings, outdir, progress, total):
    """Ghi voice.wav + voice.mp3 + timings.json (dung chung moi engine)."""
    import numpy as np  # noqa: F401  (giu import cho cac caller cu)
    import soundfile as sf
    wav_out = os.path.join(outdir, "voice.wav")
    sf.write(wav_out, full, TARGET_SR)
    total_dur = len(full) / TARGET_SR
    mp3_out = os.path.join(outdir, "voice.mp3")
    if ffmpeg_path():
        _run([ffmpeg_path(), "-y", "-v", "error", "-i", wav_out,
              "-codec:a", "libmp3lame", "-b:a", "128k", mp3_out])
    else:
        raise RuntimeError(
            "Đã tạo voice.wav nhưng chưa xuất được voice.mp3 vì máy thiếu "
            "ffmpeg. Cài ffmpeg (xem README-HUONG-DAN.md) rồi bấm TẠO GIỌNG "
            "lại.")
    with open(os.path.join(outdir, "timings.json"), "w",
              encoding="utf-8") as f:
        json.dump(timings, f, ensure_ascii=False, indent=2)
    if progress:
        progress(total, total, "Xong!")
    log("TẠO GIỌNG XONG: %.2f giây, %d câu." % (total_dur, total))
    return {"wav": wav_out, "mp3": mp3_out, "timings": timings,
            "total_duration": total_dur, "count": total}


# ---------------------------------------------------------------- sinh 1 cau (nhieu doan)
def _synth_line(line, voice, speed, pitch_mult, emphasis_on, td, cancel_event=None):
    import numpy as np
    import soundfile as sf
    segs = parse_segments(line, emphasis_on)
    parts = []
    for j, (seg_text, emph) in enumerate(segs):
        _check_cancel(cancel_event)
        seg_wav = os.path.join(td, "seg_%d.wav" % j)
        engine = voice["engine"]
        if engine == "edge":
            hz = (pitch_mult - 1.0) * 200.0 + (20.0 if emph else 0.0)
            synth_edge_segment(seg_text, voice["voice"], speed, hz, seg_wav,
                               cancel_event=cancel_event)
        elif engine == "kokoro":
            seg_pitch = pitch_mult * (1.06 if emph else 1.0)
            synth_kokoro_segment(seg_text, voice["sid"], speed, seg_pitch, seg_wav)
        elif engine == "sapi":
            synth_sapi_segment(seg_text, speed * (1.1 if emph else 1.0), seg_wav)
        else:
            raise RuntimeError("Engine lạ: " + engine)
        parts.append(_read_wav(seg_wav))
    merged = np.concatenate(parts) if len(parts) > 1 else parts[0]
    line_wav = os.path.join(td, "line.wav")
    sf.write(line_wav, merged, TARGET_SR)
    return line_wav, clean_text(line)


# ---------------------------------------------------------------- quy trinh chinh
def synthesize_script(lines, voice_id, speed=1.25, pitch_mult=1.0, pause_s=0.35,
                      emphasis_on=True, outdir=None, progress=None,
                      cancel_event=None):
    import numpy as np
    import soundfile as sf
    voice = VOICE_BY_ID[voice_id]
    lines = [ln.strip() for ln in lines if ln and ln.strip()]
    if not lines:
        raise RuntimeError("Script trống — hãy dán ít nhất 1 câu.")
    outdir = outdir or os.path.join(BASE_DIR, "output")
    os.makedirs(outdir, exist_ok=True)
    log("Bắt đầu tạo giọng: %s, %d câu, tốc độ %.2fx." %
        (voice["name"], len(lines), speed))
    gap = np.zeros(int(round(pause_s * TARGET_SR)), dtype=np.float32)
    chunks, timings = [], []
    cursor = 0.0
    total = len(lines)
    with tempfile.TemporaryDirectory() as td:
        for i, line in enumerate(lines, start=1):
            _check_cancel(cancel_event)
            if progress:
                progress(i - 1, total, "Đang đọc câu %d/%d..." % (i, total))
            line_dir = os.path.join(td, "l%d" % i)
            os.makedirs(line_dir, exist_ok=True)
            line_wav, text_clean = _synth_line(
                line, voice, speed, pitch_mult, emphasis_on, line_dir,
                cancel_event=cancel_event)
            samples = _read_wav(line_wav)
            dur = len(samples) / TARGET_SR
            timings.append({"i": i, "text": text_clean,
                            "start": round(cursor, 3),
                            "end": round(cursor + dur, 3)})
            chunks.append(samples)
            cursor += dur
            if i < total:
                chunks.append(gap)
                cursor += pause_s
            log("Câu %d/%d xong: %.2f giây." % (i, total, dur))
    _check_cancel(cancel_event)
    full = np.concatenate(chunks)
    return _write_result(full, timings, outdir, progress, total)


def synthesize_preview(voice_id, speed=1.25, pitch_mult=1.0, emphasis_on=True,
                       outdir=None, cancel_event=None):
    import soundfile as sf
    voice = VOICE_BY_ID[voice_id]
    outdir = outdir or os.path.join(BASE_DIR, "output")
    os.makedirs(outdir, exist_ok=True)
    log("Nghe thử giọng: %s" % voice["name"])
    with tempfile.TemporaryDirectory() as td:
        line_wav, _ = _synth_line(voice["sample"], voice, speed, pitch_mult,
                                  emphasis_on, td, cancel_event=cancel_event)
        samples = _read_wav(line_wav)
    out = os.path.join(outdir, "preview_%s.wav" % voice_id)
    sf.write(out, samples, TARGET_SR)
    return out
