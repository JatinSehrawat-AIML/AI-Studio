# tts/audio_generator.py

import os
import uuid
import json
import re

from gtts import gTTS
from faster_whisper import WhisperModel
from mutagen.mp3 import MP3

# ---------------- PATHS ----------------

AUDIO_DIR = "static/audio"
META_DIR = "static/audio_meta"

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(META_DIR, exist_ok=True)

# ---------------- WHISPER MODEL ----------------
# base is fine for alignment, but lock params for stability

whisper_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8",
    cpu_threads=2,
    num_workers=1
)

# ---------------- MAIN ----------------

def script_to_audio(script: str) -> dict:
    if not script or not script.strip():
        raise ValueError("Empty script cannot be converted to audio")

    audio_id = uuid.uuid4().hex
    audio_file = f"{audio_id}.mp3"
    meta_file = f"{audio_id}.json"

    audio_path = os.path.join(AUDIO_DIR, audio_file)
    meta_path = os.path.join(META_DIR, meta_file)

    # 1️⃣ TEXT → SPEECH (gTTS)
    tts = gTTS(
        text=script,
        lang="en",
        slow=False
    )
    tts.save(audio_path)

    # 2️⃣ AUDIO DURATION
    audio = MP3(audio_path)
    duration = round(audio.info.length, 2)

    # 3️⃣ WHISPER WORD ALIGNMENT
    segments, _ = whisper_model.transcribe(
        audio_path,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True
    )

    words = []
    order = 0

    for segment in segments:
        if not segment.words:
            continue

        for w in segment.words:
            raw = w.word.strip()

            # Keep punctuation for frontend spacing, but normalize
            clean = re.sub(r"\s+", " ", raw)

            if not clean:
                continue

            start = round(max(w.start - 0.03, 0), 2)  # 🔥 small early bias
            end = round(w.end, 2)

            words.append({
                "id": order,
                "word": clean,
                "start": start,
                "end": end
            })

            order += 1

    # 4️⃣ SAFETY SORT (IMPORTANT)
    words.sort(key=lambda x: x["start"])

    # 5️⃣ SAVE METADATA
    with open(meta_path, "w") as f:
        json.dump(
            {
                "audio_id": audio_id,
                "duration": duration,
                "words": words
            },
            f,
            indent=2
        )

    return {
        "audio_id": audio_id,
        "audio_url": f"/static/audio/{audio_file}",
        "timestamps": words,   # 🔥 frontend uses this
        "duration": duration
    }
