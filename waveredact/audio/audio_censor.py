import logging
import os
import sys
from enum import Enum
from pathlib import Path

from pydub import AudioSegment

import waveredact_core
from waveredact.audio.audio_manager import IOAudioManager
from waveredact.utils.console import console

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

        console.print(f"🎵 [info]Loading audio for censor: {input_path}[/info]")
        try:
            audio = AudioSegment.from_file(input_path)
            audio = audio.set_sample_width(2)
        except FileNotFoundError:
            from rich.panel import Panel
            error_msg = "[bold red]FATAL ERROR: FFmpeg not found in the system![/bold red]\n\n"
            error_msg += "WaveRedact requires FFmpeg to cut and modify audio.\n"
            error_msg += "[yellow]After installation, close and open again the terminal.[/yellow]"
            
            console.print(Panel(error_msg, title="Dependencies Error", border_style="red"))
            sys.exit(1)

        original_timestamps = self._get_interval_to_censor()

        pad_start_sec = 0.05  
        pad_end_sec = 0.2    
        
        padded_timestamps = []
        for start, end in original_timestamps:
            safe_start = max(0.0, start - pad_start_sec)
            safe_end = end + pad_end_sec
            padded_timestamps.append((safe_start, safe_end))

        raw_bytes: bytes = audio.raw_data
        sample_rate: int = audio.frame_rate
        channels: int = audio.channels
        sample_width: int = audio.sample_width

        censored_audio_bytes = waveredact_core.censor_audio(
            raw_bytes,
            sample_rate,
            channels,
            sample_width,
            padded_timestamps,
            mode.value
        )

        audio = audio._spawn(censored_audio_bytes)

        if self.output_dir:
            final_output_dir = self.output_dir
        else:
            final_output_dir = os.path.join(os.path.dirname(input_path), "censored")
            os.makedirs(final_output_dir, exist_ok=True)

        return self.audio_manager.save_censored(audio, input_path, final_output_dir)