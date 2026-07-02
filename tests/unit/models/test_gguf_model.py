import importlib
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open

import pytest


PROMPTS = {
    "maker": {
        "default": {
            "system_prompt": "system prompt",
            "user_prompt": "labels={labels} ambiguous={ambiguous} idx={idx_couples}",
        }
    }
}


def _import_gguf_model(monkeypatch: pytest.MonkeyPatch):
    for name in [
        "waveredact.models.gguf_model",
        "openai",
        "huggingface_hub",
        "dotenv",
        "yaml",
    ]:
        sys.modules.pop(name, None)

    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = object
    monkeypatch.setitem(sys.modules, "openai", fake_openai)

    fake_hf = types.ModuleType("huggingface_hub")
    fake_hf.hf_hub_download = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_hf)

    fake_dotenv = types.ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda: None
    monkeypatch.setitem(sys.modules, "dotenv", fake_dotenv)

    fake_yaml = types.ModuleType("yaml")
    fake_yaml.safe_load = lambda *_args, **_kwargs: PROMPTS
    monkeypatch.setitem(sys.modules, "yaml", fake_yaml)

    return importlib.import_module("waveredact.models.gguf_model")


class TestGGUFModel:
    def test_init_uses_existing_model_without_download(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        module = _import_gguf_model(monkeypatch)
        mock_client = MagicMock()
        monkeypatch.setattr(module, "OpenAI", MagicMock(return_value=mock_client))
        download_mock = MagicMock()
        monkeypatch.setattr(module, "hf_hub_download", download_mock)
        monkeypatch.setattr(module.os.path, "exists", lambda _path: True)
        monkeypatch.setattr("builtins.open", mock_open(read_data=json.dumps(PROMPTS)))

        model = module.GGUFModel("model.gguf", "repo/name", model_dir=str(tmp_path), server_port=9090)

        assert model.path == f"{tmp_path.resolve()}/model.gguf"
        assert model.sys_prompt == "system prompt"
        assert model.user_prompt.startswith("labels=")
        download_mock.assert_not_called()
        module.OpenAI.assert_called_once_with(base_url="http://localhost:9090/v1", api_key="locale")
        assert model.client == mock_client

    def test_init_downloads_missing_model(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        module = _import_gguf_model(monkeypatch)
        mock_client = MagicMock()
        monkeypatch.setattr(module, "OpenAI", MagicMock(return_value=mock_client))
        download_mock = MagicMock(return_value=str(tmp_path / "model.gguf"))
        monkeypatch.setattr(module, "hf_hub_download", download_mock)
        monkeypatch.setattr(module.os.path, "exists", lambda _path: False)
        monkeypatch.setenv("HF_TOKEN", "secret-token")
        monkeypatch.setattr("builtins.open", mock_open(read_data=json.dumps(PROMPTS)))

        module.GGUFModel("model.gguf", "repo/name", model_dir=str(tmp_path))

        download_mock.assert_called_once_with(
            repo_id="repo/name",
            filename="model.gguf",
            local_dir=str(tmp_path.resolve()),
            token="secret-token",
        )

    def test_init_downloads_missing_model_without_hf_token(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        module = _import_gguf_model(monkeypatch)
        mock_client = MagicMock()
        monkeypatch.setattr(module, "OpenAI", MagicMock(return_value=mock_client))
        download_mock = MagicMock(return_value=str(tmp_path / "model.gguf"))
        monkeypatch.setattr(module, "hf_hub_download", download_mock)
        monkeypatch.setattr(module.os.path, "exists", lambda _path: False)
        monkeypatch.delenv("HF_TOKEN", raising=False)
        monkeypatch.setattr("builtins.open", mock_open(read_data=json.dumps(PROMPTS)))

        module.GGUFModel("model.gguf", "repo/name", model_dir=str(tmp_path))

        download_mock.assert_called_once_with(
            repo_id="repo/name",
            filename="model.gguf",
            local_dir=str(tmp_path.resolve()),
            token=None,
        )

    def test_labels_property_round_trip(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        module = _import_gguf_model(monkeypatch)
        mock_client = MagicMock()
        monkeypatch.setattr(module, "OpenAI", MagicMock(return_value=mock_client))
        monkeypatch.setattr(module, "hf_hub_download", MagicMock())
        monkeypatch.setattr(module.os.path, "exists", lambda _path: True)
        monkeypatch.setattr("builtins.open", mock_open(read_data=json.dumps(PROMPTS)))

        model = module.GGUFModel("model.gguf", "repo/name", model_dir=str(tmp_path))
        assert model.labels == []

        model.labels = ["email", "phone_number"]
        assert model.labels == ["email", "phone_number"]

    def test_run_model_returns_final_indices(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        module = _import_gguf_model(monkeypatch)
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content='{"final_indices": [1, 3]}')
                )
            ]
        )
        mock_create = MagicMock(return_value=response)
        mock_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=mock_create)))
        monkeypatch.setattr(module, "OpenAI", MagicMock(return_value=mock_client))
        monkeypatch.setattr(module, "hf_hub_download", MagicMock())
        monkeypatch.setattr(module.os.path, "exists", lambda _path: True)
        monkeypatch.setattr("builtins.open", mock_open(read_data=json.dumps(PROMPTS)))

        model = module.GGUFModel("model.gguf", "repo/name", model_dir=str(tmp_path))
        model.labels = ["email"]

        result = model.run_model({0: "hello", 1: "world"}, [0])

        assert result == [1, 3]
        mock_create.assert_called_once()
        kwargs = mock_create.call_args.kwargs
        assert kwargs["model"] == "local-model"
        assert kwargs["temperature"] == 0.0
        assert kwargs["response_format"] == {"type": "json_object"}
        assert "Testo da analizzare" in kwargs["messages"][1]["content"]

    def test_run_model_returns_empty_list_on_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        module = _import_gguf_model(monkeypatch)
        mock_create = MagicMock(side_effect=RuntimeError("boom"))
        mock_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=mock_create)))
        monkeypatch.setattr(module, "OpenAI", MagicMock(return_value=mock_client))
        monkeypatch.setattr(module, "hf_hub_download", MagicMock())
        monkeypatch.setattr(module.os.path, "exists", lambda _path: True)
        monkeypatch.setattr("builtins.open", mock_open(read_data=json.dumps(PROMPTS)))

        model = module.GGUFModel("model.gguf", "repo/name", model_dir=str(tmp_path))

        assert model.run_model({0: "hello"}, None) == []
