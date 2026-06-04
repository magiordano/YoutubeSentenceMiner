from flask import Flask, render_template, request, jsonify
import sys
import json
from pathlib import Path

# Allow importing from core/
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.extractor import download_captions, parse_vtt
from core.audio import clip_audio
from core.anki import add_card

# Load config
config_path = Path(__file__).parent.parent / "config.json"
with open(config_path) as f:
    config = json.load(f)

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent.parent / "templates"),
    static_folder=str(Path(__file__).parent.parent / "static")
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/load", methods=["POST"])
def load():
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        raw, source = download_captions(url)
        captions = parse_vtt(raw)
        return jsonify({
            "source": source,
            "captions": captions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/mine", methods=["POST"])
def mine():
    data = request.get_json()
    url = data.get("url", "").strip()
    sentence = data.get("sentence", "").strip()
    start = data.get("start", "").strip()
    end = data.get("end", "").strip()

    if not all([url, sentence, start, end]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Clip audio
        audio_bytes = clip_audio(
            url=url,
            start=start,
            end=end,
            buffer_seconds=config["audio_buffer_seconds"]
        )

        # Add to Anki
        note_id = add_card(
            sentence=sentence,
            audio_bytes=audio_bytes,
            deck=config["anki_deck"],
            note_type=config["anki_note_type"],
            fields=config["anki_fields"]
        )

        return jsonify({"success": True, "note_id": note_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)