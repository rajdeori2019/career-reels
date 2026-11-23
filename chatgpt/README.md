# Career Reels in ChatGPT

ChatGPT can run the same engine Claude uses, but its sandbox has no internet, no Poppins font and no
person-segmentation model. On 19 Nov 2026 it quietly worked around that (colour-key mattes, DejaVu font, pop
captions, no cuts, its own renderer) and produced the rejected `Notice_Period_Reel_v1`. This folder plus the kit
closes those gaps and makes the engine refuse to degrade.

## What changed in the repo (23 Nov 2026)
| File | Why |
| --- | --- |
| `tools/fonts/Poppins-*.ttf` (OFL) | Engine finds Poppins anywhere; no DejaVu fallback |
| `CR_STRICT=1` in `tools/career_reel.py` | Stops on a missing font or a missing person matte instead of rendering a bad frame |
| `tools/preflight.py` | Checks ffmpeg, onnxruntime, model, fonts, repo files, strict mode before any work |
| `tools/spec_lint.py` | Enforces Energy v3 values (captions minimal 52/1480, look, zoom, ink on navy, cuts, keyword slams, hook/CTA pop, Save & Share, handle, B-roll rules). The approved Energy v3 template, Naukri and TMAY specs pass; the rejected Notice Period spec fails on 4 errors |
| `tools/qa_check.py` | Final file checks (1080x1920, 30 fps, −14 LUFS, true peak) + contact sheet |
| `chatgpt/PROJECT_INSTRUCTIONS.md` | Paste into the ChatGPT project's Instructions |
| `chatgpt/skills/career-reels-editor/SKILL.md` | ChatGPT plugin version of the skill (replace the 17 Nov plugin) |

## One-time setup in ChatGPT (10 min)
1. Project **Video Editing with ChatGPT** → Instructions: paste all of `chatgpt/PROJECT_INSTRUCTIONS.md`.
2. Project files: upload `D:\Prafulla Goal\Career Reels\ChatGPT Kit\Career_Reels_ChatGPT_Kit.zip`
   (engine + docs + style frames + fonts + onnxruntime wheels + u2net model, ~230 MB). Remove the old
   `Career_Reels_Project_Reference_Pack_2026-11-18.zip` and `Video_Editing_with_ChatGPT_PROJECT_MEMORY` files so it
   doesn't follow the old "lightweight mask" notes.
3. Plugin: replace `career-reels-editor` v1.0.0 with `ChatGPT Kit/career-reels-editor-chatgpt-v2.zip`.
4. First message in a new chat: `make reel` + the video (or its Drive link via the Drive connector).
   The first thing it must show you is `preflight ... RESULT: READY`. If it doesn't, it is improvising: stop it.

## Limits to know
- Transcription: the ChatGPT sandbox has no Hinglish ASR model (640 MB, over the upload limit). It uses the Descript
  connector, like the 17 Nov run. Check the Gate 1 caption table carefully.
- Mattes on navy reels need every frame: ~0.5 s/frame, so a 60 s reel is ~15 min of matte calls in chunks. That is the
  price of a clean edge. Real-room reels only need mattes on the hook and CTA.
- After any engine change in the repo, rebuild the kit (`chatgpt/build_kit.py`) and re-upload it.
