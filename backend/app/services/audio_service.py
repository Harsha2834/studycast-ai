
import asyncio
import subprocess
from uuid import uuid4

from pathlib import Path
import edge_tts

from ..config import AUDIO, TEMP


# Primary and fallback voices
VOICES = {
    "English": {
        "Alex": [
            "en-US-AndrewMultilingualNeural",
            "en-US-GuyNeural",
        ],
        "Maya": [
            "en-US-AvaMultilingualNeural",
            "en-US-JennyNeural",
        ],
    },
    "Hindi": {
        "Alex": [
            "hi-IN-MadhurNeural",
        ],
        "Maya": [
            "hi-IN-SwaraNeural",
        ],
    },
    "Telugu": {
        "Alex": [
            "te-IN-MohanNeural",
        ],
        "Maya": [
            "te-IN-ShrutiNeural",
        ],
    },
}


async def save_audio(text, voice, path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(path))

    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("No audio was received from Edge TTS")


def generate(dialogue, speaker_a, speaker_b, lang):

    job = uuid4().hex
    folder = TEMP / job

    folder.mkdir(parents=True, exist_ok=True)

    language_voices = VOICES.get(lang, VOICES["English"])

    segments = []

    async def build_audio():

        for index, turn in enumerate(dialogue):

            speaker = turn["speaker"]
            text = turn["text"].strip()

            if not text:
                continue

            if speaker == speaker_a:
                voice_list = language_voices.get(
                    "Alex",
                    VOICES["English"]["Alex"]
                )
            elif speaker == speaker_b:
                voice_list = language_voices.get(
                    "Maya",
                    VOICES["English"]["Maya"]
                )
            else:
                raise ValueError(f"Unknown speaker: {speaker}")

            audio_path = folder / f"{index:03d}.mp3"

            generated = False
            last_error = None

            # Try primary voice, then fallback voice
            for voice in voice_list:

                if generated:
                    break

                print(
                    f"\nGenerating turn {index + 1}/{len(dialogue)}"
                )
                print("Speaker:", speaker)
                print("Voice:", voice)

                # Retry each voice up to three times
                for attempt in range(1, 4):

                    try:
                        print(f"Attempt {attempt}/3")

                        await save_audio(
                            text,
                            voice,
                            audio_path
                        )

                        print(
                            "Audio generated:",
                            audio_path.stat().st_size,
                            "bytes"
                        )

                        generated = True
                        break

                    except Exception as error:

                        last_error = error

                        print(
                            f"Voice {voice} failed:",
                            repr(error)
                        )

                        audio_path.unlink(missing_ok=True)

                        await asyncio.sleep(attempt * 2)

            if not generated:
                raise RuntimeError(
                    f"All voices failed for turn {index + 1}. "
                    f"Last error: {last_error}"
                )

            segments.append(audio_path)

            # Small delay between requests
            await asyncio.sleep(1)

    try:

        # Generate all dialogue segments
        asyncio.run(build_audio())

        if not segments:
            raise RuntimeError("No audio segments were generated")

        # Create FFmpeg concat file
        listing = folder / "list.txt"

        listing.write_text(
            "\n".join(
                "file '" +
                str(segment.resolve()).replace("\\", "/") +
                "'"
                for segment in segments
            ),
            encoding="utf-8"
        )

        output = AUDIO / f"{job}.mp3"

        # Combine all dialogue segments
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(listing),
                "-c", "copy",
                str(output)
            ],
            check=True,
            capture_output=True,
            text=True
        )

        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError("Final MP3 was not created")

        print("\nStudyCast audio successfully generated:", output)

        return output

    except FileNotFoundError as error:

        raise RuntimeError(
            "FFmpeg is missing. Install FFmpeg and restart the terminal."
        ) from error

    finally:

        # Remove temporary dialogue segments
        for item in folder.glob("*"):
            item.unlink(missing_ok=True)

        folder.rmdir()
