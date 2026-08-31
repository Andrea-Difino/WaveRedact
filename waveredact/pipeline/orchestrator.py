import logging
from collections.abc import Callable

import rich.progress

from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
from waveredact.utils.console import console

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
        progress_callback   - Callback used to stream the process to the web application
    """

    def __init__(
        self,
        *,
        index_word_pair: dict[int, str],
        mappers: list[ChunkMapper],
        data_pipeline: DataPrivacyPipeline,
        use_llm: bool = False,
        interactive_mode: bool = True,
        progress_callback: Callable[[str, int], None] | None = None,
        approval_callback: Callable[[list[str]], bool] | None = None,
    ):
        self.iw_pair = index_word_pair
        self.mappers = mappers
        self.data_pipeline = data_pipeline
        self.use_llm = use_llm
        self.interactive_mode = interactive_mode
        self.progress_callback = progress_callback
        self.approval_callback = approval_callback

    def run_audio_chunks(self) -> dict[int, str]:
        """
        Use Regex and GLiNER to censor data for each chunk of the audios

        Return:
            dict mapping indices to their entity types
        """
        full_idx_labels: dict[int, str] = {}
        full_locked_idx: set[int] = set()

        chunk_ambiguous_list: list[list[int]] = []

        n_chunks = len(self.mappers)
        words_found: list[str] = []

        for i in rich.progress.track(range(n_chunks), description="Extracting sensitive data...", console=console):
            if self.progress_callback:
                percent = 40 + int((i / n_chunks) * 40)
                self.progress_callback(
                    f"Extracting sensitive data from chunk {i + 1}/{n_chunks}...",
                    percent,
                )

            res_labels, locked_res = self.data_pipeline.extract_sensitive_data(self.mappers[i])

            chunk_ambiguous = list(set(res_labels.keys()) - set(locked_res))
            chunk_ambiguous_list.append(chunk_ambiguous)

            words_found.extend([self.iw_pair[idx] for idx in sorted(res_labels.keys())])
            full_idx_labels.update(res_labels)
            full_locked_idx.update(locked_res)

        # we can still return full_idx_labels, maybe sort keys where we need them.
        ordered_idx = sorted(full_idx_labels.keys())

        if self.interactive_mode:
            if self.approval_callback:
                is_approved = self.approval_callback(words_found)
            else:
                is_approved = True

            if is_approved:
                return full_idx_labels
            else:
                if self.data_pipeline.llm_extractors:
                    return self.run_llm_extraction(
                        chunk_ambiguous_list, full_locked_idx, full_idx_labels
                    )
                else:
                    console.print("[warning]⚠️-You answered 'N', but no LLM is configured to refine the search.[/warning]")
                    console.print("[info]💡 Hint: Restart the pipeline adding the '--use-llm' flag for better precision.[/info]")
                    console.print("[warning]Proceeding with the current redaction list to ensure data safety.\n[/warning]")
                    return full_idx_labels
        else:
            if self.use_llm and self.data_pipeline.llm_extractors:
                console.print("[info]Automatic mode: Executing LLM to maximize security...[/info]")
                return self.run_llm_extraction(chunk_ambiguous_list, full_locked_idx, full_idx_labels)
            else:
                console.print("[info]Fast mode: LLM bypassed.\n[/info]")
                return full_idx_labels

    def run_llm_extraction(
        self, chunk_ambiguous_list: list[list[int]], locked_idx: set[int], initial_labels: dict[int, str]
    ) -> dict[int, str]:
        """
        Use LLM to check the answers given by the GLiNER model and find missed sensitive words

        Params:
            chunk_ambiguous_list    - list of the indices for each chunk that had a confidence score lower than 0.99 in the GLiNER step
            locked_idx              - set of the indices that must be censored because had a nearly 1.0 confidence score
            initial_labels          - initial dict mapping indices to their entity types found by simple extractors

        Return:
            dict of the final sensitive indices mapped to their entity types
        """
        checked_idx_labels: dict[int, str] = {}
        n_chunks = len(self.mappers)

        for i in rich.progress.track(range(n_chunks), description="Running LLM analysis...", console=console):
            chunk_ambiguous = chunk_ambiguous_list[i]

            if self.progress_callback:
                percent = 80 + int((i / n_chunks) * 10)
                self.progress_callback(
                    f"Running LLM analysis on chunk {i + 1}/{n_chunks}...", percent
                )
            res_labels = self.data_pipeline.extract_sensitive_with_llm(
                self.mappers[i], chunk_ambiguous
            )
            checked_idx_labels.update(res_labels)

        for idx in locked_idx:
            if idx in initial_labels:
                checked_idx_labels[idx] = initial_labels[idx]

        return checked_idx_labels


