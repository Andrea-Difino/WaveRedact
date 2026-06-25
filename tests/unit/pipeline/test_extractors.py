import pytest
from unittest.mock import patch, MagicMock
from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor

MODULE_PATH = "waveredact.pipeline.extractors.gliner_extractor"


class TestGlinerExtractor:

    @patch(f"{MODULE_PATH}.GLiNER2")
    def test_init_loads_model_correctly(self, mock_gliner):
        mock_model_instance = MagicMock()
        mock_gliner.from_pretrained.return_value = mock_model_instance
        
        extractor = GlinerExtractor("fake", "fake", ["access_token"], 0.85)
        
        assert extractor.target_labels == ["access_token"]
        assert extractor.threshold == 0.85


    @patch(f"{MODULE_PATH}.GLiNER2")
    def test_extract_returns_correct_tuples_from_nested_dict(self, mock_gliner):
        mock_model_instance = MagicMock()
        mock_gliner.from_pretrained.return_value = mock_model_instance
        
        mock_model_instance.extract_entities.return_value = {
            "entities": {
                "access_token": [
                    {"text": "Bearer_12345", "start": 38, "end": 50}
                ],
                "email": [
                    {"text": "mario@email.com", "start": 14, "end": 29}
                ],
                "password": []
            }
        }
        
        extractor = GlinerExtractor("fake", "fake", ["access_token", "email", "password"], 0.8)
        text_input = "Mario l'email mario@email.com e token Bearer_12345"
        
        result = extractor.extract(text_input)

        assert result == [(14, 29), (38, 50)]


    @patch(f"{MODULE_PATH}.GLiNER2")
    def test_extract_handles_duplicates_safely(self, mock_gliner):
        mock_model_instance = MagicMock()
        mock_gliner.from_pretrained.return_value = mock_model_instance

        mock_model_instance.extract_entities.return_value = {
            "entities": {
                "secret": [
                    {"text": "12345", "start": 12, "end": 17}
                ],
                "password": [
                    {"text": "12345", "start": 12, "end": 17}
                ]
            }
        }
        
        extractor = GlinerExtractor("fake", "fake", ["secret", "password"], 0.8)
        text_input = "Il codice è 12345"
        
        result = extractor.extract(text_input)

        assert len(result) == 1
        assert result == [(12, 17)]
