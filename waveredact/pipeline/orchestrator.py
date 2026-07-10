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
        use_llm: bool = False,
        interactive_mode: bool = True
    ):  
        self.iw_pair = index_word_pair
        self.mappers = mappers
        self.data_pipeline = data_pipeline
        self.use_llm = use_llm
        self.interactive_mode = interactive_mode

    def run_audio_chunks(
        self
    ) -> list[int]:
        full_idx: set[int] = set()
        full_locked_idx: set[int] = set()
        
        chunk_ambiguous_list: list[list[int]] = []

        n_chunks = len(self.mappers)
        words_found: list[str] = []

        for i in range(n_chunks):
            print(f"Running chunk: {i + 1}")

            res, locked_res = self.data_pipeline.extract_sensitive_data(self.mappers[i])

            chunk_ambiguous = list(set(res) - set(locked_res))
            chunk_ambiguous_list.append(chunk_ambiguous)

            words_found.extend([self.iw_pair[idx] for idx in sorted(res)])
            full_idx.update(res)
            full_locked_idx.update(locked_res)

        ordered_idx = sorted(full_idx)

        if self.interactive_mode:
            is_approved = self._human_approval(words_found)
            
            if is_approved:
                return ordered_idx
            else:
                if self.data_pipeline.llm_extractors:
                    return self.run_llm_extraction(chunk_ambiguous_list, full_locked_idx)
                else:
                    logger.warning("You answered 'N', but no LLM is configured to refine the search.")
                    print("💡 Hint: Restart the pipeline adding the '--use-llm' flag for better precision.")
                    print("Proceeding with the current redaction list to ensure data safety.\n")
                    return ordered_idx
        else:
            if self.use_llm and self.data_pipeline.llm_extractors:
                logger.info("Automatic mode: Executing LLM to maximize security...")
                return self.run_llm_extraction(chunk_ambiguous_list, full_locked_idx)
            else:
                logger.info("Fast mode: LLM bypassed.\n")
                return ordered_idx
        
    def run_llm_extraction(self, chunk_ambiguous_list: list[list[int]], locked_idx: set[int]) -> list[int]:
        checked_idx: set[int] = set()
        n_chunks = len(self.mappers)

        for i in range(n_chunks):
            chunk_ambiguous = chunk_ambiguous_list[i]

            print(f"Running LLM for chunk: {i + 1}")
            res = self.data_pipeline.extract_sensitive_with_llm(self.mappers[i], chunk_ambiguous)
            checked_idx.update(res)

        checked_idx.update(locked_idx)
        final_words_found = [self.iw_pair[idx] for idx in sorted(checked_idx)]
        
        print(f"\n🧠 [LLM Final Results] Sensitive words identified:\n{final_words_found}")
        logger.info("Trusting LLM extraction. Proceeding with redaction...")
        
        return sorted(checked_idx)
    
    def _human_approval(self, sensitive_words: list[str]) -> bool:
        while True:
            user_question = input(
                f"\nThese are the words found:\n{sensitive_words}\n\nAre they all (Y/N)? "
            )

            if user_question.upper().strip() == "Y":
                return True
            elif user_question.upper().strip() == "N":
                return False
            else:
                print("⚠️ Invalid input. Please enter Y or N.")