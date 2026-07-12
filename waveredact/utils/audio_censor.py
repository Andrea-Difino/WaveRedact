import os
from pydub import AudioSegment
from pydub.generators import Sine
import logging
import sys
import click
from pathlib import Path
from enum import Enum
from waveredact.utils.audio_manager import IOAudioManager

logger = logging.getLogger(__name__)

class AudioMaskTypes(Enum):
    BEEP = "beep"
    SILENCE = "silence"

class AudioCensor:
    """
    Apply censoring effects (beep or silence) to specific intervals in audio files.

    Attributes:
        output_dir      - Path to the directory where censored audio will be saved
        all_intervals   - Dictionary mapping indices to their time intervals
        idx_for_censor  - List of indices that need to be censored
    """
    def __init__(
        self, 
        audio_manager: IOAudioManager,
        all_intervals: dict[int, str], 
        idx_for_censor: list[int], 
        rel_output_dir: str | None = None
    ):
        if rel_output_dir:
            safe_output_dir = Path.cwd() / rel_output_dir
            self.output_dir = str(safe_output_dir)
            os.makedirs(self.output_dir, exist_ok=True)
        else:
            self.output_dir = None

        self.audio_manager = audio_manager

        self.all_intervals = all_intervals
        self.idx_for_censor = idx_for_censor

    def _get_interval_to_censor(self) -> list[tuple[float, float]]:
        """
        Retrieve the time intervals for the indices marked for censorship.

        Return:
            List of tuples containing start and end seconds
        """
        intervals_to_censor = []
        for idx in self.idx_for_censor:
            start_str, end_str = self.all_intervals[idx].split("-")
            intervals_to_censor.append((float(start_str), float(end_str)))

        return intervals_to_censor

    def censor_file(self, input_path: str, mode: AudioMaskTypes = AudioMaskTypes.SILENCE) -> str:
        """
        Apply censor to audio by silencing or beeping the sensitive intervals.

        Params:
            input_path  - Path to the input audio file
            mode        - Audio mask type to use (beep or silence)

        Return:
            Path to the saved censored audio file
        """

        logger.info(f"Loading audio for censor: {input_path}")
        try:
            audio = AudioSegment.from_file(input_path)
        except FileNotFoundError:
            click.secho("\n[FATAL ERROR] FFmpeg not found in the system!", fg="red", bold=True)
            click.echo("WaveRedact require FFmpeg to cut and modify audio")
            click.secho("After installation, close and open again the terminal.\n", fg="yellow")
            sys.exit(1)

        timestamps = self._get_interval_to_censor()

        timestamps = sorted(timestamps, key=lambda x: x[0])

        pad_start = 50
        pad_end = 130

        for start_sec, end_sec in timestamps:
            start_ms = int(start_sec * 1000)
            safe_start = max(0, start_ms - pad_start)

            end_ms = int(end_sec * 1000)
            safe_end = min(len(audio), end_ms + pad_end)

            safe_duration = safe_end - safe_start

            if safe_duration <= 0:
                continue

            if mode.value == "beep":
                censor = Sine(600).to_audio_segment(duration=safe_duration).apply_gain(-15)
            else:
                censor = AudioSegment.silent(duration=safe_duration)
                
            censor = censor.fade_in(12).fade_out(20)

            audio = audio[:safe_start] + censor + audio[safe_end:]

        if self.output_dir:
            final_output_dir = self.output_dir
        else:
            final_output_dir = os.path.join(os.path.dirname(input_path), "censored")
            os.makedirs(final_output_dir, exist_ok=True)

        return self.audio_manager.save_censored(audio, input_path, final_output_dir)