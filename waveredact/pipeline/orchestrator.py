from pathlib import Path
from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
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
        full_locked_idx: set[int] = set()

        n_chunks = len(self.mappers)
        words_found: list[str] = []

        for i in range(n_chunks):
            logger.info(f"Running chunk: {i + 1}")

            res, locked_res = self.data_pipeline.extract_sensitive_data(self.mappers[i])

            words_found.extend([self.iw_pair[idx] for idx in sorted(res)])
            full_idx.update(res)
            full_locked_idx.update(locked_res)

        ordered_idx = sorted(full_idx)

        is_approved = self._human_approval(words_found)
        if is_approved:
            return ordered_idx
        else:
            ambiguous_idx = full_idx - full_locked_idx
            return self.run_llm_extraction(sorted(ambiguous_idx), full_locked_idx)
        
    def run_llm_extraction(self, ambiguous_idx: list[int], locked_idx: set[int]) -> list[int]:
        print("Using LLM to check data...")

        checked_idx: set[int] = set()
        n_chunks = len(self.mappers)

        for i in range(n_chunks):
            logger.info(f"Running chunk: {i + 1}")

            res = self.data_pipeline.extract_sensitive_with_llm(self.mappers[i], ambiguous_idx)
            checked_idx.update(res)

        checked_idx.update(locked_idx)
        final_words_found = [self.iw_pair[idx] for idx in sorted(checked_idx)]

        is_approved = self._human_approval(final_words_found)
        if is_approved:
            return sorted(checked_idx)
        else:
            return sorted(locked_idx)
    
    def _human_approval(self, sensitive_words: list[str]) -> bool:
        while True:
            user_question = input(
                f"\nThese are the words found:\n{sensitive_words}\n\nAre they all (Y/N)? "
            )

            if user_question.upper() == "Y":
                return True
            elif user_question.upper() == "N":
                return False
            else:
                print("⚠️ Invalid input. Please enter Y or N.")
