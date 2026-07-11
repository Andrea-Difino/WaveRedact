from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s %(message)s"


class Orchestrator:
    """
        Use the DataPrivacyPipeline class to orchestrate all the programm. Handle the user_interaction and return the ids of the sensitive words.

        Attributes:
            index_word_pair     - Dict used to map each index to the corrisponding word
            mappers             - List of ChunkMapper. Every mapper contain important informations about each chunk
            data_pipeline       - Use the extractors to extract the sensitive ids from the sentences
            use_llm             - Parameter passed by command line used to activate or not the LLM step
            interactive_mode    - Parameter passed by command line used to activate or not the human interaction
    """

    def __init__(
        self,
        *,
        index_word_pair: Dict[int, str], 
        mappers: list[ChunkMapper],
        data_pipeline: DataPrivacyPipeline,
        use_llm: bool = False,
        interactive_mode: bool = True,
        progress_callback = None
    ):  
        self.iw_pair = index_word_pair
        self.mappers = mappers
        self.data_pipeline = data_pipeline
        self.use_llm = use_llm
        self.interactive_mode = interactive_mode
        self.progress_callback = progress_callback

    def run_audio_chunks(
        self
    ) -> list[int]:
        """
            Use Regex and GLiNER to censor data for each chunk of the audios

            Return:
                list of integers corresponding to the words to censor
        """
        full_idx: Set[int] = set()
        full_locked_idx: Set[int] = set()
        
        chunk_ambiguous_list: list[list[int]] = []

        n_chunks = len(self.mappers)
        words_found: list[str] = []

        for i in range(n_chunks):
            print(f"Running chunk: {i + 1}")
            if self.progress_callback:
                percent = 40 + int((i / n_chunks) * 40)
                self.progress_callback(f"Extracting sensitive data from chunk {i + 1}/{n_chunks}...", percent)

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
        
    def run_llm_extraction(
        self, 
        chunk_ambiguous_list: list[list[int]], 
        locked_idx: Set[int]
    ) -> list[int]:
        """
            Use LLM to check the answers given by the GLiNER model and find missed sensitive words

            Params:
                chunk_ambiguous_list    - list of the indices for each chunk that had a confidence score lower than 0.99 in the GLiNER step
                locked_idx              - set of the indices that must be censored because had a nearly 1.0 confidence score

            Return:
                list of the final sensitive indices
        """
        checked_idx: Set[int] = set()
        n_chunks = len(self.mappers)

        for i in range(n_chunks):
            chunk_ambiguous = chunk_ambiguous_list[i]

            print(f"Running LLM for chunk: {i + 1}")
            if self.progress_callback:
                percent = 80 + int((i / n_chunks) * 10)
                self.progress_callback(f"Running LLM analysis on chunk {i + 1}/{n_chunks}...", percent)
            res = self.data_pipeline.extract_sensitive_with_llm(self.mappers[i], chunk_ambiguous)
            checked_idx.update(res)

        checked_idx.update(locked_idx)
        final_words_found = [self.iw_pair[idx] for idx in sorted(checked_idx)]
        
        print(f"\n🧠 [LLM Final Results] Sensitive words identified:\n{final_words_found}")
        logger.info("Trusting LLM extraction. Proceeding with redaction...")
        
        return sorted(checked_idx)
    
    def _human_approval(self, sensitive_words: list[str]) -> bool:
        """
            Function used for human approval in the interactive_mode

            Params:
                sensitive_words - list of the sensitive words found until now

            Return:
                True if the user is satisfied and want to end the programm or continue to the next audio
                False if he is not satisfied and wants to use the LLM
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