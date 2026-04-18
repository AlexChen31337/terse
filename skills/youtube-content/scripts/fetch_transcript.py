#!/usr/bin/env python3
"""
fetch_transcript.py — Fetch and clean YouTube video transcripts.

Tries youtube-transcript-api first (no download, fast).
Falls back to yt-dlp subtitle extraction if needed.

Usage:
    uv run python scripts/fetch_transcript.py --url "https://youtube.com/watch?v=dQw4w9WgXcQ"
    uv run python scripts/fetch_transcript.py --url "https://youtu.be/abc123" --format json
    uv run python scripts/fetch_transcript.py --url "..." --output /tmp/transcript.txt
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import os
from pathlib import Path


# Preferred transcript language(s) to try in order
LANG_PREFERENCES = ["en", "en-US", "en-GB", "en-AU"]


# ---------------------------------------------------------------------------
# Video ID extraction
# ---------------------------------------------------------------------------

def extract_video_id(url: str) -> str:
    """Extract 11-char video ID from any YouTube URL variant."""
    patterns = [
        r"(?:youtube\.com/watch\?(?:.*&)?v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/v/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/live/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    # Last resort: treat a bare 11-char string as a video ID
    bare = url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", bare):
        return bare
    raise ValueError(f"Could not extract video ID from URL: {url!r}")


# ---------------------------------------------------------------------------
# Transcript fetching
# ---------------------------------------------------------------------------

def _ensure_package(package: str, import_name: str | None = None):
    """Install a package via uv pip if not importable."""
    imp = import_name or package
    try:
        __import__(imp)
    except ImportError:
        print(f"Installing {package}...", file=sys.stderr)
        subprocess.run(["uv", "pip", "install", package], check=True)


def fetch_via_transcript_api(video_id: str) -> list[dict]:
    """Fetch transcript using youtube-transcript-api. Returns list of {text, start, duration}."""
    _ensure_package("youtube-transcript-api", "youtube_transcript_api")
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except TranscriptsDisabled:
        raise RuntimeError("Transcripts are disabled for this video.")

    # Try preferred languages first
    transcript = None
    for lang in LANG_PREFERENCES:
        try:
            transcript = transcript_list.find_transcript([lang])
            break
        except NoTranscriptFound:
            continue

    # Fall back to any available transcript
    if transcript is None:
        available = list(transcript_list)
        if not available:
            raise RuntimeError("No transcripts available for this video.")
        transcript = available[0]
        print(f"Using transcript language: {transcript.language_code}", file=sys.stderr)

    entries = transcript.fetch()
    # Normalise to plain dicts
    return [{"text": e.text, "start": e.start, "duration": e.duration} for e in entries]


def fetch_via_yt_dlp(video_id: str) -> list[dict]:
    """Fetch transcript using yt-dlp subtitle download. Falls back strategy."""
    _ensure_package("yt-dlp", "yt_dlp")

    url = f"https://www.youtube.com/watch?v={video_id}"
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "uv", "run", "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", "en",
            "--sub-format", "json3",
            "--output", os.path.join(tmpdir, "%(id)s.%(ext)s"),
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed:\n{result.stderr}")

        # Find the downloaded subtitle file
        sub_files = list(Path(tmpdir).glob("*.json3"))
        if not sub_files:
            # Try vtt fallback
            cmd[-3] = "vtt"
            cmd[-1] = url
            subprocess.run(cmd, capture_output=True, text=True)
            sub_files = list(Path(tmpdir).glob("*.vtt"))

        if not sub_files:
            raise RuntimeError("yt-dlp ran but no subtitle file was found.")

        sub_file = sub_files[0]
        content = sub_file.read_text(encoding="utf-8")

        # Parse json3 format
        if sub_file.suffix == ".json3":
            return _parse_json3(content)
        else:
            return _parse_vtt(content)


def _parse_json3(content: str) -> list[dict]:
    """Parse yt-dlp json3 subtitle format."""
    data = json.loads(content)
    entries = []
    for event in data.get("events", []):
        segs = event.get("segs", [])
        text = "".join(s.get("utf8", "") for s in segs).strip()
        if text and text != "\n":
            entries.append({
                "text": text,
                "start": event.get("tStartMs", 0) / 1000,
                "duration": event.get("dDurationMs", 0) / 1000,
            })
    return entries


def _parse_vtt(content: str) -> list[dict]:
    """Parse WebVTT subtitle format into entries."""
    entries = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Timestamp line
        if "-->" in line:
            # Parse start time
            start_str = line.split("-->")[0].strip()
            start = _vtt_time_to_seconds(start_str)
            # Collect text lines
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() and "-->" not in lines[i]:
                text_lines.append(lines[i].strip())
                i += 1
            text = " ".join(text_lines)
            # Strip VTT tags like <c>, <00:00:00.000>
            text = re.sub(r"<[^>]+>", "", text).strip()
            if text:
                entries.append({"text": text, "start": start, "duration": 0})
        else:
            i += 1
    return entries


def _vtt_time_to_seconds(ts: str) -> float:
    """Convert VTT timestamp HH:MM:SS.mmm or MM:SS.mmm to seconds."""
    ts = ts.strip()
    parts = ts.replace(",", ".").split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        else:
            return float(parts[0])
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

NOISE_PATTERNS = [
    re.compile(r"\[Music\]", re.IGNORECASE),
    re.compile(r"\[Applause\]", re.IGNORECASE),
    re.compile(r"\[Laughter\]", re.IGNORECASE),
    re.compile(r"\[.*?\]"),        # Any remaining [bracketed] tokens
    re.compile(r"<[^>]+>"),        # Any HTML/XML tags
    re.compile(r"\s+"),            # Normalise whitespace
]


def clean_text(text: str) -> str:
    text = NOISE_PATTERNS[0].sub("", text)
    text = NOISE_PATTERNS[1].sub("", text)
    text = NOISE_PATTERNS[2].sub("", text)
    text = NOISE_PATTERNS[3].sub("", text)
    text = NOISE_PATTERNS[4].sub("", text)
    text = NOISE_PATTERNS[5].sub(" ", text)
    return text.strip()


def entries_to_plain_text(entries: list[dict]) -> str:
    """Merge transcript entries into clean readable text."""
    fragments = []
    for entry in entries:
        cleaned = clean_text(entry["text"])
        if cleaned:
            fragments.append(cleaned)

    # Simple sentence merging: join and fix spacing
    text = " ".join(fragments)
    # Fix duplicate spaces
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def entries_to_json(entries: list[dict]) -> str:
    """Return JSON array of cleaned transcript entries."""
    cleaned = []
    for entry in entries:
        text = clean_text(entry["text"])
        if text:
            cleaned.append({
                "text": text,
                "start": round(entry.get("start", 0), 2),
                "duration": round(entry.get("duration", 0), 2),
            })
    return json.dumps(cleaned, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch and clean YouTube transcripts")
    parser.add_argument("--url", required=True, help="YouTube video URL or ID")
    parser.add_argument("--format", choices=["transcript", "json"], default="transcript",
                        help="Output format: 'transcript' (plain text) or 'json' (with timestamps)")
    parser.add_argument("--output", help="Write output to this file path (default: stdout)")
    args = parser.parse_args()

    # Extract video ID
    video_id = extract_video_id(args.url)
    print(f"Video ID: {video_id}", file=sys.stderr)

    # Fetch transcript — try api first, then yt-dlp
    entries = None
    errors = []

    print("Trying youtube-transcript-api...", file=sys.stderr)
    try:
        entries = fetch_via_transcript_api(video_id)
        print(f"Got {len(entries)} entries via youtube-transcript-api.", file=sys.stderr)
    except Exception as e:
        errors.append(f"youtube-transcript-api: {e}")
        print(f"Failed: {e}", file=sys.stderr)

    if entries is None:
        print("Trying yt-dlp fallback...", file=sys.stderr)
        try:
            entries = fetch_via_yt_dlp(video_id)
            print(f"Got {len(entries)} entries via yt-dlp.", file=sys.stderr)
        except Exception as e:
            errors.append(f"yt-dlp: {e}")
            print(f"Failed: {e}", file=sys.stderr)

    if entries is None:
        print("\nERROR: Could not fetch transcript.", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    if not entries:
        print("WARNING: Transcript is empty.", file=sys.stderr)

    # Format output
    if args.format == "json":
        output = entries_to_json(entries)
    else:
        output = entries_to_plain_text(entries)

    # Write output
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
