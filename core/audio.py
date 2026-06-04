import subprocess
import tempfile
from pathlib import Path


def clip_audio(url: str, start: str, end: str, buffer_seconds: int = 5) -> bytes:
    """
    Download and clip an audio segment from a YouTube URL.
    Returns the audio as bytes (mp3).
    """
    # Convert timestamp string to seconds
    def to_seconds(ts: str) -> float:
        parts = ts.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        return float(parts[0])

    start_sec = max(0, to_seconds(start) - buffer_seconds)
    end_sec = to_seconds(end) + buffer_seconds
    duration = end_sec - start_sec

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "clip.mp3"

        # Download just the audio segment using yt-dlp + ffmpeg
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--cookies-from-browser", "firefox",
            "--remote-components", "ejs:github",
            "-x",                          # extract audio
            "--audio-format", "mp3",
            "--download-sections", f"*{start_sec}-{end_sec}",
            "-o", str(output_path),
            url
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        return output_path.read_bytes()