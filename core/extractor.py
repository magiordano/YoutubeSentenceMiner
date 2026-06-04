import re
import subprocess
import tempfile
from pathlib import Path


def download_captions(url: str, lang: str = "ja-orig") -> tuple[str, str]:
    """
    Download captions from a YouTube URL using yt-dlp.
    Tries manual subtitles first, falls back to auto-generated.
    Returns (raw VTT content, source) where source is 'manual' or 'auto'.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "captions"

        # Try manual subs first
        cmd = [
            "yt-dlp",
            "--write-sub",
            "--sub-lang", "ja",
            "--sub-format", "vtt",
            "--skip-download",
            "--no-check-formats",
            "--cookies-from-browser", "firefox",
            "--remote-components", "ejs:github",
            "-o", str(output_path),
            url
        ]

        subprocess.run(cmd, capture_output=True)
        vtt_files = list(Path(tmpdir).glob("*.vtt"))

        if vtt_files:
            return vtt_files[0].read_text(encoding="utf-8"), "manual"

        # Fall back to auto-generated
        cmd = [
            "yt-dlp",
            "--write-auto-sub",
            "--sub-lang", lang,
            "--sub-format", "vtt",
            "--skip-download",
            "-o", str(output_path),
            url
        ]

        subprocess.run(cmd, capture_output=True)
        vtt_files = list(Path(tmpdir).glob("*.vtt"))

        if not vtt_files:
            raise FileNotFoundError(f"No captions found for language: {lang}")

        return vtt_files[0].read_text(encoding="utf-8"), "auto"

def parse_vtt(vtt_content: str) -> list[dict]:
    """
    Parse raw VTT content into a list of caption entries.
    Each entry is a dict with 'start', 'end', and 'text'.
    Handles both auto-generated and manual/karaoke subtitle formats.
    """
    def clean_text(text: str) -> str:
        text = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d+>', '', text)
        text = re.sub(r'</?c(?:\.[a-zA-Z0-9]+)?>', '', text)
        text = re.sub(r'\([^\)]*\)', '', text)
        text = re.sub(r'（[^）]*）', '', text)
        text = re.sub(r'\[音楽\]', '', text)
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def is_spaced_kana(text: str) -> bool:
        tokens = text.split()
        if len(tokens) < 3:
            return False
        has_kanji = any('\u4e00' <= c <= '\u9fff' for c in text)
        avg_token_len = sum(len(t) for t in tokens) / len(tokens)
        return not has_kanji and avg_token_len <= 2.0

    entries = []

    lines = vtt_content.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if '-->' in line:
            parts = line.split('-->')
            start = parts[0].strip().split()[0]
            end = parts[1].strip().split()[0]

            i += 1
            text_parts = []
            while i < len(lines) and lines[i].strip() != '':
                text_parts.append(lines[i].strip())
                i += 1

            text = ' '.join(text_parts)
            text = clean_text(text)

            if not text:
                continue
            if re.match(r'^[。、．,.\s]+$', text):
                continue

            entries.append({
                'start': start,
                'end': end,
                'text': text
            })

        i += 1

    # Filter out karaoke spaced-kana lines
    entries = [e for e in entries if not is_spaced_kana(e['text'])]

    # Deduplicate
    seen = set()
    deduped = []
    for entry in entries:
        if entry['text'] not in seen:
            seen.add(entry['text'])
            deduped.append(entry)

    return deduped
if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=8ZP5eqm4JqM"

    print("Downloading captions...")
    raw, source = download_captions(url)
    print(f"Source: {source}")

    print("Parsing...")
    captions = parse_vtt(raw)

    for entry in captions[:20]:
        print(f"[{entry['start']} --> {entry['end']}] {entry['text']}")

    print(f"\nTotal entries: {len(captions)}")