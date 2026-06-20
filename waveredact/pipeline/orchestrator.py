from pathlib import Path
from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
from waveredact.utils.chunk import Chunker
import logging

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s %(message)s"


class Orchestrator:
    def __init__(
        self,
        *,
        mappers: list[ChunkMapper],
        data_pipeline: DataPrivacyPipeline,
    ):
        self.mappers = mappers
        self.data_pipeline = data_pipeline

    def run_audio_chunks(
        self, 
        iw_pair: dict[int, str]
    ) -> set[int]:
        full_idx: set[int] = set()
        n_chunks = len(self.mappers)

        for i in range(n_chunks):
            logger.info(f"Running chunk: {i + 1}")

            res = self.data_pipeline.extract_sensitive_data(self.mappers[i])

            words_finded = [iw_pair[idx] for idx in sorted(res)]
            full_idx.update(res)

            self._human_approval(i, n_chunks, words_finded)

        return full_idx

    def _human_approval(self, pos: int, n_chunks: int, sensitive_words: list[str]):
        while True:
            user_question = input(
                f"\nThese are the words found by the first model:\n{sensitive_words}\n\nAre they right (Y/N)? "
            )

            if user_question.upper() == "Y":
                if pos + 1 == n_chunks:
                    print("Thanks for using waveredact!")
                else:
                    print("Continue with the next chunk...")
                break
            elif user_question.upper() == "N":
                print("Second check activated! Passaggio all'LLM...")
                # TODO passare chunks a due LLM . Il primo é un modello piú piccolo e cerca di censurare le parole. Il secondo é più potente, fa quello che ha fatto il primo e sistema/aggiusta le censure. I due risultati che contengono gli id delle parole da censurare vengono messi in un set in modo da togliere i duplicati

                break
            else:
                print("⚠️ Invalid input. Please enter Y or N.")
