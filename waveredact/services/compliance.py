import json
from datetime import datetime, timezone

class ComplianceManager:
    """
    Service responsible for generating compliance reports for the privacy pipeline.
    """
    def __init__(self):
        self.software_version = "2.0.0"

    def generate_report(self, results: list, output_path: str):
        """
        Generate a compliance JSON report.
        
        Params:
            results     - list of RedactResult objects
            output_path - file path where the report should be saved
        """
        if not results:
            return

        if len(results) == 1:
            res = results[0]
            audit_info = {
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "software_version": self.software_version,
                "original_file": res.filename,
                "censored_file": res.censored_path
            }
            redactions = res.redactions
        else:
            audit_info = {
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "software_version": self.software_version,
                "original_file": [res.filename for res in results],
                "censored_file": [res.censored_path for res in results]
            }
            redactions = [res.redactions for res in results]

        report = {
            "audit_info": audit_info,
            "redactions": redactions
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
