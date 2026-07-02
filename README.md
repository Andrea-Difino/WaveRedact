# WaveRedact

WaveRedact is a local tool for transcribing audio files and automatically redacting sensitive information in spoken content. The basic workflow is simple: put audio files in the `audio/` folder, run the CLI, and find the redacted version in `audio/censored/`.

## What it does

- Transcribes local audio with Whisper.
- Detects potential sensitive data with PII extractors.
- Redacts the matched spans by replacing them with silence or beep.
- Saves the resulting file with the `_censored` suffix.
- Can optionally use an LLM to improve precision.

## Requirements

- Python 3.11 or later.
- At least 6.69GB of free disk space for the bundled local models included in the repository.
- Extra disk space for your audio files and for the first Whisper model download if it is not already cached locally.
- **`ffmpeg` installed and available in your system's `PATH`.** This is strictly required by the underlying audio processing engine to decode and slice the media files.
  - **Windows:** Open PowerShell or Command Prompt as Administrator and run:
    ```bash
    winget install ffmpeg
    ```
    *(Note: You must close and reopen your terminal after installation to refresh the PATH).*
  - **macOS:**
    ```bash
    brew install ffmpeg
    ```
  - **Linux (Ubuntu/Debian):**
    ```bash
    sudo apt update && sudo apt install ffmpeg
    ```

If you want to use the GPU, the project will try to take advantage of it; if it is not available, the CLI can continue in CPU mode.

## Installation

From a shell in the project folder:

### With `uv` (recommended)

If you already use `uv`, the setup is the simplest path: `uv sync` now installs the project itself, so the `waveredact` command becomes available after synchronization.

```bash
uv sync
```

Then run the CLI directly from the project environment:

```bash
waveredact
```

If you also want the web interface:

```bash
uv sync --extra web
```

And then:

```bash
waveredact-web
```

If your shell does not pick up the commands directly, use uv run waveredact or activate the generated .venv first.

### With `venv` and `pip`

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

If you also want the web interface:

```bash
pip install -e ".[web]"
```

## Using the CLI

The main CLI entry point is `waveredact`.

```bash
waveredact
```

By default, the command reads all supported audio files in `audio/`:

- .mp3
- .wav
- .flac
- .m4a
- .ogg

The censored file is saved in `audio/censored/` with the original name plus `_censored`.

### Available options

```bash
waveredact --auto
waveredact --level base --auto
waveredact --level medium --auto
waveredact --level total --auto
waveredact --use-llm
```

- `--auto` disables interactive mode and applies the "total" level as default without asking for confirmation.

- `--level` defines how aggressive the redaction should be when using --auto.

  - `base` removes secrets and payment data.

  - `medium` adds names, email addresses, phone numbers, and documents.

  - `total` extends redaction to addresses and time-related references.

- `--use-llm` enables the optional LLM component to improve detection.

### Example workflow

1. Copy your audio into `audio/`.

2. Run the command, for example `waveredact --auto --level total`.

3. Wait for transcription and redaction.

4. Retrieve the result from `audio/censored/`.

## Using the web interface
The project also includes a FastAPI server with a simple web interface.

Start it with:

```bash
waveredact-web
```

The server runs locally at `http://127.0.0.1:8000`.

The interface lets you upload an audio file and receive the analysis of the sensitive content it found.

## Expected output
When processing finishes, the CLI prints the path of the generated file. You will usually see a message like:

```txt
✅ File saved: .../audio/censored/file_name_censored.mp3
```

Folder structure
audio/: input folder for files to process.

audio/censored/: output folder for redacted files.

files/: local models and resources.

web/: web interface and API.

Common issues
FileNotFoundError: [WinError 2] or Couldn't find ffprobe or avprobe: You are missing ffmpeg. Follow the instructions in the Requirements section to install it, then completely close and reopen your terminal.

Nothing happens: Make sure there are supported audio files inside audio/.

LLM Server doesn't start: If you use --use-llm and the LLM server fails to initialize (e.g., due to port conflicts or missing files), WaveRedact will safely fallback and continue without that component.

License
This project is distributed under the terms of the license included in the repository.