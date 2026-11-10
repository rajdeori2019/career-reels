#!/usr/bin/env python3
"""Hindi/Hinglish transcript with sherpa-onnx Whisper ONNX models, decoded directly with onnxruntime.

Why: sherpa's own recognizer turns each Whisper byte-token into text separately, which breaks
Devanagari. Here we keep token ids and join their raw bytes before decoding to UTF-8.

  python3 hinglish_asr.py MODEL_DIR AUDIO.wav SEGMENTS.json [--lang hi] [--task transcribe]
SEGMENTS.json: [[start, end], ...] in seconds (pause-split, 1-15 s each).
Prints: start-end<TAB>text
"""
import base64, json, sys, wave
from pathlib import Path
import numpy as np
import onnxruntime as ort

SR, N_FFT, HOP, N_FRAMES = 16000, 400, 160, 3000


def mel_filters(n_mels=80, n_fft=N_FFT, sr=SR):
    # Slaney-style mel filterbank (same as librosa.filters.mel(htk=False, norm="slaney"))
    def hz_to_mel(f):
        f = np.atleast_1d(np.asarray(f, float)); m = f / (200.0 / 3)
        log = f >= 1000.0
        m[log] = 15.0 + np.log(f[log] / 1000.0) / (np.log(6.4) / 27.0)
        return m
    def mel_to_hz(m):
        m = np.atleast_1d(np.asarray(m, float)); f = m * (200.0 / 3)
        log = m >= 15.0
        f[log] = 1000.0 * np.exp((np.log(6.4) / 27.0) * (m[log] - 15.0))
        return f
    fftfreqs = np.linspace(0, sr / 2, n_fft // 2 + 1)
    mels = mel_to_hz(np.linspace(hz_to_mel(0.0)[0], hz_to_mel(sr / 2)[0], n_mels + 2))
    fdiff = np.diff(mels); ramps = mels[:, None] - fftfreqs[None, :]
    w = np.zeros((n_mels, len(fftfreqs)))
    for i in range(n_mels):
        lower = -ramps[i] / fdiff[i]; upper = ramps[i + 2] / fdiff[i + 1]
        w[i] = np.maximum(0, np.minimum(lower, upper))
    w *= (2.0 / (mels[2:n_mels + 2] - mels[:n_mels]))[:, None]
    return w


def log_mel(x, n_mels=80):
    x = np.pad(x[:SR * 30], (0, max(0, SR * 30 - len(x))))   # whisper always sees 30 s
    x = np.pad(x, (N_FFT // 2, N_FFT // 2), mode="reflect")
    win = np.hanning(N_FFT + 1)[:-1]
    n = 1 + (len(x) - N_FFT) // HOP
    frames = np.lib.stride_tricks.as_strided(x, (n, N_FFT), (x.strides[0] * HOP, x.strides[0])) * win
    mag = (np.abs(np.fft.rfft(frames, axis=1)) ** 2)[:-1]  # whisper drops the last frame
    mel = mel_filters(n_mels) @ mag.T
    log = np.log10(np.maximum(mel, 1e-10))
    log = np.maximum(log, log.max() - 8.0)
    return ((log + 4.0) / 4.0)[:, :N_FRAMES].astype(np.float32)[None]


class Whisper:
    def __init__(self, d):
        d = Path(d)
        pick = lambda pat: sorted(d.glob(pat))[0]
        enc = next(iter(sorted(d.glob("*encoder.int8.onnx"))), None) or pick("*encoder.onnx")
        dec = next(iter(sorted(d.glob("*decoder.int8.onnx"))), None) or pick("*decoder.onnx")
        so = ort.SessionOptions(); so.intra_op_num_threads = 2
        self.enc = ort.InferenceSession(str(enc), so, providers=["CPUExecutionProvider"])
        self.dec = ort.InferenceSession(str(dec), so, providers=["CPUExecutionProvider"])
        m = self.enc.get_modelmeta().custom_metadata_map
        self.meta = m
        gi = lambda k: int(m[k])
        self.n_layer, self.n_ctx, self.n_state = gi("n_text_layer"), gi("n_text_ctx"), gi("n_text_state")
        self.sot, self.eot = gi("sot"), gi("eot")
        self.transcribe, self.translate, self.no_ts = gi("transcribe"), gi("translate"), gi("no_timestamps")
        codes = m["all_language_codes"].split(","); toks = [int(x) for x in m["all_language_tokens"].split(",")]
        self.lang = dict(zip(codes, toks))
        self.n_mels = int(m.get("n_mels", 80))
        self.tok = {}
        for ln in open(pick("*tokens.txt"), encoding="utf-8"):
            p = ln.rstrip("\n").split()
            if len(p) == 2:
                self.tok[int(p[1])] = base64.b64decode(p[0])
        self.dec_in = [i.name for i in self.dec.get_inputs()]

    def run(self, audio, lang="hi", task="transcribe", max_len=None):
        max_len = max_len or int(len(audio) / SR * 12) + 10      # ~7 tokens per second is plenty
        mel = log_mel(audio.astype(np.float32), self.n_mels)
        ck, cv = self.enc.run(None, {self.enc.get_inputs()[0].name: mel})
        sk = np.zeros((self.n_layer, 1, self.n_ctx, self.n_state), np.float32); sv = sk.copy()
        seq = [self.sot, self.lang[lang], self.transcribe if task == "transcribe" else self.translate, self.no_ts]
        tokens = np.array([seq], np.int64); offset = np.array([0], np.int64); out = []
        for _ in range(max_len):
            feeds = dict(zip(self.dec_in, [tokens, sk, sv, ck, cv, offset]))
            logits, sk, sv = self.dec.run(None, feeds)
            offset = offset + tokens.shape[1]
            nxt = int(np.argmax(logits[0, -1]))
            if nxt == self.eot or nxt >= self.eot: break
            out.append(nxt); tokens = np.array([[nxt]], np.int64)
            if len(out) >= 8 and out[-4:] == out[-8:-4]:      # greedy loop guard
                out = out[:-4]; break
        return b"".join(self.tok.get(i, b"") for i in out).decode("utf-8", errors="replace").strip()


def read_wav(p):
    with wave.open(str(p)) as w:
        sr = w.getframerate(); ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    if sr != SR: sys.exit(f"need 16 kHz mono wav, got {sr} Hz")
    return x


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3: sys.exit(__doc__)
    lang = a[a.index("--lang") + 1] if "--lang" in a else "hi"
    task = a[a.index("--task") + 1] if "--task" in a else "transcribe"
    m = Whisper(a[0]); x = read_wav(a[1]); segs = json.loads(Path(a[2]).read_text())
    for s, e in segs:
        seg = x[int(max(0, s - 0.1) * SR):int((e + 0.1) * SR)]
        print(f"{s:.2f}-{e:.2f}\t{m.run(seg, lang, task)}", flush=True)
