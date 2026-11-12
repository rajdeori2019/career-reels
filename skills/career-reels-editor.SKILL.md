---
name: "career-reels-editor"
description: "Career Reels: use whenever Prafulla says \"make reel\" (or edit/make a reel, career reel) with a Google Drive link, a Drive file name, or a video in his Career Reels folder; edits it into an energetic 1080x1920 reel (Hinglish captions, Energy v3 graphics, text behind him, grade, SFX), on his laptop or in the cloud."
---

# Career Reels Editor

Part of the **Career Reels** project: Prafulla's personal system to record, upload and auto-edit his own reels. Keep it separate: don't use other projects' skills, templates, memory or folders. B-roll comes from the sibling skill **career-reels-broll**.

Approved look (Prafulla, 9 Nov 2026, "this time the video is awesome"): `D:\Prafulla Goal\Career Reels\Finished\Referral_Job_Link_Reel_FINAL.mp4`, spec in `tools\templates\approved_referral_reel.json`. Start every new reel from that template.

**Default preset = Energy v3** (approved 10 Nov 2026, "I am good with the v3 video"): `Finished\Recruiter_Cold_DM_Reel_v3.mp4`, spec `tools\templates\approved_energy_v3.json`. Use it unless he asks for the referral look. Rejected: v2_energy (zoom punches + flashes + faster speech). Energy comes from content-tied graphics every 1.5-3 s, not from zoom, flash or speed.

**HARD RULE (11 Nov 2026, he called reels without it "very basic"):** Energy v3 is ALWAYS the base of every reel, including style tests. Every reel gets: `pop_bg` hook (first spoken line) and `pop_bg` CTA, v3 look + zoom, minimal captions (C5), a `keyword` slam on the key phrase of almost every line, `header` for numbered steps, `typing_box` for any quoted message/question, `build_card` for lists, SFX on each graphic, Save & Share. Any other style (skit labels, stamp, tick list, JD cards, scissors, spotlight...) is added ON TOP of that, never instead of it. Do not use M2 calm pace, C3 karaoke or C4 accent captions unless he asks: they replace v3 parts.

**Handle (11 Nov 2026):** job-seeker topic (resume, Naukri, interviews, job switch) -> `@iamprafz`; recruiter topic (sourcing, clients, cold DMs, hiring managers, candidates backing out) -> `@i.am.a.recruiter`. Applies to the Save & Share pill and E3 Part 2 card. Say which one you picked in the confirmation table.

**Background (11 Nov 2026):** keep the real room by default. When the wall hurts text contrast (strong red/pink/busy wall, keywords hard to read on stills), switch to the navy studio: `"bg_replace": {"mode":"image","image":"<tools>/templates/bgA.png","clip":[0.4,0.85],"feather":2,"band":71,"spill_ratio":1.5}` and set every `pop_bg` to `"pattern":"ink"`. Everything else stays Energy v3. Mention the switch in the confirmation reply. bg_replace needs mattes on every frame (run `matte` over the whole reel; ~0.6 s/frame in the cloud) and renders ~0.4 s/frame. Approved example: `Finished/Proxy_Interview_Verify_Reel_v3_navy.mp4`.
Placement for his usual close framing (head near the top): top graphics at y 110-250 only, cards/stamps/rings at chest y 1000-1250, keywords y 1330, captions y 1480. Behind-head bigwords and H7 serif titles get hidden by his head in this framing, so use a `keyword` slam instead.

## Short prompt: "make reel <link>"
He may send only `make reel` plus a Google Drive link (e.g. `https://drive.google.com/file/d/<ID>/view?usp=...` or `...open?id=<ID>`). Take the file ID from the link (the part after `/d/` or `id=`), confirm it with `get_file_metadata` (title, size, video type), then run the right mode: laptop linked -> use the same file from `Raw Videos` if it is there, else laptop-off steps below. No link and no file name -> take the newest video in Drive `Career Reels/Raw Videos` (`search_files` with parentId, `orderBy modifiedTime desc`) and name it in the first reply.
Design: do NOT ask before the transcript. Pick it yourself and show it in the confirmation table step:
- Default **Energy v3** (H6 C5 L1 P6 B6 B9 B10 B11 E1 M3 S1 S2 G1 A1), speed 1.2x.
- Switch the content-tied pieces to the script: numbered steps -> `header`; a message/DM/email he quotes -> `typing_box`; a list of items -> `build_card`; myth vs truth -> H4 `myth`; before/after -> P2; a number or result -> P3/X2; a recruiter message -> P1. If he names a style or reel type, use that instead.
- In the confirmation reply add one line: `Design: Energy v3 (+ header, typing box, ...) at 1.2x. Reply OK, or name another look (Referral look / Calm / codes from the Style Guide).` One confirmation covers captions, cuts, speed and design.

