import os
from pathlib import Path

from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

OUTPUT_VIDEO = "static/videos/final_demo.mp4"
TARGET_SIZE = (1280, 720)
FPS = 24


def build_video_from_frames(
    slides: list[dict],
    audio_path: str,
    output_path: str = OUTPUT_VIDEO
):
    """
    Builds a slide-synced video:
    - Multiple frames per slide
    - Frame duration derived from audio timestamps
    - Fully MoviePy 2.x compatible
    """

    clips = []

    for slide in slides:
        frames = slide.get("frames", [])
        start = slide.get("start", 0)
        end = slide.get("end", start + 1)

        duration = max(0.5, end - start)

        if not frames:
            continue

        per_frame_duration = duration / len(frames)

        for frame_path in frames:
            frame_file = frame_path.lstrip("/")
            if not os.path.exists(frame_file):
                continue

            clip = (
                ImageClip(frame_file)
                .with_duration(per_frame_duration)
                .resized(TARGET_SIZE)
            )
            clips.append(clip)

    if not clips:
        print("[WARN] No frames found — video not created")
        return None

    video = concatenate_videoclips(clips, method="compose")

    if audio_path and os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        video = video.with_audio(audio)

    Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)

    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None
    )

    return output_path
