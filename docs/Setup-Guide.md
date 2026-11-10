# Career Reels: Setup Guide

This sets up the Career Reels editor and automatic B-roll. It does not touch any other project.

**Time needed:** about 15 minutes, done once.

**You need:** a laptop, a paid Claude plan, and the Claude desktop app.

---

## Step 1: Allow the video sites in Claude

1. On your laptop, open **claude.ai** in a web browser (not the desktop app).
2. Click your name (bottom left) → **Settings**.
3. Open **Capabilities**.
4. Find the allowed domains list (network access).
5. Add these four domains, one at a time:
   - `api.pexels.com`
   - `videos.pexels.com`
   - `pixabay.com`
   - `cdn.pixabay.com`
6. Optional, only if you want AI-generated clips (paid): `generativelanguage.googleapis.com`
7. Save.

✅ Done when all four domains show in the list.

---

## Step 2: Get your free Pexels API key

1. Go to **pexels.com/api**.
2. Sign up or log in with your email.
3. Click **Your API Key** (or "Get Started").
4. Fill the short form. Use "Career reels B-roll search" as the description.
5. Copy the key. It's a long string of letters and numbers.

✅ Keep it in a safe note for Step 4. Don't paste it into any chat.

---

## Step 3: Get your free Pixabay API key (recommended)

1. Go to **pixabay.com/api/docs**.
2. Log in (or sign up free).
3. Scroll to **Parameters → key**. Your key is shown there in green.
4. Copy it.

✅ Pixabay gives Claude more clips to choose from. You can skip it, but results will be fewer.

---

## Step 4: Create your Career Reels folder

1. Open **Documents** on your laptop.
2. Create a new folder: `Career Reels`
3. Inside it, create these six folders:

| Folder | What goes in it |
|---|---|
| `Raw Videos` | Your talking videos |
| `B-roll` | Your own short clips (named by what they show) |
| `Screen Recordings` | Your work, demos, dashboards |
| `Proof` | Screenshots of results (blur private details) |
| `References` | Reels you want to copy the style or pace of (or a `links.txt` with reel links) |
| `Finished` | Final reels land here |

✅ Keep this folder separate from any other project folders.

---

## Step 4b: Back up the folder to Google Drive

So you can see and add files from your phone when the laptop is off.

1. Install **Google Drive for desktop** (google.com/drive/download) and sign in.
2. Open Drive for desktop → **Settings (gear) → Preferences → My Computer → Add folder**.
3. Pick your `Career Reels` folder → choose **Sync with Google Drive** → Done.
4. On your phone, open the Google Drive app → **Computers** → your laptop → `Career Reels`.

✅ New videos you upload from your phone into `Raw Videos` (in Drive) appear on the laptop when it's next online.
⚠️ `broll.env` holds your API keys. Your Drive is private, so syncing it is fine. Don't share the folder with anyone.

---

## Step 5: Save your keys in a file

1. Open **Notepad** (Windows) or **TextEdit** (Mac, use Format → Make Plain Text).
2. Type these lines, using your real keys:

```
PEXELS_API_KEY=paste-your-pexels-key-here
PIXABAY_API_KEY=paste-your-pixabay-key-here
```

3. Save it inside the `Career Reels` folder with the exact name: `broll.env`
   - Windows: in "Save as type", choose **All Files**, so it doesn't become `broll.env.txt`.
4. Optional, for Veo only: add a third line `GEMINI_API_KEY=your-gemini-key`

✅ Done when `Career Reels/broll.env` exists and contains no spaces around the `=` sign.

---

## Step 6: Save the two skills

1. In the Claude chat, find the skill cards **career-reels-editor** and **career-reels-broll**.
2. Click **Save** on each.
3. Put the Career Reels `tools` folder (career_reel.py, hinglish_asr.py, broll.py, templates) inside your `Career Reels` folder.

✅ Claude now knows how to transcribe, cut, style, add B-roll and render your reel.
ℹ️ The first reel also downloads two free models into Claude's workspace on your laptop (about 800 MB): a Whisper speech model for Hinglish captions and a person cut-out model for text behind you.

---

## Step 7: Name your own B-roll clips well

Claude checks your own clips first, by file name, so name them by what they show:

- ✅ `laptop-typing-night.mp4`
- ✅ `walking-into-office.mp4`
- ✅ `metro-commute-morning.mp4`
- ❌ `VID_20261108_1234.mp4`

---

## Step 8: Start a Career Reels chat

1. Open the **Claude desktop app**.
2. Optional: create a new Project called **Career Reels**, so these chats stay apart from everything else.
3. Start a new task and add your `Career Reels` folder when asked.

---

## Step 9: Make your first reel

1. Put your talking video in `Raw Videos`.
2. Tell Claude: **"Make a career reel from `<file name>`"**. Optional: open the **TRI Reel Style Guide**, pick a reel type, tap **Copy prompt** and paste it too.
3. Claude sends a table of your **caption lines** and the **cuts** it plans (pauses, false starts, repeated takes). Fix any word, pick the take you like, and choose a **speed** (1.0x, 1.2x or 1.3x).
4. Claude shows a **contact sheet of B-roll picks**. Reply OK or ask for a swap.
5. Claude shows **8 preview stills**. Reply OK or say what to change.
6. The final reel and `credits.txt` land in `Finished` (about 15 to 30 minutes for a 1-minute reel).

---

## Step 10: Before you post

- [ ] Watch the whole reel with sound on
- [ ] No B-roll covers your proof or your hook
- [ ] No clip shows a logo, text or watermark
- [ ] Add the credits from `credits.txt` to your caption (good practice)
- [ ] Planning paid ads with it? Read the Pexels and Pixabay licence pages first

---

## If something goes wrong

| Problem | Fix |
|---|---|
| Claude says "connect_rejected" or "000" | A domain from Step 1 is missing. Add it and start a new chat. |
| Claude says "No API key found" | Check the file is named `broll.env` (not `.txt`) and sits directly in `Career Reels`. |
| Claude says "401" or "invalid key" | Copy the key again from Pexels/Pixabay. Remove any spaces. |
| Clips look generic or Western | Ask for a more specific search, like "Indian woman working on laptop at home". Add your own clips to `B-roll`. |
| No good match for a line | Tell Claude to skip B-roll for that line. Not every line needs it. |
| B-roll covers your captions | Ask Claude to place the B-roll first and add captions after. |

---

## Quick reference

| What | Where |
|---|---|
| Allowed domains | claude.ai → Settings → Capabilities |
| Pexels key | pexels.com/api |
| Pixabay key | pixabay.com/api/docs |
| Keys file | `Documents/Career Reels/broll.env` |
| Skills | career-reels-editor, career-reels-broll |
| Approved look | `Career Reels/tools/templates/approved_referral_reel.json` |
| Final reels | `Documents/Career Reels/Finished` |
| Reference reels | `Documents/Career Reels/References` |
| Phone access | Google Drive app → Computers → Career Reels |
