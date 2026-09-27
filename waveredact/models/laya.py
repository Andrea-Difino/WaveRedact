from laya import Agent


class Laya:

    def __init__(self, agent: 'Agent') -> None:
        self.agent = agent

    def validate_entity(self, entity: str, entity_label: str, full_text: str) -> bool:

        state = {
            "audio_context": full_text,
            "extracted_entity": entity,
            "pii_category": entity_label
        }

        questions = {
            "pii_validation": {
                "type": "choice",
                "instructions" : f"Does the text '{entity}' represent a valid '{entity_label}' in this context?",
                "criteria": {
                    "true_positive": f"Yes, '{entity}' is a valid {entity_label}. NOTE: For this privacy task, ANY valid {entity_label} (even public places, generic dates, or common names) MUST be strictly considered sensitive data.",
                    "false_positive": f"No, '{entity}' is NOT a {entity_label}. It is just a generic word, a field name (e.g. 'City:'), a figure of speech, or an error."
                },
            }
        }

        result = self.agent.predict(state, questions)

        response = result["answers"]["pii_validation"]["choice"]

        return response == "true_positive"