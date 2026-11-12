# Career Reels: Setup & Daily Use Guide

Your personal system: record on your phone, upload, and Claude edits it into a 1080×1920 reel.
Separate from every other project. Updated 11 Nov 2026.

---

## Part A: One-time setup (already done ✅)

| # | Item | Status |
|---|---|---|
| 1 | `D:\Prafulla Goal\Career Reels` folder with `Raw Videos`, `B-roll`, `Screen Recordings`, `Proof`, `References`, `Finished`, `tools` | ✅ |
| 2 | `broll.env` with Pexels + Pixabay keys (never share it) | ✅ |
| 3 | Allowed domains in claude.ai → Settings → Capabilities: `api.pexels.com`, `videos.pexels.com`, `pixabay.com`, `cdn.pixabay.com`, `github.com`, `objects.githubusercontent.com`, `codeload.github.com`, `drive.google.com`, `drive.usercontent.google.com` | ✅ |
| 4 | Google Drive folder `Career Reels` (with `Raw Videos`) for phone uploads | ✅ |
| 5 | Public GitHub repo `rajdeori2019/career-reels` (engine, styles, templates, skill text, docs; no keys, no videos) | ✅ |
| 6 | Skills saved: **career-reels-editor**, **career-reels-broll** | ✅ |
| 7 | Google Drive connector connected in Claude | ✅ |

If you ever set this up on a new account, repeat 3, 6 and 7. Everything else is in the folder and the repo.

---

## Part B: Make a reel

### From your phone (laptop on or off)
1. Record the video (talk to camera, 30–90 s of real content; leave some space above your head).
2. Upload it to Google Drive → `Career Reels` → `Raw Videos`.
3. In the Drive app: ⋮ → **Copy link**.
4. Claude app → **New task** (don't select a computer if the laptop is off) → send:
   `make reel <paste link>`
   Or just `make reel` to use your newest video in `Raw Videos`.
5. Claude replies with **one confirmation**: caption lines, cuts, speed (1.2x), design and handle. Reply **OK** or send corrections.
6. Claude sends the **full storyboard**: one panel for every graphic moment and every line, with time, caption and what's on screen. Reply **OK**, or point to a panel number to change (e.g. "panel 7: smaller keyword").
7. Only after your OK, Claude renders the reel and sends it in the chat. If the laptop is on, it is also saved in `Finished`.

### From the laptop
1. Put the video in `Raw Videos`.
2. In a Claude task linked to your laptop: `make reel <file name>`.
3. Same confirmation step, then the storyboard, then the reel lands in `Finished`.

### Adding proof
Put screenshots in `Proof` and screen recordings in `Screen Recordings`, then say which line they belong to (e.g. "show Proof/naukri.png on line 9"). Blur names, CTC and contact details of anyone else.

---

## Part C: The house style (applies to every reel)

- **Energy v3 is always the base:** pop-out background on the hook and the ending, a keyword slam on the key phrase of almost every line, numbered section headers for steps, typing box for quoted messages, build cards for lists, minimal captions, sound effects, Save & Share.
- **Extra styles go on top** (skit labels, stamp, tick list, proof cards, screen-top split…). See the TRI Reel Style Guide (61 styles, 53 Proven).
- **Background:** your real room by default. When the wall hurts text contrast, Claude switches to the navy studio background and the ink pop-out.
- **Handle:** job-seeker topics → `@iamprafz`. Recruiter topics → `@i.am.a.recruiter`.
- **Speed:** 1.2x unless you say otherwise.
- **Never:** graphics over your face, words you didn't say in captions, other people's private details.

---

## Part D: Good to know

| Situation | What to do |
|---|---|
| Video over 30 MB | Don't attach it in chat. Upload to Drive and send the link. |
| Laptop off | Works: Claude edits in the cloud and sends the reel in chat. Copy it to `Finished` later. |
| Wrong word in captions | Correct it in the confirmation table or on the storyboard, before the render. |
| Don't like a graphic | Say the storyboard panel number and what to change. Nothing is rendered until you OK the storyboard. |
| Wall too red/busy | Say "navy background". |
| Want a different look | Name it: "Referral look", or style codes from the Style Guide. |
| A Drive copy named `_tmp_cloud_…` in Trash | That's the temporary copy Claude downloads from. Safe to empty Trash. |
| Editing a profile in a screen recording | Use Cancel, not Save, so your real profile doesn't change. |

---

## Quick reference

| What | Where |
|---|---|
| Raw videos | Drive or laptop → `Career Reels/Raw Videos` |
| Finished reels | `Career Reels/Finished` |
| Style Guide | Interactive page + `TRI Reel Style Guide.md` / `.pdf` |
| Approved looks | `tools/templates/approved_energy_v3.json`, `approved_referral_reel.json`, `bgA.png` (navy) |
| Engine backup | github.com/rajdeori2019/career-reels |
