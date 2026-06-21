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
    def __init__(self, all_intervals: dict[int, str], idx_for_censor: set[int], rel_output_dir: str = "audio/censored"):
        project_root = Path(__file__).resolve().parent.parent.parent
        safe_output_dir = project_root / rel_output_dir
        self.output_dir = str(safe_output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        self.all_intervals = all_intervals
        self.idx_for_censor = idx_for_censor

    def _get_interval_to_censor(self) -> list[tuple[float, float]]:
        intervals_to_censor = []
        for idx in self.idx_for_censor:
            start_str, end_str = self.all_intervals[idx].split("-")
            intervals_to_censor.append((float(start_str), float(end_str)))

        return intervals_to_censor

    def censor_file(self, input_path: str, mode: AudioMaskTypes = AudioMaskTypes.SILENCE) -> str:
        """
        Apply censor to audio.

        Params:
        timestamps: list of tuples (start_seconds, end_seconds) es. [(1.2, 1.8), (5.0, 5.5)]
        """

        logger.info(f"Loading audio for censor: {input_path}")
        audio = AudioSegment.from_file(input_path)

        timestamps = self._get_interval_to_censor()

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
        
        return self._handle_file(audio, input_path)
    
    def _handle_file(self, audio, input_path: str) -> str:
        
        filename = os.path.basename(input_path)
        name_without_extension, extension = os.path.splitext(filename)
        output_filename = f"{name_without_extension}_censored{extension}"
        output_path = os.path.join(self.output_dir, output_filename)
        
        logger.info("Exporting censored file...")

        format_export = extension.replace(".", "")

        if format_export == "m4a":
            format_export = "ipod"

        audio.export(output_path, format=format_export)
        
        logger.info(f"✅ File saved: {output_path}\n\n")
        return output_path