# Career Reels

Prafulla's personal reel-editing system: record on the phone, drop the video in `Raw Videos`, and Claude edits it into a 1080x1920 reel (Hinglish captions, text behind the speaker, Energy v3 graphics, B-roll, grade, SFX, loudness).

Public repo (no keys, no videos). Separate from every other project.

**New chat? Read [`CLAUDE.md`](CLAUDE.md) first, then follow [`docs/Daily-Reel-SOP.md`](docs/Daily-Reel-SOP.md). GitHub is updated after every render.**

## Layout
| Path | What |
|---|---|
| `tools/career_reel.py` | Engine: `cut`, `matte`, `stills`, `render`, `join` |
| `tools/career_styles2.py` | Round-2 + Energy v3 styles (loaded by the engine) |
| `tools/hinglish_asr.py` | Hinglish transcript (sherpa-onnx Whisper small, decoded with onnxruntime) |
| `tools/repo_sync.py` | Copies engine, templates, reel specs and docs into this repo and logs the reel (SOP step 13) |
| `tools/broll.py` | B-roll finder (Pexels + Pixabay; keys from `broll.env`, never committed) |
| `tools/templates/approved_energy_v3.json` | Default look (approved 10 Nov 2026) |
| `tools/templates/approved_referral_reel.json` | Referral look (approved 9 Nov 2026) |
| `skills/` | Text of the `career-reels-editor` and `career-reels-broll` skills |
| `docs/` | Daily Reel SOP, setup guide, style guide (61 styles), final checklist |
| `docs/Style-Reference.md`, `docs/style-frames/` | Real reference frame for each of the 47 Proven styles |
| `docs/Reels-Log.md` | One row per rendered reel |
| `specs/` | Specs of posted reels, to copy or re-render |

## Not in this repo
`broll.env`, `github.env`, raw videos, B-roll, proof screens, references, finished reels, models (`~/asr`, `~/seg`).

## Needs
Python 3, ffmpeg, `pip install numpy pillow onnxruntime sherpa-onnx soundfile`, Poppins + Lora fonts, models:
- sherpa-onnx `sherpa-onnx-whisper-small` (k2-fsa/sherpa-onnx releases, asr-models)
- rembg `u2net_human_seg.onnx` (danielgatis/rembg releases v0.0.0)
