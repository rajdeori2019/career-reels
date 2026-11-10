# Career Reels: Final Checklist

Your personal system to record, upload and auto-edit your own reels. It is kept separate from every other project.
Status as of 10 Nov 2026.

---

## 1. Already done ✅

| Item | Where |
|---|---|
| Folder structure (Raw Videos, B-roll, Screen Recordings, Proof, References, Finished, tools) | `D:\Prafulla Goal\Career Reels` |
| B-roll API keys (Pexels + Pixabay) | `broll.env` |
| B-roll domains allowed in Claude | Settings → Capabilities |
| Editing engine + styles + Hinglish transcript + B-roll finder | `tools\` |
| Speech model (Whisper small) + person cut-out model | Claude's workspace on your laptop (downloaded once) |
| Approved looks: **Energy v3 (default)** and Referral | `tools\templates\approved_energy_v3.json`, `approved_referral_reel.json` |
| Approved reels | `Finished\Recruiter_Cold_DM_Reel_v3.mp4`, `Finished\Referral_Job_Link_Reel_FINAL.mp4` |
| 5 reference reels | `References\` |
| Style Guide: 61 styles (31 Proven, 30 Ready), 8 reel types | Interactive page + `TRI Reel Style Guide.md` + `TRI Reel Style Guide - all styles.pdf` |
| Topics of the 7 new raw videos mapped | See section 4 |

---

## 2. Your actions (one time)

| # | Action | How | Unblocks |
|---|---|---|---|
| 1 | **Save the skill update card** for `career-reels-editor` | In the Claude chat, tap **Save** on the card | Energy v3 as the default for every reel |
| 2 | **Turn on Drive sync** for the folder (if not done) | Drive for desktop → Settings → My Computer → Add folder → `Career Reels` → Sync | Uploading from your phone |
| 3 | **Add proof assets** (blur names first) | `Proof\resume_before.png`, `Proof\resume_after.png`, `Proof\naukri_insights.png`, `Proof\product.png`, `Screen Recordings\naukri_headline.mp4` | T4: test reels for the Ready styles |
| 4 | **Create a private GitHub repo** named `career-reels` | github.com → New repository → Private | T6 backup |
| 5 | **Create a GitHub token** (fine-grained, only the `career-reels` repo, Contents: Read and write) | github.com → Settings → Developer settings → Personal access tokens | T6 + T7 |
| 6 | **Save `github.env`** in the `Career Reels` folder (plain text, no spaces around `=`) | Two lines: `GITHUB_TOKEN=your-token` and `GITHUB_REPO=your-username/career-reels` | T6 + T7 |
| 7 | **Allow 3 more domains** in Claude | Settings → Capabilities: `github.com`, `objects.githubusercontent.com`, `codeload.github.com` | T7 laptop-off runs |
| 8 | **Approve delete access** when Claude asks during the GitHub setup | Tap Allow on the prompt | git needs it for its own lock files |

Never paste the token or API keys into the chat.

---

## 3. Remaining build tasks (Claude)

| Task | Status | Waiting on |
|---|---|---|
| T4 Test reels covering the Ready styles (3-4 reels from your new videos) | Pending | Action 3 |
| T6 GitHub backup of tools, templates, skill text, docs | Pending | Actions 4, 5, 6, 8 |
| T7 Phone workflow with the laptop off (cloud run from GitHub) + test | Pending | T6 + action 7 |

---

## 4. Your next reels (raw videos already in `Raw Videos`)

| Video | Topic |
|---|---|
| 20261101_194834 | "Tell me about your project" |
| 20261102_201015 | 8+ years IT, resume doesn't convince |
| 20261102_201731 | Candidate backs out on Friday before a Monday joining |
| 20261104_200902 | Hiring manager doesn't trust your shortlist |
| 20261105_195410 | Naukri headline mistake |
| 20261105_195735 | No interview update ruins credibility |
| 20261106_211222 | Opens with keyboard/paper sounds (needs full transcript) |

---

## 5. How you make a reel

**From the laptop (works now)**
1. Record on your phone. Put the video in `Raw Videos`.
2. In a Career Reels chat, say: **"Make a career reel from `<file name>`"**. Add a reel type from the Style Guide if you want something other than Energy v3.
3. Check the caption lines and cuts Claude sends. Fix words, pick takes, confirm the speed (1.2x is the default).
4. Check the preview stills (or the preview video if you're away from the laptop). Reply OK or list changes by time.
5. The final reel lands in `Finished`. Watch it with sound before posting.

**From your phone, laptop on (works now)**
1. Upload the video to Google Drive → Computers → your laptop → `Career Reels\Raw Videos`.
2. Keep the laptop on, awake and with the Claude desktop app open.
3. In the Claude app on your phone, open your Career Reels task (linked to the laptop) and use the same prompt.
4. Claude sends the finished video into the chat so you can watch and download it on your phone.

**From your phone, laptop off:** available after T7.

---

## 6. Before you post

- [ ] Watch the whole reel with sound on
- [ ] No graphic covers your face, proof or hook
- [ ] Last caption matches what you said
- [ ] Credits from `*_credits.txt` added to the caption if B-roll was used
- [ ] Names and private numbers are blurred in proof screens

---

## 7. If something goes wrong

| Problem | Fix |
|---|---|
| Claude can't reach your laptop | Wake it, check the Claude desktop app is open, then say "back" |
| "connect_rejected" or "000" on B-roll | A domain is missing in Settings → Capabilities |
| "No API key found" | `broll.env` must sit directly in `Career Reels` and not be named `.txt` |
| Render stops halfway | Normal: Claude renders in short chunks. Say "continue" if it pauses |
| Wrong word in captions | Correct it in the caption table before the render |