## Laptop-off (cloud) mode
Use when no computer is linked (no mcp__remote-devices tools, or they report no device). Tested 11 Nov 2026. He records on the phone and uploads to Google Drive `Career Reels/Raw Videos` (Drive folder id 102hHw5VzKai7Jt-KOgBh-CIty28maPJ8), then says "Make a career reel from <file> in Drive".
1. Code: PUBLIC repo `rajdeori2019/career-reels` (no keys or videos in it). `git clone https://github.com/rajdeori2019/career-reels.git ~/cr/repo` (codeload tarballs are blocked by the proxy; git clone and raw.githubusercontent.com work). Tools are in `~/cr/repo/tools`, templates in `tools/templates`.
2. Video from Drive (the phone app caps attachments at 30 MB; his raw videos are 190-600 MB, so never ask him to attach them). The Drive tools cannot remove a sharing link, so never share the original. Steps: `search_files` for the title -> `copy_file` to `_tmp_cloud_<name>.mp4` -> `share_file` the COPY with permissionId `anyoneWithLink`, role reader -> `curl -L -o v.mp4 "https://drive.usercontent.google.com/download?id=<copyId>&export=download&confirm=t"` (370 MB took 14 s) -> immediately `update_file` the copy with downloadRestriction {restrictedReader: true} -> `trash_file` the copy. Check the download is a real video with ffprobe. Tell him a temp copy sits in Drive Trash (no preview, no download) until Trash empties.
   Needs domains `drive.google.com` and `drive.usercontent.google.com` allowed (done). A short clip under 30 MB attached in the chat also works.
3. Setup once per session: `pip install --break-system-packages sherpa-onnx onnxruntime soundfile`; models with curl from GitHub releases into `~/asr` (sherpa-onnx `asr-models/sherpa-onnx-whisper-small.tar.bz2`, extract) and `~/seg/human.onnx` (danielgatis/rembg `v0.0.0/u2net_human_seg.onnx`).
4. Same workflow below (caption table + cuts + speed first, then stills, then render), with paths in the cloud. No 175 s limit here (10 min per command): render in 8-10 s chunks. 4 s of Energy v3 hook renders in ~63 s.
5. Deliver with SendUserFile (he watches on the phone). Say the reel is not on the laptop yet; next time the laptop is linked, copy it to `Finished`.
6. Never run `cut` with one ffmpeg over many trims of the 4K/HEVC source: it was OOM-killed on 8 GB. The current engine cuts per segment with `-ss/-t` before `-i`.

## Where things live (user's computer, folder `Career Reels`)
- `Raw Videos/` input, `B-roll/` own clips, `References/` reels to copy the feel of, `Finished/` output, `broll.env` API keys.
- `tools/career_reel.py` engine, `tools/career_styles2.py` round-2 styles (loaded by the engine), `tools/hinglish_asr.py` Hinglish transcript, `tools/broll.py` B-roll finder, `tools/templates/` approved specs, `tools/incoming/style_test_r2a.py` one-still-per-style test.
- Work happens on the user's computer with device_bash (the folder is mounted at `$HOME/mnt/Career Reels`). Keep scratch in `~/cr/<reel>/` (outside the user's folder: no delete permission there).

## Hard limits on the user's computer (learned)
- Each command is cut off at ~175 s and background jobs die when the call returns. Everything runs in foreground chunks.
- Speeds (2 cores): `cut` ~80 s per 100 s of source; person mattes ~1.4 s/frame (max ~120 frames per call); `render` ~3 fps with mattes/stickers (12-13 s of output per call; Energy v3: 2-8 s per call); `join` ~60 s.
- Copying a changed file to the computer: `device_commit_files` can deliver a stale copy when the same staged path or device path was used before. Stage under a NEW unique filename, commit to `tools/incoming/<unique>.py`, then `cat incoming/<unique>.py > tools/career_reel.py` and check `md5sum` on both sides.
- Models (download once into `~/asr`, `~/seg` with `curl -C -`): sherpa-onnx `sherpa-onnx-whisper-small.tar.bz2` (github k2-fsa/sherpa-onnx releases, asr-models, 640 MB) and rembg `u2net_human_seg.onnx` (github danielgatis/rembg releases v0.0.0, 176 MB). `pip install sherpa-onnx soundfile onnxruntime` if missing. Poppins fonts are at /usr/share/fonts/truetype/google-fonts.

