import os
from pydub import AudioSegment
from pydub.generators import Sine
import logging
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class AudioMaskTypes(Enum):
    BEEP = "beep"
    SILENCE = "silence"

class AudioCensor:
    def __init__(self):
        project_root = Path(__file__).resolve().parent.parent.parent
        safe_output_dir = project_root / "audio" / "censored"
        self.output_dir = str(safe_output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def censor_file(self, input_path: str, timestamps: list[tuple[float, float]], mode: AudioMaskTypes = AudioMaskTypes.SILENCE) -> str:
        """
        Apply censor to audio.

        Params:
        timestamps: list of tuples (start_seconds, end_seconds) es. [(1.2, 1.8), (5.0, 5.5)]
        """

        logger.info(f"Loading audio for censor: {input_path}")
        audio = AudioSegment.from_file(input_path)

        timestamps = sorted(timestamps, key=lambda x: x[0])

        for start_sec, end_sec in timestamps:
            start_ms = int(start_sec * 1000)
            end_ms = int(end_sec * 1000)
            duration_ms = end_ms - start_ms

            if duration_ms <= 0:
                continue

            if mode.value == "beep":
                censor = Sine(600).to_audio_segment(duration=duration_ms).apply_gain(-15)
            else:
                censor = AudioSegment.silent(duration=duration_ms)

            audio = audio[:start_ms] + censor + audio[end_ms:]

        filename = os.path.basename(input_path)
        name_without_extension, extension = os.path.splitext(filename)
        output_filename = f"{name_without_extension}_censored{extension}"
        output_path = os.path.join(self.output_dir, output_filename)
        
        logger.info("Exporting censored file...")

        format_export = extension.replace(".", "")

        if format_export == "m4a":
            format_export = "ipod"

        audio.export(output_path, format=format_export)
        
        logger.info(f"✅ File saved: {output_path}")
        return output_path