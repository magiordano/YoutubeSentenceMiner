import requests
import base64
import json


ANKI_CONNECT_URL = "http://localhost:8765"


def anki_request(action: str, **params) -> dict:
    """Send a request to AnkiConnect."""
    payload = {
        "action": action,
        "version": 6,
        "params": params
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()


def add_card(sentence: str, audio_bytes: bytes, deck: str, note_type: str, fields: dict) -> int:
    """
    Add a card to Anki via AnkiConnect.
    Returns the new note ID.
    """
    # Encode audio as base64 and store it as a media file
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_filename = f"ysm_{abs(hash(sentence))}.mp3"

    # Store audio file in Anki media
    anki_request(
        "storeMediaFile",
        filename=audio_filename,
        data=audio_b64
    )

    # Build the note fields
    note_fields = {
        fields["sentence"]: sentence,
        fields["audio"]: f"[sound:{audio_filename}]"
    }

    # Add the note
    result = anki_request(
        "addNote",
        note={
            "deckName": deck,
            "modelName": note_type,
            "fields": note_fields,
            "options": {
                "allowDuplicate": False
            },
            "tags": ["ysm"]
        }
    )

    return result.get("result")