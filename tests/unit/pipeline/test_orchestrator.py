import importlib
import sys
import types
from unittest.mock import MagicMock

import pytest

from waveredact.pipeline.mapper import ChunkMapper


class FakeGlinerExtractor:
    def __init__(self, *args, **kwargs):
        pass


def _import_orchestrator(monkeypatch: pytest.MonkeyPatch):
    for name in [
        "waveredact.pipeline.orchestrator",
        "waveredact.pipeline.privacy_pipeline",
        "waveredact.pipeline.extractors.gliner_extractor",
    ]:
        sys.modules.pop(name, None)

    fake_gliner_module = types.ModuleType("waveredact.pipeline.extractors.gliner_extractor")
    fake_gliner_module.GlinerExtractor = FakeGlinerExtractor
    monkeypatch.setitem(sys.modules, "waveredact.pipeline.extractors.gliner_extractor", fake_gliner_module)

    privacy_module = importlib.import_module("waveredact.pipeline.privacy_pipeline")
    orchestrator_module = importlib.import_module("waveredact.pipeline.orchestrator")
    return privacy_module, orchestrator_module


class TestOrchestrator:
    def _build_pipeline(self, privacy_module, llm_extractor=None):
        class FakeExtractor:
            def extract(self, _text: str):
                return [(0, 4, 0.5), (5, 9, 0.95)]

        return privacy_module.DataPrivacyPipeline(
            simple_extractors=[FakeExtractor()],
            llm_extractor=llm_extractor,
        )

    def test_run_audio_chunks_returns_ordered_indices_without_llm(self, monkeypatch: pytest.MonkeyPatch):
        privacy_module, orchestrator_module = _import_orchestrator(monkeypatch)
        pipeline = self._build_pipeline(privacy_module, llm_extractor=None)
        orchestrator = orchestrator_module.Orchestrator(
            index_word_pair={0: "name", 1: "token"},
            mappers=[ChunkMapper({0: "name ", 1: "token"})],
            data_pipeline=pipeline,
            use_llm=False,
            interactive_mode=False,
        )

        assert orchestrator.run_audio_chunks() == [0, 1]

    def test_run_audio_chunks_uses_llm_when_configured(self, monkeypatch: pytest.MonkeyPatch):
        privacy_module, orchestrator_module = _import_orchestrator(monkeypatch)
        llm_model = MagicMock()

        llm_model.run_model.return_value = [0]
        
        test_chunk = {0: "name", 1: "token"}
        
        pipeline = self._build_pipeline(privacy_module, llm_extractor=llm_model)
        orchestrator = orchestrator_module.Orchestrator(
            index_word_pair=test_chunk,
            mappers=[ChunkMapper(test_chunk)],
            data_pipeline=pipeline,
            use_llm=True,
            interactive_mode=False,
        )

        assert orchestrator.run_audio_chunks() == [0]

        llm_model.run_model.assert_called_once_with(test_chunk, [0, 1])

    def test_run_audio_chunks_bypasses_llm_in_interactive_mode_when_missing(self, monkeypatch: pytest.MonkeyPatch):
        privacy_module, orchestrator_module = _import_orchestrator(monkeypatch)
        pipeline = self._build_pipeline(privacy_module, llm_extractor=None)
        orchestrator = orchestrator_module.Orchestrator(
            index_word_pair={0: "name", 1: "token"},
            mappers=[ChunkMapper({0: "name ", 1: "token"})],
            data_pipeline=pipeline,
            use_llm=False,
            interactive_mode=True,
            approval_callback=lambda _words: False,
        )

        assert orchestrator.run_audio_chunks() == [0, 1]
