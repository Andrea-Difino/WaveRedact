import json
import os
from unittest.mock import MagicMock
from waveredact.services.compliance import ComplianceManager
from waveredact.app import RedactResult

class TestComplianceManager:
    def test_generate_report_single_file(self, tmp_path):
        manager = ComplianceManager()
        
        result = RedactResult(
            filename="audio1.wav",
            censored_path="/path/to/censored/audio1_censored.wav",
            sensitive_words=["secret"],
            redactions=[
                {"start_sec": 1.0, "end_sec": 2.0, "entity_type": "email"}
            ]
        )
        
        output_file = tmp_path / "compliance.json"
        manager.generate_report([result], str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, "r") as f:
            data = json.load(f)
            
        assert data["audit_info"]["software_version"] == "2.0.0"
        assert data["audit_info"]["original_file"] == "audio1.wav"
        assert data["audit_info"]["censored_file"] == "/path/to/censored/audio1_censored.wav"
        assert "timestamp" in data["audit_info"]
        
        assert len(data["redactions"]) == 1
        assert data["redactions"][0]["entity_type"] == "email"
        assert data["redactions"][0]["start_sec"] == 1.0

    def test_generate_report_multiple_files(self, tmp_path):
        manager = ComplianceManager()
        
        results = [
            RedactResult(
                filename="audio1.wav",
                censored_path="/path/censored/1.wav",
                sensitive_words=["word1"],
                redactions=[{"start_sec": 1.0, "end_sec": 2.0, "entity_type": "email"}]
            ),
            RedactResult(
                filename="audio2.wav",
                censored_path="/path/censored/2.wav",
                sensitive_words=[],
                redactions=[]
            )
        ]
        
        output_file = tmp_path / "compliance_folder.json"
        manager.generate_report(results, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, "r") as f:
            data = json.load(f)
            
        assert data["audit_info"]["original_file"] == ["audio1.wav", "audio2.wav"]
        assert data["audit_info"]["censored_file"] == ["/path/censored/1.wav", "/path/censored/2.wav"]
        
        assert len(data["redactions"]) == 2
        assert len(data["redactions"][0]) == 1
        assert len(data["redactions"][1]) == 0

    def test_generate_report_empty_results(self, tmp_path):
        manager = ComplianceManager()
        output_file = tmp_path / "no_compliance.json"
        
        manager.generate_report([], str(output_file))
        
        assert not output_file.exists()
