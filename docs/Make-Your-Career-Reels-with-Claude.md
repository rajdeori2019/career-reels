The Recruiter Institute · Free guide for job seekers

# Make your career reels with Claude

Turn one phone video into a polished reel recruiters remember. You tell Claude what you want in plain words. No editing app, no coding.

by **Prafulla Deori**13+ years in tech hiring@iamprafz

JOB LINK KE BINA**REFERRAL?**

Referral *maang* rahe ho

Save & Share

## Why a reel helps your job search

A resume tells a recruiter what you did. A 30-second video shows how you think and how you speak, before they ever call you. From my years of hiring, the candidates I remembered were the ones I had already heard explain their work clearly. These are the same steps I use to edit my own reels, written for complete beginners.

**A laptop**Windows or Mac, with about 5 GB free

**A paid Claude plan**Pro or higher, on the Claude desktop app

**Your video**Vertical, you talking, filmed on your phone

**A reference reel, optional**A reel whose look or pace you want, saved in References

**Proof, if you have it**Screen recordings of your work, screenshots of results

**First setup: about 30 minutes.** After that, each new reel is Parts 2 to 7.

1Do this once

## Set up Claude

This gets Claude ready to work with the video files on your laptop.

1. Step 1**Install the Claude app**Go to [claude.ai/download](https://claude.ai/download), install the desktop app and sign in with your paid plan.
2. Step 2**Make one main folder**In Documents, create a folder called `Career Reels`.
3. Step 3**Make six folders inside it**Use the names shown below, so Claude always knows where things are.
4. Step 4**Give Claude the folder**Start a new task in the app and add your `Career Reels` folder, so Claude works on files on your own laptop.

Raw Videosyou talking

B-rollshort clips of you

Screen Recordingsyour work, demos

Proofscreenshots, blurred

Referencesreels you want to copy

Finishedfinal reels

2Every reel

## Write a 30-second script

Recruiters scroll fast. Say one thing well. Every good career reel follows the same three beats.

Hook*→*Proof*→*Ask*· 20 to 40 seconds · simple words*

### Hire-Me Intro

Hook"I'm a data analyst who cut a weekly report from 6 hours to 20 minutes."

Proof"I built it in Power BI for a team of 40. Here's the dashboard."

Ask"I'm looking for analyst roles in Bangalore. DM me or check my profile."

### Project Showcase

Hook"This app tells you which jobs match your resume. I built it in 3 weeks."

ProofScreen recording: upload a resume, show the match score, show the code.

Ask"Link in my profile. I'm open to frontend roles."

### Career Switch

Hook"Eight years in IT support. Now I'm moving into cloud. Here's why."

Proof"I cleared AWS Associate and migrated our team's servers last quarter."

Ask"If your team needs a cloud engineer who knows support, let's talk."

These are examples. Use **your own real numbers** only. If you don't have a number, say what changed: faster, fewer errors, a happier client.

Or ask Claude to write it

```
Write me a 30-second reel script for my job search. Use three parts: Hook (one line that makes a recruiter stop), Proof (one specific result from my work), Ask (the role I want and what to do next). Use simple English I would actually speak. Here is my background: [paste your resume summary and the role you want]. Give me 3 options for the hook.
```

Copy

3Every reel

## Film your clips

Good raw video makes the edit easy. You don't need a camera or a mic to start.

1. Talking video**Phone vertical, eye level**Face a window for light. Keep your face in the upper half of the frame. Leave a short pause between lines, Claude will cut them.
2. Save it**Put it in Raw Videos**Give it a clear name, like `hire-me-intro.mp4`. Two takes are fine, Claude can pick the better one.
3. Proof**Record your work**Screen record your dashboard, app or portfolio slowly. Save it in Screen Recordings. Close anything private first.
4. Optional**Add B-roll**3 to 5 second clips of you working or walking into an office. Name them by what they show, like `laptop-cafe.mp4`.

**Hindi and English mixed is fine.** Speak the way you speak in interviews. Claude writes captions in Roman Hinglish, exactly as you said them.

4One tap

## Choose your style

The TRI Reel Style Guide picks the look of your reel. Tap a reel type like Hire-Me Intro or Resume Fix, change any style you like, then tap Copy prompt. The prompt describes every style for Claude, so there is nothing to install.

1. 1**Pick your reel type**The styles for that reel are chosen for you.
2. 2**Change what you like**Keep it to about 8 to 10 styles. Use one Showpiece effect at most.
3. 3**Copy the prompt**Save it in a note. You'll paste it in the next step.

[Open the TRI Reel Style Guide →](https://claude.ai/artifact/NSN1Ha3ok3r7VCqg7hCPg5)

5The easy bit

## Send it to Claude

You send one message, check a few still frames, and Claude does the editing.

1. 1**Paste your prompt**Paste what you copied, attach your video from Raw Videos, and send.
2. 2**Confirm your lines**Claude sends a table of your caption lines and the cuts it plans (pauses, false starts, repeated takes). Fix any word, pick the take you like and choose a speed: 1.0x, 1.2x or 1.3x.
3. 3**Check 8 stills**Claude shows 8 frames: the hook, big words, B-roll, clip-art and the ending. Reply OK, or say what to change.
4. 4**Wait for your reel**About 15 to 30 minutes for a 1-minute reel. The first time, Claude also installs free tools and downloads two models (about 800 MB). Keep your laptop plugged in. It lands in Finished.

**Have proof or B-roll?** Add one normal sentence, like "Use my dashboard recording when I say Power BI" or "Copy the pace of this reel: [link]".

5+Optional

## Let Claude find your B-roll

No clips of your own? Claude can search free stock video sites, pick vertical clips that match what you're saying, and cut them in. Set this up once.

1. Step 1**Allow the video sites**On claude.ai in a browser, open Settings, then Capabilities, and add `api.pexels.com`, `videos.pexels.com`, `pixabay.com` and `cdn.pixabay.com` to allowed domains.
2. Step 2**Get a free Pexels key**Sign up at [pexels.com/api](https://www.pexels.com/api/) and copy your key. A Pixabay key from [pixabay.com/api/docs](https://pixabay.com/api/docs/) gives more choice.
3. Step 3**Save the keys in a file**In your Career Reels folder, make a text file named `broll.env` with one line per key: `PEXELS_API_KEY=your-key` and `PIXABAY_API_KEY=your-key`. Don't paste keys into the chat.
4. Step 4**Add this to your prompt**Paste it after your style prompt in Part 5. Claude shows you the picks before it cuts them in.

Automatic B-roll prompt

```
Also add B-roll automatically. My API keys are in broll.env in my Career Reels folder. Read them from the file and never print them.
1. From my transcript, pick 3 to 5 lines that need B-roll. Skip the hook, the call to action, and any moment where I show proof. Keep each B-roll shot under 2.5 seconds.
2. For each line, write a short visual search phrase, like "person typing on laptop at night".
3. Check my B-roll folder first (match by file name). If nothing fits, search the Pexels video API (portrait), then the Pixabay video API.
4. Prefer vertical clips, at least 1080 pixels tall, a little longer than the line. Skip clips with logos, text or faces that look like a real brand ad.
5. Download the best match, crop it to 9:16 and trim it to the line.
6. Show me one contact sheet of the picks, with the line each one covers, before you cut them in.
7. Cut them over my video at those times and keep my voice running underneath.
8. Save the creator credits in credits.txt next to the final reel.
```

Copy

**Stock clips are generic.** They work for "typing on a laptop" or "walking into an office". They can't show your real work. Your own screen recordings always beat stock footage as proof. Read the Pexels and Pixabay licence pages before using their clips in paid ads.

6Fix it

## Fix it in one sentence

Your first version will rarely be your last. Say the time and what you want.

"At 0:08 you cut the word 'Power BI'. Put it back."

"The captions are hard to read. Put a dark label behind them."

"The hook text touches my face. Move it higher."

"Blur the client name in the screenshot at 0:14."

"Make the music quieter. I want my voice clear."

### Before you post, tick these off

I watched the whole reel with sound on
The role I want is clear in the first 3 seconds
Every caption spells my words and tools correctly
My face is never covered by text
No employer code, client names or internal screens are visible
Every number I say is real and I can explain it in an interview
The ending says exactly what to do next

7Ship it

## Post it where recruiters look

A good edit still needs a clear cover and caption. Finish these before you press Post.

1. Cover**Ask Claude for a cover**"Give me a cover image from this reel. Use a frame where I look good and add my hook without covering my face."
2. LinkedIn**Upload the video natively**Upload the MP4 itself, not a YouTube link. Then add the post to the Featured section of your profile.
3. Instagram**Post it as a Reel**Same video, with the cover. If you add music, keep it very low.
4. Outreach**Use it in your messages**When you message a recruiter or hiring manager, add one line: "Here's a 30-second intro" and the link.

Caption prompt

```
Write a LinkedIn caption and an Instagram caption for this reel, in my voice. Start with a strong first line, keep it under 80 words, mention the role I'm looking for, end with a clear next step, and suggest 5 relevant hashtags.
```

Copy

## If something goes wrong

Don't panic. Paste the error into Claude and ask what to do.

**Claude can't find my file**Drag the file into the chat instead of typing its name.

**An install fails**Ask: "Explain this in simple words and give me the next step."

**A word in the captions is wrong**Tell Claude the time and the correct word.

**A real word was cut**Give the time and ask Claude to put it back.

**The render is very slow**Plug in your laptop, close other apps and let it finish.

**My laptop runs out of space**Delete old test versions and keep only the final reel.

**A reference reel link won't open**Download the reel and drag it into the chat.

**The video won't play in the app**Open the saved file from your Finished folder.

The Recruiter Institute

## Follow for daily job-search reels

I share what recruiters actually look for: resumes, interviews, salary talks and job search plans for India's tech market.

[@iamprafz](https://www.instagram.com/iamprafz/)
YouTube: [@prafulladeori](https://www.youtube.com/@prafulladeori)
