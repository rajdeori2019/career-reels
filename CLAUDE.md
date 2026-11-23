# Career Reels: read this first in every chat

This repo and the laptop folder `D:\Prafulla Goal\Career Reels` are the real home of Prafulla's daily reel system. Every new chat that touches a reel follows these rules before anything else.

1. **Follow the SOP.** Open `docs/Daily-Reel-SOP.md` (live doc: https://claude.ai/artifact/Q9nk8WzEYTDwwWRhdr9KwU; the live doc wins if they differ) and the `career-reels-editor` + `career-reels-broll` skills. Run the reel exactly as the SOP's steps say. No step skipped.
2. **Style from the recording.** Claude picks the reel type and style codes itself from the raw recording (topic, script, framing, wall), always on the Energy v3 base, using only Proven styles from the TRI Reel Style Guide. Look at the reference frames in `docs/style-frames/` (overview: `docs/Style-Reference.md`) so each style matches the approved look.
3. **Background.** If the wall doesn't fit (strong red/pink/busy/dark wall, text hard to read, or a style needs a plain light wall), switch to the navy studio (`tools/templates/bgA.png` + `ink` pop-out) automatically and say so in the Gate 1 reply.
4. **Two gates.** Gate 1 = one confirmation reply. Gate 2 = the full storyboard. Never render without the storyboard OK.
5. **GitHub after every render. Not optional.** As soon as a reel is rendered (approved or not yet posted), attach this repo with push access, clone it, run
   `python3 tools/repo_sync.py "<Career Reels folder or staged copy>" <clone> --reel <Name> --date <YYYY-MM-DD> --handle <@...> --styles "<codes>" --bg "<Real room|Navy studio>" --status Delivered`,
   commit and push to `main`. Then tell Prafulla the commit. The laptop has no GitHub login, so the push always runs from Claude's session.
6. **Never commit** videos, `broll.env`, any `*.env`, raw footage or other people's private details. The repo is public.
7. **Checks (23 Nov 2026):** run `tools/spec_lint.py spec.json` before the storyboard and before render (must PASS), and `tools/qa_check.py` on the final file. ChatGPT runs the same engine from `chatgpt/` with `CR_STRICT=1`; see `chatgpt/README.md`.
8. Keep this project separate from every other project (ads use `reel-video-editor`, not this repo).
