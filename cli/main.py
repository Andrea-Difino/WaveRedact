import logging
import time
import click
from dotenv import load_dotenv
from pathlib import Path

from waveredact.app import WaveRedactApplication, AppConfig

project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(datefmt=FORMAT, level=logging.WARNING, force=True)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("gliner").setLevel(logging.WARNING)
logging.getLogger("gliner.model").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

def ask_user_approval(sensitive_words: list[str]) -> bool:
    """
    Callback function used for human approval in interactive_mode.
    """
    while True:
        user_question = input(
            f"\nThese are the words found:\n{sensitive_words}\n\nAre they all correct (Y/N)? "
        )

        if user_question.upper().strip() == "Y":
            return True
        elif user_question.upper().strip() == "N":
            return False
        else:
            print("⚠️ Invalid input. Please enter Y or N.")

@click.command()
@click.option(
    '--level', 
    type=click.Choice(['base', 'medium', 'total'], case_sensitive=False), 
    default='total', 
    help='''Level of PII censor. Used only if --auto is applied. Levels:

    \b
    1) Base level: Immediately redact sensitive information that could compromise the security of your accounts or savings. Remove passwords, digital access keys, tokens, and banking
    or credit card details.
    \b
    2) Medium level: It extends Base level to ensure maximum compliance with privacy regulations. It removes any data that could directly identify you or other individuals, such as 
    names, email addresses, phone numbers, and identification documents.
    \b
    3) Total level: Beyond protecting accounts and identities, it eliminates every trace of geographic and temporal context—removing addresses, cities, states, and any dates 
    mentioned in the audio—thereby rendering the conversation completely decontextualized.
    \b
    '''
)
@click.option('--auto', is_flag=True, help='Disable interactive mode (no confirm required).')
@click.option('--use-llm', is_flag=True, help="Execute LLM to maximize precision.")
@click.option('--mode', type=click.Choice(['beep', 'muted'], case_sensitive=False), default='muted', help='Censor mode')
@click.option('--file', type=click.Path(exists=True, dir_okay=False), help='Specific audio file to process.')
@click.option('--folder', type=click.Path(exists=True, file_okay=False), help='Folder containing audio files to process.')
def main(level: str, auto: bool, use_llm: bool, mode: str, file: str, folder: str) -> None:

    if not file and not folder:
        click.secho("Error: You must provide either --file or --folder.", fg="red")
        return
    if file and folder:
        click.secho("Error: You cannot provide both --file and --folder.", fg="red")
        return

    start = time.time()

    config = AppConfig(
        level=level,
        auto=auto,
        use_llm=use_llm,
        mode=mode,
        file=file,
        folder=folder
    )

    app = WaveRedactApplication(config=config, approval_callback=ask_user_approval)
    app.run()

    end = time.time()

    total = end - start
    print("Execution time:", total)

    click.secho("Thanks for using waveredact! 🌊", fg="cyan")


if __name__ == "__main__":
    main()
