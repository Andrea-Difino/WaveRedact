import importlib
import sys
import types
from unittest.mock import MagicMock

import pytest

from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.extractors.regex_extractor import RegexExtractor


class FakeGlinerExtractor:
    def __init__(self, *args, **kwargs):
        pass


def _import_privacy_pipeline(monkeypatch: pytest.MonkeyPatch):
    for name in [
        "waveredact.pipeline.privacy_pipeline",
        "waveredact.pipeline.extractors.gliner_extractor",
    ]:
        sys.modules.pop(name, None)

    fake_gliner_module = types.ModuleType("waveredact.pipeline.extractors.gliner_extractor")
    fake_gliner_module.GlinerExtractor = FakeGlinerExtractor
    monkeypatch.setitem(sys.modules, "waveredact.pipeline.extractors.gliner_extractor", fake_gliner_module)

    return importlib.import_module("waveredact.pipeline.privacy_pipeline")


class TestPrivacyPipeline:
    def test_extract_sensitive_data_combines_regex_and_gliner(self, monkeypatch: pytest.MonkeyPatch):
        module = _import_privacy_pipeline(monkeypatch)

        class FakeSimpleExtractor:
            def extract(self, _text: str):
                return [(0, 4, 0.5)]

        pipeline = module.DataPrivacyPipeline(
            simple_extractors=[RegexExtractor(), FakeSimpleExtractor()],
            llm_extractor=None,
        )

        mapper = ChunkMapper({0: "name ", 1: "foo@example.com ", 2: "12345"})
        total_idx, locked_idx = pipeline.extract_sensitive_data(mapper)

        assert total_idx == {0, 1, 2}
        assert locked_idx == {1, 2}

    def test_extract_sensitive_with_llm_returns_indices(self, monkeypatch: pytest.MonkeyPatch):
        module = _import_privacy_pipeline(monkeypatch)

        llm_model = MagicMock()
        llm_model.run_model.return_value = [0, 2]

        pipeline = module.DataPrivacyPipeline(
            simple_extractors=[MagicMock()],
            llm_extractor=llm_model,
        )

        mapper = ChunkMapper({0: "alpha", 1: "beta"})
        result = pipeline.extract_sensitive_with_llm(mapper, [1])

        assert result == {0, 2}
        llm_model.run_model.assert_called_once_with(mapper.chunk, [1])

    def test_extract_sensitive_with_llm_returns_empty_without_llm(self, monkeypatch: pytest.MonkeyPatch):
        module = _import_privacy_pipeline(monkeypatch)

        pipeline = module.DataPrivacyPipeline(simple_extractors=[MagicMock()], llm_extractor=None)

        mapper = ChunkMapper({0: "alpha", 1: "beta"})
        result = pipeline.extract_sensitive_with_llm(mapper, [1])

        assert result == set()
        assert pipeline.llm_extractors == []
