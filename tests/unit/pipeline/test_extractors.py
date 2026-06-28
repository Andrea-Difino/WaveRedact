import pytest
from unittest.mock import patch, MagicMock
from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor

MODULE_PATH = "waveredact.pipeline.extractors.gliner_extractor"


class TestGlinerExtractor:

    def test_init_sets_attributes_correctly(self):
        """Verify that constructur save everything correctly"""

        mock_model = MagicMock()
        
        extractor = GlinerExtractor(
            model=mock_model,
            target_labels=["access_token"],
            threshold=0.85
        )

        assert extractor.model == mock_model
        assert extractor.target_labels == ["access_token"]
        assert extractor.threshold == 0.85


    def test_extract_returns_correct_tuples(self):
        """Verify coordinates extraction and the use include_spans=True."""
        mock_model = MagicMock()

        mock_model.extract_entities.return_value = {
            "entities": {
                "access_token": [
                    {"text": "Bearer_12345", "start": 38, "end": 50, "confidence": 0.90}
                ],
                "email": [
                    {"text": "mario@email.com", "start": 14, "end": 29, "confidence": 0.90}
                ],
                "password": []
            }
        }
        
        extractor = GlinerExtractor(
            model=mock_model, 
            target_labels=["access_token", "email", "password"], 
            threshold=0.8
        )
        
        text_input = "Mario l'email mario@email.com e token Bearer_12345"
        result = extractor.extract(text_input)

        mock_model.extract_entities.assert_called_once_with(
            text_input, 
            ["access_token", "email", "password"], 
            threshold=0.8,
            include_spans=True,
            include_confidence=True
        )

        assert result == [(14, 29, 0.0), (38, 50, 0.0)]


    def test_extract_handles_duplicates(self):

        mock_model = MagicMock()
        mock_model.extract_entities.return_value = {
            "entities": {
                "secret": [{"text": "12345", "start": 12, "end": 17, "confidence": 0.90}],
                "password": [{"text": "12345", "start": 12, "end": 17, "confidence": 0.90}]
            }
        }
        
        extractor = GlinerExtractor(mock_model, ["secret", "password"], 0.8)
        result = extractor.extract("Il codice è 12345")

        assert len(result) == 1
        assert result == [(12, 17, 0.0)]


    def test_extract_empty_results(self):
        """Verify sensibility in case of text without sensitive data"""
        mock_model = MagicMock()

        mock_model.extract_entities.return_value = {"entities": {}}
        
        extractor = GlinerExtractor(mock_model, ["email"], 0.8)
        result = extractor.extract("Testo completamente anonimo e pulito.")
        
        assert result == []