## Workflow (one reel)
1. **Inspect + pauses.** ffprobe the video (often VFR from phones; the engine resamples to 30 fps). Extract `a.wav` (16 kHz mono) and `silencedetect=n=-32dB:d=0.35`; build pause-split segments.
2. **Transcript.** `python3 hinglish_asr.py ~/asr/sherpa-onnx-whisper-small a.wav segs.json --lang hi` (Devanagari, decoded correctly) and the same with `--lang en` (English gist; for Hinglish it often gives Roman words). Write captions in **Roman Hinglish** as he speaks. For splitting inside a segment, use 40 ms energy bins.
3. **Confirm with Prafulla before building:** a table of caption lines with times, ⚠ on unsure words, and proposed cuts (false starts, repeated takes, long pauses, repeated phrases like "lekin job ka link" twice). Ask the speed (he chose 1.2x). Keep the take he picks.
4. **B-roll** (optional): `career-reels-broll` skill: `broll.py search/fetch` into `~/cr/<reel>/broll/`; show picks; reference clips in spec `broll` (source times).
5. **Spec** (copy the template; all times in SOURCE seconds with `"time_base": "source"`): `segments`, `speed`, `look`, `behind_titles` (hook), `captions` + `caption_style` (`style: pop`, size 76, max 3 words, `emphasis` words), `bigwords` (`behind: true`, y 390), `chips` (B1 steps at the top), `broll`, `stickers`, `punches`, `shakes`, `sfx`, `save` (`text: "Save & Share"`, `share_icon: true`, handle), `lufs: -14`.
6. `python3 career_reel.py cut spec.json w` (ultrafast intermediate, speed + atempo, cleaned voice).
7. `python3 career_reel.py matte spec.json w ~/seg/u2net_human_seg.onnx --from A --to B` in chunks of ~2 s output (only frames inside behind-you windows). Re-run mattes whenever segments or speed change (frame numbers shift).
8. `python3 career_reel.py stills spec.json w t1,...,t8` -> show 8 stills (hook, each big word, B-roll entry, stickers, chips, ending). **Get OK** before the full render.
9. `render spec.json w w/cN.mp4 --from A --to B` in 12-13 s chunks, then `join spec.json w "<Career Reels>/Finished/<Name>.mp4" w/c1.mp4 ...` (voice + SFX + ducked music bed, two-pass loudnorm to -14 LUFS).
10. QA: ffprobe, ebur128 (I about -14 to -15, peak <= -1.5), contact sheet of frames at every chunk join and key beat. Report in a few lines; offer the next step.

## Approved style defaults (what made it "awesome")
- **Look:** `{"brightness":0.04,"contrast":1.10,"saturation":1.15,"gamma":1.05,"warm":0.03,"vignette":0.25}` applied per frame (an ffmpeg grade in `cut` was too slow).
- **Camera:** bottom-anchored zoom, auto per cut alternating 1.10-1.12 and 1.15-1.16, small punch on every cut, extra +6% punches on key lines, 0.3 s shake on behind-you big words.
- **Hook = text behind him:** line 1 `JOB LINK KE BINA` (96 px white) fully above the head, line 2 `REFERRAL?` (180 px yellow) overlapping the crown; `y` 170. Keep it on screen through the whole first spoken idea. Never wider than the frame (≈180 px max for a 9-letter word).
- **Big turn words behind him** (`ISKE BADLE`), y 390, 180-250 px yellow. Don't stack a big word right after the hook.
- **Captions:** pop style, 2-3 words per page, current word on a yellow box with a bounce, emphasis words in yellow, y 1420. Roman Hinglish exactly as spoken.
- **Chips (B1)** at y 215, size 44, for message/step structure (e.g. JOB ID → JOB LINK → SKILLS → RESUME).
- **Clip-art stickers** (kinds: chat, question, link, doc, check, cross, briefcase, share) at shoulder height y 1170, x 150 or 930, never over the face; one per relevant line, 2-4 s each.
- **B-roll:** white flash + whoosh on entry, slow 8% push-in.
- **Ending:** "Save & Share" pill with bookmark + share icons and the topic handle (see Handle rule), after the last word; the last caption must match what he says (e.g. "save and share karna").
- **Sound:** SFX at -22 dB (whoosh on hook/B-roll, pop on stickers/big words, tick on chips, chime on CTA); music bed 0.05 under voice, 0.10 in gaps.

