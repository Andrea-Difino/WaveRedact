from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class IOAudioManager:
    """
    Manage input and output of audio files from the specified directory.

    Attributes:
        SUPPORTED_EXTENSIONS - Set of supported audio file formats
        path                 - Absolute path to the audio directory
    """
    SUPPORTED_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}

    def __init__(self, audio_path: str = "audio"):
        project_root = Path(__file__).resolve().parent.parent.parent
        safe_audio_dir = project_root / audio_path
        safe_audio_dir.mkdir(parents=True, exist_ok=True)
        self.path = str(safe_audio_dir)

    def get_audio(self) -> list[Path]:
        """
        Retrieve a list of supported audio files from the audio directory.

        Return:
            List of Path objects for the found audio files
        """
        audio_files = []
        for file_path in Path(self.path).glob("*"):

            if not file_path.is_file():
                continue

            extension = file_path.suffix.lower()
            
            if extension not in self.SUPPORTED_EXTENSIONS:
                print(f"File ignored (Format not supported): {file_path.name}")
                continue
            
            audio_files.append(file_path)

        return audio_files

    def save_censored(self, audio, input_path: str, output_dir: str) -> str:
        """
        Export the censored audio segment to a file.

        Params:
            audio       - Processed AudioSegment object
            input_path  - Original input file path
            output_dir  - Directory where the file should be saved

        Return:
            Path to the saved file
        """
        
        filename = os.path.basename(input_path)
        name_without_extension, extension = os.path.splitext(filename)
        output_filename = f"{name_without_extension}_censored{extension}"
        output_path = os.path.join(output_dir, output_filename)
        
        logger.info("Exporting censored file...")

        format_export = extension.replace(".", "")

        if format_export == "m4a":
            format_export = "ipod"

        audio.export(output_path, format=format_export)
        
        print(f"✅ File saved: {output_path}\n")
        return output_path
