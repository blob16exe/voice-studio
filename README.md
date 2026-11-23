# Voice Studio

**Type a script — get a finished voiceover.** Voice Studio is a free Windows desktop app that turns a text script into narration audio for faceless videos, plus a `timings.json` file with the exact start/end time of every line, so your video cuts land precisely on the words.

This is the tool behind the narration on the [Blob](https://www.youtube.com/@blob16exe) YouTube channel.

![status](https://img.shields.io/badge/platform-Windows%2010%2F11-blue) ![python](https://img.shields.io/badge/python-3.10--3.12-blue) ![price](https://img.shields.io/badge/price-free-green)

## Download

Grab the ready-to-run package from the [**Releases**](https://github.com/blob16exe/voice-studio/releases) page (`voice-studio-public.zip`, includes the offline Kokoro model), unzip it anywhere, and double-click `run.bat`. No installer, no account, no API key.

## Voices included — 20 voices, 4 groups

| Group | Voices | Needs internet? |
|---|---|---|
| Vietnamese — Microsoft Edge | Nam Minh, Hoai My | Yes (Microsoft's online voices) |
| English — Microsoft Edge | Guy, Andrew, Brian, Eric, Christopher, Jenny | Yes |
| English — Kokoro | am_adam, am_michael, bm_george, bm_lewis, af_bella, af_sarah, af_nicole, af_sky, af, bf_emma, bf_isabella (11 total) | **No — runs fully offline on your PC** |
| Windows SAPI | David / Zira (built into Windows) | No |

## What it does

- **Line-by-line generation** — paste a script (one sentence per line), pick a voice, hit generate. Each line is synthesized separately, so fixing one sentence never means redoing the whole read.
- **timings.json export** — every line's start and end timestamp, ready to cut video against.
- **Speed, pitch and pause controls**, plus `*emphasis*` markup: wrap words in asterisks to have them read with stress.
- **5-second voice preview** for every voice before you commit.
- **Runs on your own machine** — your scripts never leave your PC (Edge voices are the exception: the text of each line is sent to Microsoft's voice service, like any online TTS).

## Requirements

- Windows 10/11
- Python 3.10–3.12 (tick **"Add python.exe to PATH"** when installing) — `run.bat` installs the needed Python packages automatically on first launch
- [ffmpeg](https://ffmpeg.org/) on PATH (e.g. `winget install Gyan.FFmpeg`)
- Internet for the Edge voices and for the first-launch package install; Kokoro voices then work fully offline

## Run from source

```bat
git clone https://github.com/blob16exe/voice-studio.git
cd voice-studio
run.bat
```

Note: the Kokoro model file (`models/kokoro-en-v0_19/model.onnx`, ~330 MB) is **not** in this repository because of GitHub's file-size limit. It is included in the release zip. If you clone the source, download the release zip and copy the `models` folder over, or fetch the `kokoro-en-v0_19` model from the sherpa-onnx model zoo.

A Vietnamese user guide is included as `README-HUONG-DAN.md`.

## Credits

- Voice synthesis: [edge-tts](https://github.com/rany2/edge-tts) (Microsoft Edge online voices) and [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) run locally via [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx); SAPI via pyttsx3.
- The Kokoro model files are distributed under their own license — see `models/kokoro-en-v0_19/LICENSE`.
- Built by [Blob](https://blob.blob16exe.workers.dev/) — a desk robot built on ESP32, drifting through the internet and making videos about AI.