## Energy v3 preset (approved, default)
Measured from his 5 reference reels: low camera motion, a new on-screen graphic tied to the words every 1.5-3 s.
- `speed` 1.2. `look` `{"brightness":0.045,"contrast":1.12,"saturation":1.15,"vibrance":0.2,"gamma":1.05,"warm":0.03,"vignette":0.2}`. `zoom_levels` `[[1.08,1.10],[1.10,1.12]]`. No punches, no cut flash, no stickers. One `shakes` hit max.
- `caption_style.style` `minimal` (size 52, y 1480, yellow underline on the active word). A `keyword` element hides captions during its window.
- Elements (`career_styles2.py`): `pop_bg` {pattern stripes|paper|brand|ink, from, to} background swap with white matte outline + doodles (hook and CTA; needs mattes) · `typing_box` {label, text, from, to, type_dur, y, size 44} (key is `type_dur`, never `type`) · `keyword` {small, big, at, dur, size, color yellow|white, y 1330} · `header` {items [{num, text, from, to}], y 150} · `build_card` {title, subtitle, icon, chips [{text, at}], badge {text, at}, y} · `serif_title` {text, from, to, dim} · plus `bigwords` behind him for the turn word.
- Laptop render cost: `pop_bg` chunks ~2-4 s of output per call, plain sections ~8 s. Name chunks `w/pNN.mp4` and `join` them.
- Style codes: H6 C5 L1 P6 B6 B9 B10 B11 E1 M3 S1 S2 G1 A1.

## Round-2 styles (built 9 Nov 2026, status Ready: tested on stills, not yet in a posted reel)
All go in the spec; times are SOURCE seconds with `time_base: source` (keys from/to/at/strike_at/truth_at/wipe_at/split_at/snap_at/tap_at are mapped automatically, also inside lists).
- `elements` (overlays), each `{"type": ...}`:
  - H2 `skit_label` {text, from, to, x 60, y 1200} · H3 `rising_headline` {text with \n, key, from, to, y 230, size 92} · H4 `myth` {myth, truth, from, to, strike_at, truth_at, y 260}
  - L3 `side_column` {image, side left|right, text [..], from, to, y 1120, w 280, h 380} · L4 `float_card` {text or image, from, to, y 250}
  - P1 `message_card` {lines [..], highlight idx, from, to, y 330} · P2 `before_after` {before, after, from, to, wipe_at, y, w, h} · P3 `number` {value, prefix, suffix, decimals, roll, from, to, y, size} · P4 `insights` {image, point [x,y] 0-1, zoom, zoom_dur, from, to} · P5 `stamp` {text, from, to, y}
  - B2 `jd_fan` {titles [3], from, to, y} · B3 `resume_split` {labels [3], split_at} · B4 `scissors` {text, cut, y} · B5 `tick_list` {items [{text, at}], side, y 1150} · B7 `phone_alert` {app, title, body, from, to, y 200} · B8 `steps` {steps [{text, at}], from, to, y 190}
  - X2 `number_slam` (P3 + rays/ring; add the slam time to `shakes`) · E2 `comment_keyword` {keyword, from, y 1430} · E3 `part_two` {text, handle, from} · E4 `shop_button` {text, from, tap_at, y}
- `effects` (frame level, under overlays): L2 `split` {clip (video or image), from, to, top 0.46, face_y 0.42, clip_start} · X3 `spotlight` {from, to, x, y} · X4 `glitch` {at, dur 0.4} · X5 `grid` {clips [4], from, to, snap_at, speaker_last}
- Captions: `caption_style.style` = `pop` (default, approved), `karaoke` (C3 frosted pill) or `accent` (C4 serif italic on `accents` words, max_words 4). M2: `"pace": "calm"` (zoom 1.03-1.06, no cut punch).
- Placement: face sits roughly x 280-800, y 450-1250 at 1.10 zoom. Side elements (L3, B5, stickers) only at shoulder height and screen edges; P2/P4 cover the speaker briefly like a cutaway (say so in the stills). Proof images come from `Proof/` or `Screen Recordings/`; blur names first.
- After a Ready style appears in a reel Prafulla approves, mark it Proven in the Style Guide data and docs.

## Rules
- Never put text or graphics over the face; check stills at the strongest zoom.
- Captions only from his confirmed words; mark guesses ⚠ and ask.
- Cut false starts and repeated takes; ask which take when unsure.
- Real proof (his screens) beats stock B-roll; no logos/brand marks in clip-art.
- If the computer disconnects, stop retrying, prepare code in the cloud, and continue when he says he's back.