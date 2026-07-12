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

    def __init__(self, input_path: str = "audio", is_file: bool = False):
        path_obj = Path(input_path)
        if not path_obj.is_absolute():
            path_obj = Path.cwd() / input_path
            
        self.is_file = is_file
        self.path = str(path_obj)
        
        if not self.is_file:
            path_obj.mkdir(parents=True, exist_ok=True)

    def get_audio(self) -> list[Path]:
        """
        Retrieve a list of supported audio files from the audio directory,
        or a single file if initialized with a file path.

        Return:
            List of Path objects for the found audio files
        """
        audio_files = []
        path_obj = Path(self.path)
        
        if self.is_file:
            files_to_check = [path_obj] if path_obj.exists() else []
        else:
            files_to_check = path_obj.glob("*") if path_obj.exists() else []
            
        for file_path in files_to_check:

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
