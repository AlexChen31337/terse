---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'youtube-content')"
---


# youtube-content

Fetch transcripts from YouTube videos and transform them into summaries, blog posts, chapters, or structured JSON. Works with any video that has captions (auto-generated or manual).

## When to Use

- User shares a YouTube URL and asks for a summary, key points, or blog post
- User wants to extract chapters or timestamps from a long video
- User needs the raw transcript for further processing
- User wants to turn a video lecture/talk into written content

## Procedure

1. **Extract video ID** — Parse the URL to get the 11-character video ID (handles `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`, etc.)
2. **Fetch transcript** — Try `youtube-transcript-api` first (fast, no download). Fall back to `yt-dlp` if unavailable or captions fail.
3. **Clean text** — Strip timestamps, merge short fragments, normalise whitespace.
4. **Transform** — Output as plain text transcript or JSON with timestamps.
5. **Further processing** — Pipe clean transcript to Claude for summarisation, blog post generation, etc.

```bash
# Get plain transcript
uv run python skills/youtube-content/scripts/fetch_transcript.py --url "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Get JSON with timestamps
uv run python skills/youtube-content/scripts/fetch_transcript.py --url "https://youtu.be/dQw4w9WgXcQ" --format json

# Save to file
uv run python skills/youtube-content/scripts/fetch_transcript.py --url "https://youtube.com/watch?v=dQw4w9WgXcQ" --output /tmp/transcript.txt
```

## Pitfalls

- **No captions:** Some videos have no captions at all (live streams, music, auto-caption disabled). Script exits with a clear error.
- **Age-restricted / private videos:** `youtube-transcript-api` will fail; `yt-dlp` may also fail without cookies. Use `--cookies-from-browser chrome` with yt-dlp as a manual workaround.
- **Auto-generated captions:** Quality varies. May have run-on sentences or incorrect punctuation.
- **Language:** By default fetches English (`en`). For other languages, pass `--lang` (not yet exposed in CLI — edit script's `LANG` constant).
- **Rate limiting:** Avoid hammering the same video repeatedly. Add a delay between batch requests.

## Verification

After running:
- Output is non-empty text / valid JSON
- For JSON format: each entry has `text`, `start`, `duration` keys
- No raw `[Music]` or `[Applause]` tokens in transcript (cleaned out)
- Video title printed to stderr confirms correct video was fetched
