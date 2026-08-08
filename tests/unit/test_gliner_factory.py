from unittest.mock import patch, MagicMock, mock_open
import os
import json
from waveredact.factories.gliner_factory import GlinerFactory

def test_gliner_factory_build_local():
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=["model.bin"]), \
         patch("waveredact.factories.gliner_factory.Path.exists", return_value=False), \
         patch("waveredact.factories.gliner_factory.GLiNER2") as mock_gliner_class:
         
        factory = GlinerFactory(target_labels=["PERSON"])
        model = factory.build()
        mock_gliner_class.from_pretrained.assert_called_once()
        assert model == mock_gliner_class.from_pretrained.return_value

def test_gliner_factory_build_download():
    with patch("os.path.exists", return_value=False), \
         patch("os.makedirs"), \
         patch("waveredact.factories.gliner_factory.Path.exists", return_value=False), \
         patch("waveredact.factories.gliner_factory.snapshot_download") as mock_download, \
         patch("waveredact.factories.gliner_factory.GLiNER2") as mock_gliner_class:
         
        factory = GlinerFactory(target_labels=["PERSON"])
        model = factory.build()
        mock_download.assert_called_once()
        mock_gliner_class.from_pretrained.assert_called_once()
        assert model == mock_gliner_class.from_pretrained.return_value

def test_gliner_factory_fix_tokenizer():
    mock_config = {"extra_special_tokens": ["token1", "token2"]}
    m_open = mock_open(read_data=json.dumps(mock_config))
    
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=["model.bin"]), \
         patch("waveredact.factories.gliner_factory.Path.exists", return_value=True), \
         patch("builtins.open", m_open), \
         patch("waveredact.factories.gliner_factory.GLiNER2") as mock_gliner_class:
         
        factory = GlinerFactory(target_labels=["PERSON"])
        factory.build()

        assert m_open.call_count >= 2
