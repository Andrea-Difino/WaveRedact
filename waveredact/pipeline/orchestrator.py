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
        index_word_pair: dict[int, str], 
        mappers: list[ChunkMapper],
        data_pipeline: DataPrivacyPipeline,
    ):  
        self.iw_pair = index_word_pair
        self.mappers = mappers
        self.data_pipeline = data_pipeline

    def run_audio_chunks(
        self
    ) -> list[int]:
        full_idx: set[int] = set()
        n_chunks = len(self.mappers)
        words_found: list[str] = []

        for i in range(n_chunks):
            logger.info(f"Running chunk: {i + 1}")

            res = self.data_pipeline.extract_sensitive_data(self.mappers[i])

            words_found.extend([self.iw_pair[idx] for idx in sorted(res)])
            full_idx.update(res)

        ordered_idx = sorted(full_idx)
        print(ordered_idx)
        is_approved = self._human_approval(words_found)
        if is_approved:
            return ordered_idx
        else:
            return self.run_llm_extraction(ordered_idx)
        
    def run_llm_extraction(self, old_idx: list[int]) -> list[int]:
        checked_idx: set[int] = set()
        n_chunks = len(self.mappers)
        words_found: list[str] = []

        for i in range(n_chunks):
            logger.info(f"Running chunk: {i + 1}")

            res = self.data_pipeline.extract_sensitive_with_llm(self.mappers[i], old_idx)

            words_found.extend([self.iw_pair[idx] for idx in sorted(res)])
            checked_idx.update(res)

        is_approved = self._human_approval(words_found)
        if is_approved:
            return sorted(checked_idx)
        else:
            return []
    
    def _human_approval(self, sensitive_words: list[str]) -> bool:
        while True:
            user_question = input(
                f"\nThese are the words found:\n{sensitive_words}\n\nAre they all (Y/N)? "
            )

            if user_question.upper() == "Y":
                print("Thanks for using waveredact!")
                return True
            elif user_question.upper() == "N":
                print("Second check activated! Giving it to an LLM...")
                return False
            else:
                print("⚠️ Invalid input. Please enter Y or N.")
